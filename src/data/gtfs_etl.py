"""Deterministic GTFS normalization and analytics-layer ETL utilities."""

from collections.abc import Mapping
from pathlib import Path
import json
import os
import re
import shutil
import tempfile
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.data.gtfs_validation import validate_gtfs_structure
from src.data.ingestion import GTFSFeed, load_gtfs_zip


_GTFS_TIME_PATTERN = re.compile(r"^(\d+):([0-5]\d):([0-5]\d)$")


def parse_gtfs_time(value: str) -> int:
    """Convert a GTFS ``HH:MM:SS`` time to seconds from service-day midnight.

    GTFS permits hours beyond 23 to represent trips continuing after midnight.

    Raises:
        TypeError: If ``value`` is not a string.
        ValueError: If ``value`` is not a valid GTFS time.
    """
    if not isinstance(value, str):
        raise TypeError("GTFS time must be a string")
    match = _GTFS_TIME_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"Invalid GTFS time: {value!r}")
    hours, minutes, seconds = (int(part) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


TABLE_COLUMNS = {
    "agencies": (
        "feed_id",
        "agency_id",
        "source_agency_id",
        "agency_name",
        "agency_url",
        "agency_timezone",
        "agency_lang",
        "agency_phone",
    ),
    "routes": (
        "feed_id",
        "route_id",
        "source_route_id",
        "agency_id",
        "source_agency_id",
        "route_short_name",
        "route_long_name",
        "route_type",
        "route_color",
        "route_text_color",
    ),
    "stops": (
        "feed_id",
        "stop_id",
        "source_stop_id",
        "stop_name",
        "stop_desc",
        "stop_lat",
        "stop_lon",
        "zone_id",
        "parent_station",
        "source_parent_station",
        "location_type",
        "platform_code",
    ),
    "trips": (
        "feed_id",
        "trip_id",
        "source_trip_id",
        "route_id",
        "source_route_id",
        "service_id",
        "source_service_id",
        "trip_headsign",
        "trip_short_name",
        "direction_id",
        "block_id",
        "shape_id",
        "source_shape_id",
    ),
    "stop_times": (
        "feed_id",
        "trip_id",
        "source_trip_id",
        "arrival_time",
        "arrival_seconds",
        "departure_time",
        "departure_seconds",
        "stop_id",
        "source_stop_id",
        "stop_sequence",
        "timepoint",
        "shape_dist_traveled",
    ),
    "calendar": (
        "feed_id",
        "service_id",
        "source_service_id",
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
    "calendar_dates": (
        "feed_id",
        "service_id",
        "source_service_id",
        "date",
        "exception_type",
    ),
    "route_stops": (
        "feed_id",
        "route_id",
        "source_route_id",
        "stop_id",
        "source_stop_id",
        "stop_sequence",
        "trip_count",
        "service_count",
    ),
    "route_service_summary": (
        "feed_id",
        "route_id",
        "source_route_id",
        "route_short_name",
        "route_long_name",
        "route_type",
        "trip_count",
        "unique_stop_count",
        "service_id_count",
        "first_departure_seconds",
        "last_arrival_seconds",
    ),
    "stop_service_summary": (
        "feed_id",
        "stop_id",
        "source_stop_id",
        "stop_name",
        "route_count",
        "trip_count",
        "first_service_seconds",
        "last_service_seconds",
    ),
}

_STRING_COLUMNS = {
    "feed_id",
    "agency_id",
    "source_agency_id",
    "agency_name",
    "agency_url",
    "agency_timezone",
    "agency_lang",
    "agency_phone",
    "route_id",
    "source_route_id",
    "source_agency_id",
    "route_short_name",
    "route_long_name",
    "route_color",
    "route_text_color",
    "stop_id",
    "source_stop_id",
    "stop_name",
    "stop_desc",
    "zone_id",
    "parent_station",
    "source_parent_station",
    "platform_code",
    "trip_id",
    "source_trip_id",
    "source_service_id",
    "trip_headsign",
    "trip_short_name",
    "block_id",
    "shape_id",
    "source_shape_id",
    "arrival_time",
    "departure_time",
    "service_id",
}
_INTEGER_COLUMNS = {
    "route_type",
    "location_type",
    "direction_id",
    "stop_sequence",
    "timepoint",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "exception_type",
    "trip_count",
    "unique_stop_count",
    "service_id_count",
    "route_count",
    "service_count",
    "arrival_seconds",
    "departure_seconds",
    "first_departure_seconds",
    "last_arrival_seconds",
    "first_service_seconds",
    "last_service_seconds",
}
_FLOAT_COLUMNS = {"stop_lat", "stop_lon", "shape_dist_traveled"}
_DATE_COLUMNS = {"date", "start_date", "end_date"}
_NORMALIZED_TABLES = (
    "agencies",
    "routes",
    "stops",
    "trips",
    "stop_times",
    "calendar",
    "calendar_dates",
    "route_stops",
    "route_service_summary",
    "stop_service_summary",
)
_SOURCE_TABLES = {
    "agencies": "agency",
    "routes": "routes",
    "stops": "stops",
    "trips": "trips",
    "stop_times": "stop_times",
    "calendar": "calendar",
    "calendar_dates": "calendar_dates",
}
_PRIMARY_KEYS = {
    "agencies": ("feed_id", "agency_id"),
    "routes": ("feed_id", "route_id"),
    "stops": ("feed_id", "stop_id"),
    "trips": ("feed_id", "trip_id"),
    "stop_times": ("feed_id", "trip_id", "stop_sequence"),
    "calendar": ("feed_id", "service_id"),
    "calendar_dates": ("feed_id", "service_id", "date"),
    "route_stops": ("feed_id", "route_id", "stop_id"),
    "route_service_summary": ("feed_id", "route_id"),
    "stop_service_summary": ("feed_id", "stop_id"),
}


def _source_text(table: pd.DataFrame, column: str) -> pd.Series:
    """Return source identifiers unchanged except blank-to-null conversion."""
    if column not in table.columns:
        return pd.Series(pd.NA, index=table.index, dtype="string")
    values = table[column].astype("string")
    return values.mask(values.str.strip().eq(""), pd.NA)


def _normalized_text(table: pd.DataFrame, column: str) -> pd.Series:
    """Trim a source text field and convert blank strings to null."""
    if column not in table.columns:
        return pd.Series(pd.NA, index=table.index, dtype="string")
    values = table[column].astype("string").str.strip()
    return values.mask(values.eq(""), pd.NA)


def _canonical_id(feed_id: str, source_ids: pd.Series) -> pd.Series:
    """Prefix nonblank source IDs with their feed to prevent collisions."""
    normalized = source_ids.astype("string").str.strip()
    values = normalized.map(
        lambda value: pd.NA if pd.isna(value) or value == "" else f"{feed_id}:{value}"
    )
    return values.astype("string")


def _numeric(
    table: pd.DataFrame, column: str, dtype: str
) -> pd.Series:
    """Convert a numeric source column, preserving blanks and rejecting junk."""
    text = _normalized_text(table, column)
    converted = pd.to_numeric(text, errors="coerce")
    invalid = text.notna() & converted.isna()
    if invalid.any():
        examples = text.loc[invalid].head(3).tolist()
        raise ValueError(f"Invalid numeric values in {column}: {examples}")
    return converted.astype(dtype)


def _normalized_dates(table: pd.DataFrame, column: str) -> pd.Series:
    """Parse a GTFS YYYYMMDD column without inventing missing dates."""
    text = _normalized_text(table, column)
    parsed = pd.to_datetime(text, format="%Y%m%d", errors="coerce")
    invalid = text.notna() & parsed.isna()
    if invalid.any():
        examples = text.loc[invalid].head(3).tolist()
        raise ValueError(f"Invalid GTFS dates in {column}: {examples}")
    return parsed


def _normalized_times(table: pd.DataFrame, column: str) -> pd.Series:
    """Preserve trimmed GTFS clock text and derive nullable service seconds."""
    text = _normalized_text(table, column)
    seconds = text.map(
        lambda value: pd.NA if pd.isna(value) else parse_gtfs_time(str(value))
    )
    return seconds.astype("Int64")


def _finish_table(table_name: str, values: dict[str, Any], index: pd.Index) -> pd.DataFrame:
    """Apply the stable canonical column order and nullable logical types."""
    frame = pd.DataFrame(values, index=index)
    for column in TABLE_COLUMNS[table_name]:
        if column not in frame.columns:
            frame[column] = pd.Series(pd.NA, index=frame.index)
        if column in _STRING_COLUMNS:
            frame[column] = frame[column].astype("string")
        elif column in _INTEGER_COLUMNS:
            frame[column] = pd.to_numeric(frame[column], errors="raise").astype("Int64")
        elif column in _FLOAT_COLUMNS:
            frame[column] = pd.to_numeric(frame[column], errors="raise").astype("Float64")
        elif column in _DATE_COLUMNS:
            frame[column] = pd.to_datetime(frame[column], errors="raise")
    return frame.loc[:, TABLE_COLUMNS[table_name]]


def _feed_key(feed_id: str) -> str:
    """Validate and normalize a feed namespace used in canonical IDs."""
    normalized = feed_id.strip().upper()
    if not normalized or ":" in normalized:
        raise ValueError("feed_id must be nonblank and must not contain ':'")
    return normalized


def _lookup_id_map(source_ids: pd.Series, canonical_ids: pd.Series) -> dict[str, str]:
    """Map normalized source identifiers to canonical identifiers."""
    lookup: dict[str, str] = {}
    for source_id, canonical_id in zip(source_ids, canonical_ids, strict=True):
        if pd.isna(source_id) or pd.isna(canonical_id):
            continue
        lookup[str(source_id).strip()] = str(canonical_id)
    return lookup


def _remap_reference(
    values: pd.Series,
    lookup: dict[str, str],
    field_name: str,
    fallback: str | None = None,
) -> pd.Series:
    """Map a source foreign key to its normalized ID without dropping rows."""
    source = values.astype("string").str.strip()
    mapped = source.map(lookup)
    blank = source.isna() | source.eq("")
    if fallback is not None:
        mapped = mapped.mask(blank, fallback)
    invalid = ~blank & mapped.isna()
    if invalid.any():
        examples = source.loc[invalid].drop_duplicates().head(3).tolist()
        raise ValueError(f"Unresolved {field_name} references: {examples}")
    return mapped.astype("string")


def _validate_source(feed: GTFSFeed) -> None:
    """Reject source feeds with validation errors; warnings remain reportable."""
    report = validate_gtfs_structure(feed)
    if report.errors:
        details = "; ".join(
            f"{issue.code} [{issue.table}]: {issue.message}" for issue in report.errors
        )
        raise ValueError(f"GTFS feed failed validation: {details}")


def normalize_gtfs_feed(feed: GTFSFeed, feed_id: str) -> dict[str, pd.DataFrame]:
    """Normalize one validated source feed without mutating its input tables.

    Every row receives ``feed_id``; source IDs are retained and canonical IDs
    are namespaced as ``FEED:source_id``. Source fields absent from the
    canonical schema remain available in the immutable source ZIP.
    """
    normalized_feed_id = _feed_key(feed_id)
    _validate_source(feed)

    agency_source = feed.tables["agency"]
    agency_ids = _source_text(agency_source, "agency_id")
    canonical_agency_ids = _canonical_id(normalized_feed_id, agency_ids)
    if canonical_agency_ids.isna().any():
        if len(agency_source) != 1:
            raise ValueError("Missing agency_id can only be normalized for a single-agency feed")
        canonical_agency_ids = canonical_agency_ids.fillna(
            f"{normalized_feed_id}:__single_agency__"
        )
    agency_map = _lookup_id_map(agency_ids, canonical_agency_ids)
    if len(agency_source) == 1:
        implicit_agency_id = str(canonical_agency_ids.iloc[0])
    else:
        implicit_agency_id = None

    agencies = _finish_table(
        "agencies",
        {
            "feed_id": normalized_feed_id,
            "agency_id": canonical_agency_ids,
            "source_agency_id": agency_ids,
            "agency_name": _normalized_text(agency_source, "agency_name"),
            "agency_url": _normalized_text(agency_source, "agency_url"),
            "agency_timezone": _normalized_text(agency_source, "agency_timezone"),
            "agency_lang": _normalized_text(agency_source, "agency_lang"),
            "agency_phone": _normalized_text(agency_source, "agency_phone"),
        },
        agency_source.index,
    )

    route_source = feed.tables["routes"]
    source_route_ids = _source_text(route_source, "route_id")
    route_ids = _canonical_id(normalized_feed_id, source_route_ids)
    source_route_agency_ids = _source_text(route_source, "agency_id")
    route_agency_ids = _remap_reference(
        source_route_agency_ids,
        agency_map,
        "routes.agency_id",
        fallback=implicit_agency_id,
    )
    route_agency_source = source_route_agency_ids
    routes = _finish_table(
        "routes",
        {
            "feed_id": normalized_feed_id,
            "route_id": route_ids,
            "source_route_id": source_route_ids,
            "agency_id": route_agency_ids,
            "source_agency_id": route_agency_source,
            "route_short_name": _normalized_text(route_source, "route_short_name"),
            "route_long_name": _normalized_text(route_source, "route_long_name"),
            "route_type": _numeric(route_source, "route_type", "Int64"),
            "route_color": _normalized_text(route_source, "route_color"),
            "route_text_color": _normalized_text(route_source, "route_text_color"),
        },
        route_source.index,
    )
    route_map = _lookup_id_map(source_route_ids, route_ids)

    stop_source = feed.tables["stops"]
    source_stop_ids = _source_text(stop_source, "stop_id")
    stop_ids = _canonical_id(normalized_feed_id, source_stop_ids)
    stop_map = _lookup_id_map(source_stop_ids, stop_ids)
    source_parent_ids = _source_text(stop_source, "parent_station")
    parent_ids = _remap_reference(
        source_parent_ids, stop_map, "stops.parent_station"
    )
    stops = _finish_table(
        "stops",
        {
            "feed_id": normalized_feed_id,
            "stop_id": stop_ids,
            "source_stop_id": source_stop_ids,
            "stop_code": _normalized_text(stop_source, "stop_code"),
            "stop_name": _normalized_text(stop_source, "stop_name"),
            "stop_desc": _normalized_text(stop_source, "stop_desc"),
            "stop_lat": _numeric(stop_source, "stop_lat", "Float64"),
            "stop_lon": _numeric(stop_source, "stop_lon", "Float64"),
            "zone_id": _normalized_text(stop_source, "zone_id"),
            "parent_station": parent_ids,
            "source_parent_station": source_parent_ids,
            "location_type": _numeric(stop_source, "location_type", "Int64"),
            "platform_code": _normalized_text(stop_source, "platform_code"),
        },
        stop_source.index,
    )

    service_source_ids: list[pd.Series] = []
    for table_name in ("calendar", "calendar_dates"):
        source_table = feed.tables.get(table_name)
        if source_table is not None:
            service_source_ids.append(_source_text(source_table, "service_id"))
    all_service_ids = pd.concat(service_source_ids, ignore_index=True)
    unique_service_ids = all_service_ids.dropna().drop_duplicates()
    service_map = {
        str(source_id).strip(): f"{normalized_feed_id}:{str(source_id).strip()}"
        for source_id in unique_service_ids
    }

    trip_source = feed.tables["trips"]
    source_trip_ids = _source_text(trip_source, "trip_id")
    trip_ids = _canonical_id(normalized_feed_id, source_trip_ids)
    source_trip_route_ids = _source_text(trip_source, "route_id")
    trip_route_ids = _remap_reference(
        source_trip_route_ids, route_map, "trips.route_id"
    )
    source_trip_service_ids = _source_text(trip_source, "service_id")
    trip_service_ids = _remap_reference(
        source_trip_service_ids, service_map, "trips.service_id"
    )
    source_shape_ids = _source_text(trip_source, "shape_id")
    shape_ids = _canonical_id(normalized_feed_id, source_shape_ids)
    trips = _finish_table(
        "trips",
        {
            "feed_id": normalized_feed_id,
            "trip_id": trip_ids,
            "source_trip_id": source_trip_ids,
            "route_id": trip_route_ids,
            "source_route_id": source_trip_route_ids,
            "service_id": trip_service_ids,
            "source_service_id": source_trip_service_ids,
            "trip_headsign": _normalized_text(trip_source, "trip_headsign"),
            "trip_short_name": _normalized_text(trip_source, "trip_short_name"),
            "direction_id": _numeric(trip_source, "direction_id", "Int64"),
            "block_id": _normalized_text(trip_source, "block_id"),
            "shape_id": shape_ids,
            "source_shape_id": source_shape_ids,
        },
        trip_source.index,
    )
    trip_map = _lookup_id_map(source_trip_ids, trip_ids)

    stop_time_source = feed.tables["stop_times"]
    source_stop_time_trip_ids = _source_text(stop_time_source, "trip_id")
    source_stop_time_stop_ids = _source_text(stop_time_source, "stop_id")
    stop_times = _finish_table(
        "stop_times",
        {
            "feed_id": normalized_feed_id,
            "trip_id": _remap_reference(
                source_stop_time_trip_ids, trip_map, "stop_times.trip_id"
            ),
            "source_trip_id": source_stop_time_trip_ids,
            "arrival_time": _normalized_text(stop_time_source, "arrival_time"),
            "arrival_seconds": _normalized_times(stop_time_source, "arrival_time"),
            "departure_time": _normalized_text(stop_time_source, "departure_time"),
            "departure_seconds": _normalized_times(stop_time_source, "departure_time"),
            "stop_id": _remap_reference(
                source_stop_time_stop_ids, stop_map, "stop_times.stop_id"
            ),
            "source_stop_id": source_stop_time_stop_ids,
            "stop_sequence": _numeric(stop_time_source, "stop_sequence", "Int64"),
            "timepoint": _numeric(stop_time_source, "timepoint", "Int64"),
            "shape_dist_traveled": _numeric(
                stop_time_source, "shape_dist_traveled", "Float64"
            ),
        },
        stop_time_source.index,
    )

    calendar_source = feed.tables.get("calendar")
    normalized: dict[str, pd.DataFrame] = {
        "agencies": agencies,
        "routes": routes,
        "stops": stops,
        "trips": trips,
        "stop_times": stop_times,
    }
    if calendar_source is not None:
        calendar_source_ids = _source_text(calendar_source, "service_id")
        normalized["calendar"] = _finish_table(
            "calendar",
            {
                "feed_id": normalized_feed_id,
                "service_id": _remap_reference(
                    calendar_source_ids, service_map, "calendar.service_id"
                ),
                "source_service_id": calendar_source_ids,
                **{
                    day: _numeric(calendar_source, day, "Int64")
                    for day in (
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    )
                },
                "start_date": _normalized_dates(calendar_source, "start_date"),
                "end_date": _normalized_dates(calendar_source, "end_date"),
            },
            calendar_source.index,
        )

    calendar_dates_source = feed.tables.get("calendar_dates")
    if calendar_dates_source is not None:
        exception_service_ids = _source_text(calendar_dates_source, "service_id")
        normalized["calendar_dates"] = _finish_table(
            "calendar_dates",
            {
                "feed_id": normalized_feed_id,
                "service_id": _remap_reference(
                    exception_service_ids, service_map, "calendar_dates.service_id"
                ),
                "source_service_id": exception_service_ids,
                "date": _normalized_dates(calendar_dates_source, "date"),
                "exception_type": _numeric(
                    calendar_dates_source, "exception_type", "Int64"
                ),
            },
            calendar_dates_source.index,
        )

    normalized["route_stops"] = build_route_stops(normalized)
    normalized["route_service_summary"] = build_route_service_summary(normalized)
    normalized["stop_service_summary"] = build_stop_service_summary(normalized)
    validate_normalized_layer(normalized)
    return normalized


def build_route_stops(tables: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Aggregate route-stop links, retaining a representative minimum sequence.

    One row is emitted per feed-scoped route/stop pair. ``stop_sequence`` is
    the minimum source sequence for that pair; trip/service counts are
    schedule structure, not passenger demand.
    """
    trips = tables["trips"]
    stop_times = tables["stop_times"]
    trip_routes = trips[
        ["feed_id", "trip_id", "route_id", "source_route_id", "service_id"]
    ]
    rows = stop_times.merge(
        trip_routes,
        on=["feed_id", "trip_id"],
        how="inner",
        validate="many_to_one",
    )
    if rows.empty:
        return _finish_table("route_stops", {}, pd.RangeIndex(0))
    grouped = rows.groupby(
        [
            "feed_id",
            "route_id",
            "source_route_id",
            "stop_id",
            "source_stop_id",
        ],
        as_index=False,
        dropna=False,
        sort=True,
    ).agg(
        stop_sequence=("stop_sequence", "min"),
        trip_count=("trip_id", "nunique"),
        service_count=("service_id", "nunique"),
    )
    return _finish_table("route_stops", grouped.to_dict("series"), grouped.index)


def build_route_service_summary(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Summarize scheduled trips, stops, services, and route time envelope."""
    routes = tables["routes"]
    trips = tables["trips"]
    stop_times = tables["stop_times"]
    route_stops = tables["route_stops"]

    trip_counts = trips.groupby(["feed_id", "route_id"], as_index=False).agg(
        trip_count=("trip_id", "nunique"),
        service_id_count=("service_id", "nunique"),
    )
    stop_counts = route_stops.groupby(
        ["feed_id", "route_id"], as_index=False
    ).agg(unique_stop_count=("stop_id", "nunique"))

    ordered = stop_times.sort_values(
        ["feed_id", "trip_id", "stop_sequence"], kind="stable"
    )
    departures = ordered.loc[ordered["departure_seconds"].notna()].drop_duplicates(
        ["feed_id", "trip_id"], keep="first"
    )[["feed_id", "trip_id", "departure_seconds"]]
    arrivals = ordered.loc[ordered["arrival_seconds"].notna()].drop_duplicates(
        ["feed_id", "trip_id"], keep="last"
    )[["feed_id", "trip_id", "arrival_seconds"]]
    trip_times = trips[["feed_id", "trip_id", "route_id"]].merge(
        departures, on=["feed_id", "trip_id"], how="left", validate="one_to_one"
    ).merge(
        arrivals, on=["feed_id", "trip_id"], how="left", validate="one_to_one"
    )
    route_times = trip_times.groupby(
        ["feed_id", "route_id"], as_index=False
    ).agg(
        first_departure_seconds=("departure_seconds", "min"),
        last_arrival_seconds=("arrival_seconds", "max"),
    )

    summary = routes[
        [
            "feed_id",
            "route_id",
            "source_route_id",
            "route_short_name",
            "route_long_name",
            "route_type",
        ]
    ].merge(trip_counts, on=["feed_id", "route_id"], how="left").merge(
        stop_counts, on=["feed_id", "route_id"], how="left"
    ).merge(route_times, on=["feed_id", "route_id"], how="left")
    for column in ("trip_count", "unique_stop_count", "service_id_count"):
        summary[column] = summary[column].fillna(0).astype("Int64")
    return _finish_table("route_service_summary", summary.to_dict("series"), summary.index)


def build_stop_service_summary(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Summarize scheduled route/trip coverage and times for each source stop."""
    stops = tables["stops"]
    route_stops = tables["route_stops"]
    stop_times = tables["stop_times"]
    coverage = route_stops.groupby(["feed_id", "stop_id"], as_index=False).agg(
        route_count=("route_id", "nunique"),
        trip_count=("trip_count", "sum"),
    )
    arrival = stop_times.groupby(["feed_id", "stop_id"])["arrival_seconds"].min()
    departure = stop_times.groupby(["feed_id", "stop_id"])["departure_seconds"].min()
    first_times = pd.concat([arrival.rename("arrival"), departure.rename("departure")], axis=1).min(axis=1)
    arrival_last = stop_times.groupby(["feed_id", "stop_id"])["arrival_seconds"].max()
    departure_last = stop_times.groupby(["feed_id", "stop_id"])["departure_seconds"].max()
    last_times = pd.concat(
        [arrival_last.rename("arrival"), departure_last.rename("departure")], axis=1
    ).max(axis=1)
    times = pd.concat(
        [first_times.rename("first_service_seconds"), last_times.rename("last_service_seconds")],
        axis=1,
    ).reset_index()
    summary = stops[
        ["feed_id", "stop_id", "source_stop_id", "stop_name"]
    ].merge(coverage, on=["feed_id", "stop_id"], how="left").merge(
        times, on=["feed_id", "stop_id"], how="left"
    )
    for column in ("route_count", "trip_count"):
        summary[column] = summary[column].fillna(0).astype("Int64")
    return _finish_table("stop_service_summary", summary.to_dict("series"), summary.index)


def validate_normalized_layer(tables: Mapping[str, pd.DataFrame]) -> None:
    """Check normalized IDs, feed lineage, references, and nonnegative counts."""
    for table_name, table in tables.items():
        if "feed_id" not in table.columns:
            raise ValueError(f"{table_name} is missing feed_id")
        keys = _PRIMARY_KEYS.get(table_name)
        if keys and table.duplicated(subset=list(keys)).any():
            raise ValueError(f"{table_name} contains duplicate canonical keys: {keys}")

    agencies = tables["agencies"]
    routes = tables["routes"]
    stops = tables["stops"]
    trips = tables["trips"]
    stop_times = tables["stop_times"]
    _assert_foreign_key(routes, agencies, ("feed_id", "agency_id"), "routes.agency_id")
    _assert_foreign_key(trips, routes, ("feed_id", "route_id"), "trips.route_id")
    _assert_foreign_key(stop_times, trips, ("feed_id", "trip_id"), "stop_times.trip_id")
    _assert_foreign_key(stop_times, stops, ("feed_id", "stop_id"), "stop_times.stop_id")

    service_keys: set[tuple[str, str]] = set()
    for table_name in ("calendar", "calendar_dates"):
        table = tables.get(table_name)
        if table is not None:
            service_keys.update(zip(table["feed_id"], table["service_id"], strict=True))
    trip_service_keys = set(zip(trips["feed_id"], trips["service_id"], strict=True))
    if not trip_service_keys.issubset(service_keys):
        raise ValueError("trips contains service IDs absent from normalized calendars")

    route_stops = tables["route_stops"]
    _assert_foreign_key(route_stops, routes, ("feed_id", "route_id"), "route_stops.route_id")
    _assert_foreign_key(route_stops, stops, ("feed_id", "stop_id"), "route_stops.stop_id")
    for table_name in (
        "route_stops",
        "route_service_summary",
        "stop_service_summary",
    ):
        table = tables[table_name]
        count_columns = [column for column in table if column.endswith("_count")]
        for column in count_columns:
            if table[column].lt(0).any():
                raise ValueError(f"{table_name}.{column} contains a negative count")
    route_summary = tables["route_service_summary"]
    comparable = route_summary["first_departure_seconds"].notna() & route_summary[
        "last_arrival_seconds"
    ].notna()
    if (
        route_summary.loc[comparable, "first_departure_seconds"]
        > route_summary.loc[comparable, "last_arrival_seconds"]
    ).any():
        raise ValueError("A route's first departure is after its last arrival")


def _assert_foreign_key(
    source: pd.DataFrame,
    target: pd.DataFrame,
    columns: tuple[str, str],
    label: str,
) -> None:
    source_keys = set(zip(source[columns[0]], source[columns[1]], strict=True))
    target_keys = set(zip(target[columns[0]], target[columns[1]], strict=True))
    if not source_keys.issubset(target_keys):
        raise ValueError(f"Unresolved normalized relationship: {label}")


def build_unified_mobility_layer(
    feeds: Mapping[str, GTFSFeed],
) -> dict[str, pd.DataFrame]:
    """Normalize multiple feeds independently, then concatenate by table.

    IDs are feed-prefixed before concatenation; source feeds are never joined
    on unqualified IDs.
    """
    normalized_feeds = [
        normalize_gtfs_feed(feed, feed_id) for feed_id, feed in feeds.items()
    ]
    combined: dict[str, pd.DataFrame] = {}
    for table_name in _NORMALIZED_TABLES:
        frames = [tables[table_name] for tables in normalized_feeds if table_name in tables]
        if not frames:
            continue
        combined[table_name] = pd.concat(frames, ignore_index=True)
        sort_columns = [
            column
            for column in _PRIMARY_KEYS.get(table_name, ())
            if column in combined[table_name].columns
        ]
        if sort_columns:
            combined[table_name] = combined[table_name].sort_values(
                sort_columns, kind="stable", ignore_index=True
            )
    validate_normalized_layer(combined)
    return combined


def _duplicate_key_count(table_name: str, table: pd.DataFrame) -> int:
    keys = _PRIMARY_KEYS[table_name]
    return int(table.duplicated(subset=list(keys), keep=False).sum())


def _quality_rows(
    feed: GTFSFeed, tables: Mapping[str, pd.DataFrame]
) -> list[dict[str, Any]]:
    source_table_for_output = {
        "agencies": "agency",
        "routes": "routes",
        "stops": "stops",
        "trips": "trips",
        "stop_times": "stop_times",
        "calendar": "calendar",
        "calendar_dates": "calendar_dates",
        "route_stops": "stop_times",
        "route_service_summary": "trips",
        "stop_service_summary": "stop_times",
    }
    conversions = {
        "agencies": "IDs namespaced; text trimmed; blanks converted to null.",
        "routes": "IDs and agency FK namespaced; route_type converted to nullable integer; text trimmed; blanks to null.",
        "stops": "IDs and parent-station FK namespaced; coordinates converted to nullable floats; location_type converted to nullable integer; text trimmed; blanks to null.",
        "trips": "Trip, route, service, and shape IDs namespaced; direction_id converted to nullable integer; text trimmed; blanks to null.",
        "stop_times": "Trip/stop IDs namespaced; stop_sequence/timepoint converted to nullable integers; shape distance to nullable float; original times retained and seconds derived.",
        "calendar": "Service IDs namespaced; weekday flags converted to nullable integers; dates parsed as datetime64[ns].",
        "calendar_dates": "Service IDs namespaced; exception_type converted to nullable integer; date parsed as datetime64[ns].",
        "route_stops": "Grouped by feed, route, and stop; minimum observed stop_sequence retained; trip/service counts derived.",
        "route_service_summary": "Trips, unique stops, services, earliest first departure, and latest last arrival aggregated by route.",
        "stop_service_summary": "Distinct route/trip counts and observed first/last scheduled times aggregated by stop.",
    }
    rows: list[dict[str, Any]] = []
    for table_name, table in tables.items():
        source_table_name = source_table_for_output[table_name]
        source_table = feed.tables.get(source_table_name)
        if table_name == "route_service_summary":
            before_count = len(feed.tables.get("trips", pd.DataFrame()))
        elif table_name in {"route_stops", "stop_service_summary"}:
            before_count = len(feed.tables.get("stop_times", pd.DataFrame()))
        else:
            before_count = len(source_table) if source_table is not None else None
        null_counts = {
            column: int(count)
            for column, count in table.isna().sum().items()
            if count
        }
        rows.append(
            {
                "table": table_name,
                "rows_before": before_count,
                "rows_after": len(table),
                "columns": list(table.columns),
                "null_counts": null_counts,
                "duplicate_key_rows": _duplicate_key_count(table_name, table),
                "data_type_conversions": conversions[table_name],
                "records_filtered": 0,
                "filter_reason": "No records filtered.",
            }
        )
    return rows


def _format_quality_report(rows_by_feed: Mapping[str, list[dict[str, Any]]]) -> str:
    """Render reproducible ETL row/type/null/duplicate accounting as Markdown."""
    lines = [
        "# Phase 2C ETL Quality Report",
        "",
        "The feeds were normalized independently and appended using feed-prefixed canonical IDs. Original GTFS ZIP files remain unchanged. No passenger-demand fields were created.",
        "",
    ]
    for feed_id, rows in rows_by_feed.items():
        lines.extend([f"## {feed_id}", ""])
        lines.extend(
            [
                "| Table | Rows before | Rows after | Columns | Null counts | Duplicate key rows | Type conversions | Records filtered | Filter reason |",
                "| --- | ---: | ---: | --- | --- | ---: | --- | ---: | --- |",
            ]
        )
        for row in rows:
            before = "Not applicable" if row["rows_before"] is None else str(row["rows_before"])
            columns = ", ".join(row["columns"])
            null_counts = json.dumps(row["null_counts"], sort_keys=True) if row["null_counts"] else "None"
            conversions = row["data_type_conversions"].replace("|", "\\|")
            lines.append(
                f"| `{row['table']}` | {before} | {row['rows_after']} | {columns} | `{null_counts}` | {row['duplicate_key_rows']} | {conversions} | {row['records_filtered']} | {row['filter_reason']} |"
            )
        lines.extend(["", "No records filtered.", ""])
    lines.extend(
        [
            "## Notes",
            "",
            "For derived tables, rows-before counts are the source schedule rows entering aggregation; the lower output row count reflects grouping, not record filtering. Null counts describe the normalized output. Source-specific GTFS tables and fields not mapped to the canonical layer remain available in the immutable raw ZIPs and are documented in `UNIFIED_SCHEMA.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def run_gtfs_etl(
    feed_paths: Mapping[str, str | Path],
    output_directory: str | Path,
    quality_report_path: str | Path,
) -> dict[str, dict[str, int]]:
    """Validate and normalize source feeds sequentially into Parquet files.

    Existing output directories and quality reports are never overwritten.
    Feed processing is sequential so the full shape tables from both source
    archives are not retained in memory together.
    """
    output_path = Path(output_directory)
    report_path = Path(quality_report_path)
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output_path}")
    if report_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing quality report: {report_path}")
    if not feed_paths:
        raise ValueError("At least one GTFS feed path is required")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path = Path(
        tempfile.mkdtemp(prefix=".gtfs-etl-", dir=output_path.parent)
    )
    report_temp_path: Path | None = None
    writers: dict[str, pq.ParquetWriter] = {}
    schemas: dict[str, pa.Schema] = {}
    quality_rows: dict[str, list[dict[str, Any]]] = {}
    output_counts: dict[str, dict[str, int]] = {}
    promoted = False
    try:
        for feed_id, source_path in feed_paths.items():
            feed = load_gtfs_zip(source_path)
            normalized = normalize_gtfs_feed(feed, feed_id)
            normalized_feed_id = _feed_key(feed_id)
            quality_rows[normalized_feed_id] = _quality_rows(feed, normalized)
            output_counts[normalized_feed_id] = {
                table_name: len(table) for table_name, table in normalized.items()
            }
            for table_name, table in normalized.items():
                arrow_table = pa.Table.from_pandas(table, preserve_index=False)
                if table_name not in writers:
                    schemas[table_name] = arrow_table.schema
                    writers[table_name] = pq.ParquetWriter(
                        staging_path / f"{table_name}.parquet",
                        arrow_table.schema,
                        compression="zstd",
                    )
                elif not arrow_table.schema.equals(schemas[table_name], check_metadata=False):
                    try:
                        arrow_table = arrow_table.cast(schemas[table_name])
                    except (pa.ArrowInvalid, pa.ArrowNotImplementedError) as error:
                        raise ValueError(
                            f"Inconsistent Parquet schema for {table_name} in {normalized_feed_id}"
                        ) from error
                writers[table_name].write_table(arrow_table, row_group_size=100_000)
            del normalized, feed

        for writer in writers.values():
            writer.close()
        report_text = _format_quality_report(quality_rows)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            delete=False,
            dir=report_path.parent,
            prefix=f".{report_path.name}.",
            suffix=".tmp",
        ) as report_file:
            report_file.write(report_text)
            report_temp_path = Path(report_file.name)

        if output_path.exists() or report_path.exists():
            raise FileExistsError("ETL output appeared during processing; refusing overwrite")
        os.replace(staging_path, output_path)
        promoted = True
        os.replace(report_temp_path, report_path)
        report_temp_path = None
        return output_counts
    finally:
        for writer in writers.values():
            if not writer.is_open:
                continue
            writer.close()
        if not promoted and staging_path.exists():
            shutil.rmtree(staging_path)
        if report_temp_path is not None and report_temp_path.exists():
            report_temp_path.unlink()