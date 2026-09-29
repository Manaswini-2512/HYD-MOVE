"""Tests using generated SYNTHETIC TEST DATA - NOT REAL HYDERABAD DATA."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from src.data.gtfs_transform import build_analytics_tables
from src.data.gtfs_validation import validate_gtfs_structure
from src.data.ingestion import discover_gtfs_files, load_gtfs_zip


SYNTHETIC_FIXTURE_LABEL = "SYNTHETIC TEST DATA - NOT REAL HYDERABAD DATA"
SYNTHETIC_GTFS_TABLES = {
    "agency.txt": (
        "agency_id,agency_name,agency_url,agency_timezone\n"
        f"SYN-AGENCY,{SYNTHETIC_FIXTURE_LABEL},https://example.invalid,Etc/UTC\n"
    ),
    "routes.txt": (
        "route_id,agency_id,route_short_name,route_type\n"
        "SYN-ROUTE,SYN-AGENCY,SYN-1,3\n"
    ),
    "stops.txt": (
        "stop_id,stop_name,stop_lat,stop_lon\n"
        "SYN-STOP-1,Synthetic Stop A,0.0,0.0\n"
        "SYN-STOP-2,Synthetic Stop B,0.1,0.1\n"
    ),
    "trips.txt": (
        "route_id,service_id,trip_id\n"
        "SYN-ROUTE,SYN-SERVICE,SYN-TRIP\n"
    ),
    "stop_times.txt": (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "SYN-TRIP,08:00:00,08:00:00,SYN-STOP-1,1\n"
        "SYN-TRIP,08:20:00,08:20:00,SYN-STOP-2,2\n"
    ),
    "calendar.txt": (
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,"
        "start_date,end_date\n"
        "SYN-SERVICE,1,1,1,1,1,0,0,20260101,20261231\n"
    ),
}


def write_synthetic_gtfs_zip(
    path: Path,
    tables: dict[str, str] | None = None,
    omitted_files: tuple[str, ...] = (),
) -> Path:
    """Generate a tiny, clearly synthetic GTFS archive for tests only."""
    selected_tables = SYNTHETIC_GTFS_TABLES if tables is None else tables
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for filename, contents in selected_tables.items():
            if filename not in omitted_files:
                archive.writestr(f"synthetic_test_feed/{filename}", contents)
    return path


@pytest.fixture
def synthetic_gtfs_zip(tmp_path: Path) -> Path:
    """Create the synthetic test-only archive under pytest temporary storage."""
    return write_synthetic_gtfs_zip(tmp_path / "synthetic_gtfs_test.zip")


def test_gtfs_zip_discovery(synthetic_gtfs_zip: Path) -> None:
    """Discovery finds GTFS files in a nested archive directory."""
    files = discover_gtfs_files(synthetic_gtfs_zip)

    assert "agency.txt" in files
    assert files["agency.txt"].startswith("synthetic_test_feed/")


def test_required_file_validation(tmp_path: Path) -> None:
    """The feed reports missing required GTFS files as validation errors."""
    archive_path = write_synthetic_gtfs_zip(
        tmp_path / "missing_required.zip", omitted_files=("stop_times.txt",)
    )
    feed = load_gtfs_zip(archive_path)
    report = validate_gtfs_structure(feed)

    assert feed.missing_required_files == ("stop_times.txt",)
    assert any(issue.code == "missing_required_file" for issue in report.errors)


def test_service_calendar_is_required(tmp_path: Path) -> None:
    """At least one calendar table must define a service ID."""
    archive_path = write_synthetic_gtfs_zip(
        tmp_path / "missing_calendar.zip", omitted_files=("calendar.txt",)
    )
    report = validate_gtfs_structure(load_gtfs_zip(archive_path))

    assert any(issue.code == "missing_service_calendar" for issue in report.errors)


def test_missing_optional_files_are_reported(synthetic_gtfs_zip: Path) -> None:
    """Absent optional files are exposed on the feed and as report warnings."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)
    report = validate_gtfs_structure(feed)

    assert "shapes.txt" in feed.missing_optional_files
    assert any(issue.code == "missing_optional_file" for issue in report.warnings)


def test_schema_validation_reports_missing_columns(tmp_path: Path) -> None:
    """Required GTFS schema columns are checked by table."""
    tables = dict(SYNTHETIC_GTFS_TABLES)
    tables["routes.txt"] = (
        "route_id,agency_id,route_short_name\nSYN-ROUTE,SYN-AGENCY,SYN-1\n"
    )
    feed = load_gtfs_zip(write_synthetic_gtfs_zip(tmp_path / "bad_schema.zip", tables))

    report = validate_gtfs_structure(feed)

    assert any(
        issue.code == "missing_columns" and "route_type" in issue.message
        for issue in report.errors
    )


