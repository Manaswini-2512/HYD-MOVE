# Phase 3A GTFS Exploratory Data Analysis

## Objective

Describe the published TGSRTC and HMRL route, stop, trip-template, stop-time, and recurring calendar structures using the existing processed GTFS layer. This phase is descriptive schedule analysis only. It does not estimate passenger demand or actual service delivery and does not fit forecasting or machine-learning models.

## Dataset

The analysis uses the nine existing feed-scoped Parquet tables under `data/processed/gtfs/`: `agencies`, `calendar`, `routes`, `route_service_summary`, `route_stops`, `stop_service_summary`, `stop_times`, `stops`, and `trips`. They contain `feed_id` values `TGSRTC` and `HMRL`; original source IDs remain alongside feed-prefixed IDs. The actual Parquet columns were inspected before analysis. There is no `calendar_dates.parquet` because neither source feed includes `calendar_dates.txt`. No source ZIP or processed Parquet table was changed. Input provenance and feed validation are documented in `data/external/manifest.json`, `docs/DATA_PROVENANCE.md`, and `docs/REAL_GTFS_QUALITY_REPORT.md`.

| Operator/feed | Routes | Stops | Scheduled trip records | Stop-time records | Calendar services | Published service-date bounds |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| TGSRTC | 4,133 | 5,177 | 51,985 | 1,286,284 | 1 | 2026-09-01 to 2031-09-01 |
| HMRL | 3 | 705 | 2,895 | 62,759 | 3 | 2026-09-02 to 2030-01-01 |

The dates are calendar coverage bounds in the static feeds, not a record of trips observed operating during those years.

## Metrics

- **Routes / stops:** distinct feed-scoped route or stop IDs in the corresponding Parquet table.
- **Scheduled trips:** distinct `trip_id` rows in `trips`. These are scheduled GTFS trip records, not observed departures or passengers.
- **Stop-time records:** rows in `stop_times`, each describing a scheduled stop event.
- **Calendar services / active weekdays:** distinct `service_id` values and the union of weekday flags enabled in `calendar` for that feed.
- **Trips per route (`trip_count`):** distinct scheduled trip records linked to each route; routes with no trips remain with zero.
- **Stops per route (`stop_count`):** distinct stop IDs in the feed's route-stop relationships; routes without such relationships remain with zero.
- **Service days:** number of weekday flags on which at least one trip linked to a route's service IDs is scheduled.
- **GTFS-derived service intensity (`scheduled_service_intensity`):** mean count of route trip records scheduled on the weekdays when the route has service. A route with no scheduled service has zero; if calendar information is unavailable, the result is missing.
- **Routes per stop (`routes_per_stop`):** distinct routes in the feed's route-stop relationships serving that stop.
- **Trips per stop (`trips_per_stop`):** sum of the distinct scheduled trip counts for that stop across its route-stop relationships.
- **Weekday scheduled trip count:** distinct trip records whose linked recurring calendar enables that weekday. Calendar exceptions are not applied because neither feed has `calendar_dates`.
- **Hourly scheduled service:** count of scheduled stop departures by service-day hour, using arrival time only when departure time is blank. `service_day_hour` retains values beyond 23; `clock_hour` is the wall-clock hour modulo 24 and `service_day_offset` indicates subsequent service days. For example, 25:30:00 maps to service-day hour 25, clock hour 1, offset 1.
- **First / last scheduled service:** the route first departure and last arrival seconds from `route_service_summary`, expressed as seconds from service-day midnight and retaining extended hours.
- **Operator averages:** total scheduled trip records or distinct route-stop links divided by all feed route records, including routes with no trip/stop links.
- **Defined peak / off-peak:** an explicitly analyst-selected convention: wall-clock hours 07:00-09:59 and 16:00-18:59 are grouped as `defined_peak`; other hours are `off_peak`. These windows are not declared peaks from either operator.

## Findings

### Feed summaries

| Operator/feed | Mean scheduled trips per route | Mean distinct stops per route |
| --- | ---: | ---: |
| TGSRTC | 12.58 | 24.90 |
| HMRL | 965.00 | 40.33 |

These aggregates are calculated with the same table-level definitions but should not be used to rank operator performance: the feeds describe different modes, route concepts, schedule structures, and coverage periods. The means include every route record, including the two TGSRTC routes with no trip records.

### Route schedule distributions

