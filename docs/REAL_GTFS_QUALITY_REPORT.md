# Real GTFS Quality Report

The two official source ZIPs were inspected independently and read-only with the Phase 2A GTFS loader and validator. Neither archive was extracted to disk or modified. All loaded GTFS fields were read as text (`object` dtype) to preserve identifiers and source representations. ZIP integrity checks passed for both archives. The archives contain only recognized GTFS `.txt` members; no non-GTFS ZIP members were found.

Service periods below are taken from `calendar.txt` and corroborated by `feed_info.txt`. Validation results reflect the project's current GTFS structural validator; they are not a certification by an external GTFS conformance checker.

## 1. TGSRTC

### Feed Summary

- File: `data/external/tgsrtc/TGSRTC_GTFS.zip`
- File size: 37,364,557 bytes (37.364557 MB, decimal)
- SHA-256: `74f343762f6900a6e23ecacb08beeb13df00bcc25e0859d93867ca02d8a7500a`
- ZIP entries: 8
- Service period: 2026-09-01 to 2031-09-01
- Feed version: `20260901`
- Available files: `agency.txt`, `feed_info.txt`, `stops.txt`, `routes.txt`, `calendar.txt`, `trips.txt`, `stop_times.txt`, `shapes.txt`
- Required GTFS files: all present (`agency.txt`, `routes.txt`, `stops.txt`, `trips.txt`, `stop_times.txt`)

### Tables

| GTFS table | Present | Rows | Empty |
| --- | --- | ---: | --- |
| `agency` | Yes | 1 | No |
| `routes` | Yes | 4,133 | No |
| `stops` | Yes | 5,177 | No |
| `trips` | Yes | 51,985 | No |
| `stop_times` | Yes | 1,286,284 | No |
| `calendar` | Yes | 1 | No |
| `calendar_dates` | No | Not applicable | Not applicable |
| `shapes` | Yes | 3,011,781 | No |
| `feed_info` | Yes | 1 | No |

Observed columns:

- `agency`: `agency_id`, `agency_name`, `agency_url`, `agency_timezone`, `agency_lang`
- `routes`: `route_id`, `route_short_name`, `route_long_name`, `agency_id`, `route_type`
- `stops`: `stop_id`, `stop_name`, `zone_id`, `stop_lat`, `stop_lon`, `stop_desc`
- `trips`: `route_id`, `trip_id`, `service_id`, `direction_id`, `trip_short_name`, `shape_id`
- `stop_times`: `trip_id`, `stop_sequence`, `stop_id`, `departure_time`, `arrival_time`, `timepoint`, `shape_dist_traveled`
- `calendar`: `service_id`, `start_date`, `end_date`, `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`
- `shapes`: `shape_id`, `shape_pt_lat`, `shape_pt_lon`, `shape_pt_sequence`
- `feed_info`: `feed_publisher_name`, `feed_publisher_url`, `feed_contact_email`, `feed_contact_url`, `feed_lang`, `feed_start_date`, `feed_end_date`, `feed_version`

`calendar_dates.txt`, `fare_attributes.txt`, and `fare_rules.txt` are absent.

### Data Quality

- Validation errors: **0**
- Validation warnings: **9**, all missing optional files listed below
- Required schema columns: all present; no required-column errors
- Missing or blank IDs: none in the checked identifier/key columns
- Duplicate IDs/keys: none for the validator's checked entity and composite keys, including `(shape_id, shape_pt_sequence)` and `(trip_id, stop_sequence)`
- Foreign-key violations: none detected for agency/route, route/trip, trip/stop-time, stop/stop-time, shape, or service-calendar relationships
- Invalid coordinates: none detected in stops or shape points
- Invalid dates: none detected in calendar/feed date fields
- Invalid service periods: none; every calendar start date is on or before its end date
- Invalid times: none detected in stop-time fields
- Empty tables: none
- Blank values: none observed in the ingested tables
- Missing optional files: `calendar_dates.txt`, `fare_attributes.txt`, `fare_rules.txt`, `frequencies.txt`, `transfers.txt`, `translations.txt`, `pathways.txt`, `levels.txt`, `attributions.txt`

#### Errors

None.

#### Warnings

- Missing optional files: `calendar_dates.txt`, `fare_attributes.txt`, `fare_rules.txt`, `frequencies.txt`, `transfers.txt`, `translations.txt`, `pathways.txt`, `levels.txt`, `attributions.txt`.

#### Informational Observations

