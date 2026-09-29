"""Structural and referential validation for GTFS schedule feeds."""

from dataclasses import dataclass
import re
from typing import Literal

import pandas as pd

from src.data.ingestion import GTFSFeed, GTFS_REQUIRED_FILES, validate_required_gtfs_files


Severity = Literal["error", "warning"]

REQUIRED_COLUMNS = {
    "agency": ("agency_name", "agency_url", "agency_timezone"),
    "routes": ("route_id", "route_type"),
    "stops": ("stop_id", "stop_name", "stop_lat", "stop_lon"),
    "trips": ("route_id", "service_id", "trip_id"),
    "stop_times": ("trip_id", "stop_id", "stop_sequence"),
    "calendar": (
        "service_id",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "start_date",
        "end_date",
    ),
    "calendar_dates": ("service_id", "date", "exception_type"),
    "shapes": ("shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"),
    "fare_attributes": (
        "fare_id",
        "price",
        "currency_type",
        "payment_method",
        "transfers",
    ),
    "fare_rules": ("fare_id",),
    "frequencies": ("trip_id", "start_time", "end_time", "headway_secs"),
}

IDENTIFIER_COLUMNS = {
    "agency": ("agency_id",),
    "routes": ("route_id",),
    "stops": ("stop_id",),
    "trips": ("trip_id", "route_id", "service_id"),
    "stop_times": ("trip_id", "stop_id", "stop_sequence"),
    "calendar": ("service_id",),
    "calendar_dates": ("service_id", "date"),
    "shapes": ("shape_id", "shape_pt_sequence"),
    "fare_attributes": ("fare_id",),
    "fare_rules": ("fare_id",),
}

DUPLICATE_KEYS = {
    "agency": ("agency_id",),
    "routes": ("route_id",),
    "stops": ("stop_id",),
    "trips": ("trip_id",),
    "calendar": ("service_id",),
    "shapes": ("shape_id", "shape_pt_sequence"),
    "fare_attributes": ("fare_id",),
    "stop_times": ("trip_id", "stop_sequence"),
    "calendar_dates": ("service_id", "date"),
}

TIME_PATTERN = re.compile(r"\d+:[0-5]\d:[0-5]\d")


@dataclass(frozen=True)
class GTFSValidationIssue:
    """One actionable GTFS validation finding."""

    severity: Severity
    code: str
    table: str
    message: str


