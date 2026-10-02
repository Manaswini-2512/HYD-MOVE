"""Deterministic synthetic tests for GTFS network and temporal analytics."""

import networkx as nx
import pandas as pd
import pytest

from src.analysis.gtfs_network import (
    build_bipartite_graphs,
    build_bipartite_network_summary,
    build_degree_distribution,
    build_hourly_profile,
    build_route_network_features,
    build_route_overlap,
    build_route_stop_edges,
    build_service_concentration,
    build_service_concentration_curve,
    build_service_windows,
    build_stop_connectivity,
    build_stop_to_stop_time_features,
    build_weekday_profile,
    build_weekday_weekend_comparison,
    _jaccard_similarity,
)


def make_network_tables() -> dict[str, pd.DataFrame]:
    """Create small synthetic feed tables; no values are real observations."""
    return {
        "routes": pd.DataFrame(
            {
                "feed_id": ["F1", "F1", "F1", "F2"],
                "route_id": ["F1:R1", "F1:R2", "F1:R3", "F2:R1"],
                "source_route_id": ["R1", "R2", "R3", "R1"],
                "route_short_name": ["1", "2", "3", "1"],
                "route_long_name": ["North", "South", "Unused", "Metro"],
            }
        ),
        "stops": pd.DataFrame(
            {
                "feed_id": ["F1"] * 4 + ["F2"],
                "stop_id": ["F1:S1", "F1:S2", "F1:S3", "F1:S4", "F2:S1"],
                "source_stop_id": ["S1", "S2", "S3", "S4", "S1"],
                "stop_name": ["Central", "Shared", "South", "Isolated", "Central"],
            }
        ),
        "trips": pd.DataFrame(
            {
                "feed_id": ["F1", "F1", "F1", "F2"],
                "trip_id": ["F1:T1", "F1:T2", "F1:T3", "F2:T1"],
                "route_id": ["F1:R1", "F1:R1", "F1:R2", "F2:R1"],
                "service_id": ["F1:WK", "F1:WE", "F1:WK", "F2:WK"],
            }
        ),
        "route_stops": pd.DataFrame(
            {
                "feed_id": ["F1", "F1", "F1", "F1", "F2"],
                "route_id": ["F1:R1", "F1:R1", "F1:R2", "F1:R2", "F2:R1"],
                "stop_id": ["F1:S1", "F1:S2", "F1:S2", "F1:S3", "F2:S1"],
                "source_route_id": ["R1", "R1", "R2", "R2", "R1"],
                "source_stop_id": ["S1", "S2", "S2", "S3", "S1"],
                "stop_sequence": [1, 2, 1, 2, 1],
                "trip_count": [2, 2, 1, 1, 1],
                "service_count": [2, 2, 1, 1, 1],
            }
        ),
        "calendar": pd.DataFrame(
            {
                "feed_id": ["F1", "F1", "F2"],
                "service_id": ["F1:WK", "F1:WE", "F2:WK"],
                "monday": [1, 0, 1],
                "tuesday": [1, 0, 0],
                "wednesday": [1, 0, 0],
                "thursday": [1, 0, 0],
                "friday": [1, 0, 0],
                "saturday": [0, 1, 0],
                "sunday": [0, 1, 0],
                "start_date": pd.to_datetime(["2026-01-01"] * 3),
                "end_date": pd.to_datetime(["2026-12-31"] * 3),
            }
        ),
        "route_service_summary": pd.DataFrame(
            {
                "feed_id": ["F1", "F1", "F1", "F2"],
                "route_id": ["F1:R1", "F1:R2", "F1:R3", "F2:R1"],
                "first_departure_seconds": [85800, 600, pd.NA, 0],
                "last_arrival_seconds": [93900, 2700, pd.NA, 3600],
                "trip_count": [2, 1, 0, 1],
                "unique_stop_count": [2, 2, 0, 1],
            }
        ),
        "stop_service_summary": pd.DataFrame(
            {
                "feed_id": ["F1"] * 4 + ["F2"],
                "stop_id": ["F1:S1", "F1:S2", "F1:S3", "F1:S4", "F2:S1"],
                "route_count": [1, 2, 1, 0, 1],
                "trip_count": [2, 3, 1, 0, 1],
            }
        ),
        "stop_times": pd.DataFrame(
            {
                "feed_id": ["F1"] * 6 + ["F2"],
                "trip_id": ["F1:T1", "F1:T1", "F1:T2", "F1:T2", "F1:T3", "F1:T3", "F2:T1"],
                "stop_id": ["F1:S1", "F1:S2", "F1:S1", "F1:S2", "F1:S2", "F1:S3", "F2:S1"],
                "stop_sequence": [1, 2, 1, 2, 1, 2, 1],
                "arrival_time": ["23:45:00", "25:30:00", "25:25:00", "26:05:00", "00:05:00", "00:45:00", "00:00:00"],
                "departure_time": ["23:50:00", "25:35:00", "25:30:00", "26:10:00", "00:10:00", "00:50:00", "00:00:00"],
                "arrival_seconds": [85500, 91800, 91500, 93900, 300, 2700, 0],
                "departure_seconds": [85800, 92100, 91800, 94200, 600, 3000, 0],
            }
        ),
    }


