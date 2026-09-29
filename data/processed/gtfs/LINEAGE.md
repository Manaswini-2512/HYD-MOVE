# Phase 2C GTFS Lineage

The source ZIPs below are immutable and remain stored separately. Each feed was loaded and validated independently, normalized without filtering records, then appended to the corresponding feed-tagged Parquet tables. Large tables may span multiple row groups.

```text
data/external/tgsrtc/TGSRTC_GTFS.zip
    -> GTFS ingestion and source validation
    -> feed_id = TGSRTC
    -> agencies, routes, stops, trips, stop_times, calendar
    -> route_stops, route_service_summary, stop_service_summary

data/external/hmrl/HMRL_GTFS.zip
    -> GTFS ingestion and source validation
    -> feed_id = HMRL
    -> agencies, routes, stops, trips, stop_times, calendar
    -> route_stops, route_service_summary, stop_service_summary
```

## Output Tables

The Parquet datasets in this directory contain rows from both feeds, identified by `feed_id`: `agencies.parquet`, `routes.parquet`, `stops.parquet`, `trips.parquet`, `stop_times.parquet`, `calendar.parquet`, `route_stops.parquet`, `route_service_summary.parquet`, and `stop_service_summary.parquet`.

No `calendar_dates.parquet` was generated because `calendar_dates.txt` is absent from both archives. Source IDs are retained in `source_*_id` fields, and canonical IDs are prefixed with their feed identifier. Referential joins are scoped by `feed_id`.

`route_stops`, `route_service_summary`, and `stop_service_summary` are derived by aggregation from normalized schedules. Trip, stop, route, and service counts describe scheduled network/service structure, not passenger demand. No passenger counts, boardings, alightings, occupancy, or demand estimates are included.

GTFS tables/fields outside the Phase 2C canonical schema (including source shapes, fares, and feed metadata) remain available in their unchanged source ZIPs; see `docs/UNIFIED_SCHEMA.md`.