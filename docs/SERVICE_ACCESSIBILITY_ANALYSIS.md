# Phase 3C: Route-Level Service & Accessibility Analytics

## Analytical question

How do the GTFS feeds describe scheduled service intensity, route connectivity,
stop coverage, and service times? This phase produces descriptive, reusable
features of published service supply. It does not measure observed operation,
passenger accessibility, passenger demand, ridership, equity, or usage.

## Inputs and expected grains

The public functions accept a mapping of table names to pandas DataFrames. The
canonical inputs are feed-scoped `routes` and `stops` (one row per entity),
`trips` (one scheduled trip record), `stop_times` (one trip/stop sequence),
`calendar` (one recurring service ID), `route_stops` (one feed/route/stop
relationship), and `route_service_summary` (one route). `stop_service_summary`
can supply existing Phase 2C stop aggregations. Keys always include `feed_id`;
source IDs are never joined across feeds. The schemas and units are specified
in `UNIFIED_SCHEMA.md`.

## Outputs and metric definitions

`build_service_accessibility_analytics` returns route and stop service
profiles, route overlap, hourly service profile, descriptive feed summary,
quality report, and schedule-supply gap flags.

- **Scheduled trip count:** distinct `trip_id` records attached to a route.
- **Active service IDs:** distinct non-null `service_id` values attached to
  route trips or stop events.
- **Active service weekday count:** number of weekday types for which linked
  recurring calendar flags enable at least one scheduled trip. It is not a
  count of calendar dates. Missing, invalid, or unmatched weekday flags leave
  route weekday metrics missing.
- **Unique scheduled service-day count:** distinct dates formed by expanding
  each route's linked calendar service IDs over `start_date`/`end_date` and
  enabled weekdays, then unioning dates across those services. Supplied
  `calendar_dates` additions/removals are applied. A missing calendar, invalid
  date bound, or unmatched route service ID makes the result missing; no
  dates are fabricated.
- **Trips per service day:** mean number of scheduled trip templates active
  on each derived service date. Counts from overlapping service IDs are
  summed for each date. No active dates or missing calendar derivation yields
  missing. This is a schedule property, not an observed daily operation.
- **Scheduled departures:** timed stop-event records joined to a trip, route,
  and (for stop profiles) stop, using arrival time only when departure time is
  unavailable. This is a GTFS schedule record count, not operated departures.
  Stop weekday/weekend counts count schedule event templates enabled on at
  least one corresponding recurring weekday flag; they are not daily totals
  and do not expand exception dates.
- **Service span:** latest scheduled arrival minus earliest scheduled
  departure in service-day seconds. Extended hours remain extended. It is an
  envelope, not continuous operation.
- **Unique stop sequence count:** distinct non-null `stop_sequence` values
  observed for the route in its schedule records.
- **Stop connectivity:** distinct serving routes, with transparent bands:
  isolated (0), low (1-2), medium (3-10), high (>10). These labels describe
  schedule topology only.
- **Route overlap:** reuses Phase 3B's positive shared-stop pairs and Jaccard
  definition. Degree is the number of routes with a positive shared-stop edge;
  disjoint pairs are omitted by that established API and therefore do not
  count as overlap neighbors. Route-level `shared_stop_count` is the sum of
  shared-stop counts across positive-overlap neighbors; it can count a shared
  physical stop once for each neighboring route.
- **Temporal profile:** scheduled departures grouped by service-day hour.
  Hours above 23 are retained. Start/end hour and active duration are the
  observed hour-bin envelope; hourly peak means the maximum schedule-record
  count in a route/hour bin, not a passenger peak.
- **Scheduled headway:** positive differences between first scheduled trip
  departure times, calculated within each `(feed_id, route_id, service_id)`.
  Missing or nonpositive gaps are excluded. `large_scheduled_headway` flags
  maximum within-pattern gaps above one hour. This is a schedule-template
  interval, not a measured wait or an interval between operated vehicles.
- **GTFS service accessibility score:** a configurable descriptive composite
  on [0, 1], named `gtfs_service_accessibility_score`. By default, weights are
  frequency 0.35, connectivity 0.25, service span 0.20, and stop coverage
  0.20. Each nonnegative component is divided by its maximum in the supplied
  dataset (min-max scaling is intentionally not used); if its maximum is zero,
  observed zero values normalize to zero. Per route, missing components are
  omitted and remaining weights renormalized. If no component is available,
  the score is missing. The score is not passenger accessibility, demand,
  equity, or observed usage.
- **Gap flags:** `low_scheduled_frequency` uses fewer than one scheduled trip
  per active weekday type; `limited_scheduled_service_span` uses less than six
  hours; `limited_route_connectivity` means no positive shared-stop neighbor.
  These are transparent analyst thresholds, not operator standards.
- **Feed summaries:** within-feed descriptive totals/means. No feed ranking is
  produced; feed modes, structures, and coverage may differ.

## Missing data, exclusions, and quality reporting

The quality table identifies missing input tables/columns, table row counts,
rows excluded because their feed-scoped primary keys are absent/null, and rows
with any null values in expected columns. Joins that require valid feed-scoped
keys naturally omit those records; unmatched references are not presented
as complete coverage. Optional
features return missing when their source columns are unavailable. An absent
calendar leaves date-derived metrics missing. An absent `calendar_dates` is
reported; recurring calendar rules are used as published, while supplied
exception rows are applied explicitly. Zero denominators produce missing
per-day rates. Connectivity for routes with no
overlap is zero because absence of an edge in the supplied edge table is
observable; missing edge inputs remain distinguishable through the quality
report.

The quality report includes assumptions and calendar semantics. Its
`excluded_records` count reports rows missing primary-key fields used for
feed-scoped joins (or all rows when an input table lacks a key column).
`rows_with_any_null_value` is a separate completeness indicator and may include
legitimate nullable GTFS values. Excluded counts do not include all
cross-table unmatched references, so they are not proof that every source
record matched.
Calendar expansion assumes each recurring rule applies over its inclusive
date bounds; it describes scheduled eligibility, not field operation.

## Reproducibility and limitations

The module uses only pandas, NumPy, and existing project analysis functions.
It performs no network access, file writes, model fitting, or random sampling.
The included notebook uses local processed Parquet only when already present;
otherwise it demonstrates function calls with clearly labelled synthetic
fixtures. Synthetic outputs are examples, never Hyderabad findings. GTFS
static schedules cannot establish operated service or passenger activity.
When date bounds or complete weekday flags are absent, unique service dates
cannot be derived and remain missing.