def test_route_stop_edge_builder_uses_feed_scoped_trip_join() -> None:
    tables = make_network_tables()
    edges = build_route_stop_edges(tables)
    reconstructed = build_route_stop_edges({key: value for key, value in tables.items() if key != "route_stops"})

    assert len(edges) == 5
    assert reconstructed["feed_id"].nunique() == 2
    assert set(map(tuple, reconstructed[["feed_id", "route_id", "stop_id"]].to_numpy())) == set(
        map(tuple, edges[["feed_id", "route_id", "stop_id"]].to_numpy())
    )


def test_bipartite_graph_includes_degree_zero_nodes_and_feed_partitions() -> None:
    tables = make_network_tables()
    graphs = build_bipartite_graphs(tables)

    assert set(graphs) == {"F1", "F2"}
    assert all(isinstance(graph, nx.Graph) for graph in graphs.values())
    assert graphs["F1"].number_of_nodes() == 7
    assert graphs["F1"].number_of_edges() == 4
    assert graphs["F1"].degree[("route", "F1", "F1:R3")] == 0
    assert graphs["F1"].degree[("stop", "F1", "F1:S4")] == 0
    assert all(node[1] == feed_id for feed_id, graph in graphs.items() for node in graph)


def test_route_and_stop_degrees_are_calculated_from_edges() -> None:
    tables = make_network_tables()
    route_connectivity = build_route_network_features(tables).set_index(["feed_id", "route_id"])
    stop_connectivity = build_stop_connectivity(tables).set_index(["feed_id", "stop_id"])

    assert route_connectivity.loc[("F1", "F1:R1"), "stops_per_route"] == 2
    assert route_connectivity.loc[("F1", "F1:R3"), "stops_per_route"] == 0
    assert stop_connectivity.loc[("F1", "F1:S2"), "routes_per_stop"] == 2
    assert stop_connectivity.loc[("F1", "F1:S2"), "trips_per_stop"] == 3
    assert stop_connectivity.loc[("F1", "F1:S4"), "routes_per_stop"] == 0


def test_bipartite_summary_reports_nodes_edges_and_degree_statistics() -> None:
    summary = build_bipartite_network_summary(make_network_tables()).set_index("feed_id")

    assert summary.loc["F1", "route_node_count"] == 3
    assert summary.loc["F1", "stop_node_count"] == 4
    assert summary.loc["F1", "edge_count"] == 4
    assert summary.loc["F1", "isolated_route_count"] == 1
    assert summary.loc["F1", "isolated_stop_count"] == 1
    assert summary.loc["F1", "max_routes_per_stop"] == 2
    assert len(build_degree_distribution(make_network_tables())) == 9


def test_pairwise_route_overlap_is_feed_isolated_and_unique() -> None:
    edges = build_route_stop_edges(make_network_tables())
    edges = pd.concat([edges, edges.iloc[[0]]], ignore_index=True)
    overlap = build_route_overlap(edges)

    assert len(overlap) == 1
    pair = overlap.iloc[0]
    assert pair["feed_id"] == "F1"
    assert pair["route_id_a"] == "F1:R1"
    assert pair["route_id_b"] == "F1:R2"
    assert pair["shared_stop_count"] == 1
    assert pair["union_stop_count"] == 3
    assert pair["jaccard_similarity"] == pytest.approx(1 / 3)
    assert not (overlap["route_id_a"] == overlap["route_id_b"]).any()