- `route_type`: raw code `3` occurs on 4,133 routes. Under the standard GTFS route-type mapping, code `3` denotes bus. Sample route short names include `277D`, `189M`, and `250C`; source values were not relabelled.
- `calendar.txt` has 1 service ID (`MTWTFSS`) with pattern `1111111` (all seven weekdays enabled), from 2026-09-01 through 2031-09-01. No calendar-date exceptions are present.
- Extended hours are present and valid: 459 arrival and 459 departure values have hours at or above 24; maximum observed hour is 45. The GTFS time validator accepts these values.
- Trips reference 1 calendar service ID; all trip/service, route/trip, trip/stop-time, and stop/stop-time references resolve.
- Two route records have no trips. The reason is not determined from the feed.
- No stops are unreferenced by `stop_times`; no trips lack stop-time rows.
- Structural distributions: trips per route (routes with trips), min 1, p25 1, median 3, mean 12.58, p75 8, max 601; distinct scheduled stops per route, min 3, p25 16, median 25, mean 24.91, p75 33, max 72; routes per served stop, min 1, p25 2, median 6, mean 19.88, p75 19, max 812; stop-time rows per trip, min 3, p25 18, median 25, mean 24.74, p75 32, max 72.
- All GTFS fields were loaded as strings. Repeated `trip_id` values in stop times and repeated `shape_id` values across shape points are expected relationships; the checked composite keys are unique.

### Structural Statistics

| Measure | Observed distribution |
| --- | --- |
| Trips per route (routes with trips) | min 1; p25 1; median 3; mean 12.58; p75 8; max 601; 4,131 routes have trips, 2 do not |
| Distinct scheduled stops per route | min 3; p25 16; median 25; mean 24.91; p75 33; max 72 |
| Routes per served stop | min 1; p25 2; median 6; mean 19.88; p75 19; max 812 |
| Stop-time rows per trip | min 3; p25 18; median 25; mean 24.74; p75 32; max 72 |

### Data-quality Interpretation

The archive contains all required schedule tables and one recurring calendar service. Optional date exceptions and fare tables are not included. Validation found no schema, identifier, relationship, date, time, or coordinate errors. Two routes have no scheduled trips, but no cause can be inferred from this feed alone. All counts and distributions describe published schedule/network structure, not passenger demand.

## 2. HMRL

### Feed Summary

- File: `data/external/hmrl/HMRL_GTFS.zip`
- File size: 2,996,166 bytes (2.996166 MB, decimal)
- SHA-256: `c35bda6768e71fdef742080d1436a5d751d7b2a64f6882839574d768a6498f2a`
- ZIP entries: 10
- Service period: 2026-09-02 to 2030-01-01
- Feed version: Not determined from available source material; `feed_info.txt` has no `feed_version` column
- Available files: `agency.txt`, `calendar.txt`, `fare_rules.txt`, `fare_attributes.txt`, `stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`, `shapes.txt`, `feed_info.txt`
- Required GTFS files: all present (`agency.txt`, `routes.txt`, `stops.txt`, `trips.txt`, `stop_times.txt`)

### Tables

| GTFS table | Present | Rows | Empty |
| --- | --- | ---: | --- |
| `agency` | Yes | 1 | No |
| `routes` | Yes | 3 | No |
| `stops` | Yes | 705 | No |
| `trips` | Yes | 2,895 | No |
| `stop_times` | Yes | 62,759 | No |
| `calendar` | Yes | 3 | No |
| `calendar_dates` | No | Not applicable | Not applicable |
| `fare_attributes` | Yes | 10 | No |
| `fare_rules` | Yes | 3,249 | No |
| `shapes` | Yes | 2,450 | No |
| `feed_info` | Yes | 1 | No |

Observed columns:

- `agency`: `agency_id`, `agency_name`, `agency_url`, `agency_timezone`, `agency_lang`, `agency_fare_url`, `agency_email`, `agency_phone`
- `routes`: `route_id`, `agency_id`, `route_short_name`, `route_long_name`, `route_type`, `route_color`, `route_text_color`, `route_sort_order`
- `stops`: `stop_id`, `stop_name`, `stop_lat`, `stop_lon`, `zone_id`, `location_type`, `parent_station`, `platform_code`
- `trips`: `service_id`, `route_id`, `trip_id`, `direction_id`, `trip_headsign`, `block_id`, `shape_id`
- `stop_times`: `trip_id`, `stop_sequence`, `stop_id`, `arrival_time`, `departure_time`, `timepoint`, `shape_dist_traveled`
- `calendar`: `service_id`, `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`, `start_date`, `end_date`
- `fare_attributes`: `fare_id`, `price`, `currency_type`, `payment_method`, `transfers`, `agency_id`
- `fare_rules`: `origin_id`, `destination_id`, `fare_id`
- `shapes`: `shape_id`, `shape_pt_lat`, `shape_pt_lon`, `shape_pt_sequence`, `shape_dist_traveled`
- `feed_info`: `feed_publisher_name`, `feed_publisher_url`, `feed_lang`, `feed_contact_url`, `feed_start_date`, `feed_end_date`

`calendar_dates.txt` is absent.

### Data Quality

