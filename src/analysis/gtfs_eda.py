"""Descriptive analytics for feed-scoped, schedule-only GTFS Parquet tables."""

from pathlib import Path
from typing import Mapping

import pandas as pd

from src.data.gtfs_etl import parse_gtfs_time


WEEKDAY_COLUMNS = (
    ("monday", "Monday"),
    ("tuesday", "Tuesday"),
    ("wednesday", "Wednesday"),
    ("thursday", "Thursday"),
    ("friday", "Friday"),
    ("saturday", "Saturday"),
    ("sunday", "Sunday"),
)

_EMPTY_ROUTE_COLUMNS = [
    "operator",
    "route_id",
    "trip_count",
    "stop_count",
    "service_days",
    "scheduled_service_intensity",
    "first_departure_seconds",
    "last_arrival_seconds",
]
_EMPTY_STOP_COLUMNS = [
    "operator",
    "stop_id",
    "routes_per_stop",
    "trips_per_stop",
    "first_service_seconds",
    "last_service_seconds",
]
_EMPTY_HOURLY_COLUMNS = [
    "operator",
    "service_day_hour",
    "clock_hour",
    "service_day_offset",
    "scheduled_departure_count",
]


def load_processed_tables(
    directory: str | Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Load the available processed GTFS Parquet tables without fixed paths.

    When ``directory`` is omitted, the repository's ``data/processed/gtfs``
    directory is resolved relative to this module.
    """
    source_directory = (
        Path(directory)
        if directory is not None
        else Path(__file__).resolve().parents[2] / "data" / "processed" / "gtfs"
    )
    if not source_directory.is_dir():
        raise FileNotFoundError(f"Processed GTFS directory does not exist: {source_directory}")
    return {
        path.stem: pd.read_parquet(path)
        for path in sorted(source_directory.glob("*.parquet"))
    }


def _table(tables: Mapping[str, pd.DataFrame], name: str) -> pd.DataFrame:
    value = tables.get(name)
    return value.copy() if isinstance(value, pd.DataFrame) else pd.DataFrame()


def _operators(tables: Mapping[str, pd.DataFrame]) -> list[str]:
    values: set[str] = set()
    for table in tables.values():
        if "feed_id" in table.columns:
            values.update(table["feed_id"].dropna().astype(str).unique())
    return sorted(values)


def _operator_rows(table: pd.DataFrame, operator: str) -> pd.DataFrame:
    if "feed_id" not in table.columns:
        return table.iloc[0:0]
    return table.loc[table["feed_id"].astype("string").eq(operator)]


def _unique_count(table: pd.DataFrame, operator: str, column: str) -> int:
    rows = _operator_rows(table, operator)
    return int(rows[column].nunique()) if column in rows.columns else 0


def _has_weekday_flag(calendar: pd.DataFrame, column: str) -> pd.Series:
    if column not in calendar.columns:
        return pd.Series(False, index=calendar.index)
    return pd.to_numeric(calendar[column], errors="coerce").eq(1)


def _calendar_trip_tables(
    tables: Mapping[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return weekday-level and route/weekday trip counts from calendar flags."""
    trips = _table(tables, "trips")
    calendar = _table(tables, "calendar")
    weekday_columns = [
        (column, label)
        for column, label in WEEKDAY_COLUMNS
        if column in calendar.columns
    ]
    weekday_fields = [
        "operator",
        "weekday",
        "weekday_order",
        "scheduled_trip_count",
        "active_services",
    ]
    route_day_fields = ["operator", "route_id", "weekday", "scheduled_trip_count"]
    if (
        not weekday_columns
        or not {"feed_id", "service_id"}.issubset(calendar.columns)
        or not {"feed_id", "service_id", "trip_id", "route_id"}.issubset(trips.columns)
    ):
        return pd.DataFrame(columns=weekday_fields), pd.DataFrame(columns=route_day_fields)

    trip_services = trips[
        ["feed_id", "service_id", "trip_id", "route_id"]
    ].dropna(subset=["feed_id", "service_id", "trip_id", "route_id"])
    trip_services = trip_services.drop_duplicates(["feed_id", "trip_id"])
    weekday_rows: list[dict[str, object]] = []
    route_day_frames: list[pd.DataFrame] = []

    for weekday_order, (column, weekday) in enumerate(weekday_columns):
        active = calendar.loc[
            _has_weekday_flag(calendar, column), ["feed_id", "service_id"]
        ].dropna().drop_duplicates()
        matched = trip_services.merge(
            active,
            on=["feed_id", "service_id"],
            how="inner",
            validate="many_to_one",
        )
        route_counts = (
            matched.groupby(["feed_id", "route_id"], as_index=False)
            .agg(scheduled_trip_count=("trip_id", "nunique"))
            .rename(columns={"feed_id": "operator"})
        )
        route_counts["weekday"] = weekday
        route_day_frames.append(route_counts[route_day_fields])

        trip_counts = matched.groupby("feed_id")["trip_id"].nunique()
        active_service_counts = active.groupby("feed_id")["service_id"].nunique()
        for operator in sorted(set(calendar["feed_id"].dropna().astype(str))):
            weekday_rows.append(
                {
                    "operator": operator,
                    "weekday": weekday,
                    "weekday_order": weekday_order,
                    "scheduled_trip_count": int(trip_counts.get(operator, 0)),
                    "active_services": int(active_service_counts.get(operator, 0)),
                }
            )

    weekday_table = pd.DataFrame(weekday_rows, columns=weekday_fields)
    route_day_table = (
        pd.concat(route_day_frames, ignore_index=True)
        if route_day_frames
        else pd.DataFrame(columns=route_day_fields)
    )
    return weekday_table, route_day_table


def build_network_summary(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Summarize feed-scoped network size and recurring calendar coverage.

    Counts describe GTFS entities and scheduled records. Calendar dates are
    published service bounds, not proof that service operated on every date.
    """
    fields = [
        "operator",
        "routes",
        "stops",
        "trips",
        "stop_times",
        "calendar_services",
        "active_weekday_count",
        "active_weekdays",
        "service_start",
        "service_end",
    ]
    if not _operators(tables):
        return pd.DataFrame(columns=fields)

    routes = _table(tables, "routes")
    stops = _table(tables, "stops")
    trips = _table(tables, "trips")
    stop_times = _table(tables, "stop_times")
    calendar = _table(tables, "calendar")
    rows: list[dict[str, object]] = []
    for operator in _operators(tables):
        operator_calendar = _operator_rows(calendar, operator)
        active_weekdays = [
            label
            for column, label in WEEKDAY_COLUMNS
            if column in operator_calendar.columns
            and _has_weekday_flag(operator_calendar, column).any()
        ]
        start = (
            operator_calendar["start_date"].min()
            if "start_date" in operator_calendar.columns
            else pd.NaT
        )
        end = (
            operator_calendar["end_date"].max()
            if "end_date" in operator_calendar.columns
            else pd.NaT
        )
        rows.append(
            {
                "operator": operator,
                "routes": _unique_count(routes, operator, "route_id"),
                "stops": _unique_count(stops, operator, "stop_id"),
                "trips": _unique_count(trips, operator, "trip_id"),
                "stop_times": len(_operator_rows(stop_times, operator)),
                "calendar_services": _unique_count(
                    calendar, operator, "service_id"
                ),
                "active_weekday_count": len(active_weekdays),
                "active_weekdays": ", ".join(active_weekdays),
                "service_start": start,
                "service_end": end,
            }
        )
    return pd.DataFrame(rows, columns=fields)


def build_route_analytics(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build route-level schedule counts, connectivity, and calendar intensity.

    ``scheduled_service_intensity`` is the mean number of scheduled trip rows
    on weekdays when a route has service, derived from trips and calendar flags.
    It is not an observed vehicle count or passenger measure.
    """
    routes = _table(tables, "routes")
    if not {"feed_id", "route_id"}.issubset(routes.columns):
        return pd.DataFrame(columns=_EMPTY_ROUTE_COLUMNS)

    result = routes.copy().rename(columns={"feed_id": "operator"})
    trips = _table(tables, "trips")
    if {"feed_id", "route_id", "trip_id"}.issubset(trips.columns):
        trip_counts = trips.groupby(["feed_id", "route_id"])["trip_id"].nunique()
        result["trip_count"] = [
            int(trip_counts.get((operator, route_id), 0))
            for operator, route_id in zip(
                result["operator"], result["route_id"], strict=True
            )
        ]
    else:
        result["trip_count"] = pd.NA

    route_stops = _table(tables, "route_stops")
    if {"feed_id", "route_id", "stop_id"}.issubset(route_stops.columns):
        stop_counts = route_stops.groupby(["feed_id", "route_id"])["stop_id"].nunique()
        result["stop_count"] = [
            int(stop_counts.get((operator, route_id), 0))
            for operator, route_id in zip(
                result["operator"], result["route_id"], strict=True
            )
        ]
    else:
        summary = _table(tables, "route_service_summary")
        if {"feed_id", "route_id", "unique_stop_count"}.issubset(summary.columns):
            stop_counts = summary.set_index(["feed_id", "route_id"])[
                "unique_stop_count"
            ]
            result["stop_count"] = [
                int(stop_counts.get((operator, route_id), 0))
                for operator, route_id in zip(
                    result["operator"], result["route_id"], strict=True
                )
            ]
        else:
            result["stop_count"] = pd.NA

    _, route_weekday_counts = _calendar_trip_tables(tables)
    if route_weekday_counts.empty:
        result["service_days"] = pd.NA
        result["scheduled_service_intensity"] = pd.NA
    else:
        intensity_rows: list[dict[str, object]] = []
        for (operator, route_id), group in route_weekday_counts.groupby(
            ["operator", "route_id"], sort=False
        ):
            positive = group.loc[group["scheduled_trip_count"].gt(0), "scheduled_trip_count"]
            intensity_rows.append(
                {
                    "operator": operator,
                    "route_id": route_id,
                    "service_days": int(positive.size),
                    "scheduled_service_intensity": float(positive.mean())
                    if not positive.empty
                    else 0.0,
                }
            )
        intensity = pd.DataFrame(intensity_rows)
        result = result.merge(
            intensity,
            on=["operator", "route_id"],
            how="left",
            validate="one_to_one",
        )
        result["service_days"] = result["service_days"].fillna(0).astype("Int64")
        result["scheduled_service_intensity"] = result[
            "scheduled_service_intensity"
        ].fillna(0.0)

    calendar = _table(tables, "route_service_summary")
    time_columns = [
        column
        for column in ("first_departure_seconds", "last_arrival_seconds")
        if column in calendar.columns
    ]
    if {"feed_id", "route_id"}.issubset(calendar.columns) and time_columns:
        result = result.merge(
            calendar[["feed_id", "route_id", *time_columns]].rename(
                columns={"feed_id": "operator"}
            ),
            on=["operator", "route_id"],
            how="left",
            validate="one_to_one",
        )
    for column in ("first_departure_seconds", "last_arrival_seconds"):
        if column not in result.columns:
            result[column] = pd.NA

    if "route_short_name" in result.columns or "route_long_name" in result.columns:
        short_name = (
            result["route_short_name"].astype("string").str.strip()
            if "route_short_name" in result.columns
            else pd.Series(pd.NA, index=result.index, dtype="string")
        )
        long_name = (
            result["route_long_name"].astype("string").str.strip()
            if "route_long_name" in result.columns
            else pd.Series(pd.NA, index=result.index, dtype="string")
        )
        short_name = short_name.mask(short_name.eq(""), pd.NA)
        long_name = long_name.mask(long_name.eq(""), pd.NA)
        names = short_name.fillna(long_name)
        both = short_name.notna() & long_name.notna() & short_name.ne(long_name)
        names.loc[both] = short_name.loc[both] + " | " + long_name.loc[both]
        result["route_name"] = names

    preferred = [
        "operator",
        "route_id",
        "source_route_id",
        "route_name",
        "route_short_name",
        "route_long_name",
        "route_type",
        "trip_count",
        "stop_count",
        "service_days",
        "scheduled_service_intensity",
        "first_departure_seconds",
        "last_arrival_seconds",
    ]
    columns = [column for column in preferred if column in result.columns]
    return result.loc[:, columns].sort_values(
        ["operator", "route_id"], kind="stable", ignore_index=True
    )


def build_route_statistics(route_analytics: pd.DataFrame) -> pd.DataFrame:
    """Summarize route-level schedule distributions by operator."""
    fields = [
        "operator",
        "metric",
        "route_count",
        "mean",
        "median",
        "standard_deviation",
        "minimum",
        "25th_percentile",
        "75th_percentile",
        "maximum",
    ]
    records: list[dict[str, object]] = []
    metrics = (
        "trip_count",
        "stop_count",
        "scheduled_service_intensity",
    )
    if not {"operator", *metrics}.issubset(route_analytics.columns):
        return pd.DataFrame(columns=fields)
    for operator, operator_routes in route_analytics.groupby("operator", sort=True):
        for metric in metrics:
            values = pd.to_numeric(operator_routes[metric], errors="coerce").dropna()
            if values.empty:
                continue
            records.append(
                {
                    "operator": operator,
                    "metric": metric,
                    "route_count": int(values.size),
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "standard_deviation": float(values.std()),
                    "minimum": float(values.min()),
                    "25th_percentile": float(values.quantile(0.25)),
                    "75th_percentile": float(values.quantile(0.75)),
                    "maximum": float(values.max()),
                }
            )
    return pd.DataFrame(records, columns=fields)


def build_stop_connectivity(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Calculate routes-per-stop and scheduled trips-per-stop metrics."""
    stops = _table(tables, "stops")
    if not {"feed_id", "stop_id"}.issubset(stops.columns):
        return pd.DataFrame(columns=_EMPTY_STOP_COLUMNS)
    result = stops.copy().rename(columns={"feed_id": "operator"})

    route_stops = _table(tables, "route_stops")
    if {"feed_id", "stop_id", "route_id"}.issubset(route_stops.columns):
        aggregations: dict[str, tuple[str, str]] = {"routes_per_stop": ("route_id", "nunique")}
        if "trip_count" in route_stops.columns:
            aggregations["trips_per_stop"] = ("trip_count", "sum")
        connectivity = route_stops.groupby(
            ["feed_id", "stop_id"], as_index=False
        ).agg(**aggregations).rename(columns={"feed_id": "operator"})
        result = result.merge(
            connectivity,
            on=["operator", "stop_id"],
            how="left",
            validate="one_to_one",
        )
    else:
        summary = _table(tables, "stop_service_summary")
        if {"feed_id", "stop_id"}.issubset(summary.columns):
            rename = {"feed_id": "operator", "route_count": "routes_per_stop", "trip_count": "trips_per_stop"}
            summary = summary.rename(columns=rename)
            keep = [
                column
                for column in (
                    "operator",
                    "stop_id",
                    "routes_per_stop",
                    "trips_per_stop",
                    "first_service_seconds",
                    "last_service_seconds",
                )
                if column in summary.columns
            ]
            result = result.merge(
                summary[keep],
                on=["operator", "stop_id"],
                how="left",
                validate="one_to_one",
            )

    summary = _table(tables, "stop_service_summary")
    time_columns = [
        column
        for column in ("first_service_seconds", "last_service_seconds")
        if column in summary.columns
    ]
    if {"feed_id", "stop_id"}.issubset(summary.columns) and time_columns:
        summary_times = summary[["feed_id", "stop_id", *time_columns]].rename(
            columns={"feed_id": "operator"}
        )
        for column in time_columns:
            if column in result.columns:
                summary_times = summary_times.drop(columns=column)
        result = result.merge(
            summary_times,
            on=["operator", "stop_id"],
            how="left",
            validate="one_to_one",
        )

    for column in ("routes_per_stop", "trips_per_stop"):
        if column not in result.columns:
            result[column] = pd.NA
        else:
            result[column] = result[column].fillna(0).astype("Int64")
    for column in ("first_service_seconds", "last_service_seconds"):
        if column not in result.columns:
            result[column] = pd.NA

    preferred = [
        "operator",
        "stop_id",
        "source_stop_id",
        "stop_name",
        "routes_per_stop",
        "trips_per_stop",
        "first_service_seconds",
        "last_service_seconds",
    ]
    columns = [column for column in preferred if column in result.columns]
    return result.loc[:, columns].sort_values(
        ["operator", "stop_id"], kind="stable", ignore_index=True
    )


def top_connected_stops(
    stop_connectivity: pd.DataFrame,
    top_n: int = 10,
    metric: str = "routes_per_stop",
) -> pd.DataFrame:
    """Return the most-connected or highest scheduled-service stops.

    ``metric`` may be ``routes_per_stop`` or ``trips_per_stop``; results are
    not passenger-volume rankings.
    """
    if top_n < 0:
        raise ValueError("top_n must be non-negative")
    if metric not in {"routes_per_stop", "trips_per_stop"}:
        raise ValueError("metric must be 'routes_per_stop' or 'trips_per_stop'")
    if metric not in stop_connectivity.columns:
        return stop_connectivity.iloc[0:0].copy()
    eligible = stop_connectivity.loc[
        pd.to_numeric(stop_connectivity[metric], errors="coerce").gt(0)
    ]
    sort_columns = [metric]
    ascending = [False]
    tie_breakers = [
        column
        for column in ("trips_per_stop", "routes_per_stop", "operator", "stop_id")
        if column in eligible.columns and column != metric
    ]
    sort_columns.extend(tie_breakers)
    ascending.extend(
        [column not in {"trips_per_stop", "routes_per_stop"} for column in tie_breakers]
    )
    return eligible.sort_values(
        sort_columns, ascending=ascending, kind="stable"
    ).head(top_n).reset_index(drop=True)


def build_weekday_service(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Count scheduled trip rows active under each recurring weekday flag.

    These are calendar-pattern counts. They do not account for date exceptions
    (absent from the current feeds) or prove that a trip operated.
    """
    weekday_table, _ = _calendar_trip_tables(tables)
    return weekday_table


def _parse_time_column(values: pd.Series) -> pd.Series:
    text = values.astype("string").str.strip()
    present_values = text.loc[text.notna() & text.ne("")].drop_duplicates()
    parsed = {value: parse_gtfs_time(str(value)) for value in present_values}
    return text.map(parsed).astype("Int64")


def _scheduled_seconds(stop_times: pd.DataFrame) -> pd.Series:
    """Choose scheduled departure seconds, falling back to arrival when blank."""
    seconds = pd.Series(pd.NA, index=stop_times.index, dtype="Int64")
    for numeric_column, text_column in (
        ("departure_seconds", "departure_time"),
        ("arrival_seconds", "arrival_time"),
    ):
        if numeric_column in stop_times.columns:
            raw = stop_times[numeric_column]
            converted = pd.to_numeric(raw, errors="coerce")
            invalid = raw.notna() & converted.isna()
            if invalid.any():
                raise ValueError(f"Invalid numeric GTFS time values in {numeric_column}")
            negative = converted.notna() & converted.lt(0)
            if negative.any():
                raise ValueError(f"Negative GTFS time values in {numeric_column}")
            seconds = seconds.fillna(converted.astype("Int64"))
        if text_column in stop_times.columns:
            parsed = _parse_time_column(stop_times[text_column])
            seconds = seconds.fillna(parsed)
    return seconds


def build_hourly_service(
    stop_times: pd.DataFrame,
) -> pd.DataFrame:
    """Count scheduled stop departures by service-day and wall-clock hour.

    GTFS times beyond 24:00 are retained as ``service_day_hour`` values. The
    separate ``clock_hour`` wraps to 0-23 and ``service_day_offset`` records
    how many days after the service-day start the event occurs. If departure
    time is blank, arrival time is used for that stop event.
    """
    if stop_times.empty:
        return pd.DataFrame(columns=_EMPTY_HOURLY_COLUMNS)
    seconds = _scheduled_seconds(stop_times)
    valid = seconds.notna()
    if not valid.any() or "feed_id" not in stop_times.columns:
        return pd.DataFrame(columns=_EMPTY_HOURLY_COLUMNS)
    service_day_hour = seconds.loc[valid].floordiv(3600).astype("int64")
    events = pd.DataFrame(
        {
            "operator": stop_times.loc[valid, "feed_id"].astype("string"),
            "service_day_hour": service_day_hour,
            "clock_hour": service_day_hour.mod(24),
            "service_day_offset": service_day_hour.floordiv(24),
        }
    )
    result = (
        events.groupby(
            ["operator", "service_day_hour", "clock_hour", "service_day_offset"],
            as_index=False,
            sort=True,
        )
        .size()
        .rename(columns={"size": "scheduled_departure_count"})
    )
    return result[_EMPTY_HOURLY_COLUMNS]


def build_peak_offpeak_service(
    hourly_service: pd.DataFrame,
    peak_hour_ranges: tuple[tuple[int, int], ...] = ((7, 10), (16, 19)),
) -> pd.DataFrame:
    """Aggregate scheduled service into defined peak and off-peak clock hours.

    Ranges are half-open wall-clock hours, so the defaults mean 07:00-09:59
    and 16:00-18:59. They are analytical conventions, not feed-published peaks.
    """
    fields = ["operator", "period", "scheduled_departure_count"]
    if hourly_service.empty:
        return pd.DataFrame(columns=fields)
    for start, end in peak_hour_ranges:
        if not 0 <= start < end <= 24:
            raise ValueError("peak hour ranges must satisfy 0 <= start < end <= 24")
    result = hourly_service[["operator", "clock_hour", "scheduled_departure_count"]].copy()
    clock_hours = pd.to_numeric(result["clock_hour"], errors="raise")
    is_peak = pd.Series(False, index=result.index)
    for start, end in peak_hour_ranges:
        is_peak |= clock_hours.ge(start) & clock_hours.lt(end)
    result["period"] = is_peak.map({True: "defined_peak", False: "off_peak"})
    return (
        result.groupby(["operator", "period"], as_index=False)
        .agg(scheduled_departure_count=("scheduled_departure_count", "sum"))
        [fields]
    )


def build_operator_comparison(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Compare feed-level network counts and per-route schedule averages."""
    network = build_network_summary(tables)
    fields = [
        "operator",
        "routes",
        "stops",
        "trips",
        "stop_times",
        "average_trips_per_route",
        "average_stops_per_route",
    ]
    if network.empty:
        return pd.DataFrame(columns=fields)
    route_analytics = build_route_analytics(tables)
    averages = (
        route_analytics.groupby("operator", as_index=False)
        .agg(
            average_trips_per_route=("trip_count", "mean"),
            average_stops_per_route=("stop_count", "mean"),
        )
        if not route_analytics.empty
        else pd.DataFrame(columns=["operator", "average_trips_per_route", "average_stops_per_route"])
    )
    comparison = network.merge(averages, on="operator", how="left", validate="one_to_one")
    return comparison[fields]


def build_eda_tables(
    tables: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build all reusable GTFS EDA tables from processed Parquet tables."""
    routes = build_route_analytics(tables)
    stops = build_stop_connectivity(tables)
    hourly = build_hourly_service(_table(tables, "stop_times"))
    return {
        "network_summary": build_network_summary(tables),
        "routes": routes,
        "route_statistics": build_route_statistics(routes),
        "stop_connectivity": stops,
        "hourly_service": hourly,
        "weekday_service": build_weekday_service(tables),
        "peak_offpeak_service": build_peak_offpeak_service(hourly),
        "operator_comparison": build_operator_comparison(tables),
    }