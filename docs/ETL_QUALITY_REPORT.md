# Phase 2C ETL Quality Report

The feeds were normalized independently and appended using feed-prefixed canonical IDs. Both passed source validation with zero errors; TGSRTC has 9 warnings and HMRL 7, all for absent optional GTFS files. Original GTFS ZIP files remain unchanged. No passenger-demand fields were created.

## TGSRTC

| Table | Rows before | Rows after | Columns | Null counts | Duplicate key rows | Type conversions | Records filtered | Filter reason |
| --- | ---: | ---: | --- | --- | ---: | --- | ---: | --- |
| `agencies` | 1 | 1 | feed_id, agency_id, source_agency_id, agency_name, agency_url, agency_timezone, agency_lang, agency_phone | `{"agency_phone": 1}` | 0 | IDs namespaced; text trimmed; blanks converted to null. | 0 | No records filtered. |
| `routes` | 4133 | 4133 | feed_id, route_id, source_route_id, agency_id, source_agency_id, route_short_name, route_long_name, route_type, route_color, route_text_color | `{"route_color": 4133, "route_text_color": 4133}` | 0 | IDs and agency FK namespaced; route_type converted to nullable integer; text trimmed; blanks to null. | 0 | No records filtered. |
| `stops` | 5177 | 5177 | feed_id, stop_id, source_stop_id, stop_name, stop_desc, stop_lat, stop_lon, zone_id, parent_station, source_parent_station, location_type, platform_code | `{"location_type": 5177, "parent_station": 5177, "platform_code": 5177, "source_parent_station": 5177}` | 0 | IDs and parent-station FK namespaced; coordinates converted to nullable floats; location_type converted to nullable integer; text trimmed; blanks to null. | 0 | No records filtered. |
| `trips` | 51985 | 51985 | feed_id, trip_id, source_trip_id, route_id, source_route_id, service_id, source_service_id, trip_headsign, trip_short_name, direction_id, block_id, shape_id, source_shape_id | `{"block_id": 51985, "trip_headsign": 51985}` | 0 | Trip, route, service, and shape IDs namespaced; direction_id converted to nullable integer; text trimmed; blanks to null. | 0 | No records filtered. |
| `stop_times` | 1286284 | 1286284 | feed_id, trip_id, source_trip_id, arrival_time, arrival_seconds, departure_time, departure_seconds, stop_id, source_stop_id, stop_sequence, timepoint, shape_dist_traveled | `None` | 0 | Trip/stop IDs namespaced; stop_sequence/timepoint converted to nullable integers; shape distance to nullable float; original times retained and seconds derived. | 0 | No records filtered. |
| `calendar` | 1 | 1 | feed_id, service_id, source_service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date | `None` | 0 | Service IDs namespaced; weekday flags converted to nullable integers; dates parsed as datetime64[ns]. | 0 | No records filtered. |
| `route_stops` | 1286284 | 102915 | feed_id, route_id, source_route_id, stop_id, source_stop_id, stop_sequence, trip_count, service_count | `None` | 0 | Grouped by feed, route, and stop; minimum observed stop_sequence retained; trip/service counts derived. | 0 | No records filtered. |
| `route_service_summary` | 51985 | 4133 | feed_id, route_id, source_route_id, route_short_name, route_long_name, route_type, trip_count, unique_stop_count, service_id_count, first_departure_seconds, last_arrival_seconds | `{"first_departure_seconds": 2, "last_arrival_seconds": 2}` | 0 | Trips, unique stops, services, earliest first departure, and latest last arrival aggregated by route. | 0 | No records filtered. |
| `stop_service_summary` | 1286284 | 5177 | feed_id, stop_id, source_stop_id, stop_name, route_count, trip_count, first_service_seconds, last_service_seconds | `None` | 0 | Distinct route/trip counts and observed first/last scheduled times aggregated by stop. | 0 | No records filtered. |

No records filtered.

## HMRL

| Table | Rows before | Rows after | Columns | Null counts | Duplicate key rows | Type conversions | Records filtered | Filter reason |
| --- | ---: | ---: | --- | --- | ---: | --- | ---: | --- |
| `agencies` | 1 | 1 | feed_id, agency_id, source_agency_id, agency_name, agency_url, agency_timezone, agency_lang, agency_phone | `None` | 0 | IDs namespaced; text trimmed; blanks converted to null. | 0 | No records filtered. |
| `routes` | 3 | 3 | feed_id, route_id, source_route_id, agency_id, source_agency_id, route_short_name, route_long_name, route_type, route_color, route_text_color | `None` | 0 | IDs and agency FK namespaced; route_type converted to nullable integer; text trimmed; blanks to null. | 0 | No records filtered. |
| `stops` | 705 | 705 | feed_id, stop_id, source_stop_id, stop_name, stop_desc, stop_lat, stop_lon, zone_id, parent_station, source_parent_station, location_type, platform_code | `{"parent_station": 57, "platform_code": 588, "source_parent_station": 57, "stop_desc": 705, "zone_id": 533}` | 0 | IDs and parent-station FK namespaced; coordinates converted to nullable floats; location_type converted to nullable integer; text trimmed; blanks to null. | 0 | No records filtered. |
| `trips` | 2895 | 2895 | feed_id, trip_id, source_trip_id, route_id, source_route_id, service_id, source_service_id, trip_headsign, trip_short_name, direction_id, block_id, shape_id, source_shape_id | `{"trip_short_name": 2895}` | 0 | Trip, route, service, and shape IDs namespaced; direction_id converted to nullable integer; text trimmed; blanks to null. | 0 | No records filtered. |
| `stop_times` | 62759 | 62759 | feed_id, trip_id, source_trip_id, arrival_time, arrival_seconds, departure_time, departure_seconds, stop_id, source_stop_id, stop_sequence, timepoint, shape_dist_traveled | `None` | 0 | Trip/stop IDs namespaced; stop_sequence/timepoint converted to nullable integers; shape distance to nullable float; original times retained and seconds derived. | 0 | No records filtered. |
| `calendar` | 3 | 3 | feed_id, service_id, source_service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date | `None` | 0 | Service IDs namespaced; weekday flags converted to nullable integers; dates parsed as datetime64[ns]. | 0 | No records filtered. |
| `route_stops` | 62759 | 121 | feed_id, route_id, source_route_id, stop_id, source_stop_id, stop_sequence, trip_count, service_count | `None` | 0 | Grouped by feed, route, and stop; minimum observed stop_sequence retained; trip/service counts derived. | 0 | No records filtered. |
| `route_service_summary` | 2895 | 3 | feed_id, route_id, source_route_id, route_short_name, route_long_name, route_type, trip_count, unique_stop_count, service_id_count, first_departure_seconds, last_arrival_seconds | `None` | 0 | Trips, unique stops, services, earliest first departure, and latest last arrival aggregated by route. | 0 | No records filtered. |
| `stop_service_summary` | 62759 | 705 | feed_id, stop_id, source_stop_id, stop_name, route_count, trip_count, first_service_seconds, last_service_seconds | `{"first_service_seconds": 588, "last_service_seconds": 588}` | 0 | Distinct route/trip counts and observed first/last scheduled times aggregated by stop. | 0 | No records filtered. |

No records filtered.

## Notes

For derived tables, rows-before counts are the source schedule rows entering aggregation; the lower output row count reflects grouping, not record filtering. Null counts describe the normalized output. Source-specific GTFS tables and fields not mapped to the canonical layer remain available in the immutable raw ZIPs and are documented in `UNIFIED_SCHEMA.md`.
