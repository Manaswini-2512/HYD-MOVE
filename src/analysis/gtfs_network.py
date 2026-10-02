"""Feed-scoped route-stop network and scheduled-service temporal analytics."""

from collections import Counter, defaultdict
from itertools import combinations
from math import ceil
from pathlib import Path
from typing import Mapping

import networkx as nx
import pandas as pd

from src.analysis.gtfs_eda import (
    build_hourly_service,
    build_route_analytics,
    build_weekday_service,
)


_EDGE_COLUMNS = ["feed_id", "route_id", "stop_id"]
_OVERLAP_COLUMNS = [
    "feed_id",
    "route_id_a",
    "route_id_b",
    "shared_stop_count",
    "union_stop_count",
    "jaccard_similarity",
]
_WINDOW_COLUMNS = [
    "feed_id",
    "route_id",
    "first_departure_seconds",
    "last_arrival_seconds",
    "service_span_seconds",
]
_STOP_TIME_COLUMNS = [
    "feed_id",
    "route_id",
    "scheduled_segment_count",
    "mean_scheduled_stop_to_stop_minutes",
    "median_scheduled_stop_to_stop_minutes",
]


def _table(tables: Mapping[str, pd.DataFrame], name: str) -> pd.DataFrame:
    value = tables.get(name)
    return value.copy() if isinstance(value, pd.DataFrame) else pd.DataFrame()


def _feed_ids(tables: Mapping[str, pd.DataFrame]) -> list[str]:
    feeds: set[str] = set()
    for table in tables.values():
        if "feed_id" in table.columns:
            feeds.update(table["feed_id"].dropna().astype(str).unique())
    return sorted(feeds)


