"""Synthetic tests for GTFS scheduled-service accessibility analytics."""

import pandas as pd
import pytest

from src.analysis.gtfs_service import (
    build_accessibility_score,
    build_route_service_profile,
    build_service_accessibility_analytics,
    build_temporal_service_profile,
)


def make_tables() -> dict[str, pd.DataFrame]:
    """Return a small synthetic schedule; no values represent real service."""
    return {
        "routes": pd.DataFrame({"feed_id": ["A", "A", "B"], "route_id": ["A:r1", "A:r2", "B:r1"]}),
        "stops": pd.DataFrame({"feed_id": ["A", "A", "A", "B"], "stop_id": ["A:s1", "A:s2", "A:s3", "B:s1"]}),
        "trips": pd.DataFrame({"feed_id": ["A", "A", "A", "B"], "trip_id": ["A:t1", "A:t2", "A:t3", "B:t1"], "route_id": ["A:r1", "A:r1", "A:r2", "B:r1"], "service_id": ["A:w", "A:w", "A:w", "B:w"]}),
        "stop_times": pd.DataFrame({"feed_id": ["A"] * 5 + ["B"], "trip_id": ["A:t1", "A:t1", "A:t2", "A:t3", "A:t3", "B:t1"], "stop_id": ["A:s1", "A:s2", "A:s1", "A:s2", "A:s3", "B:s1"], "stop_sequence": [1, 2, 1, 1, 2, 1], "departure_time": ["25:30:00", "25:45:00", "08:00:00", "09:00:00", "09:15:00", "07:00:00"]}),
        "route_stops": pd.DataFrame({"feed_id": ["A"] * 3 + ["B"], "route_id": ["A:r1", "A:r1", "A:r2", "B:r1"], "stop_id": ["A:s1", "A:s2", "A:s2", "B:s1"], "trip_count": [2, 2, 1, 1], "service_count": [1, 1, 1, 1]}),
        "route_service_summary": pd.DataFrame({"feed_id": ["A", "A", "B"], "route_id": ["A:r1", "A:r2", "B:r1"], "first_departure_seconds": [28800, 32400, 25200], "last_arrival_seconds": [92700, 33300, 27000]}),
        "stop_service_summary": pd.DataFrame({"feed_id": ["A"] * 3 + ["B"], "stop_id": ["A:s1", "A:s2", "A:s3", "B:s1"], "route_count": [1, 2, 0, 1], "trip_count": [2, 3, 0, 1]}),
        "calendar": pd.DataFrame({"feed_id": ["A", "B"], "service_id": ["A:w", "B:w"], "monday": [1, 1], "tuesday": [1, 1], "wednesday": [1, 1], "thursday": [1, 1], "friday": [1, 1], "saturday": [0, 0], "sunday": [0, 0], "start_date": pd.to_datetime(["2026-01-01"] * 2), "end_date": pd.to_datetime(["2026-01-07"] * 2)}),
    }


def test_builds_deterministic_profiles_and_keeps_feeds_isolated() -> None:
    result = build_service_accessibility_analytics(make_tables())
    routes = result["route_service_profile"].set_index(["feed_id", "route_id"])
    assert routes.loc[("A", "A:r1"), "scheduled_trip_count"] == 2
    assert routes.loc[("A", "A:r1"), "active_service_id_count"] == 1
    assert routes.loc[("A", "A:r1"), "scheduled_service_span_seconds"] == 63900
    assert routes.loc[("A", "A:r1"), "unique_scheduled_service_day_count"] == 5
    assert routes.loc[("A", "A:r1"), "trips_per_service_day"] == 2
    assert routes.loc[("A", "A:r1"), "overlapping_route_count"] == 1
    assert routes.loc[("A", "A:r1"), "maximum_scheduled_headway_seconds"] == 63000
    assert routes.loc[("B", "B:r1"), "overlapping_route_count"] == 0
    assert result["route_service_profile"]["route_id"].tolist() == ["A:r1", "A:r2", "B:r1"]
    assert result["stop_service_profile"].set_index("stop_id").loc["A:s3", "service_connectivity_category"] == "isolated"


def test_extended_service_day_hour_is_preserved() -> None:
    profile = build_temporal_service_profile(make_tables())
    row = profile.loc[profile["service_day_hour"].eq(25)].iloc[0]
    assert row["clock_hour"] == 1
    assert row["service_day_offset"] == 1


def test_missing_calendar_keeps_unique_service_dates_undefined() -> None:
    tables = make_tables()
    tables.pop("calendar")
    result = build_service_accessibility_analytics(tables)
    assert result["route_service_profile"]["unique_scheduled_service_day_count"].isna().all()
    assert result["quality_report"].loc[lambda frame: frame.table.eq("calendar_dates"), "note"].iloc[0].startswith("Absent")


def test_empty_and_optional_inputs_have_stable_outputs() -> None:
    result = build_service_accessibility_analytics({})
    assert all(frame.empty for name, frame in result.items() if name != "quality_report")
    assert not result["quality_report"].empty
    partial = build_service_accessibility_analytics({"routes": pd.DataFrame({"feed_id": ["X"], "route_id": ["X:r"]})})
    assert pd.isna(partial["route_service_profile"].loc[0, "scheduled_departure_count"])
    partial_feed = partial["feed_service_summary"].iloc[0]
    assert pd.isna(partial_feed["scheduled_trip_count"])
    assert pd.isna(partial_feed["mean_scheduled_service_span_seconds"])


