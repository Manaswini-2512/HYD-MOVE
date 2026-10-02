"""Route, stop, temporal, and accessibility analytics for GTFS service supply.

All counts describe scheduled GTFS records. They are not observed operations,
passenger accessibility, passenger demand, ridership, or usage.
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from src.analysis.gtfs_eda import build_route_analytics, build_stop_connectivity
from src.analysis.gtfs_network import (
    build_route_network_features,
    build_route_overlap,
    build_route_stop_edges,
)
from src.data.gtfs_etl import parse_gtfs_time


DEFAULT_SCORE_WEIGHTS = {
    "frequency": 0.35,
    "connectivity": 0.25,
    "service_span": 0.20,
    "stop_coverage": 0.20,
}
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday")
WEEKENDS = ("saturday", "sunday")


def _table(tables: Mapping[str, pd.DataFrame], name: str) -> pd.DataFrame:
    frame = tables.get(name)
    return frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame()


def _has(frame: pd.DataFrame, *columns: str) -> bool:
    return set(columns).issubset(frame.columns)


def _stable(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    present = [key for key in keys if key in frame.columns]
    return frame.sort_values(present, kind="stable", ignore_index=True) if present else frame


def _count_by(frame: pd.DataFrame, keys: list[str], column: str, name: str) -> pd.DataFrame:
    if not _has(frame, *keys, column):
        return pd.DataFrame(columns=keys + [name])
    valid = frame.dropna(subset=keys + [column]).drop_duplicates(keys + [column])
    return valid.groupby(keys, as_index=False, sort=True)[column].nunique().rename(columns={column: name})


def _departure_seconds(frame: pd.DataFrame) -> pd.Series:
    """Return departure seconds, using arrival only when departure is absent."""
    departure = pd.Series(np.nan, index=frame.index, dtype="float64")
    arrival = pd.Series(np.nan, index=frame.index, dtype="float64")
    if "departure_seconds" in frame:
        departure = pd.to_numeric(frame["departure_seconds"], errors="coerce")
    if "departure_time" in frame:
        departure = departure.fillna(frame["departure_time"].map(parse_gtfs_time))
    if "arrival_seconds" in frame:
        arrival = pd.to_numeric(frame["arrival_seconds"], errors="coerce")
    if "arrival_time" in frame:
        arrival = arrival.fillna(frame["arrival_time"].map(parse_gtfs_time))
    return departure.fillna(arrival)


def _normalized(series: pd.Series) -> pd.Series:
    """Scale non-missing nonnegative values by their maximum to [0, 1]."""
    values = pd.to_numeric(series, errors="coerce").where(lambda value: value >= 0)
    maximum = values.max(skipna=True)
    if pd.isna(maximum) or maximum == 0:
        return values.where(values.isna(), 0.0)
    return (values / maximum).clip(0, 1)


def _parse_calendar_date(value: object) -> pd.Timestamp:
    """Parse canonical timestamps or GTFS YYYYMMDD date values."""
    if pd.isna(value):
        return pd.NaT
    if isinstance(value, (pd.Timestamp,)):
        return value.normalize()
    text = str(value)
    date_format = "%Y%m%d" if text.isdigit() and len(text) == 8 else None
    return pd.to_datetime(text, format=date_format, errors="coerce").normalize()


def _route_calendar_metrics(tables: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Derive route-level scheduled service dates and mean templates per date."""
    trips, calendar = _table(tables, "trips"), _table(tables, "calendar")
    output_columns = ["feed_id", "route_id", "unique_scheduled_service_day_count", "trips_per_service_day"]
    if not _has(trips, "feed_id", "route_id", "trip_id", "service_id") or not _has(calendar, "feed_id", "service_id", "start_date", "end_date", *WEEKDAYS, "saturday", "sunday"):
        return pd.DataFrame(columns=output_columns)
    exceptions = _table(tables, "calendar_dates")
    if not exceptions.empty and not _has(exceptions, "feed_id", "service_id", "date", "exception_type"):
        route_keys = _table(tables, "routes")
        if not _has(route_keys, "feed_id", "route_id"):
            route_keys = trips[["feed_id", "route_id"]].dropna().drop_duplicates()
        return route_keys[["feed_id", "route_id"]].drop_duplicates().assign(
            unique_scheduled_service_day_count=pd.NA, trips_per_service_day=pd.NA
        )
    trip_counts = trips.dropna(subset=["feed_id", "route_id", "trip_id", "service_id"]).drop_duplicates(["feed_id", "trip_id"]).groupby(["feed_id", "route_id", "service_id"], as_index=False).agg(trips=("trip_id", "nunique"))
    calendar = calendar.drop_duplicates(["feed_id", "service_id"])
    service_dates: dict[tuple[object, object], set[pd.Timestamp]] = {}
    complete: dict[tuple[object, object], bool] = {}
    day_columns = (*WEEKDAYS, "saturday", "sunday")
    for row in calendar.to_dict("records"):
        key = (row["feed_id"], row["service_id"])
        start, end = _parse_calendar_date(row["start_date"]), _parse_calendar_date(row["end_date"])
        if pd.isna(start) or pd.isna(end) or end < start:
            service_dates[key], complete[key] = set(), False
            continue
        active_weekdays: set[int] = set()
        flags_complete = True
        for weekday, flag in enumerate(day_columns):
            value = pd.to_numeric(pd.Series([row.get(flag)]), errors="coerce").iloc[0]
            if pd.isna(value) or value not in (0, 1):
                flags_complete = False
            if pd.notna(value) and value == 1:
                active_weekdays.add(weekday)
        date_range = pd.date_range(start, end, freq="D")
        service_dates[key] = {date for date in date_range if date.weekday() in active_weekdays}
        complete[key] = flags_complete
    if not exceptions.empty and _has(exceptions, "feed_id", "service_id", "date", "exception_type"):
        for row in exceptions.to_dict("records"):
            key = (row["feed_id"], row["service_id"])
            if key not in service_dates:
                continue
            date = _parse_calendar_date(row["date"])
            exception_type = pd.to_numeric(pd.Series([row["exception_type"]]), errors="coerce").iloc[0]
            if pd.isna(date) or pd.isna(exception_type) or exception_type not in (1, 2):
                complete[key] = False
                continue
            if exception_type == 1:
                service_dates[key].add(date)
            elif exception_type == 2:
                service_dates[key].discard(date)

    rows: list[dict[str, object]] = []
    for (feed_id, route_id), route_services in trip_counts.groupby(["feed_id", "route_id"], sort=True):
        service_day_trip_counts: dict[pd.Timestamp, int] = {}
        derivable = True
        for service in route_services.itertuples(index=False):
            key = (service.feed_id, service.service_id)
            if key not in complete or not complete[key]:
                derivable = False
                break
            for date in service_dates[key]:
                service_day_trip_counts[date] = service_day_trip_counts.get(date, 0) + int(service.trips)
        day_count = len(service_day_trip_counts) if derivable else pd.NA
        trips_per_day = (sum(service_day_trip_counts.values()) / len(service_day_trip_counts)) if derivable and service_day_trip_counts else pd.NA
        rows.append({"feed_id": feed_id, "route_id": route_id, "unique_scheduled_service_day_count": day_count, "trips_per_service_day": trips_per_day})
    known = {(row["feed_id"], row["route_id"]) for row in rows}
    route_keys = trips[["feed_id", "route_id"]].dropna().drop_duplicates()
    routes = _table(tables, "routes")
    if _has(routes, "feed_id", "route_id"):
        route_keys = pd.concat([route_keys, routes[["feed_id", "route_id"]]], ignore_index=True).drop_duplicates()
    for route in route_keys.itertuples(index=False):
        if (route.feed_id, route.route_id) not in known:
            rows.append({"feed_id": route.feed_id, "route_id": route.route_id, "unique_scheduled_service_day_count": 0, "trips_per_service_day": pd.NA})
    return pd.DataFrame(rows, columns=output_columns)


