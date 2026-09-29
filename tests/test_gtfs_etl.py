"""Deterministic tests using SYNTHETIC TEST DATA - NOT REAL HYDERABAD DATA."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import pytest

from src.data.gtfs_etl import (
    build_unified_mobility_layer,
    normalize_gtfs_feed,
    parse_gtfs_time,
    run_gtfs_etl,
)
from src.data.ingestion import GTFSFeed, GTFS_OPTIONAL_FILES


@pytest.mark.parametrize(
    ("value", "expected_seconds"),
    [
        ("00:00:00", 0),
        ("00:15:00", 900),
        ("12:30:15", 45015),
        ("24:00:00", 86400),
        ("24:30:00", 88200),
        ("25:30:00", 91800),
        ("25:45:00", 92700),
    ],
)
def test_parse_gtfs_time(value: str, expected_seconds: int) -> None:
    """Valid service-day times convert to integer seconds, including >24h."""
    assert parse_gtfs_time(value) == expected_seconds


@pytest.mark.parametrize("value", ["", "8:00", "08:60:00", "08:00:60", "-1:00:00", "abc"])
def test_parse_gtfs_time_rejects_malformed_values(value: str) -> None:
    """Malformed GTFS time strings are rejected rather than coerced."""
    with pytest.raises(ValueError):
        parse_gtfs_time(value)


def make_synthetic_feed(route_id: str = " 123 ") -> GTFSFeed:
    """Return a tiny synthetic GTFS feed for deterministic ETL tests."""
    tables = {
        "agency": pd.DataFrame(
            {
                "agency_id": ["A1"],
                "agency_name": [" Synthetic Test Agency "],
                "agency_url": ["https://example.invalid"],
                "agency_timezone": ["Asia/Kolkata"],
                "agency_lang": ["en"],
            }
        ),
        "routes": pd.DataFrame(
            {
                "route_id": [route_id],
                "agency_id": ["A1"],
                "route_short_name": [" R1 "],
                "route_long_name": ["   "],
                "route_type": ["3"],
            }
        ),
        "stops": pd.DataFrame(
            {
                "stop_id": [" 01 ", "02"],
                "stop_name": [" Synthetic Stop A ", "Synthetic Stop B"],
                "stop_lat": ["17.0", "17.1"],
                "stop_lon": ["78.0", "78.1"],
                "zone_id": ["", "Z1"],
            }
        ),
        "trips": pd.DataFrame(
            {
                "route_id": [route_id, route_id],
                "service_id": ["WK", "WK"],
                "trip_id": ["T1", "T2"],
                "direction_id": ["0", "1"],
            }
        ),
        "stop_times": pd.DataFrame(
            {
                "trip_id": ["T1", "T1", "T2", "T2"],
                "arrival_time": ["23:50:00", "25:30:00", "00:14:00", "00:45:00"],
                "departure_time": ["24:00:00", "25:31:00", "00:15:00", "00:46:00"],
                "stop_id": [" 01 ", "02", " 01 ", "02"],
                "stop_sequence": ["1", "2", "1", "2"],
                "shape_dist_traveled": ["0", "1.5", "0", "1.5"],
            }
        ),
        "calendar": pd.DataFrame(
            {
                "service_id": ["WK"],
                "monday": ["1"],
                "tuesday": ["1"],
                "wednesday": ["1"],
                "thursday": ["1"],
                "friday": ["1"],
                "saturday": ["0"],
                "sunday": ["0"],
                "start_date": ["20260101"],
                "end_date": ["20261231"],
            }
        ),
    }
    files = tuple(f"{name}.txt" for name in tables)
    return GTFSFeed(
        source_path=Path("synthetic_test_feed.zip"),
        tables=tables,
        available_files=tuple(sorted(files)),
        missing_required_files=(),
        missing_optional_files=tuple(
            filename for filename in GTFS_OPTIONAL_FILES if filename not in files
        ),
    )


def test_feed_and_source_ids_are_preserved_and_namespaced() -> None:
    """Same source identifiers remain distinct across feed namespaces."""
    feed = make_synthetic_feed()
    layer = build_unified_mobility_layer(
        {"TGSRTC": feed, "HMRL": make_synthetic_feed()}
    )

    routes = layer["routes"].sort_values("feed_id").reset_index(drop=True)
    assert routes["feed_id"].tolist() == ["HMRL", "TGSRTC"]
    assert routes["route_id"].tolist() == ["HMRL:123", "TGSRTC:123"]
    assert routes["source_route_id"].tolist() == [" 123 ", " 123 "]
    assert layer["trips"]["route_id"].nunique() == 2
    for table in layer.values():
        assert set(table["feed_id"].dropna()).issubset({"TGSRTC", "HMRL"})


def test_normalization_trims_text_converts_blanks_and_numeric_dates() -> None:
    """Canonical text, numbers, nulls, and service dates use stable types."""
    source = make_synthetic_feed()
    normalized = normalize_gtfs_feed(source, "TGSRTC")

    route = normalized["routes"].iloc[0]
    stop = normalized["stops"].iloc[0]
    calendar = normalized["calendar"].iloc[0]
    assert route["route_short_name"] == "R1"
    assert pd.isna(route["route_long_name"])
    assert route["route_type"] == 3
    assert stop["stop_id"] == "TGSRTC:01"
    assert stop["source_stop_id"] == " 01 "
    assert stop["stop_lat"] == pytest.approx(17.0)
    assert pd.isna(normalized["stops"].loc[0, "zone_id"])
    assert calendar["start_date"] == pd.Timestamp("2026-01-01")
    assert calendar["end_date"] == pd.Timestamp("2026-12-31")
    assert "calendar_dates" not in normalized
    assert source.tables["routes"].loc[0, "route_short_name"] == " R1 "


def test_stop_times_preserve_text_and_derive_extended_seconds() -> None:
    """Extended GTFS clocks remain intact while seconds are derived correctly."""
    normalized = normalize_gtfs_feed(make_synthetic_feed(), "TGSRTC")
    stop_times = normalized["stop_times"]

    assert stop_times.loc[1, "arrival_time"] == "25:30:00"
    assert stop_times.loc[1, "arrival_seconds"] == 91800
    assert stop_times.loc[0, "departure_seconds"] == 86400


def test_route_stop_and_service_summaries_are_schedule_based() -> None:
    """Derived relationship and service summaries use only scheduled fields."""
    normalized = normalize_gtfs_feed(make_synthetic_feed(), "TGSRTC")
    route_stops = normalized["route_stops"]
    route_summary = normalized["route_service_summary"].iloc[0]
    stop_summary = normalized["stop_service_summary"].set_index("source_stop_id")

    assert len(route_stops) == 2
    assert route_stops["trip_count"].tolist() == [2, 2]
    assert route_stops["service_count"].tolist() == [1, 1]
    assert route_summary["trip_count"] == 2
    assert route_summary["unique_stop_count"] == 2
    assert route_summary["service_id_count"] == 1
    assert route_summary["first_departure_seconds"] == 900
    assert route_summary["last_arrival_seconds"] == 91800
    assert stop_summary.loc[" 01 ", "route_count"] == 1
    assert stop_summary.loc[" 01 ", "trip_count"] == 2
    assert "passenger_count" not in normalized["route_service_summary"].columns
    assert not any("passenger" in column.lower() for table in normalized.values() for column in table)


def test_normalized_layer_is_deterministic() -> None:
    """Repeated normalization produces identical values and row ordering."""
    first = normalize_gtfs_feed(make_synthetic_feed(), "TGSRTC")
    second = normalize_gtfs_feed(make_synthetic_feed(), "TGSRTC")

    assert first.keys() == second.keys()
    for table_name in first:
        pd.testing.assert_frame_equal(first[table_name], second[table_name])


def test_real_format_writer_creates_parquet_without_overwrite(tmp_path: Path) -> None:
    """The file pipeline writes Parquet and refuses to replace existing data."""
    source_path = tmp_path / "synthetic_gtfs.zip"
    with ZipFile(source_path, "w", compression=ZIP_DEFLATED) as archive:
        for table_name, table in make_synthetic_feed().tables.items():
            archive.writestr(f"{table_name}.txt", table.to_csv(index=False))

    output_path = tmp_path / "processed" / "gtfs"
    report_path = tmp_path / "ETL_QUALITY_REPORT.md"
    run_gtfs_etl({"TGSRTC": source_path}, output_path, report_path)

    assert (output_path / "routes.parquet").is_file()
    assert not (output_path / "calendar_dates.parquet").exists()
    assert pd.read_parquet(output_path / "routes.parquet").loc[0, "route_id"] == "TGSRTC:123"
    quality_report = report_path.read_text(encoding="utf-8")
    assert "| Records filtered | Filter reason |" in quality_report
    assert "No records filtered." in quality_report
    with pytest.raises(FileExistsError):
        run_gtfs_etl({"TGSRTC": source_path}, output_path, tmp_path / "second_report.md")