def build_route_stop_edges(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return one feed-scoped row for each scheduled route-stop relationship.

    The canonical ``route_stops`` table is preferred. If it is unavailable,
    relationships are reconstructed by joining ``stop_times`` to ``trips`` on
    both ``feed_id`` and ``trip_id``. Required identifiers are never joined
    across feeds.
    """
    source = _table(tables, "route_stops")
    if set(_EDGE_COLUMNS).issubset(source.columns):
        if source[_EDGE_COLUMNS].isna().any(axis=None):
            raise ValueError("route_stops contains a missing feed, route, or stop ID")
        if source.duplicated(_EDGE_COLUMNS).any():
            raise ValueError("route_stops contains duplicate feed/route/stop keys")
        columns = [
            column
            for column in (
                "feed_id",
                "route_id",
                "stop_id",
                "source_route_id",
                "source_stop_id",
                "stop_sequence",
                "trip_count",
                "service_count",
            )
            if column in source.columns
        ]
        return source[columns].sort_values(
            _EDGE_COLUMNS, kind="stable", ignore_index=True
        )

    trips = _table(tables, "trips")
    stop_times = _table(tables, "stop_times")
    trip_keys = {"feed_id", "trip_id", "route_id"}
    stop_keys = {"feed_id", "trip_id", "stop_id"}
    if not trip_keys.issubset(trips.columns) or not stop_keys.issubset(
        stop_times.columns
    ):
        return pd.DataFrame(columns=_EDGE_COLUMNS)

    trip_columns = [
        column
        for column in ("feed_id", "trip_id", "route_id", "service_id")
        if column in trips.columns
    ]
    stop_columns = [
        column
        for column in (
            "feed_id",
            "trip_id",
            "stop_id",
            "source_stop_id",
            "stop_sequence",
        )
        if column in stop_times.columns
    ]
    relationships = stop_times[stop_columns].merge(
        trips[trip_columns],
        on=["feed_id", "trip_id"],
        how="inner",
        validate="many_to_one",
    )
    if relationships[_EDGE_COLUMNS].isna().any(axis=None):
        raise ValueError("GTFS relationships contain a missing feed, route, or stop ID")
    aggregations: dict[str, tuple[str, str]] = {
        "trip_count": ("trip_id", "nunique")
    }
    if "service_id" in relationships.columns:
        aggregations["service_count"] = ("service_id", "nunique")
    if "stop_sequence" in relationships.columns:
        aggregations["stop_sequence"] = ("stop_sequence", "min")
    if "source_stop_id" in relationships.columns:
        aggregations["source_stop_id"] = ("source_stop_id", "first")
    edges = relationships.groupby(
        _EDGE_COLUMNS, as_index=False, sort=True, dropna=False
    ).agg(**aggregations)
    route_source_ids = trips[
        [column for column in ("feed_id", "route_id", "source_route_id") if column in trips]
    ]
    if "source_route_id" in route_source_ids.columns:
        route_source_ids = route_source_ids.drop_duplicates(["feed_id", "route_id"])
        edges = edges.merge(
            route_source_ids,
            on=["feed_id", "route_id"],
            how="left",
            validate="many_to_one",
        )
    columns = [
        column
        for column in (
            "feed_id",
            "route_id",
            "stop_id",
            "source_route_id",
            "source_stop_id",
            "stop_sequence",
            "trip_count",
            "service_count",
        )
        if column in edges.columns
    ]
    return edges[columns].sort_values(
        _EDGE_COLUMNS, kind="stable", ignore_index=True
    )


def build_bipartite_graphs(
    tables: Mapping[str, pd.DataFrame],
) -> dict[str, nx.Graph]:
    """Build one NetworkX route-stop bipartite graph per feed.

    Nodes are typed tuples ``(partition, feed_id, source_id)``. Published
    routes/stops with no edge are retained as degree-zero nodes when their
    source tables are supplied.
    """
    edges = build_route_stop_edges(tables)
    routes = _table(tables, "routes")
    stops = _table(tables, "stops")
    graphs: dict[str, nx.Graph] = {}
    for feed_id in _feed_ids({"edges": edges, "routes": routes, "stops": stops}):
        graph = nx.Graph(feed_id=feed_id, bipartite=True)
        feed_routes = routes.loc[
            routes.get("feed_id", pd.Series(dtype="string")).astype("string").eq(feed_id)
        ]
        for row in feed_routes.itertuples(index=False):
            route_id = getattr(row, "route_id")
            node = ("route", feed_id, route_id)
            attributes: dict[str, object] = {
                "bipartite": 0,
                "node_type": "route",
                "feed_id": feed_id,
                "route_id": route_id,
            }
            for column in ("source_route_id", "route_short_name", "route_long_name"):
                if column in feed_routes.columns:
                    value = getattr(row, column)
                    if not pd.isna(value):
                        attributes[column] = value
            graph.add_node(node, **attributes)

        feed_stops = stops.loc[
            stops.get("feed_id", pd.Series(dtype="string")).astype("string").eq(feed_id)
        ]
        for row in feed_stops.itertuples(index=False):
            stop_id = getattr(row, "stop_id")
            node = ("stop", feed_id, stop_id)
            attributes = {
                "bipartite": 1,
                "node_type": "stop",
                "feed_id": feed_id,
                "stop_id": stop_id,
            }
            for column in ("source_stop_id", "stop_name"):
                if column in feed_stops.columns:
                    value = getattr(row, column)
                    if not pd.isna(value):
                        attributes[column] = value
            graph.add_node(node, **attributes)

        feed_edges = edges.loc[edges["feed_id"].astype("string").eq(feed_id)]
        for row in feed_edges.itertuples(index=False):
            route_node = ("route", feed_id, row.route_id)
            stop_node = ("stop", feed_id, row.stop_id)
            edge_attributes: dict[str, object] = {}
            for column in ("trip_count", "service_count", "stop_sequence"):
                if column in feed_edges.columns:
                    value = getattr(row, column)
                    if not pd.isna(value):
                        edge_attributes[column] = value
            graph.add_edge(route_node, stop_node, **edge_attributes)
        graphs[feed_id] = graph
    return graphs


def build_degree_distribution(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return route and stop node degrees, including published isolates."""
    records: list[dict[str, object]] = []
    for feed_id, graph in build_bipartite_graphs(tables).items():
        for node, degree in graph.degree:
            records.append(
                {
                    "feed_id": feed_id,
                    "node_type": node[0],
                    "node_id": node[2],
                    "degree": int(degree),
                }
            )
    return pd.DataFrame(
        records, columns=["feed_id", "node_type", "node_id", "degree"]
    ).sort_values(
        ["feed_id", "node_type", "node_id"], kind="stable", ignore_index=True
    )


def build_bipartite_network_summary(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Summarize bipartite node counts, edge counts, and degree ranges."""
    fields = [
        "feed_id",
        "route_node_count",
        "stop_node_count",
        "edge_count",
        "isolated_route_count",
        "isolated_stop_count",
        "mean_stops_per_route",
        "median_stops_per_route",
        "max_stops_per_route",
        "mean_routes_per_stop",
        "median_routes_per_stop",
        "max_routes_per_stop",
    ]
    degree = build_degree_distribution(tables)
    if degree.empty:
        return pd.DataFrame(columns=fields)
    edge_counts = build_route_stop_edges(tables).groupby("feed_id").size()
    rows: list[dict[str, object]] = []
    for feed_id, feed_degree in degree.groupby("feed_id", sort=True):
        route_degrees = feed_degree.loc[
            feed_degree["node_type"].eq("route"), "degree"
        ]
        stop_degrees = feed_degree.loc[
            feed_degree["node_type"].eq("stop"), "degree"
        ]
        rows.append(
            {
                "feed_id": feed_id,
                "route_node_count": int(route_degrees.size),
                "stop_node_count": int(stop_degrees.size),
                "edge_count": int(edge_counts.get(feed_id, 0)),
                "isolated_route_count": int(route_degrees.eq(0).sum()),
                "isolated_stop_count": int(stop_degrees.eq(0).sum()),
                "mean_stops_per_route": float(route_degrees.mean())
                if not route_degrees.empty
                else pd.NA,
                "median_stops_per_route": float(route_degrees.median())
                if not route_degrees.empty
                else pd.NA,
                "max_stops_per_route": int(route_degrees.max())
                if not route_degrees.empty
                else pd.NA,
                "mean_routes_per_stop": float(stop_degrees.mean())
                if not stop_degrees.empty
                else pd.NA,
                "median_routes_per_stop": float(stop_degrees.median())
                if not stop_degrees.empty
                else pd.NA,
                "max_routes_per_stop": int(stop_degrees.max())
                if not stop_degrees.empty
                else pd.NA,
            }
        )
    return pd.DataFrame(rows, columns=fields)


def build_route_connectivity(
    tables: Mapping[str, pd.DataFrame],
    route_stop_edges: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate scheduled stop coverage and trip-record counts by route."""
    routes = _table(tables, "routes")
    fields = [
        "feed_id",
        "route_id",
        "source_route_id",
        "route_short_name",
        "route_long_name",
        "stops_per_route",
        "scheduled_trip_count",
    ]
    if not {"feed_id", "route_id"}.issubset(routes.columns):
        return pd.DataFrame(columns=fields)
    edges = route_stop_edges if route_stop_edges is not None else build_route_stop_edges(tables)
    result = routes.copy()
    if {"feed_id", "route_id", "stop_id"}.issubset(edges.columns):
        stop_counts = edges.groupby(["feed_id", "route_id"]).stop_id.nunique()
        result["stops_per_route"] = [
            int(stop_counts.get((feed_id, route_id), 0))
            for feed_id, route_id in zip(result.feed_id, result.route_id, strict=True)
        ]
    else:
        result["stops_per_route"] = pd.NA
    trips = _table(tables, "trips")
    if {"feed_id", "route_id", "trip_id"}.issubset(trips.columns):
        trip_counts = trips.groupby(["feed_id", "route_id"]).trip_id.nunique()
        result["scheduled_trip_count"] = [
            int(trip_counts.get((feed_id, route_id), 0))
            for feed_id, route_id in zip(result.feed_id, result.route_id, strict=True)
        ]
    else:
        summary = _table(tables, "route_service_summary")
        if {"feed_id", "route_id", "trip_count"}.issubset(summary.columns):
            trip_counts = summary.set_index(["feed_id", "route_id"]).trip_count
            result["scheduled_trip_count"] = [
                trip_counts.get((feed_id, route_id), 0)
                for feed_id, route_id in zip(result.feed_id, result.route_id, strict=True)
            ]
        else:
            result["scheduled_trip_count"] = pd.NA
    columns = [column for column in fields if column in result.columns]
    return result[columns].sort_values(
        ["feed_id", "route_id"], kind="stable", ignore_index=True
    )


def build_stop_connectivity(
    tables: Mapping[str, pd.DataFrame],
    route_stop_edges: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate route degree and scheduled-trip connectivity per stop."""
    stops = _table(tables, "stops")
    fields = [
        "feed_id",
        "stop_id",
        "source_stop_id",
        "stop_name",
        "routes_per_stop",
        "trips_per_stop",
        "route_stop_edge_count",
    ]
    if not {"feed_id", "stop_id"}.issubset(stops.columns):
        return pd.DataFrame(columns=fields)
    edges = route_stop_edges if route_stop_edges is not None else build_route_stop_edges(tables)
    if {"feed_id", "route_id", "stop_id"}.issubset(edges.columns):
        aggregation: dict[str, tuple[str, str]] = {
            "routes_per_stop": ("route_id", "nunique"),
            "route_stop_edge_count": ("route_id", "size"),
        }
        if "trip_count" in edges.columns:
            aggregation["trips_per_stop"] = ("trip_count", "sum")
        counts = edges.groupby(["feed_id", "stop_id"], as_index=False).agg(**aggregation)
        result = stops.merge(
            counts,
            on=["feed_id", "stop_id"],
            how="left",
            validate="one_to_one",
        )
        summary = _table(tables, "stop_service_summary")
        if "trips_per_stop" not in result.columns and {
            "feed_id",
            "stop_id",
            "trip_count",
        }.issubset(summary.columns):
            result = result.merge(
                summary[["feed_id", "stop_id", "trip_count"]].rename(
                    columns={"trip_count": "trips_per_stop"}
                ),
                on=["feed_id", "stop_id"],
                how="left",
                validate="one_to_one",
            )
    else:
        result = stops.copy()
    for column in ("routes_per_stop", "trips_per_stop", "route_stop_edge_count"):
        if column not in result.columns:
            result[column] = pd.NA
        result[column] = result[column].fillna(0).astype("Int64")
    columns = [column for column in fields if column in result.columns]
    return result[columns].sort_values(
        ["feed_id", "stop_id"], kind="stable", ignore_index=True
    )


def build_route_overlap(
    route_stop_edges: pd.DataFrame,
    route_catalog: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate positive-overlap pairs among edge-bearing routes per feed.

    ``route_catalog`` may include isolated route records so the edge-bearing
    analysis domain is explicit; routes with empty stop sets are excluded.
    Pairs with no shared stops are omitted. Two empty stop sets have undefined
    Jaccard because their union is empty; no zero similarity is assigned.
    """
    if not set(_EDGE_COLUMNS).issubset(route_stop_edges.columns):
        return pd.DataFrame(columns=_OVERLAP_COLUMNS)
    edges = route_stop_edges[_EDGE_COLUMNS].drop_duplicates()
    if edges[_EDGE_COLUMNS].isna().any(axis=None):
        raise ValueError("Route-stop overlap requires non-null feed, route, and stop IDs")
    route_stops: dict[tuple[str, str], set[str]] = {}
    if route_catalog is not None:
        route_keys = {"feed_id", "route_id"}
        if not route_keys.issubset(route_catalog.columns):
            raise ValueError("route_catalog must contain feed_id and route_id")
        catalog = route_catalog[["feed_id", "route_id"]].drop_duplicates()
        if catalog.isna().any(axis=None):
            raise ValueError("route_catalog contains a missing feed or route ID")
        route_stops = {
            (feed_id, route_id): set()
            for feed_id, route_id in catalog.itertuples(index=False, name=None)
        }
        edge_route_keys = set(
            edges[["feed_id", "route_id"]].drop_duplicates().itertuples(
                index=False, name=None
            )
        )
        if edge_route_keys.difference(route_stops):
            raise ValueError("route_stop_edges contains routes absent from route_catalog")
    for (feed_id, route_id), group in edges.groupby(
        ["feed_id", "route_id"], sort=True
    ):
        route_stops[(feed_id, route_id)] = set(group.stop_id)
    shared_counts: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    for (feed_id, stop_id), group in edges.groupby(
        ["feed_id", "stop_id"], sort=True
    ):
        route_ids = sorted(group.route_id.unique())
        shared_counts[str(feed_id)].update(combinations(route_ids, 2))

    records: list[dict[str, object]] = []
    for feed_id, pairs in sorted(shared_counts.items()):
        for (route_id_a, route_id_b), shared_count in sorted(pairs.items()):
            stop_count_a = len(route_stops[(feed_id, route_id_a)])
            stop_count_b = len(route_stops[(feed_id, route_id_b)])
            union_count = stop_count_a + stop_count_b - shared_count
            similarity = _jaccard_similarity(
                route_stops[(feed_id, route_id_a)],
                route_stops[(feed_id, route_id_b)],
            )
            if similarity is None:
                continue
            records.append(
                {
                    "feed_id": feed_id,
                    "route_id_a": route_id_a,
                    "route_id_b": route_id_b,
                    "shared_stop_count": int(shared_count),
                    "union_stop_count": int(union_count),
                    "jaccard_similarity": similarity,
                }
            )
    return pd.DataFrame(records, columns=_OVERLAP_COLUMNS)


def _jaccard_similarity(stops_a: set[str], stops_b: set[str]) -> float | None:
    """Return Jaccard similarity, or ``None`` when the union is empty."""
    union = stops_a | stops_b
    if not union:
        return None
    return len(stops_a & stops_b) / len(union)


def build_route_overlap_summary(
    routes: pd.DataFrame,
    route_overlap: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize each route's positive-overlap neighbors and similarities."""
    keys = ["feed_id", "route_id"]
    if not set(keys).issubset(routes.columns):
        return pd.DataFrame(
            columns=[*keys, "overlapping_route_count", "mean_overlapping_jaccard"]
        )
    endpoints: list[pd.DataFrame] = []
    if not route_overlap.empty:
        for route_column, neighbor_column in (
            ("route_id_a", "route_id_b"),
            ("route_id_b", "route_id_a"),
        ):
            endpoints.append(
                route_overlap[["feed_id", route_column, neighbor_column, "jaccard_similarity"]]
                .rename(columns={route_column: "route_id", neighbor_column: "overlapping_route_id"})
            )
    if endpoints:
        summary = pd.concat(endpoints, ignore_index=True).groupby(
            keys, as_index=False
        ).agg(
            overlapping_route_count=("overlapping_route_id", "nunique"),
            mean_overlapping_jaccard=("jaccard_similarity", "mean"),
        )
    else:
        summary = pd.DataFrame(
            columns=[*keys, "overlapping_route_count", "mean_overlapping_jaccard"]
        )
    result = routes[keys].drop_duplicates().merge(
        summary, on=keys, how="left", validate="one_to_one"
    )
    result["overlapping_route_count"] = result[
        "overlapping_route_count"
    ].fillna(0).astype("Int64")
    result["mean_overlapping_jaccard"] = result["mean_overlapping_jaccard"].fillna(0.0)
    return result.sort_values(keys, kind="stable", ignore_index=True)


def build_weekday_profile(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return calendar-derived scheduled trip counts by feed and weekday."""
    profile = build_weekday_service(tables)
    if profile.empty:
        return profile.rename(columns={"operator": "feed_id"})
    return profile.rename(columns={"operator": "feed_id"}).sort_values(
        ["feed_id", "weekday_order"], kind="stable", ignore_index=True
    )


def build_weekday_weekend_comparison(
    weekday_profile: pd.DataFrame,
) -> pd.DataFrame:
    """Compare average calendar weekday and weekend scheduled trip counts."""
    fields = [
        "feed_id",
        "weekday_mean_scheduled_trip_count",
        "weekend_mean_scheduled_trip_count",
        "weekend_to_weekday_mean_ratio",
    ]
    if not {"feed_id", "weekday", "scheduled_trip_count"}.issubset(
        weekday_profile.columns
    ):
        return pd.DataFrame(columns=fields)
    rows: list[dict[str, object]] = []
    weekday_names = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
    weekend_names = {"Saturday", "Sunday"}
    for feed_id, group in weekday_profile.groupby("feed_id", sort=True):
        values = pd.to_numeric(group["scheduled_trip_count"], errors="coerce")
        weekdays = values.loc[group.weekday.isin(weekday_names)].dropna()
        weekends = values.loc[group.weekday.isin(weekend_names)].dropna()
        weekday_mean = float(weekdays.mean()) if not weekdays.empty else pd.NA
        weekend_mean = float(weekends.mean()) if not weekends.empty else pd.NA
        ratio = (
            weekend_mean / weekday_mean
            if not pd.isna(weekday_mean) and weekday_mean != 0 and not pd.isna(weekend_mean)
            else pd.NA
        )
        rows.append(
            {
                "feed_id": feed_id,
                "weekday_mean_scheduled_trip_count": weekday_mean,
                "weekend_mean_scheduled_trip_count": weekend_mean,
                "weekend_to_weekday_mean_ratio": ratio,
            }
        )
    return pd.DataFrame(rows, columns=fields)


def build_hourly_profile(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return stop-departure schedule counts with service-day hours preserved."""
    stop_times = _table(tables, "stop_times")
    if stop_times.empty:
        return pd.DataFrame(
            columns=[
                "feed_id",
                "service_day_hour",
                "clock_hour",
                "service_day_offset",
                "scheduled_departure_count",
            ]
        )
    return build_hourly_service(stop_times).rename(columns={"operator": "feed_id"})


def build_service_windows(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return per-route scheduled first departure, last arrival, and span."""
    summary = _table(tables, "route_service_summary")
    required = set(_WINDOW_COLUMNS[:4])
    if not required.issubset(summary.columns):
        return pd.DataFrame(columns=_WINDOW_COLUMNS)
    result = summary[
        ["feed_id", "route_id", "first_departure_seconds", "last_arrival_seconds"]
    ].copy()
    result["service_span_seconds"] = (
        pd.to_numeric(result["last_arrival_seconds"], errors="coerce")
        - pd.to_numeric(result["first_departure_seconds"], errors="coerce")
    )
    return result.sort_values(
        ["feed_id", "route_id"], kind="stable", ignore_index=True
    )


def build_stop_to_stop_time_features(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Calculate same-trip scheduled segment durations where adjacent times exist.

    A segment runs from one stop's scheduled departure to the following stop's
    scheduled arrival. Missing end points are not derivable and are excluded;
    a negative derived segment raises instead of being silently discarded.
    """
    fields = _STOP_TIME_COLUMNS
    stop_times = _table(tables, "stop_times")
    trips = _table(tables, "trips")
    required_times = {"feed_id", "trip_id", "stop_sequence", "departure_seconds"}
    if (
        not required_times.issubset(stop_times.columns)
        or not {"feed_id", "trip_id", "route_id"}.issubset(trips.columns)
        or "arrival_seconds" not in stop_times.columns
    ):
        return pd.DataFrame(columns=fields)
    route_trips = trips[["feed_id", "trip_id", "route_id"]].drop_duplicates(
        ["feed_id", "trip_id"]
    )
    segments = stop_times[
        ["feed_id", "trip_id", "stop_sequence", "departure_seconds", "arrival_seconds"]
    ].merge(
        route_trips,
        on=["feed_id", "trip_id"],
        how="inner",
        validate="many_to_one",
    ).sort_values(["feed_id", "trip_id", "stop_sequence"], kind="stable")
    segments["next_arrival_seconds"] = segments.groupby(
        ["feed_id", "trip_id"], sort=False
    )["arrival_seconds"].shift(-1)
    durations = (
        pd.to_numeric(segments["next_arrival_seconds"], errors="coerce")
        - pd.to_numeric(segments["departure_seconds"], errors="coerce")
    )
    derivable = durations.notna()
    if durations.loc[derivable].lt(0).any():
        raise ValueError("Negative scheduled stop-to-stop time interval found")
    segments["scheduled_segment_minutes"] = durations / 60
    valid_segments = segments.loc[derivable]
    if valid_segments.empty:
        return pd.DataFrame(columns=fields)
    result = valid_segments.groupby(["feed_id", "route_id"], as_index=False).agg(
        scheduled_segment_count=("scheduled_segment_minutes", "count"),
        mean_scheduled_stop_to_stop_minutes=("scheduled_segment_minutes", "mean"),
        median_scheduled_stop_to_stop_minutes=("scheduled_segment_minutes", "median"),
    )
    return result[fields].sort_values(
        ["feed_id", "route_id"], kind="stable", ignore_index=True
    )


def build_route_network_features(
    tables: Mapping[str, pd.DataFrame],
    route_overlap: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create feed-scoped route features for later exploratory/modeling phases.

    All features describe scheduled structure. No passenger measurements or
    inferred usage variables are included.
    """
    edges = build_route_stop_edges(tables)
    routes = build_route_connectivity(tables, edges)
    if routes.empty:
        return pd.DataFrame(
            columns=[
                "feed_id",
                "route_id",
                "source_route_id",
                "route_short_name",
                "route_long_name",
                "scheduled_trip_count",
                "stops_per_route",
                "service_days",
                "service_span_seconds",
                "scheduled_service_intensity",
                "scheduled_segment_count",
                "mean_scheduled_stop_to_stop_minutes",
                "median_scheduled_stop_to_stop_minutes",
                "overlapping_route_count",
                "mean_overlapping_jaccard",
            ]
        )
    analytics = build_route_analytics(tables).rename(
        columns={
            "operator": "feed_id",
            "trip_count": "scheduled_trip_count",
            "stop_count": "stops_per_route",
        }
    )
    analytics_columns = [
        column
        for column in (
            "feed_id",
            "route_id",
            "service_days",
            "scheduled_service_intensity",
        )
        if column in analytics.columns
    ]
    features = routes.merge(
        analytics[analytics_columns],
        on=["feed_id", "route_id"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_calendar"),
    )
    duplicate_count = "scheduled_trip_count_calendar"
    if duplicate_count in features.columns:
        features = features.drop(columns=duplicate_count)
    duplicate_stops = "stops_per_route_calendar"
    if duplicate_stops in features.columns:
        features = features.drop(columns=duplicate_stops)

    windows = build_service_windows(tables)
    features = features.merge(
        windows,
        on=["feed_id", "route_id"],
        how="left",
        validate="one_to_one",
    )
    segment_features = build_stop_to_stop_time_features(tables)
    if not segment_features.empty:
        features = features.merge(
            segment_features,
            on=["feed_id", "route_id"],
            how="left",
            validate="one_to_one",
        )
    else:
        features["scheduled_segment_count"] = pd.NA
        features["mean_scheduled_stop_to_stop_minutes"] = pd.NA
        features["median_scheduled_stop_to_stop_minutes"] = pd.NA

    overlaps = (
        route_overlap
        if route_overlap is not None
        else build_route_overlap(edges, _table(tables, "routes"))
    )
    overlap_summary = build_route_overlap_summary(routes, overlaps)
    features = features.merge(
        overlap_summary,
        on=["feed_id", "route_id"],
        how="left",
        validate="one_to_one",
    )
    preferred = [
        "feed_id",
        "route_id",
        "source_route_id",
        "route_short_name",
        "route_long_name",
        "scheduled_trip_count",
        "stops_per_route",
        "service_days",
        "service_span_seconds",
        "scheduled_service_intensity",
        "scheduled_segment_count",
        "mean_scheduled_stop_to_stop_minutes",
        "median_scheduled_stop_to_stop_minutes",
        "overlapping_route_count",
        "mean_overlapping_jaccard",
    ]
    return features[[column for column in preferred if column in features.columns]].sort_values(
        ["feed_id", "route_id"], kind="stable", ignore_index=True
    )


def build_service_concentration_curve(
    route_features: pd.DataFrame,
) -> pd.DataFrame:
    """Return cumulative scheduled-trip share by ranked route, per feed."""
    fields = [
        "feed_id",
        "route_id",
        "route_rank",
        "route_rank_fraction",
        "cumulative_scheduled_trip_share",
    ]
    required = {"feed_id", "route_id", "scheduled_trip_count"}
    if not required.issubset(route_features.columns):
        return pd.DataFrame(columns=fields)
    records: list[dict[str, object]] = []
    for feed_id, group in route_features.groupby("feed_id", sort=True):
        values = pd.to_numeric(group["scheduled_trip_count"], errors="raise")
        if values.lt(0).any():
            raise ValueError("Scheduled trip counts must be non-negative")
        ranked = group.assign(_scheduled_trip_count=values).sort_values(
            ["_scheduled_trip_count", "route_id"],
            ascending=[False, True],
            kind="stable",
        )
        total = float(ranked["_scheduled_trip_count"].sum())
        if total <= 0:
            continue
        cumulative = ranked["_scheduled_trip_count"].cumsum() / total
        route_count = len(ranked)
        for rank, ((_, row), share) in enumerate(
            zip(ranked.iterrows(), cumulative, strict=True), start=1
        ):
            records.append(
                {
                    "feed_id": feed_id,
                    "route_id": row["route_id"],
                    "route_rank": rank,
                    "route_rank_fraction": rank / route_count,
                    "cumulative_scheduled_trip_share": float(share),
                }
            )
    return pd.DataFrame(records, columns=fields)


def build_service_concentration(
    route_features: pd.DataFrame,
    stop_connectivity: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize scheduled-trip, route-stop-edge, and stop-degree concentration.

    HHI is computed as the sum of squared entity shares, where each share is
    that entity's count divided by the total count. HHI describes distribution
    across schedule/network entities only; it is not passenger concentration.
    """
    fields = [
        "feed_id",
        "route_count",
        "total_scheduled_trip_records",
        "top_10_routes_scheduled_trip_share",
        "top_10_percent_routes_scheduled_trip_share",
        "scheduled_trip_hhi",
        "total_route_stop_edges",
        "route_stop_edge_hhi",
        "stop_route_edge_hhi",
        "top_10_percent_stops_route_edge_share",
        "routes_per_stop_mean",
        "routes_per_stop_median",
        "routes_per_stop_p90",
        "routes_per_stop_max",
    ]
    if not {"feed_id", "route_id", "scheduled_trip_count", "stops_per_route"}.issubset(
        route_features.columns
    ):
        return pd.DataFrame(columns=fields)
    rows: list[dict[str, object]] = []
    for feed_id, routes in route_features.groupby("feed_id", sort=True):
        trip_counts = pd.to_numeric(routes["scheduled_trip_count"], errors="raise")
        stop_counts = pd.to_numeric(routes["stops_per_route"], errors="coerce").fillna(0)
        if trip_counts.lt(0).any() or stop_counts.lt(0).any():
            raise ValueError("Concentration counts must be non-negative")
        trip_total = float(trip_counts.sum())
        edge_total = float(stop_counts.sum())
        trip_shares = trip_counts / trip_total if trip_total else trip_counts * 0
        edge_shares = stop_counts / edge_total if edge_total else stop_counts * 0
        route_count = len(routes)
        top_ten_route_count = min(10, route_count)
        top_tenth_route_count = ceil(route_count * 0.10)
        top_route_share = (
            float(trip_counts.nlargest(top_ten_route_count).sum() / trip_total)
            if trip_total
            else pd.NA
        )
        top_decile_share = (
            float(trip_counts.nlargest(top_tenth_route_count).sum() / trip_total)
            if trip_total
            else pd.NA
        )

        stops = stop_connectivity.loc[
            stop_connectivity.get("feed_id", pd.Series(dtype="string")).eq(feed_id)
        ]
        stop_degree = (
            pd.to_numeric(stops["routes_per_stop"], errors="coerce").fillna(0)
            if "routes_per_stop" in stops.columns
            else pd.Series(dtype="float64")
        )
        stop_total = float(stop_degree.sum())
        top_stop_count = ceil(len(stop_degree) * 0.10)
        top_stop_edge_share = (
            float(stop_degree.nlargest(top_stop_count).sum() / stop_total)
            if stop_total and top_stop_count
            else pd.NA
        )
        rows.append(
            {
                "feed_id": feed_id,
                "route_count": route_count,
                "total_scheduled_trip_records": int(trip_total),
                "top_10_routes_scheduled_trip_share": top_route_share,
                "top_10_percent_routes_scheduled_trip_share": top_decile_share,
                "scheduled_trip_hhi": float((trip_shares**2).sum())
                if trip_total
                else pd.NA,
                "total_route_stop_edges": int(edge_total),
                "route_stop_edge_hhi": float((edge_shares**2).sum())
                if edge_total
                else pd.NA,
                "stop_route_edge_hhi": float(((stop_degree / stop_total) ** 2).sum())
                if stop_total
                else pd.NA,
                "top_10_percent_stops_route_edge_share": top_stop_edge_share,
                "routes_per_stop_mean": float(stop_degree.mean())
                if not stop_degree.empty
                else pd.NA,
                "routes_per_stop_median": float(stop_degree.median())
                if not stop_degree.empty
                else pd.NA,
                "routes_per_stop_p90": float(stop_degree.quantile(0.90))
                if not stop_degree.empty
                else pd.NA,
                "routes_per_stop_max": int(stop_degree.max())
                if not stop_degree.empty
                else pd.NA,
            }
        )
    return pd.DataFrame(rows, columns=fields)


def build_network_temporal_analysis(
    tables: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build reusable network, overlap, calendar, and route-feature tables."""
    edges = build_route_stop_edges(tables)
    routes = build_route_connectivity(tables, edges)
    stops = build_stop_connectivity(tables, edges)
    overlap = build_route_overlap(edges, _table(tables, "routes"))
    route_features = build_route_network_features(tables, overlap)
    weekday = build_weekday_profile(tables)
    hourly = build_hourly_profile(tables)
    curve = build_service_concentration_curve(route_features)
    return {
        "route_stop_edges": edges,
        "bipartite_summary": build_bipartite_network_summary(tables),
        "degree_distribution": build_degree_distribution(tables),
        "route_connectivity": routes,
        "stop_connectivity": stops,
        "route_overlap": overlap,
        "service_windows": build_service_windows(tables),
        "weekday_profile": weekday,
        "weekday_weekend_comparison": build_weekday_weekend_comparison(weekday),
        "hourly_profile": hourly,
        "stop_to_stop_time_features": build_stop_to_stop_time_features(tables),
        "route_network_features": route_features,
        "service_concentration_curve": curve,
        "service_concentration": build_service_concentration(
            route_features, stops
        ),
    }