def test_zero_denominators_and_score_weights_are_explicit() -> None:
    frame = pd.DataFrame({"feed_id": ["X", "X"], "route_id": ["X:a", "X:b"], "scheduled_trip_count": [0, 2], "overlapping_route_count": [0, 1], "scheduled_service_span_seconds": [0, 3600], "stop_count": [0, 2], "active_service_weekday_count": [0, 2]})
    score = build_accessibility_score(frame, {"frequency": 2, "connectivity": 1, "service_span": 1, "stop_coverage": 0})
    assert score["gtfs_service_accessibility_score"].between(0, 1).all()
    assert score.loc[0, "gtfs_service_accessibility_score"] == 0
    missing_weighted_component = frame.iloc[[0]].copy()
    missing_weighted_component["scheduled_trip_count"] = pd.NA
    zero_weight_score = build_accessibility_score(
        missing_weighted_component,
        {"frequency": 1, "connectivity": 0, "service_span": 0, "stop_coverage": 0},
    )
    assert pd.isna(zero_weight_score.loc[0, "gtfs_service_accessibility_score"])
    with pytest.raises(ValueError):
        build_accessibility_score(frame, {"frequency": -1})


def test_unique_dates_are_not_conflated_with_service_ids() -> None:
    result = build_service_accessibility_analytics(make_tables())
    profile = result["route_service_profile"].set_index(["feed_id", "route_id"])
    assert profile.loc[("A", "A:r1"), "active_service_id_count"] == 1
    assert profile.loc[("A", "A:r1"), "unique_scheduled_service_day_count"] == 5


def test_calendar_exceptions_adjust_scheduled_date_counts() -> None:
    tables = make_tables()
    tables["calendar_dates"] = pd.DataFrame({"feed_id": ["A", "A"], "service_id": ["A:w", "A:w"], "date": pd.to_datetime(["2026-01-05", "2026-01-10"]), "exception_type": [2, 1]})
    profile = build_service_accessibility_analytics(tables)["route_service_profile"].set_index(["feed_id", "route_id"])
    assert profile.loc[("A", "A:r1"), "unique_scheduled_service_day_count"] == 5


def test_zero_active_calendar_days_produces_zero_dates_and_missing_daily_rate() -> None:
    tables = make_tables()
    for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
        tables["calendar"].loc[0, day] = 0
    profile = build_service_accessibility_analytics(tables)["route_service_profile"].set_index(["feed_id", "route_id"])
    assert profile.loc[("A", "A:r1"), "unique_scheduled_service_day_count"] == 0
    assert pd.isna(profile.loc[("A", "A:r1"), "trips_per_service_day"])


def test_missing_calendar_flag_keeps_date_metrics_undefined() -> None:
    tables = make_tables()
    tables["calendar"].loc[0, "monday"] = pd.NA
    profile = build_service_accessibility_analytics(tables)["route_service_profile"].set_index(["feed_id", "route_id"])
    assert pd.isna(profile.loc[("A", "A:r1"), "unique_scheduled_service_day_count"])
    assert pd.isna(profile.loc[("A", "A:r1"), "active_service_weekday_count"])
    stops = build_service_accessibility_analytics(tables)["stop_service_profile"].set_index(["feed_id", "stop_id"])
    assert pd.isna(stops.loc[("A", "A:s1"), "scheduled_weekday_service_count"])


def test_departure_count_without_sequence_counts_available_event_rows() -> None:
    tables = {
        "routes": pd.DataFrame({"feed_id": ["X"], "route_id": ["X:r"]}),
        "trips": pd.DataFrame({"feed_id": ["X"], "trip_id": ["X:t"], "route_id": ["X:r"]}),
        "stop_times": pd.DataFrame({"feed_id": ["X", "X"], "trip_id": ["X:t", "X:t"], "departure_time": ["07:00:00", "07:15:00"]}),
    }
    profile = build_route_service_profile(tables)
    assert profile.loc[0, "scheduled_departure_count"] == 2

    tables["stop_times"]["stop_sequence"] = pd.Series([pd.NA, pd.NA], dtype="Int64")
    profile = build_route_service_profile(tables)
    assert profile.loc[0, "scheduled_departure_count"] == 2


def test_malformed_calendar_dates_do_not_silently_ignore_exceptions() -> None:
    tables = make_tables()
    tables["calendar_dates"] = pd.DataFrame({"feed_id": ["A"], "service_id": ["A:w"], "date": [pd.Timestamp("2026-01-05")]})
    profile = build_service_accessibility_analytics(tables)["route_service_profile"].set_index(["feed_id", "route_id"])
    assert pd.isna(profile.loc[("A", "A:r1"), "unique_scheduled_service_day_count"])
    quality = build_service_accessibility_analytics(tables)["quality_report"].set_index("table")
    assert "exception_type" in quality.loc["calendar_dates", "missing_fields"]


def test_unmatched_calendar_service_does_not_become_zero_stop_service() -> None:
    tables = make_tables()
    tables["calendar"] = tables["calendar"].loc[tables["calendar"]["feed_id"].ne("A")]
    analytics = build_service_accessibility_analytics(tables)
    stop_profile = analytics["stop_service_profile"].set_index(["feed_id", "stop_id"])
    assert pd.isna(stop_profile.loc[("A", "A:s1"), "scheduled_weekday_service_count"])
