# Phase 2C Unified Mobility Schema

The canonical layer contains standardized schedule/network data from TGSRTC and HMRL. Every row carries `feed_id`; source identifiers are retained alongside namespaced canonical IDs. The feeds are appended as separate observations, never joined using unqualified source IDs.

## ID and Field Normalization

- `feed_id` is the uppercase source namespace (`TGSRTC` or `HMRL`).
- Canonical entity IDs use `FEED_ID:source_id`, for example `TGSRTC:123` and `HMRL:123`. The source fields (`source_route_id`, `source_stop_id`, and corresponding agency/trip/service fields) retain the original string value; the canonical suffix is derived after trimming surrounding whitespace.
- A source ID that is blank remains null; no source ID is fabricated. For the GTFS-valid single-agency case where `agency_id` is absent, the ETL can create an internal `FEED_ID:__single_agency__` key while leaving `source_agency_id` null. Neither current feed requires that fallback.
- Text fields are trimmed and blank strings become null. Numeric fields are converted strictly; nonblank invalid values stop the ETL instead of being coerced or repaired.
- Coordinates use nullable floating-point degrees. Route/type/sequence/calendar flag values use nullable integers. GTFS dates become `datetime64[ns]` values. Times remain in their original GTFS `HH:MM:SS` form and also receive nullable integer seconds from service-day midnight; hours above 23 are preserved.
- Canonical output columns are the common schema union supported by at least one acquired feed. When a field is absent in one feed but present in the other, its canonical cells are null for the feed that did not publish it. Fields absent from both feeds are not added as null-only columns.

## Canonical Tables

| Table | Grain / key | Canonical columns | Types and units |
| --- | --- | --- | --- |
| `agencies` | One row per feed agency; `(feed_id, agency_id)` | `feed_id`, `agency_id`, `source_agency_id`, `agency_name`, `agency_url`, `agency_timezone`, `agency_lang`, `agency_phone` | IDs/text: string; phone is source text. `agency_phone` is present only where the feed provides it. |
| `routes` | One row per feed route; `(feed_id, route_id)` | `feed_id`, `route_id`, `source_route_id`, `agency_id`, `source_agency_id`, `route_short_name`, `route_long_name`, `route_type`, `route_color`, `route_text_color` | IDs/names/colors: string; `route_type`: integer GTFS code, retained without relabelling. |
| `stops` | One row per feed stop; `(feed_id, stop_id)` | `feed_id`, `stop_id`, `source_stop_id`, `stop_name`, `stop_desc`, `stop_lat`, `stop_lon`, `zone_id`, `parent_station`, `source_parent_station`, `location_type`, `platform_code` | IDs/text: string; coordinates: decimal degrees; `location_type`: integer. `parent_station` is feed-namespaced. |
| `trips` | One row per feed trip; `(feed_id, trip_id)` | `feed_id`, `trip_id`, `source_trip_id`, `route_id`, `source_route_id`, `service_id`, `source_service_id`, `trip_headsign`, `trip_short_name`, `direction_id`, `block_id`, `shape_id`, `source_shape_id` | IDs/text: string; `direction_id`: integer. Route/service/shape references are feed-namespaced. |
| `stop_times` | One row per trip stop sequence; `(feed_id, trip_id, stop_sequence)` | `feed_id`, `trip_id`, `source_trip_id`, `arrival_time`, `arrival_seconds`, `departure_time`, `departure_seconds`, `stop_id`, `source_stop_id`, `stop_sequence`, `timepoint`, `shape_dist_traveled` | IDs/time strings: string; seconds/sequence/timepoint: integer; shape distance: source GTFS numeric units. |
| `calendar` | One recurring weekly service; `(feed_id, service_id)` | `feed_id`, `service_id`, `source_service_id`, weekday flags, `start_date`, `end_date` | IDs: string; weekday flags: nullable 0/1 integers; dates: `datetime64[ns]`. |
| `calendar_dates` | One exception per service/date; `(feed_id, service_id, date)` | `feed_id`, `service_id`, `source_service_id`, `date`, `exception_type` | IDs: string; date: `datetime64[ns]`; exception type: integer. The output is omitted when the source file is absent. |
| `route_stops` | One row per feed route/stop pair; `(feed_id, route_id, stop_id)` | `feed_id`, `route_id`, `source_route_id`, `stop_id`, `source_stop_id`, `stop_sequence`, `trip_count`, `service_count` | Sequence/counts: integer. `stop_sequence` is the minimum observed sequence for that pair; counts describe schedules, not demand. |
| `route_service_summary` | One row per feed route; `(feed_id, route_id)` | `feed_id`, `route_id`, `source_route_id`, `route_short_name`, `route_long_name`, `route_type`, `trip_count`, `unique_stop_count`, `service_id_count`, `first_departure_seconds`, `last_arrival_seconds` | Counts/type: integer; time envelope: service-day seconds. Earliest first departure and latest last arrival are aggregated across scheduled trips. |
| `stop_service_summary` | One row per feed stop; `(feed_id, stop_id)` | `feed_id`, `stop_id`, `source_stop_id`, `stop_name`, `route_count`, `trip_count`, `first_service_seconds`, `last_service_seconds` | Counts: integer; times: service-day seconds. Stops without stop-time references remain present with zero counts and null times. |

## Source Lineage and Preserved Extensions

Each row-level standardized record retains `feed_id` and a source ID. Normalized foreign keys are checked within the same feed. Trip `shape_id` is retained as a feed-prefixed source reference, while shape points remain in the raw archive and are not yet a canonical Parquet table. The normalized Parquet files are deterministic outputs; the original `data/external/{tgsrtc,hmrl}/*.zip` archives remain the authoritative, immutable record of every source field.

The canonical layer intentionally does not expand every GTFS table. `shapes.txt`, `fare_attributes.txt`, `fare_rules.txt`, and `feed_info.txt` remain in the raw archives for later, explicitly scoped ETL. Suggested fields such as `route_desc`, `route_url`, `stop_code`, `wheelchair_boarding`, `bikes_allowed`, `stop_headsign`, `pickup_type`, and `drop_off_type` were not present in either acquired feed and are therefore not emitted as all-null canonical columns. Source-only fields not mapped to the canonical columns also remain in those archives. Current examples include HMRL agency fare URL/email and route sort order. These values are not discarded from the project source of record, but are not copied into the Phase 2C analytics layer.

## Output and Interpretation

Parquet outputs are under `data/processed/gtfs/`; absent `calendar_dates.txt` means no `calendar_dates.parquet` is created for the current feeds. `LINEAGE.md` records the feed-to-table flow. Route, trip, stop, service, and schedule-time counts describe scheduled transport service. No passenger count, boarding, alighting, occupancy, or demand field is created; demand analysis requires separate observed passenger data.