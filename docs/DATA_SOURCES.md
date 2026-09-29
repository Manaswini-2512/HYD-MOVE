# Planned Data Sources

The TGSRTC and HMRL official GTFS archives listed below were manually acquired through their official data-request mechanisms, as reported by the project owner. The raw ZIP files are preserved unchanged and independently validated. No pages were scraped and no API was called for acquisition.

| Source | Organization | Dataset type | Acquired format | Observed contents |
| --- | --- | --- | --- | --- |
| [TGSRTC Open Data](https://tgsrtc.telangana.gov.in/open-data) | Telangana State Road Transport Corporation (TGSRTC) | Public transport static schedule feed | GTFS Schedule ZIP; acquired file `TGSRTC_GTFS.zip` | Observed tables include agency, routes, stops, trips, stop times, calendar, shapes, and feed metadata. See the quality report. |
| [HMRL Open Data](https://hmrl.co.in/open-data/) | Hyderabad Metro Rail Ltd. (HMRL) | Public transport static schedule and fare feed | GTFS Schedule ZIP; acquired file `HMRL_GTFS.zip` | Observed tables include agency, routes, stops, trips, stop times, calendar, fares, shapes, and feed metadata. See the quality report. |

## Acquisition and Provenance Requirements

- Phase 2B acquisition is complete for these two source archives; retrieval timestamp and direct download URL are not determined. File-level provenance and observed date coverage are in `DATA_PROVENANCE.md`.
- Before any future refresh or new acquisition, review the publisher's current access, attribution, reuse, redistribution, and update terms. Record relevant terms and obtain any required permission.
- Do not scrape pages or use undocumented endpoints. Use a publisher-provided download mechanism or documented access method only after the project explicitly approves acquisition.
- Keep original feed archives immutable under their separate `data/external/tgsrtc/` and `data/external/hmrl/` directories; store validated or transformed derivatives separately under `data/processed/`.
- Record retrieval date/time and direct feed URL when verifiable. For these acquisitions those values are explicitly marked "Not determined" rather than inferred from filesystem timestamps.
- A GTFS schedule contains static/scheduled service information, not actual ridership or passenger demand. Any demand analysis requires a separate source and provenance/permissions review.