def _routes_with_incomplete_weekday_calendar(
    tables: Mapping[str, pd.DataFrame],
) -> set[tuple[object, object]]:
    """Find routes whose linked trips lack complete recurring calendar flags."""
    trips, calendar = _table(tables, "trips"), _table(tables, "calendar")
    if not _has(trips, "feed_id", "route_id", "trip_id", "service_id"):
        return set()
    trip_services = trips[["feed_id", "route_id", "trip_id", "service_id"]].drop_duplicates()
    route_keys = list(zip(trip_services["feed_id"], trip_services["route_id"], strict=True))
    required = [*WEEKDAYS, *WEEKENDS]
    if not _has(calendar, "feed_id", "service_id", *required):
        return set(route_keys)
    flags = calendar[["feed_id", "service_id", *required]].drop_duplicates(["feed_id", "service_id"])
    valid_flags = flags[required].apply(pd.to_numeric, errors="coerce").isin([0, 1]).all(axis=1)
    valid_services = set(map(tuple, flags.loc[valid_flags, ["feed_id", "service_id"]].to_numpy()))
    return {
        (row.feed_id, row.route_id)
        for row in trip_services.itertuples(index=False)
        if pd.isna(row.service_id) or (row.feed_id, row.service_id) not in valid_services
    }


def build_route_service_profile(
    tables: Mapping[str, pd.DataFrame],
    route_overlap: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build feed-scoped route schedule intensity and topology features.

    Calendar dates are expanded from recurring weekday flags and inclusive date
    bounds; supplied exception dates are applied. Missing calendar details leave
    date-based metrics undefined.
    """
    routes = _table(tables, "routes")
    if not _has(routes, "feed_id", "route_id"):
        return pd.DataFrame(columns=["feed_id", "route_id"])
    # Phase 3A and 3B builders own established schedule and overlap semantics.
    eda = build_route_analytics(tables).rename(columns={"operator": "feed_id"})
    network = build_route_network_features(tables, route_overlap=route_overlap)
    reusable_network_fields = {
        "scheduled_segment_count",
        "mean_scheduled_stop_to_stop_minutes",
        "median_scheduled_stop_to_stop_minutes",
        "overlapping_route_count",
        "mean_overlapping_jaccard",
    }
    network_additions = network[[
        column for column in network.columns
        if column in {"feed_id", "route_id"} or column in reusable_network_fields
    ]]
    profile = eda.merge(
        network_additions,
        on=["feed_id", "route_id"], how="left", suffixes=("", "_network"), validate="one_to_one",
    )
    profile = profile.rename(columns={"trip_count": "scheduled_trip_count", "stop_count": "stop_count", "service_days": "active_service_weekday_count", "scheduled_service_intensity": "trips_per_active_service_weekday"})
    incomplete_calendar_routes = _routes_with_incomplete_weekday_calendar(tables)
    if incomplete_calendar_routes:
        incomplete_mask = [
            (feed_id, route_id) in incomplete_calendar_routes
            for feed_id, route_id in zip(profile["feed_id"], profile["route_id"], strict=True)
        ]
        profile.loc[incomplete_mask, ["active_service_weekday_count", "trips_per_active_service_weekday"]] = pd.NA

    trips = _table(tables, "trips")
    if _has(trips, "feed_id", "route_id", "service_id"):
        service_counts = _count_by(trips, ["feed_id", "route_id"], "service_id", "active_service_id_count")
        profile = profile.merge(service_counts, on=["feed_id", "route_id"], how="left", validate="one_to_one")
    else:
        profile["active_service_id_count"] = pd.NA

    stop_times = _table(tables, "stop_times")
    if _has(stop_times, "feed_id", "trip_id") and _has(trips, "feed_id", "trip_id", "route_id"):
        trip_route = trips[["feed_id", "trip_id", "route_id"]].dropna().drop_duplicates(["feed_id", "trip_id"])
        joined = stop_times.merge(trip_route, on=["feed_id", "trip_id"], how="inner", validate="many_to_one")
        joined["_departure_seconds"] = _departure_seconds(joined)
        departures = joined.dropna(subset=["_departure_seconds"])
        if "stop_sequence" in joined:
            known_sequence = departures["stop_sequence"].notna()
            identified = departures.loc[known_sequence].drop_duplicates(
                ["feed_id", "trip_id", "stop_sequence"]
            )
            unidentified = departures.loc[~known_sequence]
            departures = pd.concat([identified, unidentified], ignore_index=True)
        dep_counts = departures.groupby(["feed_id", "route_id"], as_index=False).size().rename(columns={"size": "scheduled_departure_count"})
        profile = profile.merge(dep_counts, on=["feed_id", "route_id"], how="left", validate="one_to_one")
        if "stop_sequence" in joined.columns:
            seq_counts = joined.dropna(subset=["stop_sequence"]).groupby(["feed_id", "route_id"], as_index=False)["stop_sequence"].nunique().rename(columns={"stop_sequence": "unique_stop_sequence_count"})
            profile = profile.merge(seq_counts, on=["feed_id", "route_id"], how="left", validate="one_to_one")
    else:
        profile["scheduled_departure_count"] = pd.NA
        profile["unique_stop_sequence_count"] = pd.NA
    for name in ("scheduled_departure_count", "unique_stop_sequence_count"):
        if name not in profile:
            profile[name] = pd.NA

    span_col = None
    for candidate in ("service_span_seconds",):
        if candidate in profile:
            span_col = candidate
    if span_col is None and {"first_departure_seconds", "last_arrival_seconds"}.issubset(profile.columns):
        profile["scheduled_service_span_seconds"] = (
            pd.to_numeric(profile["last_arrival_seconds"], errors="coerce")
            - pd.to_numeric(profile["first_departure_seconds"], errors="coerce")
        ).where(lambda values: values >= 0)
    else:
        profile["scheduled_service_span_seconds"] = profile[span_col] if span_col else pd.NA
    if "scheduled_service_span_seconds" not in profile:
        profile["scheduled_service_span_seconds"] = pd.NA
    calendar_metrics = _route_calendar_metrics(tables)
    if not calendar_metrics.empty:
        profile = profile.drop(columns=["unique_scheduled_service_day_count", "trips_per_service_day"], errors="ignore").merge(calendar_metrics, on=["feed_id", "route_id"], how="left", validate="one_to_one")
    else:
        profile["unique_scheduled_service_day_count"] = pd.NA
        profile["trips_per_service_day"] = pd.NA
    headways = _build_route_headways(tables)
    if not headways.empty:
        profile = profile.merge(headways, on=["feed_id", "route_id"], how="left", validate="one_to_one")
    else:
        profile["mean_scheduled_headway_seconds"] = pd.NA
        profile["maximum_scheduled_headway_seconds"] = pd.NA
    return _stable(profile, ["feed_id", "route_id"])


def _build_route_headways(tables: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Derive gaps between trip start times within each route and service ID."""
    trips, times = _table(tables, "trips"), _table(tables, "stop_times")
    keys = ["feed_id", "route_id"]
    if not _has(trips, "feed_id", "trip_id", "route_id", "service_id") or not _has(times, "feed_id", "trip_id", "stop_sequence"):
        return pd.DataFrame(columns=keys + ["mean_scheduled_headway_seconds", "maximum_scheduled_headway_seconds"])
    event_cols = [column for column in ("feed_id", "trip_id", "stop_sequence", "departure_seconds", "departure_time", "arrival_seconds", "arrival_time") if column in times]
    events = times[event_cols].merge(trips[["feed_id", "trip_id", "route_id", "service_id"]].dropna(subset=["feed_id", "trip_id", "route_id", "service_id"]).drop_duplicates(["feed_id", "trip_id"]), on=["feed_id", "trip_id"], how="inner", validate="many_to_one")
    events["_departure_seconds"] = _departure_seconds(events)
    events = events.dropna(subset=["_departure_seconds", "stop_sequence"])
    first = events.sort_values(["feed_id", "route_id", "service_id", "trip_id", "stop_sequence"], kind="stable").drop_duplicates(["feed_id", "trip_id"], keep="first")
    first = first.sort_values(["feed_id", "route_id", "service_id", "_departure_seconds", "trip_id"], kind="stable")
    first["_headway"] = first.groupby(["feed_id", "route_id", "service_id"], sort=False)["_departure_seconds"].diff()
    valid = first.loc[first["_headway"].gt(0)]
    if valid.empty:
        return pd.DataFrame(columns=keys + ["mean_scheduled_headway_seconds", "maximum_scheduled_headway_seconds"])
    return valid.groupby(keys, as_index=False, sort=True).agg(
        mean_scheduled_headway_seconds=("_headway", "mean"),
        maximum_scheduled_headway_seconds=("_headway", "max"),
    )


def build_stop_service_profile(tables: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Build stop-level scheduled service supply and transparent connectivity bands."""
    stops = _table(tables, "stops")
    if not _has(stops, "feed_id", "stop_id"):
        return pd.DataFrame(columns=["feed_id", "stop_id"])
    result = build_stop_connectivity(tables).rename(columns={"operator": "feed_id", "routes_per_stop": "routes_serving_stop", "trips_per_stop": "scheduled_trips_serving_stop"})
    route_stops = _table(tables, "route_stops")
    if _has(route_stops, "feed_id", "stop_id", "route_id"):
        edges = route_stops.dropna(subset=["feed_id", "stop_id", "route_id"])
        degrees = edges.groupby(["feed_id", "stop_id"])["route_id"].nunique()
        result["service_connectivity_category"] = [
            "isolated" if pd.isna(degrees.get((feed, stop))) or degrees.get((feed, stop)) == 0
            else "low" if degrees.get((feed, stop)) <= 2
            else "medium" if degrees.get((feed, stop)) <= 10
            else "high"
            for feed, stop in zip(result["feed_id"], result["stop_id"], strict=True)
        ]
    else:
        result["service_connectivity_category"] = pd.NA

    trips, times = _table(tables, "trips"), _table(tables, "stop_times")
    if _has(trips, "feed_id", "trip_id", "service_id") and _has(times, "feed_id", "trip_id", "stop_id"):
        trip_info = trips[["feed_id", "trip_id", "service_id"]].dropna().drop_duplicates(["feed_id", "trip_id"])
        events = times.merge(trip_info, on=["feed_id", "trip_id"], how="inner", validate="many_to_one")
        services = _count_by(events, ["feed_id", "stop_id"], "service_id", "active_service_id_count")
        result = result.merge(services, on=["feed_id", "stop_id"], how="left", validate="one_to_one")
        timed_events = events.copy()
        timed_events["_departure_seconds"] = _departure_seconds(timed_events)
        timed_events = timed_events.dropna(subset=["_departure_seconds"])
        result["scheduled_departure_count"] = timed_events.groupby(["feed_id", "stop_id"]).size().reindex(pd.MultiIndex.from_frame(result[["feed_id", "stop_id"]])).to_numpy()
        result["scheduled_departure_count"] = result["scheduled_departure_count"].fillna(0).astype("Int64")
    else:
        result["active_service_id_count"] = pd.NA
        result["scheduled_departure_count"] = pd.NA

    calendar, trips = _table(tables, "calendar"), _table(tables, "trips")
    if _has(calendar, "feed_id", "service_id") and _has(trips, "feed_id", "trip_id", "service_id") and _has(times, "feed_id", "trip_id", "stop_id"):
        service_columns = [column for column in (*WEEKDAYS, *WEEKENDS) if column in calendar.columns]
        service_flags = calendar[["feed_id", "service_id", *service_columns]].drop_duplicates(["feed_id", "service_id"])
        event_services = times.merge(trips[["feed_id", "trip_id", "service_id"]].drop_duplicates(["feed_id", "trip_id"]), on=["feed_id", "trip_id"], how="inner", validate="many_to_one").merge(service_flags, on=["feed_id", "service_id"], how="left", validate="many_to_one")
        event_services["_departure_seconds"] = _departure_seconds(event_services)
        for label, days in (("weekday", WEEKDAYS), ("weekend", WEEKENDS)):
            output_column = f"scheduled_{label}_service_count"
            if not set(days).issubset(event_services.columns):
                result[output_column] = pd.NA
                continue
            flag_values = event_services[list(days)].apply(pd.to_numeric, errors="coerce")
            known_flags = flag_values.isin([0, 1]).all(axis=1)
            active_flags = flag_values.eq(1).any(axis=1)
            eligible = known_flags & active_flags & event_services["_departure_seconds"].notna()
            counts = event_services.loc[eligible].groupby(["feed_id", "stop_id"]).size().rename(output_column).reset_index()
            result = result.merge(counts, on=["feed_id", "stop_id"], how="left", validate="one_to_one")
            result[output_column] = result[output_column].fillna(0).astype("Int64")
            incomplete_stops = set(
                map(
                    tuple,
                    event_services.loc[~known_flags, ["feed_id", "stop_id"]]
                    .dropna()
                    .drop_duplicates()
                    .to_numpy(),
                )
            )
            incomplete_mask = [
                (feed_id, stop_id) in incomplete_stops
                for feed_id, stop_id in zip(result["feed_id"], result["stop_id"], strict=True)
            ]
            result.loc[incomplete_mask, output_column] = pd.NA
    for column in ("scheduled_weekday_service_count", "scheduled_weekend_service_count"):
        if column not in result:
            result[column] = pd.NA
    return _stable(result, ["feed_id", "stop_id"])


def build_temporal_service_profile(tables: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Count scheduled stop departures by feed, route, and extended service-day hour."""
    times, trips = _table(tables, "stop_times"), _table(tables, "trips")
    if not _has(times, "feed_id", "trip_id") or not _has(trips, "feed_id", "trip_id", "route_id"):
        return pd.DataFrame(columns=["feed_id", "route_id", "service_day_hour", "scheduled_departure_count"])
    joined = times.merge(trips[["feed_id", "trip_id", "route_id"]].drop_duplicates(["feed_id", "trip_id"]), on=["feed_id", "trip_id"], how="inner", validate="many_to_one")
    if not ({"departure_time", "departure_seconds", "arrival_time", "arrival_seconds"} & set(joined.columns)):
        return pd.DataFrame(columns=["feed_id", "route_id", "service_day_hour", "scheduled_departure_count"])
    seconds = _departure_seconds(joined)
    joined["service_day_hour"] = (seconds // 3600).astype("Int64")
    joined = joined.dropna(subset=["service_day_hour"])
    profile = joined.groupby(["feed_id", "route_id", "service_day_hour"], as_index=False, sort=True).size().rename(columns={"size": "scheduled_departure_count"})
    profile["clock_hour"] = profile["service_day_hour"] % 24
    profile["service_day_offset"] = profile["service_day_hour"] // 24
    return _stable(profile, ["feed_id", "route_id", "service_day_hour"])


def build_accessibility_score(
    route_profile: pd.DataFrame,
    weights: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    """Calculate a normalized GTFS service accessibility score by route.

    Each nonnegative component is scaled by its maximum within the dataset.
    Missing components are omitted per row and remaining weights renormalized.
    """
    configured = dict(DEFAULT_SCORE_WEIGHTS if weights is None else weights)
    if set(configured) != set(DEFAULT_SCORE_WEIGHTS) or any(not np.isfinite(v) or v < 0 for v in configured.values()) or sum(configured.values()) <= 0:
        raise ValueError("weights must define four nonnegative components with positive total")
    frame = route_profile.copy()
    fields = {
        "frequency": "scheduled_trip_count",
        "connectivity": "overlapping_route_count",
        "service_span": "scheduled_service_span_seconds",
        "stop_coverage": "stop_count",
    }
    component_names = {key: f"normalized_{key}" for key in fields}
    for component, source in fields.items():
        frame[component_names[component]] = _normalized(frame[source]) if source in frame else np.nan
    weight_total = sum(configured.values())
    frame["gtfs_service_accessibility_score"] = np.nan
    for idx, row in frame.iterrows():
        available = [
            (component, row[component_names[component]])
            for component in fields
            if configured[component] > 0 and pd.notna(row[component_names[component]])
        ]
        denom = sum(configured[component] for component, _ in available)
        if denom > 0:
            frame.at[idx, "gtfs_service_accessibility_score"] = sum(configured[c] * value for c, value in available) / denom
    frame.attrs["score_weights"] = {key: value / weight_total for key, value in configured.items()}
    return _stable(frame, ["feed_id", "route_id"])


def build_service_gap_flags(route_profile: pd.DataFrame) -> pd.DataFrame:
    """Flag explicitly schedule-based sparse frequency, span, and connectivity."""
    result = route_profile.copy()
    if "trips_per_active_service_weekday" in result:
        result["low_scheduled_frequency"] = pd.to_numeric(result["trips_per_active_service_weekday"], errors="coerce").lt(1).where(result["trips_per_active_service_weekday"].notna())
    else:
        result["low_scheduled_frequency"] = pd.NA
    if "maximum_scheduled_headway_seconds" in result:
        result["large_scheduled_headway"] = pd.to_numeric(result["maximum_scheduled_headway_seconds"], errors="coerce").gt(3600).where(result["maximum_scheduled_headway_seconds"].notna())
    else:
        result["large_scheduled_headway"] = pd.NA
    if "scheduled_service_span_seconds" in result:
        result["limited_scheduled_service_span"] = pd.to_numeric(result["scheduled_service_span_seconds"], errors="coerce").lt(6 * 3600).where(result["scheduled_service_span_seconds"].notna())
    else:
        result["limited_scheduled_service_span"] = pd.NA
    if "overlapping_route_count" in result:
        result["limited_route_connectivity"] = pd.to_numeric(result["overlapping_route_count"], errors="coerce").eq(0).where(result["overlapping_route_count"].notna())
    else:
        result["limited_route_connectivity"] = pd.NA
    return result


def build_feed_service_summary(route_profile: pd.DataFrame, stop_profile: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive feed summaries with no cross-feed ranking."""
    if "feed_id" not in route_profile:
        return pd.DataFrame(columns=["feed_id", "route_count"])
    stop_counts = (
        stop_profile.groupby("feed_id")["stop_id"].nunique().to_dict()
        if _has(stop_profile, "feed_id", "stop_id")
        else {}
    )
    rows: list[dict[str, object]] = []
    for feed_id, group in route_profile.groupby("feed_id", sort=True):
        row: dict[str, object] = {
            "feed_id": feed_id,
            "route_count": group["route_id"].nunique() if "route_id" in group else pd.NA,
            "stop_count": stop_counts.get(feed_id, pd.NA),
        }
        if "scheduled_trip_count" in group:
            row["scheduled_trip_count"] = pd.to_numeric(
                group["scheduled_trip_count"], errors="coerce"
            ).sum(min_count=1)
        else:
            row["scheduled_trip_count"] = pd.NA
        if "scheduled_service_span_seconds" in group:
            row["mean_scheduled_service_span_seconds"] = pd.to_numeric(
                group["scheduled_service_span_seconds"], errors="coerce"
            ).mean()
        else:
            row["mean_scheduled_service_span_seconds"] = pd.NA
        rows.append(row)
    return _stable(pd.DataFrame(rows), ["feed_id"])


def build_service_quality_report(tables: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Report absent tables/columns, excluded rows, and calendar limitations."""
    requirements = {
        "routes": ("feed_id", "route_id"),
        "trips": ("feed_id", "trip_id", "route_id", "service_id"),
        "stops": ("feed_id", "stop_id"),
        "stop_times": ("feed_id", "trip_id", "stop_id", "stop_sequence", "departure_time", "arrival_time", "departure_seconds", "arrival_seconds"),
        "calendar": ("feed_id", "service_id", "start_date", "end_date", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"),
        "route_stops": ("feed_id", "route_id", "stop_id"),
        "route_service_summary": ("feed_id", "route_id", "first_departure_seconds", "last_arrival_seconds"),
    }
    primary_keys = {
        "routes": ("feed_id", "route_id"),
        "trips": ("feed_id", "trip_id"),
        "stops": ("feed_id", "stop_id"),
        "stop_times": ("feed_id", "trip_id", "stop_id"),
        "calendar": ("feed_id", "service_id"),
        "route_stops": ("feed_id", "route_id", "stop_id"),
        "route_service_summary": ("feed_id", "route_id"),
    }
    rows = []
    for table_name, expected in requirements.items():
        frame = _table(tables, table_name)
        missing = [column for column in expected if column not in frame]
        present = [column for column in expected if column in frame]
        keys = primary_keys[table_name]
        present_keys = [column for column in keys if column in frame]
        excluded = (
            len(frame)
            if len(frame) and len(present_keys) != len(keys)
            else int(frame[present_keys].isna().any(axis=1).sum())
            if present_keys
            else 0
        )
        null_values = int(frame[present].isna().any(axis=1).sum()) if present else 0
        rows.append({"table": table_name, "row_count": len(frame), "missing_fields": ", ".join(missing), "excluded_records": excluded, "rows_with_any_null_value": null_values, "note": "Table absent" if table_name not in tables else "Missing required fields" if missing else "Available"})
    calendar_dates = _table(tables, "calendar_dates")
    exception_fields = ("feed_id", "service_id", "date", "exception_type")
    missing_exception_fields = (
        [field for field in exception_fields if field not in calendar_dates]
        if "calendar_dates" in tables
        else []
    )
    exception_note = (
        "Absent; service exception dates are not applied"
        if "calendar_dates" not in tables
        else "Missing required fields"
        if missing_exception_fields
        else "Exception dates supplied"
    )
    exception_keys = ("feed_id", "service_id", "date")
    present_exception_keys = [column for column in exception_keys if column in calendar_dates]
    exception_excluded = (
        len(calendar_dates)
        if len(calendar_dates) and len(present_exception_keys) != len(exception_keys)
        else int(calendar_dates[present_exception_keys].isna().any(axis=1).sum())
        if present_exception_keys
        else 0
    )
    exception_nulls = int(calendar_dates[list(calendar_dates.columns)].isna().any(axis=1).sum()) if not calendar_dates.empty else 0
    rows.append({"table": "calendar_dates", "row_count": len(calendar_dates), "missing_fields": ", ".join(missing_exception_fields), "excluded_records": exception_excluded, "rows_with_any_null_value": exception_nulls, "note": exception_note})
    rows.append({"table": "service_day_semantics", "row_count": 0, "missing_fields": "", "excluded_records": 0, "rows_with_any_null_value": 0, "note": "Unique scheduled dates expand recurring weekday flags over calendar start/end bounds and apply supplied calendar_dates exceptions. Missing bounds or unmatched service IDs leave date metrics undefined. Zero denominators yield missing rates. Headways use positive gaps between trip start times within each feed/route/service ID; gaps above one hour are flagged."})
    return pd.DataFrame(rows)


def build_service_accessibility_analytics(
    tables: Mapping[str, pd.DataFrame],
    weights: Mapping[str, float] | None = None,
) -> dict[str, pd.DataFrame]:
    """Build reusable schedule-supply profiles and transparent quality outputs."""
    stops = build_stop_service_profile(tables)
    edges = build_route_stop_edges(tables)
    route_catalog = _table(tables, "routes")
    if not _has(route_catalog, "feed_id", "route_id"):
        route_catalog = None
    overlap = build_route_overlap(edges, route_catalog)
    routes = build_route_service_profile(tables, route_overlap=overlap)
    if not overlap.empty:
        shared_stops = pd.concat(
            [
                overlap[["feed_id", "route_id_a", "shared_stop_count"]].rename(columns={"route_id_a": "route_id"}),
                overlap[["feed_id", "route_id_b", "shared_stop_count"]].rename(columns={"route_id_b": "route_id"}),
            ],
            ignore_index=True,
        ).groupby(["feed_id", "route_id"], as_index=False, sort=True)["shared_stop_count"].sum()
        routes = routes.merge(shared_stops, on=["feed_id", "route_id"], how="left", validate="one_to_one")
    else:
        routes["shared_stop_count"] = 0 if "route_id" in routes else pd.NA
    if "overlapping_route_count" not in routes:
        routes["overlapping_route_count"] = pd.NA
    if "mean_overlapping_jaccard" not in routes:
        routes["mean_overlapping_jaccard"] = pd.NA
    routes["shared_stop_count"] = routes["shared_stop_count"].fillna(0).astype("Int64")
    routes["connectivity_degree"] = routes["overlapping_route_count"]
    routes["unique_connected_route_count"] = routes["overlapping_route_count"]
    temporal = build_temporal_service_profile(tables)
    if not temporal.empty:
        hours = temporal.groupby(["feed_id", "route_id"], as_index=False).agg(
            service_start_hour=("service_day_hour", "min"), service_end_hour=("service_day_hour", "max"),
            active_scheduled_duration_hours=("service_day_hour", lambda values: float(values.max() - values.min())),
            scheduled_service_intensity_peak=("scheduled_departure_count", "max"))
        routes = routes.merge(hours, on=["feed_id", "route_id"], how="left", validate="one_to_one")
    else:
        for column in ("service_start_hour", "service_end_hour", "active_scheduled_duration_hours", "scheduled_service_intensity_peak"):
            routes[column] = pd.NA
    routes = build_accessibility_score(routes, weights)
    gaps = build_service_gap_flags(routes)
    return {
        "route_service_profile": _stable(routes, ["feed_id", "route_id"]),
        "stop_service_profile": stops,
        "route_overlap": overlap,
        "temporal_service_profile": temporal,
        "feed_service_summary": build_feed_service_summary(routes, stops),
        "quality_report": build_service_quality_report(tables),
        "service_gap_flags": gaps,
    }
