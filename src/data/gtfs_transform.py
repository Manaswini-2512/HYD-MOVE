"""Schedule-derived GTFS summaries; no passenger-demand measures are inferred."""

import pandas as pd

from src.data.ingestion import GTFSFeed


def _table(feed: GTFSFeed, name: str) -> pd.DataFrame:
    return feed.tables.get(name, pd.DataFrame()).copy()


def _route_stop_rows(feed: GTFSFeed) -> pd.DataFrame:
    stop_times = _table(feed, "stop_times")
    trips = _table(feed, "trips")
    required_stop_columns = {"trip_id", "stop_id", "stop_sequence"}
    if not required_stop_columns.issubset(stop_times.columns):
        return pd.DataFrame(columns=["route_id", "trip_id", "stop_id", "stop_sequence"])
    if not {"trip_id", "route_id"}.issubset(trips.columns):
        return pd.DataFrame(columns=["route_id", "trip_id", "stop_id", "stop_sequence"])
    route_trips = trips[["trip_id", "route_id"]].drop_duplicates("trip_id")
    rows = stop_times.merge(route_trips, on="trip_id", how="inner")
    rows["stop_sequence"] = pd.to_numeric(rows["stop_sequence"], errors="coerce")
    return rows


def build_route_summary(feed: GTFSFeed) -> pd.DataFrame:
    """Summarize route metadata and scheduled trip/stop counts."""
    routes = _table(feed, "routes")
    if "route_id" not in routes.columns:
        routes = pd.DataFrame(columns=["route_id"])

    trips = _table(feed, "trips")
    if {"route_id", "trip_id"}.issubset(trips.columns):
        trip_counts = trips.groupby("route_id", dropna=False)["trip_id"].nunique()
        routes["scheduled_trip_count"] = (
            routes["route_id"].map(trip_counts).fillna(0).astype(int)
        )
    else:
        routes["scheduled_trip_count"] = 0

    relationships = build_route_stop_relationships(feed)
    stop_counts = relationships.groupby("route_id")["stop_id"].nunique()
    routes["distinct_stop_count"] = (
        routes["route_id"].map(stop_counts).fillna(0).astype(int)
    )
    return routes


def build_stop_summary(feed: GTFSFeed) -> pd.DataFrame:
    """Summarize stop metadata and scheduled visits by route and trip."""
    stops = _table(feed, "stops")
    if "stop_id" not in stops.columns:
        stops = pd.DataFrame(columns=["stop_id"])
    rows = _route_stop_rows(feed)
    if rows.empty:
        stops["scheduled_visit_count"] = 0
        stops["scheduled_trip_count"] = 0
        stops["route_count"] = 0
        return stops

    counts = rows.groupby("stop_id").agg(
        scheduled_visit_count=("trip_id", "size"),
        scheduled_trip_count=("trip_id", "nunique"),
        route_count=("route_id", "nunique"),
    )
    return stops.merge(counts, how="left", left_on="stop_id", right_index=True).fillna(
        {"scheduled_visit_count": 0, "scheduled_trip_count": 0, "route_count": 0}
    )