def test_overlap_jaccard_counts_shared_and_union_stops() -> None:
    edges = pd.DataFrame(
        {
            "feed_id": ["F"] * 5,
            "route_id": ["A", "A", "B", "B", "B"],
            "stop_id": ["s1", "s2", "s2", "s3", "s4"],
        }
    )
    overlap = build_route_overlap(edges).iloc[0]

    assert overlap["shared_stop_count"] == 1
    assert overlap["union_stop_count"] == 4
    assert overlap["jaccard_similarity"] == pytest.approx(0.25)


def test_identical_nonempty_route_sets_have_jaccard_one() -> None:
    edges = pd.DataFrame(
        {
            "feed_id": ["F"] * 4,
            "route_id": ["F:A", "F:A", "F:B", "F:B"],
            "stop_id": ["F:S1", "F:S2", "F:S1", "F:S2"],
        }
    )
    routes = pd.DataFrame({"feed_id": ["F", "F"], "route_id": ["F:A", "F:B"]})

    overlap = build_route_overlap(edges, routes)

    assert len(overlap) == 1
    assert overlap.iloc[0]["shared_stop_count"] == 2
    assert overlap.iloc[0]["union_stop_count"] == 2
    assert overlap.iloc[0]["jaccard_similarity"] == pytest.approx(1.0)


def test_disjoint_nonempty_route_sets_are_omitted() -> None:
    edges = pd.DataFrame(
        {
            "feed_id": ["F", "F"],
            "route_id": ["F:A", "F:B"],
            "stop_id": ["F:S1", "F:S2"],
        }
    )
    routes = pd.DataFrame({"feed_id": ["F", "F"], "route_id": ["F:A", "F:B"]})

    assert build_route_overlap(edges, routes).empty
    assert _jaccard_similarity({"F:S1"}, {"F:S2"}) == 0.0


def test_route_pair_with_one_empty_stop_set_is_not_emitted() -> None:
    edges = pd.DataFrame(
        {"feed_id": ["F"], "route_id": ["F:A"], "stop_id": ["F:S1"]}
    )
    routes = pd.DataFrame({"feed_id": ["F", "F"], "route_id": ["F:A", "F:EMPTY"]})

    overlap = build_route_overlap(edges, routes)

    assert overlap.empty
    assert not (
        overlap.route_id_a.eq("F:EMPTY") | overlap.route_id_b.eq("F:EMPTY")
    ).any()


def test_two_empty_stop_sets_have_undefined_jaccard_and_are_not_emitted() -> None:
    edges = pd.DataFrame(columns=["feed_id", "route_id", "stop_id"])
    routes = pd.DataFrame({"feed_id": ["F", "F"], "route_id": ["F:A", "F:B"]})

    assert build_route_overlap(edges, routes).empty
    assert _jaccard_similarity(set(), set()) is None


def test_extended_hourly_time_keeps_service_day_and_clock_hours_distinct() -> None:
    profile = build_hourly_profile(make_network_tables())
    extended = profile.loc[
        profile.feed_id.eq("F1") & profile.service_day_hour.eq(25)
    ].iloc[0]

    assert extended["clock_hour"] == 1
    assert extended["service_day_offset"] == 1
    assert extended["scheduled_departure_count"] == 2


def test_weekday_and_weekend_profiles_use_calendar_definitions() -> None:
    profile = build_weekday_profile(make_network_tables())
    comparison = build_weekday_weekend_comparison(profile).set_index("feed_id")
    f1 = profile.loc[profile.feed_id.eq("F1")].set_index("weekday")

    assert f1.loc["Monday", "scheduled_trip_count"] == 2
    assert f1.loc["Friday", "scheduled_trip_count"] == 2
    assert f1.loc["Saturday", "scheduled_trip_count"] == 1
    assert f1.loc["Sunday", "scheduled_trip_count"] == 1
    assert comparison.loc["F1", "weekday_mean_scheduled_trip_count"] == 2
    assert comparison.loc["F1", "weekend_mean_scheduled_trip_count"] == 1
    assert comparison.loc["F1", "weekend_to_weekday_mean_ratio"] == pytest.approx(0.5)


