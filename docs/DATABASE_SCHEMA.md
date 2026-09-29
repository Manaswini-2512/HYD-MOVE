# Planned SQLite Schema

This is a normalized design proposal only. No SQLite database has been created. Every GTFS identifier is stored as text and is scoped to a feed so that the planned TGSRTC and HMRL datasets can coexist without identifier collisions.

## Proposed Tables

| Table | Primary key | Important columns and relationships |
| --- | --- | --- |
| `feed_registry` | `feed_id` | Source/publisher, source URL, retrieved-at UTC, feed version, archive name/checksum, license/terms notes. Parent of all imported feed rows and provenance anchor. |
| `agency` | `(feed_id, agency_pk)` | Internal agency key; nullable/unique-within-feed `gtfs_agency_id`, name, URL, timezone. The internal key supports the valid single-agency case where GTFS omits `agency_id`. |
| `routes` | `(feed_id, route_id)` | `agency_pk` FK to agency, route names, route type, descriptions/colors. Route IDs are feed-scoped. |
| `stops` | `(feed_id, stop_id)` | Stop name, latitude/longitude, location type, optional `parent_station` self-FK within the same feed. |
| `services` | `(feed_id, service_id)` | ETL-derived registry of IDs found across calendar files; parent for service references even if a feed supplies only exceptions. |
| `trips` | `(feed_id, trip_id)` | Route and service composite FKs; optional shape FK; headsign/direction. |
| `stop_times` | `(feed_id, trip_id, stop_sequence)` | Composite trip FK, stop FK, arrival/departure times and pickup/drop-off fields. Add an index on `(feed_id, stop_id)`. |
| `calendar` | `(feed_id, service_id)` | Service FK, weekday flags, start/end dates; at most one recurring definition per service. |
| `calendar_dates` | `(feed_id, service_id, date)` | Service FK and exception type; composite key prevents repeated exceptions for one service/date. |
| `shape_paths` | `(feed_id, shape_id)` | Shape identity parent, allowing trips to reference a shape while point rows remain ordered. |
| `shapes` | `(feed_id, shape_id, shape_pt_sequence)` | Shape-path FK plus ordered latitude/longitude points. |
| `fares` | `(feed_id, fare_id)` | Normalized equivalent of `fare_attributes.txt`: price, currency, payment method, transfer rules. |
| `fare_rules` | `(feed_id, fare_id, rule_ordinal)` | Fare FK, optional route FK, and GTFS zone identifiers/conditions. Ordinal preserves multiple rules per fare. |

## Relationship Outline

```text
feed_registry 1 --- many agency, routes, stops, services, shapes, fares
agency 1 --- many routes 1 --- many trips 1 --- many stop_times many --- 1 stops
services 1 --- many trips; services 1 --- 0..1 calendar; services 1 --- many calendar_dates
shape_paths 1 --- many ordered shapes; trips may reference one shape path
fares 1 --- many fare_rules; a fare rule may reference a route
```

## Loading Notes

- Enable SQLite foreign-key enforcement for each connection and load parent rows before dependent rows.
- Use composite foreign keys containing `feed_id` to prevent links across source feeds. Preserve source IDs as text, even when values look numeric.
- Populate `services` from the union of IDs in `calendar.txt` and `calendar_dates.txt`; it is an ETL-derived table, not a GTFS file.
- `agency_pk` is an internal key. If GTFS omits `agency_id` for a single agency, retain that omission in the source representation and link routes to the one agency row during database loading.
- Record feed version and retrieval provenance in `feed_registry`; do not modify source archives.
- This design stores scheduled/static transit information. It has no passenger-demand table because GTFS does not provide observed passenger counts.
- Revisit nullability, uniqueness, source-specific extensions, and retention rules against the actual permitted feeds before database implementation.