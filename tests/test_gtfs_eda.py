"""Deterministic synthetic tests for schedule-only GTFS EDA."""

import pandas as pd
import pytest

from src.analysis.gtfs_eda import (
    build_eda_tables,
    build_hourly_service,
    build_operator_comparison,
    build_route_analytics,
    build_stop_connectivity,
    build_weekday_service,
    top_connected_stops,
)


def make_eda_tables() -> dict[str, pd.DataFrame]:
    """Return a small synthetic feed; values are not real-world observations."""
    return {
        "routes": pd.DataFrame(
            {
                "feed_id": ["OP", "OP", "OP"],
                "route_id": ["OP:R1", "OP:R2", "OP:R3"],
                "source_route_id": ["R1", "R2", "R3"],
                "route_short_name": ["1", "2", "3"],
                "route_long_name": ["North", "South", "Unused"],
            }
        ),
        "stops": pd.DataFrame(
            {
                "feed_id": ["OP"] * 4,
                "stop_id": ["OP:S1", "OP:S2", "OP:S3", "OP:S4"],
                "source_stop_id": ["S1", "S2", "S3", "S4"],
                "stop_name": ["Central", "North", "South", "Unserved"],
            }
        ),
        "trips": pd.DataFrame(
            {
                "feed_id": ["OP"] * 4,
                "trip_id": ["OP:T1", "OP:T2", "OP:T3", "OP:T4"],
                "route_id": ["OP:R1", "OP:R1", "OP:R1", "OP:R2"],
                "service_id": ["OP:WK", "OP:WK", "OP:SA", "OP:WK"],
            }
        ),
        "route_stops": pd.DataFrame(
            {
                "feed_id": ["OP"] * 4,
                "route_id": ["OP:R1", "OP:R1", "OP:R2", "OP:R2"],
                "stop_id": ["OP:S1", "OP:S2", "OP:S1", "OP:S3"],
                "trip_count": [2, 3, 1, 1],
            }
        ),
        "calendar": pd.DataFrame(
            {
                "feed_id": ["OP", "OP"],
                "service_id": ["OP:WK", "OP:SA"],
                "monday": [1, 0],
                "tuesday": [1, 0],
                "wednesday": [1, 0],
                "thursday": [1, 0],
                "friday": [1, 0],
                "saturday": [0, 1],
                "sunday": [0, 1],
                "start_date": pd.to_datetime(["2026-01-01"] * 2),
                "end_date": pd.to_datetime(["2026-12-31"] * 2),
            }
        ),
        "route_service_summary": pd.DataFrame(
            {
                "feed_id": ["OP"] * 3,
                "route_id": ["OP:R1", "OP:R2", "OP:R3"],
                "first_departure_seconds": [3600, 7200, pd.NA],
                "last_arrival_seconds": [7200, 10800, pd.NA],
            }
        ),
        "stop_service_summary": pd.DataFrame(
            {
                "feed_id": ["OP"] * 4,
                "stop_id": ["OP:S1", "OP:S2", "OP:S3", "OP:S4"],
                "route_count": [2, 1, 1, 0],
                "trip_count": [3, 3, 1, 0],
                "first_service_seconds": [3600, 5400, 7200, pd.NA],
                "last_service_seconds": [14400, 18000, 21600, pd.NA],
            }
        ),
        "stop_times": pd.DataFrame(
            {
                "feed_id": ["OP"] * 3,
                "trip_id": ["OP:T1", "OP:T2", "OP:T3"],
                "departure_time": ["25:30:00", "24:00:00", ""],
                "arrival_time": ["25:20:00", "23:55:00", "01:15:00"],
            }
        ),
    }


def test_route_aggregation_includes_zero_trip_route_and_calendar_intensity() -> None:
    routes = build_route_analytics(make_eda_tables()).set_index("route_id")

    assert routes.loc["OP:R1", "trip_count"] == 3
    assert routes.loc["OP:R1", "stop_count"] == 2
    assert routes.loc["OP:R1", "service_days"] == 7
    assert routes.loc["OP:R1", "scheduled_service_intensity"] == pytest.approx(12 / 7)
    assert routes.loc["OP:R1", "route_name"] == "1 | North"
    assert routes.loc["OP:R3", "trip_count"] == 0
    assert routes.loc["OP:R3", "stop_count"] == 0
    assert routes.loc["OP:R3", "service_days"] == 0


def test_stop_connectivity_and_top_connected_stops() -> None:
    stops = build_stop_connectivity(make_eda_tables()).set_index("stop_id")

    assert stops.loc["OP:S1", "routes_per_stop"] == 2
    assert stops.loc["OP:S1", "trips_per_stop"] == 3
    assert stops.loc["OP:S4", "routes_per_stop"] == 0
    assert stops.loc["OP:S4", "trips_per_stop"] == 0
    assert top_connected_stops(stops.reset_index(), top_n=1).iloc[0]["stop_id"] == "OP:S1"
    assert top_connected_stops(
        stops.reset_index(), top_n=1, metric="trips_per_stop"
    ).iloc[0]["stop_id"] == "OP:S1"


def test_hourly_service_keeps_extended_gtfs_times_and_arrival_fallback() -> None:
    hourly = build_hourly_service(make_eda_tables()["stop_times"]).set_index(
        "service_day_hour"
    )

    assert hourly.loc[25, "clock_hour"] == 1
    assert hourly.loc[25, "service_day_offset"] == 1
    assert hourly.loc[25, "scheduled_departure_count"] == 1
    assert hourly.loc[24, "clock_hour"] == 0
    assert hourly.loc[1, "scheduled_departure_count"] == 1


def test_weekday_service_uses_calendar_flags_not_stop_times() -> None:
    weekday = build_weekday_service(make_eda_tables()).set_index("weekday")

    assert weekday.loc["Monday", "scheduled_trip_count"] == 3
    assert weekday.loc["Friday", "scheduled_trip_count"] == 3
    assert weekday.loc["Saturday", "scheduled_trip_count"] == 1
    assert weekday.loc["Sunday", "scheduled_trip_count"] == 1


def test_operator_comparison_uses_network_counts_and_route_averages() -> None:
    comparison = build_operator_comparison(make_eda_tables()).iloc[0]

    assert comparison["operator"] == "OP"
    assert comparison["routes"] == 3
    assert comparison["stops"] == 4
    assert comparison["trips"] == 4
    assert comparison["stop_times"] == 3
    assert comparison["average_trips_per_route"] == pytest.approx(4 / 3)
    assert comparison["average_stops_per_route"] == pytest.approx(4 / 3)


def test_empty_inputs_return_empty_eda_tables() -> None:
    outputs = build_eda_tables({})

    assert outputs
    assert all(frame.empty for frame in outputs.values())


def test_missing_optional_names_and_calendar_columns_are_not_invented() -> None:
    tables = {
        "routes": pd.DataFrame({"feed_id": ["OP"], "route_id": ["OP:R1"]}),
        "trips": pd.DataFrame(
            {"feed_id": ["OP"], "route_id": ["OP:R1"], "trip_id": ["OP:T1"]}
        ),
    }

    routes = build_route_analytics(tables)

    assert "route_name" not in routes.columns
    assert routes.loc[0, "trip_count"] == 1
    assert pd.isna(routes.loc[0, "service_days"])
    assert pd.isna(routes.loc[0, "scheduled_service_intensity"])


def test_empty_hourly_input_has_stable_schema() -> None:
    hourly = build_hourly_service(pd.DataFrame(columns=["feed_id"]))

    assert hourly.empty
    assert "service_day_hour" in hourly.columns
    assert "clock_hour" in hourly.columns
