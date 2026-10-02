# Passenger-Demand Data Provenance and Access Record

## Phase 2E Outcome

- **Review date:** 2026-10-01
- **Outcome:** B — no legitimate machine-readable Hyderabad passenger-demand dataset was confirmed as available for acquisition under documented reuse terms.
- **Acquired demand artifacts:** None.
- **Requests submitted:** None. Manual request forms or RTI channels were not submitted or automated.

This file records source-page verification and the acquisition boundary; it is not provenance for an acquired dataset. No dataset file was downloaded, copied, or saved. Therefore original filename/format, byte size, SHA-256, row count, columns, observed period, and geographic coverage do not apply. No transformations, data cleaning, or demand validation were performed. No demand dictionary or processed output was created because there are no observed fields to describe.

## Sources Checked

| Publisher/source | Official URL | Classification | Finding and reuse status |
| --- | --- | --- | --- |
| L&T Metro Rail (Hyderabad) Limited, Ridership | https://ltmetro.com/ridership/ | `WEBPAGE_ONLY` | Public HTML table remains visible for July 2024-June 2025 at monthly, network-level granularity. It does not define the count or link a machine-readable file/API. The site's copyright notice says all content is protected and warns against unauthorized copying/reproduction/use. Reuse of the table is not established; do not copy values without written permission. |
| Telangana State Road Transport Corporation, Vision & Legacy | https://tgsrtc.telangana.gov.in/about-vision-legacy | `WEBPAGE_ONLY` | Historical narrative contains an approximate passenger-per-day statement without a defined reference date, method, or series. It is not a validated observation series. Reuse terms for that statement were not found. |
| TGSRTC Open Data and RTI | https://tgsrtc.telangana.gov.in/open-data ; https://tgsrtc.telangana.gov.in/rti-act | `MANUAL_REQUEST` for passenger records | Open-data description and terms concern static GTFS supply data (routes, stops, schedules, fares); they do not publish passenger counts. The RTI page provides an information-request route but does not confirm demand-record availability. GTFS reuse terms do not govern a separate demand release. |
| Hyderabad Metro Rail Limited Open Data and RTI | https://hmrl.co.in/open-data/ ; https://hmrl.co.in/right-to-information/ | `MANUAL_REQUEST` for passenger records | Open data describes static GTFS; no passenger count dataset/API was identified there. The RTI page lists a Public Information Officer. Terms for any separate passenger aggregate are not established. |
| L&T Metro Rail contact | https://ltmetro.com/contact-us/ | `MANUAL_REQUEST` for machine-readable metro series | Official operator contact details are published. Request the source series and written reuse permission rather than extracting/reproducing the webpage. |
| Telangana Open Data, RTA Vehicle Registrations | https://data.telangana.gov.in/dataset/regional-transport-authority-vehicle-registrations-data | `PUBLIC_DOWNLOAD` | Public monthly CSV records are listed under Open Government License, India, with RTA-level granularity. This is vehicle registration/motorization context, not passenger demand; `Regn_No` requires data minimization/privacy review. Not acquired. |
| Open Data Telangana Transportation catalog | https://data.telangana.gov.in/search?theme=Transportation | `NOT_AVAILABLE` for passenger observations | Checked transportation listings included static GTFS and administrative/vehicle data but no confirmed passenger count dataset. Search coverage may not be exhaustive. |
| Government of India Open Government Data search | https://www.data.gov.in/search?title=Hyderabad%20Metro ; https://www.data.gov.in/search?title=TGSRTC | `NOT_AVAILABLE` for Hyderabad/Telangana passenger observations | No qualifying local transit passenger dataset was identified in the inspected results. Delhi/Mumbai ridership records and unrelated results were excluded. OGL India applies only to datasets carrying that license, not to the separate L&T webpage. |
| HMDA “CTS - HMA” research lead | https://www.hmda.gov.in/ | `MANUAL_REQUEST` to verify existence | HMDA links to an external legacy site, but publisher, dataset existence, secure access, methodology, geography, and reuse rights remain unverified. Do not acquire from the unverified host; ask HMDA to confirm an official source first. |

The source assessment and its known limitations are retained and extended in [DEMAND_DATA_SOURCE_ASSESSMENT.md](DEMAND_DATA_SOURCE_ASSESSMENT.md). Classification is specific to this review date and is not a claim that no other source exists.

## Manual Request Requirements

No request has been sent. The project owner must contact TGSRTC and HMRL/L&T through their official channels and request only already-aggregated, privacy-safe observations.

For TGSRTC, ask whether dated daily or monthly total passengers or aggregate boardings/alightings exist, and whether route/depot/region/network dimensions can be provided safely. Request definitions, units, counting method, coverage period, gaps/revisions, schema, and written license, attribution, and redistribution terms.

For HMRL/L&T, ask for a machine-readable copy of the monthly public series, the exact meaning and method of its ridership measure, unit, date coverage, revisions, and reuse terms. Ask separately whether non-identifying station/month aggregates are documented and releasable. Do not presume the public table means boardings or station entries.

For any response, reject or quarantine records containing names, phone numbers, email addresses, card/ticket identifiers, individual journeys, precise individual tracking, or other personally identifying passenger information. Do not ingest personal-level data. Preserve any future original artifact unchanged only after source authority, permissions, and privacy are confirmed; then record its actual filename, format, retrieval date, byte size, SHA-256, actual observed fields, and documented limitations before processing.

## Quality and Processing Status

There are no acquired rows to profile or validate. Missing values, duplicates, date ranges, granularity, negative/impossible values, units, and coverage gaps are therefore **not assessed**, not zero or clean. No repair or normalization was performed. No output was written under `data/external/demand/` or `data/processed/demand/`. The GTFS raw ZIPs and existing GTFS Parquet outputs were not modified.