def build_trip_summary(feed: GTFSFeed) -> pd.DataFrame:
    """Summarize each scheduled trip and its first/last stops and times."""
    trips = _table(feed, "trips")
    stop_times = _table(feed, "stop_times")
    if "trip_id" not in trips.columns:
        return pd.DataFrame(
            columns=["trip_id", "scheduled_stop_count", "first_stop_id", "last_stop_id"]
        )
    if not {"trip_id", "stop_id", "stop_sequence"}.issubset(stop_times.columns):
        trips["scheduled_stop_count"] = 0
        trips["first_stop_id"] = pd.NA
        trips["last_stop_id"] = pd.NA
        return trips

    ordered = stop_times.copy()
    ordered["_sequence"] = pd.to_numeric(ordered["stop_sequence"], errors="coerce")
    ordered = ordered.sort_values(["trip_id", "_sequence"], kind="stable")
    summary = ordered.groupby("trip_id", as_index=False).agg(
        scheduled_stop_count=("stop_id", "size")
    )
    first = ordered.drop_duplicates("trip_id", keep="first").set_index("trip_id")
    last = ordered.drop_duplicates("trip_id", keep="last").set_index("trip_id")
    summary["first_stop_id"] = summary["trip_id"].map(first["stop_id"])
    summary["last_stop_id"] = summary["trip_id"].map(last["stop_id"])
    for output_column, time_columns, source in (
        ("first_scheduled_time", ("arrival_time", "departure_time"), first),
        ("last_scheduled_time", ("departure_time", "arrival_time"), last),
    ):
        available = [column for column in time_columns if column in source.columns]
        if available:
            times = source[available[0]].astype("string")
            if len(available) == 2:
                times = times.mask(times.str.strip().eq(""), source[available[1]])
            summary[output_column] = summary["trip_id"].map(times)

    return trips.merge(summary, on="trip_id", how="left", validate="one_to_one")


def build_service_frequency(feed: GTFSFeed) -> pd.DataFrame:
    """Summarize scheduled trip templates and optional GTFS headway periods."""
    trips = _table(feed, "trips")
    output_columns = [
        "route_id",
        "service_id",
        "scheduled_trip_count",
        "frequency_period_count",
        "mean_headway_seconds",
    ]
    if not {"route_id", "service_id", "trip_id"}.issubset(trips.columns):
        return pd.DataFrame(columns=output_columns)

    summary = trips.groupby(["route_id", "service_id"], as_index=False).agg(
        scheduled_trip_count=("trip_id", "nunique")
    )
    frequencies = _table(feed, "frequencies")
    if {"trip_id", "headway_secs"}.issubset(frequencies.columns):
        trip_services = trips[["trip_id", "route_id", "service_id"]].drop_duplicates(
            "trip_id"
        )
        frequency_rows = frequencies.merge(trip_services, on="trip_id", how="inner")
        frequency_rows["headway_secs"] = pd.to_numeric(
            frequency_rows["headway_secs"], errors="coerce"
        )
        frequency_summary = frequency_rows.groupby(
            ["route_id", "service_id"], as_index=False
        ).agg(
            frequency_period_count=("trip_id", "size"),
            mean_headway_seconds=("headway_secs", "mean"),
        )
        summary = summary.merge(
            frequency_summary, on=["route_id", "service_id"], how="left"
        )
    else:
        summary["frequency_period_count"] = 0
        summary["mean_headway_seconds"] = pd.NA
    summary["frequency_period_count"] = summary["frequency_period_count"].fillna(0).astype(int)
    return summary[output_columns]


def build_route_stop_relationships(feed: GTFSFeed) -> pd.DataFrame:
    """Summarize which scheduled trips serve each route-stop pair."""
    rows = _route_stop_rows(feed)
    if rows.empty:
        return pd.DataFrame(
            columns=[
                "route_id",
                "stop_id",
                "scheduled_trip_count",
                "min_stop_sequence",
                "max_stop_sequence",
            ]
        )
    return rows.groupby(["route_id", "stop_id"], as_index=False).agg(
        scheduled_trip_count=("trip_id", "nunique"),
        min_stop_sequence=("stop_sequence", "min"),
        max_stop_sequence=("stop_sequence", "max"),
    )


def build_analytics_tables(feed: GTFSFeed) -> dict[str, pd.DataFrame]:
    """Build schedule-derived summary tables from an ingested GTFS feed."""
    return {
        "route_summary": build_route_summary(feed),
        "stop_summary": build_stop_summary(feed),
        "trip_summary": build_trip_summary(feed),
        "service_frequency": build_service_frequency(feed),
        "route_stop_relationships": build_route_stop_relationships(feed),
    }