- TGSRTC has 4,133 route records; 4,131 have at least one scheduled trip and 2 have none. Scheduled trips per route have mean 12.58, median 3, 25th percentile 1, 75th percentile 8, and maximum 601. The distribution is strongly right-skewed.
- TGSRTC distinct scheduled stops per route have mean 24.90, median 25, and maximum 72; the zero-trip routes have zero route-stop links.
- HMRL has three route records. Scheduled trip counts range from 544 to 1,176 (mean 965, median 1,175). Distinct scheduled stops per route range from 17 to 56 (mean 40.33, median 48).
- The highest scheduled-trip route in TGSRTC is source route `229` from Secunderabad Railway Station to Medchal Bus Station, with 601 scheduled trip records. The HMRL source route `C3_BLUE` has 1,176 scheduled trip records. These are schedule counts, not observed trips or riders.

### Stop connectivity

- TGSRTC's most-connected stop by `routes_per_stop` is Secunderabad Railway Station (812 route-stop relationships); it also has 15,455 scheduled trips per stop under the feed's route-stop aggregation.
- The highest TGSRTC `trips_per_stop` value is also Secunderabad Railway Station (15,455).
- HMRL's maximum route connectivity is 2 routes, observed at four Ameerpet stop IDs in the source feed. Its highest `trips_per_stop` value is Raidurg (905), which is a scheduled-service aggregation.
- HMRL has 588 stop records with zero stop-time/route-stop service relationships in the processed layer. They remain present; the reason is not inferred.

These are most-connected/highest scheduled-service stops, not busiest stops or passenger-volume rankings.

### Calendar and hourly service

- TGSRTC has one calendar service with all seven weekday flags enabled. The current feed therefore yields 51,985 scheduled trip records for each calendar weekday. This is a recurring schedule pattern, not a measured daily operation count.
- HMRL has separate weekday, Saturday, and Sunday services. Calendar-linked scheduled trip-record counts are 1,081 on each Monday-Friday, 1,002 on Saturday, and 812 on Sunday.
- All seven weekdays are enabled by at least one calendar service in each feed. The feeds contain no `calendar_dates` exceptions, so exception-day service cannot be described.
- The processed departure-time profile retains extended service-day hours. TGSRTC departures span service-day hours 0-45; HMRL spans hours 4-24. The source quality review counted 459 TGSRTC and 120 HMRL departure values at or beyond 24:00:00. These values were retained rather than wrapped or discarded in the service-day-hour table.
- Under the notebook's defined peak convention, scheduled stop-departure records in the selected clock-hour windows total 520,102 for TGSRTC and 22,311 for HMRL; outside those windows they total 766,182 and 40,448, respectively. These totals aggregate schedule stop events across service templates, not vehicles or passengers, and the peak windows are analytical choices.

## Visualizations

`notebooks/03_gtfs_eda.ipynb` reproduces the summaries and generates:

1. Trips-per-route distributions by operator, plotted as `log10(1 + scheduled trips)` to make the highly skewed TGSRTC distribution visible.
2. Top routes by scheduled trip records, separated by operator.
3. Most-connected stops by route connectivity, separated by operator.
4. Hourly scheduled stop-departure profiles by service-day hour, including extended hours.
5. Operator comparisons in separate panels for each count/average metric, avoiding one shared scale across unlike units.
6. Route-level distributions for scheduled trips and distinct scheduled stops.

All chart labels explicitly refer to scheduled service or network connectivity. The notebook loads local processed Parquet files via repository-relative paths and performs no internet access.

## Limitations

- GTFS represents scheduled service. It does not establish actual passenger usage, whether service operated, or how many passengers boarded or alighted.
- Scheduled service frequency/intensity is not ridership or passenger demand. Stop connectivity is not passenger volume.
- Calendar bounds limit interpretation to the schedule coverage periods; they are not historical operating observations.
- Neither feed contains `calendar_dates`, so exceptional service additions/removals cannot be applied to weekday profiles.
- Two TGSRTC routes have no trip records, and 588 HMRL stops have no stop-time/route-stop references. Their causes are not known from these files.
- Comparison metrics are mechanically defined the same way but reflect different operators, modes, route structures, feed coverage, and schedule conventions. They are descriptive, not operator rankings.
- TGSRTC trip rows are linked to an all-days service calendar; HMRL uses weekday, Saturday, and Sunday calendars. A trip record need not represent one distinct vehicle run per calendar day.
- The optional defined peak windows are not operator-defined and should not be treated as observed demand peaks.
- No passenger-demand data was acquired or fabricated. No regression, classification, clustering, ARIMA, forecasting, or advanced machine learning was performed.