def test_service_windows_preserve_extended_seconds_and_compute_span() -> None:
    windows = build_service_windows(make_network_tables()).set_index(["feed_id", "route_id"])

    assert windows.loc[("F1", "F1:R1"), "first_departure_seconds"] == 85800
    assert windows.loc[("F1", "F1:R1"), "last_arrival_seconds"] == 93900
    assert windows.loc[("F1", "F1:R1"), "service_span_seconds"] == 8100
    assert pd.isna(windows.loc[("F1", "F1:R3"), "service_span_seconds"])


def test_scheduled_stop_to_stop_time_features_use_same_trip_sequence() -> None:
    features = build_stop_to_stop_time_features(make_network_tables()).set_index(
        ["feed_id", "route_id"]
    )

    assert features.loc[("F1", "F1:R1"), "scheduled_segment_count"] == 2
    assert features.loc[("F1", "F1:R1"), "mean_scheduled_stop_to_stop_minutes"] == pytest.approx(67.5)
    assert features.loc[("F1", "F1:R2"), "mean_scheduled_stop_to_stop_minutes"] == pytest.approx(35)


def test_route_feature_table_contains_only_supported_schedule_features() -> None:
    features = build_route_network_features(make_network_tables())

    assert {"scheduled_trip_count", "stops_per_route", "service_days", "service_span_seconds"}.issubset(features.columns)
    assert "mean_scheduled_stop_to_stop_minutes" in features.columns
    assert "overlapping_route_count" in features.columns
    assert not any("passenger" in column.lower() for column in features.columns)


def test_schedule_concentration_shares_hhi_and_curve() -> None:
    routes = pd.DataFrame(
        {
            "feed_id": ["F"] * 4,
            "route_id": ["A", "B", "C", "D"],
            "scheduled_trip_count": [60, 30, 10, 0],
            "stops_per_route": [3, 2, 1, 0],
        }
    )
    stops = pd.DataFrame(
        {
            "feed_id": ["F"] * 4,
            "stop_id": ["s1", "s2", "s3", "s4"],
            "routes_per_stop": [2, 1, 1, 0],
        }
    )
    summary = build_service_concentration(routes, stops).iloc[0]
    curve = build_service_concentration_curve(routes)

    assert summary["top_10_routes_scheduled_trip_share"] == pytest.approx(1)
    assert summary["top_10_percent_routes_scheduled_trip_share"] == pytest.approx(0.6)
    assert summary["scheduled_trip_hhi"] == pytest.approx(0.46)
    assert summary["route_stop_edge_hhi"] == pytest.approx(14 / 36)
    assert summary["stop_route_edge_hhi"] == pytest.approx(0.375)
    assert summary["top_10_percent_stops_route_edge_share"] == pytest.approx(0.5)
    assert curve.iloc[-1]["cumulative_scheduled_trip_share"] == pytest.approx(1)


def test_empty_inputs_return_empty_frames() -> None:
    assert build_route_stop_edges({}).empty
    assert build_route_overlap(pd.DataFrame()).empty
    assert build_bipartite_graphs({}) == {}
    assert build_bipartite_network_summary({}).empty
    assert build_degree_distribution({}).empty
    assert build_weekday_profile({}).empty
    assert build_hourly_profile({}).empty
    assert build_service_windows({}).empty
    assert build_stop_to_stop_time_features({}).empty
    assert build_route_network_features({}).empty


def test_cross_feed_identical_unqualified_ids_do_not_overlap() -> None:
    edges = pd.DataFrame(
        {
            "feed_id": ["F1", "F1", "F2", "F2"],
            "route_id": ["R1", "R2", "R1", "R2"],
            "stop_id": ["S1", "S1", "S1", "S2"],
        }
    )
    overlap = build_route_overlap(edges)

    assert set(overlap.feed_id) == {"F1"}
    assert len(overlap) == 1