@dataclass(frozen=True)
class GTFSValidationReport:
    """Collection of validation findings for a GTFS feed."""

    issues: tuple[GTFSValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Whether the feed has no error-severity findings."""
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def errors(self) -> tuple[GTFSValidationIssue, ...]:
        """Return error-severity findings."""
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[GTFSValidationIssue, ...]:
        """Return warning-severity findings."""
        return tuple(issue for issue in self.issues if issue.severity == "warning")


def _is_missing(values: pd.Series) -> pd.Series:
    return values.isna() | values.astype("string").str.strip().eq("")


def _append_issue(
    issues: list[GTFSValidationIssue],
    severity: Severity,
    code: str,
    table: str,
    message: str,
) -> None:
    issues.append(GTFSValidationIssue(severity, code, table, message))


def validate_gtfs_structure(feed: GTFSFeed) -> GTFSValidationReport:
    """Check GTFS file requirements, schemas, keys, references, times, and coordinates."""
    issues: list[GTFSValidationIssue] = []
    missing_required = validate_required_gtfs_files(feed.available_files)
    for filename in missing_required:
        _append_issue(
            issues,
            "error",
            "missing_required_file",
            filename,
            "Required GTFS file is absent.",
        )
    has_service_definition = any(
        table_name in feed.tables
        and "service_id" in feed.tables[table_name].columns
        and (~_is_missing(feed.tables[table_name]["service_id"])).any()
        for table_name in ("calendar", "calendar_dates")
    )
    if not has_service_definition:
        _append_issue(
            issues,
            "error",
            "missing_service_calendar",
            "calendar",
            "At least one of calendar.txt or calendar_dates.txt is required.",
        )

    for filename in feed.missing_optional_files:
        _append_issue(
            issues,
            "warning",
            "missing_optional_file",
            filename,
            "Optional GTFS file is absent.",
        )

    required_table_names = {filename.removesuffix(".txt") for filename in GTFS_REQUIRED_FILES}
    for table_name, table in feed.tables.items():
        if table.empty:
            severity: Severity = "error" if table_name in required_table_names else "warning"
            _append_issue(
                issues, severity, "empty_table", table_name, "GTFS table has no rows."
            )

    for table_name, required_columns in REQUIRED_COLUMNS.items():
        table = feed.tables.get(table_name)
        if table is None:
            continue

        missing_columns = set(required_columns).difference(table.columns)
        if table_name == "routes" and not {
            "route_short_name",
            "route_long_name",
        }.intersection(table.columns):
            missing_columns.add("route_short_name or route_long_name")
        if table_name == "stop_times" and not {
            "arrival_time",
            "departure_time",
        }.intersection(table.columns):
            missing_columns.add("arrival_time or departure_time")
        if missing_columns:
            _append_issue(
                issues,
                "error",
                "missing_columns",
                table_name,
                "Missing required columns: " + ", ".join(sorted(missing_columns)),
            )

    _validate_identifiers(feed, issues)
    _validate_foreign_keys(feed, issues)
    _validate_stop_times(feed, issues)
    _validate_dates(feed, issues)
    _validate_service_periods(feed, issues)
    _validate_coordinates(feed, issues)
    return GTFSValidationReport(tuple(issues))


def _validate_identifiers(
    feed: GTFSFeed, issues: list[GTFSValidationIssue]
) -> None:
    for table_name, columns in IDENTIFIER_COLUMNS.items():
        table = feed.tables.get(table_name)
        if table is None:
            continue
        for column in columns:
            if column not in table.columns:
                continue
            missing = _is_missing(table[column])
            missing_count = int(missing.sum())
            if missing_count:
                _append_issue(
                    issues,
                    "error",
                    "missing_id",
                    table_name,
                    f"{missing_count} row(s) have a missing {column}.",
                )

    for table_name, columns in DUPLICATE_KEYS.items():
        table = feed.tables.get(table_name)
        if table is None or not set(columns).issubset(table.columns):
            continue
        duplicate_count = int(table.duplicated(subset=list(columns), keep=False).sum())
        if duplicate_count:
            key_name = ", ".join(columns)
            _append_issue(
                issues,
                "error",
                "duplicate_id",
                table_name,
                f"{duplicate_count} row(s) duplicate key ({key_name}).",
            )


def _validate_foreign_keys(
    feed: GTFSFeed, issues: list[GTFSValidationIssue]
) -> None:
    relationships = (
        ("routes", "agency_id", "agency", "agency_id"),
        ("trips", "route_id", "routes", "route_id"),
        ("stop_times", "trip_id", "trips", "trip_id"),
        ("stop_times", "stop_id", "stops", "stop_id"),
        ("trips", "shape_id", "shapes", "shape_id"),
        ("fare_rules", "fare_id", "fare_attributes", "fare_id"),
        ("fare_rules", "route_id", "routes", "route_id"),
    )
    for source_name, source_column, target_name, target_column in relationships:
        source = feed.tables.get(source_name)
        target = feed.tables.get(target_name)
        if (
            source is None
            or target is None
            or source_column not in source.columns
            or target_column not in target.columns
        ):
            continue
        source_values = source[source_column].astype("string").str.strip()
        target_values = set(target[target_column].astype("string").str.strip())
        invalid = ~_is_missing(source[source_column]) & ~source_values.isin(target_values)
        invalid_count = int(invalid.sum())
        if invalid_count:
            _append_issue(
                issues,
                "error",
                "invalid_foreign_key",
                source_name,
                f"{invalid_count} row(s) reference unknown {target_name}.{target_column} values.",
            )

    service_ids: set[str] = set()
    for table_name in ("calendar", "calendar_dates"):
        table = feed.tables.get(table_name)
        if table is not None and "service_id" in table.columns:
            service_ids.update(table["service_id"].astype("string").str.strip())
    trips = feed.tables.get("trips")
    if trips is not None and "service_id" in trips.columns:
        trip_services = trips["service_id"].astype("string").str.strip()
        invalid = ~_is_missing(trips["service_id"]) & ~trip_services.isin(service_ids)
        invalid_count = int(invalid.sum())
        if invalid_count:
            _append_issue(
                issues,
                "error",
                "invalid_foreign_key",
                "trips",
                f"{invalid_count} row(s) reference unknown calendar service_id values.",
            )


def _validate_stop_times(feed: GTFSFeed, issues: list[GTFSValidationIssue]) -> None:
    for table_name, columns in (
        ("stop_times", ("arrival_time", "departure_time")),
        ("frequencies", ("start_time", "end_time")),
    ):
        table = feed.tables.get(table_name)
        if table is None:
            continue
        for column in columns:
            if column not in table.columns:
                continue
            values = table[column].astype("string").str.strip()
            malformed = ~_is_missing(table[column]) & ~values.str.fullmatch(TIME_PATTERN)
            malformed_count = int(malformed.sum())
            if malformed_count:
                _append_issue(
                    issues,
                    "error",
                    "malformed_time",
                    table_name,
                    f"{malformed_count} malformed {column} value(s); expected H:MM:SS.",
                )

    table = feed.tables.get("stop_times")
    if table is None:
        return
    if {"arrival_time", "departure_time"}.issubset(table.columns):
        no_time = _is_missing(table["arrival_time"]) & _is_missing(table["departure_time"])
        if no_time.any():
            _append_issue(
                issues,
                "error",
                "missing_stop_time",
                "stop_times",
                f"{int(no_time.sum())} row(s) have neither arrival_time nor departure_time.",
            )


def _validate_dates(feed: GTFSFeed, issues: list[GTFSValidationIssue]) -> None:
    date_columns = (
        ("calendar", "start_date"),
        ("calendar", "end_date"),
        ("calendar_dates", "date"),
    )
    for table_name, column in date_columns:
        table = feed.tables.get(table_name)
        if table is None or column not in table.columns:
            continue
        values = table[column].astype("string").str.strip()
        parsed = pd.to_datetime(values, format="%Y%m%d", errors="coerce")
        malformed = _is_missing(table[column]) | parsed.isna()
        malformed_count = int(malformed.sum())
        if malformed_count:
            _append_issue(
                issues,
                "error",
                "malformed_date",
                table_name,
                f"{malformed_count} malformed {column} value(s); expected YYYYMMDD.",
            )


def _validate_service_periods(
    feed: GTFSFeed, issues: list[GTFSValidationIssue]
) -> None:
    table = feed.tables.get("calendar")
    if table is None or not {"start_date", "end_date"}.issubset(table.columns):
        return
    starts = pd.to_datetime(table["start_date"], format="%Y%m%d", errors="coerce")
    ends = pd.to_datetime(table["end_date"], format="%Y%m%d", errors="coerce")
    comparable = starts.notna() & ends.notna()
    invalid = comparable & starts.gt(ends)
    invalid_count = int(invalid.sum())
    if invalid_count:
        _append_issue(
            issues,
            "error",
            "invalid_service_period",
            "calendar",
            f"{invalid_count} service period(s) have start_date after end_date.",
        )


def _validate_coordinates(feed: GTFSFeed, issues: list[GTFSValidationIssue]) -> None:
    coordinate_columns = (
        ("stops", "stop_lat", -90.0, 90.0),
        ("stops", "stop_lon", -180.0, 180.0),
        ("shapes", "shape_pt_lat", -90.0, 90.0),
        ("shapes", "shape_pt_lon", -180.0, 180.0),
    )
    for table_name, column, lower, upper in coordinate_columns:
        table = feed.tables.get(table_name)
        if table is None or column not in table.columns:
            continue
        values = pd.to_numeric(table[column], errors="coerce")
        invalid = values.isna() | values.lt(lower) | values.gt(upper)
        invalid_count = int(invalid.sum())
        if invalid_count:
            _append_issue(
                issues,
                "error",
                "malformed_coordinate",
                table_name,
                f"{invalid_count} invalid {column} value(s); expected {lower:g} to {upper:g}.",
            )