def test_malformed_coordinates_are_detected(synthetic_gtfs_zip: Path) -> None:
    """Coordinate columns are checked for numeric values and valid ranges."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)
    feed.tables["stops"].loc[0, "stop_lat"] = "91.0"
    feed.tables["stops"].loc[1, "stop_lon"] = "not-a-coordinate"

    report = validate_gtfs_structure(feed)

    coordinate_issues = [
        issue for issue in report.errors if issue.code == "malformed_coordinate"
    ]
    assert len(coordinate_issues) == 2


def test_duplicate_ids_are_detected(synthetic_gtfs_zip: Path) -> None:
    """Entity identifier columns are checked for duplicate values."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)
    feed.tables["stops"].loc[1, "stop_id"] = "SYN-STOP-1"

    report = validate_gtfs_structure(feed)

    assert any(
        issue.code == "duplicate_id" and issue.table == "stops"
        for issue in report.errors
    )


def test_missing_ids_are_detected(synthetic_gtfs_zip: Path) -> None:
    """Required GTFS identifiers cannot be blank."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)
    feed.tables["stops"].loc[0, "stop_id"] = ""

    report = validate_gtfs_structure(feed)

    assert any(
        issue.code == "missing_id" and issue.table == "stops"
        for issue in report.errors
    )


def test_malformed_times_and_dates_are_detected(synthetic_gtfs_zip: Path) -> None:
    """GTFS clock values and service dates use valid schedule formats."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)
    feed.tables["stop_times"].loc[0, "arrival_time"] = "25:61:00"
    feed.tables["calendar"].loc[0, "start_date"] = "20260230"

    report = validate_gtfs_structure(feed)

    assert any(issue.code == "malformed_time" for issue in report.errors)
    assert any(issue.code == "malformed_date" for issue in report.errors)


def test_invalid_service_period_is_detected(synthetic_gtfs_zip: Path) -> None:
    """A calendar range cannot end before it starts."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)
    feed.tables["calendar"].loc[0, "end_date"] = "20251231"

    report = validate_gtfs_structure(feed)

    assert any(issue.code == "invalid_service_period" for issue in report.errors)


def test_extended_gtfs_times_are_valid(synthetic_gtfs_zip: Path) -> None:
    """After-midnight GTFS times with hours above 23 remain valid."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)
    feed.tables["stop_times"].loc[0, "arrival_time"] = "25:30:00"

    report = validate_gtfs_structure(feed)

    assert not any(issue.code == "malformed_time" for issue in report.errors)


def test_invalid_foreign_keys_are_detected(synthetic_gtfs_zip: Path) -> None:
    """Trip references must resolve to an existing route and service."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)
    feed.tables["trips"].loc[0, "route_id"] = "UNKNOWN-ROUTE"

    report = validate_gtfs_structure(feed)

    assert any(
        issue.code == "invalid_foreign_key" and issue.table == "trips"
        for issue in report.errors
    )


def test_empty_optional_table_is_reported_as_warning(tmp_path: Path) -> None:
    """An optional empty GTFS table is reported without invalidating the feed."""
    tables = dict(SYNTHETIC_GTFS_TABLES)
    tables["shapes.txt"] = "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
    feed = load_gtfs_zip(write_synthetic_gtfs_zip(tmp_path / "empty_shapes.zip", tables))

    report = validate_gtfs_structure(feed)

    assert any(
        issue.code == "empty_table" and issue.table == "shapes"
        for issue in report.warnings
    )


def test_synthetic_gtfs_ingestion_preserves_identifiers(synthetic_gtfs_zip: Path) -> None:
    """Ingestion reads tables without extracting or coercing GTFS identifiers."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)

    assert feed.tables["agency"].loc[0, "agency_id"] == "SYN-AGENCY"
    assert feed.tables["stop_times"].loc[1, "stop_sequence"] == "2"
    assert synthetic_gtfs_zip.is_file()
    assert validate_gtfs_structure(feed).is_valid


def test_schedule_summaries_do_not_claim_passenger_demand(
    synthetic_gtfs_zip: Path,
) -> None:
    """Derived tables describe scheduled service rather than ridership."""
    feed = load_gtfs_zip(synthetic_gtfs_zip)

    summaries = build_analytics_tables(feed)

    assert set(summaries) == {
        "route_summary",
        "stop_summary",
        "trip_summary",
        "service_frequency",
        "route_stop_relationships",
    }
    assert summaries["route_summary"].loc[0, "scheduled_trip_count"] == 1
    assert not any(
        "passenger" in column.lower()
        for table in summaries.values()
        for column in table
    )