# Planned Data Sources

The following are intended external source pages for Phase 2. No files have been downloaded, no pages have been scraped, and no API has been called as part of Phase 2A.

| Intended source | Organization | Dataset type | Planned format | Expected contents |
| --- | --- | --- | --- | --- |
| [TGSRTC Open Data](https://tgsrtc.telangana.gov.in/open-data) | Telangana State Road Transport Corporation (TGSRTC) | Public transport schedule feed, subject to availability and verification | GTFS Schedule ZIP, if provided | Potential agency, bus routes, stops, trips, stop times, and calendar/service data. Actual contents are not yet known. |
| [HMRL Open Data](https://hmrl.co.in/open-data/) | Hyderabad Metro Rail (HMRL) | Public transport schedule feed, subject to availability and verification | GTFS Schedule ZIP, if provided | Potential agency, metro routes/stations, trips, stop times, and calendar/service data. Actual contents are not yet known. |

## Acquisition and Provenance Requirements

- These are planned Phase 2 sources, not downloaded or integrated datasets. Availability, format, coverage, and freshness must be verified at acquisition time.
- Before retrieval, review the publisher's current access, attribution, reuse, redistribution, and update terms. Record relevant terms and obtain any required permission.
- Do not scrape pages or use undocumented endpoints. Use a publisher-provided download mechanism or documented access method only after the project explicitly approves acquisition.
- When a file is actually downloaded, record retrieval date/time, source page and direct feed URL, publisher, feed version (if available), file name, checksum, license/terms, and retrieval method.
- Keep original feed archives immutable under `data/raw/`; store validated or transformed derivatives separately under `data/processed/`.
- A GTFS schedule contains static/scheduled service information, not actual ridership or passenger demand. Any demand analysis requires a separate source and provenance/permissions review.