- Validation errors: **0**
- Validation warnings: **7**, all missing optional files listed below
- Required schema columns: all present; no required-column errors
- Missing or blank IDs: none in the checked identifier/key columns
- Duplicate IDs/keys: none for the validator's checked entity and composite keys, including `(shape_id, shape_pt_sequence)` and `(trip_id, stop_sequence)`
- Foreign-key violations: none detected for agency/route, route/trip, trip/stop-time, stop/stop-time, shape, fare, or service-calendar relationships
- Invalid coordinates: none detected in stops or shape points
- Invalid dates: none detected in calendar/feed date fields
- Invalid service periods: none; every calendar start date is on or before its end date
- Invalid times: none detected in stop-time fields
- Empty tables: none
- Blank values observed: `fare_attributes.transfers` has 10 blank values; `stops.zone_id` has 533, `stops.parent_station` has 57, and `stops.platform_code` has 588. The meaning of blank `transfers` values is not determined from the available source material. Source values were not filled or changed.
- Missing optional files: `calendar_dates.txt`, `frequencies.txt`, `transfers.txt`, `translations.txt`, `pathways.txt`, `levels.txt`, `attributions.txt`

#### Errors

None.

#### Warnings

- Missing optional files: `calendar_dates.txt`, `frequencies.txt`, `transfers.txt`, `translations.txt`, `pathways.txt`, `levels.txt`, `attributions.txt`.

#### Informational Observations

- `route_type`: raw code `1` occurs on 3 routes. Under the standard GTFS route-type mapping, code `1` denotes subway. Observed short names are `C1_RED`, `C2_GREEN`, and `C3_BLUE`; source values were not relabelled.
- `calendar.txt` has 3 service IDs: `WK` uses Monday-Friday (`1111100`), `SA` uses Saturday (`0000010`), and `SU` uses Sunday (`0000001`). All have service dates 2026-09-02 through 2030-01-01. No calendar-date exceptions are present.
- Extended hours are present and valid: 119 arrival and 120 departure values have hours at or above 24; maximum observed hour is 24. The GTFS time validator accepts these values.
- Trips reference all 3 calendar service IDs; all trip/service, route/trip, trip/stop-time, and stop/stop-time references resolve.
- 588 stop records are not referenced by any `stop_times` row. The feed alone does not establish why.
- No routes lack trips and no trips lack stop-time rows.
- Structural distributions: trips per route, min 544, p25 859.5, median 1,175, mean 965, p75 1,175.5, max 1,176; distinct scheduled stops per route, min 17, p25 32.5, median 48, mean 40.33, p75 52, max 56; routes per served stop, min 1, p25 1, median 1, mean 1.03, p75 1, max 2; trips per service, min 812, p25 907, median 1,002, mean 965, p75 1,041.5, max 1,081; stop-time rows per trip, min 4, p25 23, median 23, mean 21.68, p75 27, max 27.
- Blank source cells observed: `fare_attributes.transfers` (10), `stops.zone_id` (533), `stops.parent_station` (57), and `stops.platform_code` (588). Their intended semantics are not determined from these blank cells; no value was inferred or filled.
- Repeated `trip_id` and `stop_id` values in stop times and repeated `shape_id` values across shape points are expected relationships; checked composite keys are unique. Repeated `fare_id` values in fare rules are references, not unique row IDs.

### Structural Statistics

| Measure | Observed distribution |
| --- | --- |
| Trips per route | min 544; p25 859.5; median 1,175; mean 965; p75 1,175.5; max 1,176 |
| Distinct scheduled stops per route | min 17; p25 32.5; median 48; mean 40.33; p75 52; max 56 |
| Routes per served stop | min 1; p25 1; median 1; mean 1.03; p75 1; max 2 |
| Trips per service ID | min 812; p25 907; median 1,002; mean 965; p75 1,041.5; max 1,081 |
| Stop-time rows per trip | min 4; p25 23; median 23; mean 21.68; p75 27; max 27 |

### Data-quality Interpretation

The archive contains required schedule tables, three recurring service calendars, fares, and shapes. Validation found no schema, identifier, relationship, date, time, or coordinate errors. The 588 stops without stop-time references and blank optional-looking source fields are recorded observations only; their causes or intended semantics are not inferred. Route, trip, stop-time, fare-rule, and coverage statistics describe the published schedule/network, not passenger demand.

## 3. Cross-feed Observations

- TGSRTC contains 8 GTFS files and HMRL contains 10; both contain all required files, while each omits `calendar_dates.txt`.
- TGSRTC has route type `3` (standard GTFS bus code); HMRL has route type `1` (standard GTFS subway code). These raw source codes are retained.
- TGSRTC covers 2026-09-01 through 2031-09-01 with one all-days service. HMRL covers 2026-09-02 through 2030-01-01 with separate weekday, Saturday, and Sunday services.
- Both feeds have zero errors in the current validator; optional-file warnings differ with the supplied files.
- HMRL has blank source cells in fare/stop fields and stops not referenced by stop times; TGSRTC has two routes without trips. These are feed-specific structural observations and are not used to rank the datasets.
- The feeds remain separate. All schedule/network statistics above are not passenger-demand measurements.

## Interpretation Limit

GTFS describes scheduled/static transit service, routes, stops, fares, and related network structure. It does not provide actual passenger counts, boardings, alightings, or observed demand. These feeds remain separate; no TGSRTC/HMRL records were combined and no demand fields were created.