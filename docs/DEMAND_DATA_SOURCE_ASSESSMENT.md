# Passenger Demand Data Source Assessment

**Initial assessment checked:** 2026-09-29. **Phase 2E source verification checked:** 2026-10-01. No demand dataset was downloaded, integrated, copied into project data, or used to make passenger estimates. Findings below separate what a source explicitly publishes from claims, interpretation, and unknowns.

## Definition

- **Supply data** describes the service offered: routes, stops, trips, schedules, and service calendars. The current TGSRTC/HMRL GTFS layer is supply data. A trip or stop-time count is not passenger demand.
- **Direct demand observations** are source-recorded passenger activity, such as boardings, alightings, station entries/exits, ticket validations, ticket-sale counts, or published ridership totals. Published aggregate totals are direct observations only at the granularity the source actually reports; their measurement definition still needs confirmation.
- **Demand proxies** are indirect measures that may describe mobility context, such as footfall, vehicle flows, travel surveys, or origin-destination observations. Vehicle registrations indicate motorization/vehicle acquisition, not trips, transit use, or passenger demand.

## Candidate Sources

| Source | Publisher | Mode | Coverage | Time coverage | Granularity | Demand type | Access | License / reuse status | Acquisition effort |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Hyderabad Metro Ridership page](https://ltmetro.com/ridership/) | L&T Metro Rail (Hyderabad) Limited website; table-specific author not stated | Metro | Hyderabad Metro network; no station/line breakdown shown | 12 visible months: July 2024-June 2025; latest visible month June 2025 | Monthly, network-level | Direct source-labelled ridership totals; exact counting definition unknown | Direct public HTML page; no file/API for this table found | Reuse terms not determined; operator website states its content is protected | Medium: a summary is visible, but a documented, reusable time series and definition must be requested |
| [TGSRTC Vision & Legacy page](https://tgsrtc.telangana.gov.in/about-vision-legacy) | Telangana State Road Transport Corporation | Bus | The page discusses Telangana and neighboring-state operations; coverage for the passenger figure is not specified | Reference period for the statement is not specified | One approximate daily aggregate statement, not a time series | Direct-demand claim only: page says “around 90 lakhs passengers every day”; method and denominator are not documented | Direct public HTML page | Reuse terms for this statistic are not determined; TGSRTC open-data terms specifically describe its published open data | High: a dated, defined and machine-readable aggregate would require a separate request |
| [Telangana RTA Vehicle Registrations Data](https://data.telangana.gov.in/dataset/regional-transport-authority-vehicle-registrations-data) | Transport Commissioner, Telangana Department of Transport | Road vehicles, multiple classes | Telangana; metadata says RTA-level granularity | 2014-February 2026 | Monthly resource files, RTA-level registrations | Contextual motorization proxy only; not passenger trips or public-transport demand | Public CSV resource links and a catalog API link are shown | Catalog metadata lists Open Government License, India; review resource terms/attribution and privacy before use | Medium: monthly files, office-code/geographic alignment, and registration-number privacy screening are needed |
| TGSRTC operational passenger aggregates (request target; dataset not confirmed) | Potentially TGSRTC, if such aggregates are releasable | Bus | Not determined | Not determined | Desired request could ask for documented daily/monthly counts by route/depot/time, but availability is unknown | Potential direct observations; no such dataset confirmed in the inspected public sources | Manual request to TGSRTC/RTI channel; existing GTFS request form is for static GTFS, not demonstrated demand data | Not determined; obtain written terms, attribution and redistribution conditions with any response | High: manual response, data dictionary, privacy review and terms required |
| HMRL/operator passenger aggregates (request target; dataset not confirmed) | Potentially HMRL or L&T Metro Rail (Hyderabad) Limited; record owner not determined | Metro | Not determined | Not determined | Desired request could ask for monthly network or station entries/exits, but no such release was confirmed | Potential direct observations; no station-level or ticket-validation dataset confirmed | Manual inquiry to HMRL/operator; the public GTFS form is not a demand-data request | Not determined; obtain written terms, definitions and privacy conditions | High: owner, definitions, access route and permissible granularity need confirmation |
| [CTS - HMA link on HMDA](https://www.hmda.gov.in/) | HMDA page links to a separate `ctshma2011.finnaclle.com` site; actual publisher/data custodian not confirmed | Potentially multimodal; not confirmed from the landing page | “HMA” appears in the linked title; exact study boundary unknown | Not determined | Not determined; survey/OD granularity is not documented on the HMDA page | Potential travel-survey/OD proxy lead only; no underlying survey data confirmed | HMDA home page links to a separate legacy HTTP site; actual content/access was not verified | Reuse terms not determined; linked-site ownership and provenance need verification | High: confirm publisher, secure/current access, data availability, methodology, license and geographic/temporal definitions |
| [TGSRTC GTFS catalog record](https://data.telangana.gov.in/dataset/telangana-state-road-transport-corporation-tgsrtc-general-transit-feed-specification-gtfs) | TGSRTC; catalog record by Open Data Telangana | Bus | Telangana/Hyderabad-tagged supply feed; precise boundary must be read from the feed | Current project feed calendar: 2026-09-01 to 2031-09-01 | Routes, stops, trips, stop times and calendar | **Supply only** | Official form/manual email download; catalog says filling the TGSRTC form yields a download link | Catalog lists Government Open Data License - India; TGSRTC page has its own terms/attribution | Medium for supply refresh; does not fill the demand-data gap |
| [HMRL GTFS catalog record](https://data.telangana.gov.in/dataset/gtfs-hmrl-hyderabad) | Hyderabad Metro Rail Limited; catalog record by Open Data Telangana | Metro | Hyderabad Metro network | Current project feed calendar: 2026-09-02 to 2030-01-01 | Routes, stations/stops, trips, stop times, calendars and fares | **Supply only** | Official form/manual email download | Catalog lists Open Government License, India; HMRL page has separate terms/required attribution | Medium for supply refresh; does not fill the demand-data gap |
| [MMTS Hyderabad GTFS catalog record](https://data.telangana.gov.in/dataset/gtfs-mmts-hyderabad) | South Central Railway; catalog record by Open Data Telangana | Suburban rail | Hyderabad MMTS; precise feed extent not inspected | Catalog last update 15 February 2023; feed service dates not determined | Routes, stops, trips, stop times and calendar | **Supply only** | Manual Google Form request and emailed link, per catalog | Catalog lists Open Government License, India; verify the source terms before use | Medium/high: manual request and stale catalog update require freshness verification |

## Detailed Source Profiles

### Hyderabad Metro Ridership Page

**Publisher:** L&T Metro Rail (Hyderabad) Limited operates the `ltmetro.com` site; the ridership table does not state a separate data author.

**Official URL:** [ltmetro.com/ridership](https://ltmetro.com/ridership/)

**Geographic coverage:** Hyderabad Metro network is implied by the page identity; station/corridor coverage is not itemized.

**Transport mode:** Metro.

**Time period:** The page currently exposes 12 monthly rows from July 2024 through June 2025. No earlier history or update cadence was established.

**Demand variables:** The visible table has month and a source-labelled ridership count. The page does not define whether the count represents entries, boardings, journeys, validations, or another operator metric.

**Granularity:** Monthly, network-level. No station, route, direction, or hourly breakdown is shown.

**Access method:** Public human-readable webpage. No downloadable table or API was documented on the page. Do not scrape or automate extraction without permission.

**License/terms:** Reuse terms for the table are not determined. The operator site states its content is protected by applicable intellectual-property laws and warns against unauthorized copying/reproduction.

**Update frequency:** Not determined. June 2025 is the latest visible month as of this review.

**Known limitations:** Only 12 values were visible; no data dictionary, counting definition, revision history, station breakdown, or machine-readable file was found.

**Manual action required:** Ask the operator for the underlying monthly series, exact measure definition, coverage, revision policy, and reuse/attribution permission.

**Potential use in HYD-MOVE:** Could support network-level monthly metro demand trends after the measure definition and reuse rights are confirmed; it cannot support station-level analysis as currently published.

**Evidence status:** **Confirmed:** the page displays month and ridership values for July 2024-June 2025. **Unknown:** the count definition, collection method and license for reuse.

### TGSRTC Published Passenger-Volume Statement

**Publisher:** Telangana State Road Transport Corporation.

**Official URL:** [TGSRTC Vision & Legacy](https://tgsrtc.telangana.gov.in/about-vision-legacy)

**Geographic coverage:** Not specified for the passenger figure. The page separately describes services in Telangana and neighboring states; this does not establish the figure’s geography.

**Transport mode:** Bus.

**Time period:** Not determined. The page does not date the “around 90 lakhs passengers every day” statement.

**Demand variables:** One approximate daily passenger-volume statement only. No table, field definitions, route/station dimensions, source files, or observed rows are provided.

**Granularity:** Stated daily aggregate, with no time series.

**Access method:** Public HTML statement, not a dataset. TGSRTC’s [RTI page](https://tgsrtc.telangana.gov.in/rti-act) describes information held electronically and identifies RTI authorities; it does not confirm that route/time ridership records are available.

**License/terms:** Reuse terms for this page statement are not determined. Do not assume the separate GTFS license applies to this text.

**Update frequency:** Not determined.

**Known limitations:** The figure is approximate, undated, undefined, and not reproducible from accompanying records. It must not be treated as a verified daily time series.

**Manual action required:** Request a dated, defined, anonymized aggregate dataset and supporting data dictionary/terms from TGSRTC; use the formal RTI process only if appropriate.

**Potential use in HYD-MOVE:** At most, contextual evidence that the agency has published an approximate scale statement; it is not suitable as a training series or for route-level analysis.

**Evidence status:** **Confirmed:** the TGSRTC page contains the approximate phrase. **Unknown:** reference date, geographic scope, measurement definition and underlying source data.

### Telangana RTA Vehicle Registrations Data

**Publisher:** Transport Commissioner, Telangana Department of Transport, according to the Open Data Telangana record.

**Official URL:** [Regional Transport Authority Vehicle Registrations Data](https://data.telangana.gov.in/dataset/regional-transport-authority-vehicle-registrations-data)

**Geographic coverage:** Telangana; catalog metadata specifies RTA-level granularity.

**Transport mode:** Multiple vehicle classes; not a public-transport ridership dataset.

**Time period:** The record states 2014 through February 2026. Metadata shows last update `12/03/2026`; the date-format interpretation is not assumed here.

**Demand variables:** Published fields include `Regn_No`, `Regn_VFDt`, `Regn_VTDt`, `Maker_Name`, `Model_Desc`, `BodyTyp`, `CC`, `Cylinder`, `Engine Fuel`, `HP`, `Seat_Capacity`, `Apprved_Dt`, and `OfficeCd`. These describe registrations/vehicles, not passenger journeys.

**Granularity:** RTA-level, with monthly CSV resource files listed on the record page.

**Access method:** The record exposes public CSV preview/download links and an API link. API authentication/key requirements were not determined from the rendered API page.

**License/terms:** Record metadata lists **Open Government License, India**. Follow the current license and any record-specific conditions; source-specific attribution wording was not determined from the landing page. The portal’s general copyright policy also describes permission/acknowledgement requirements for portal material, distinct from the dataset license.

**Update frequency:** Catalog metadata says monthly; latest period displayed is February 2026.

**Known limitations:** RTA-level boundaries may not align with feed coverage. Registration activity is vehicle acquisition/registration, not vehicle use, trips, transit choices, boardings, or passenger demand. `Regn_No` is an identifying vehicle field and requires privacy/data-minimization review before any future use.

**Manual action required:** No manual form was shown for CSV access. Before integration, review the actual resource terms, API requirements, `OfficeCd` geography, and whether identifying fields can be excluded at ingestion.

**Potential use in HYD-MOVE:** Could provide contextual motorization/vehicle-fleet trends, clearly separated from transit demand. It must not be used as passenger counts or an estimate of transit ridership.

**Evidence status:** **Confirmed:** the catalog lists publisher, fields, RTA granularity, monthly frequency, 2014-February 2026 coverage, public level, and OGL India. **Unknown:** actual record-level quality and any city/office crosswalk; files were not downloaded or inspected.

### TGSRTC Passenger-Count Request Target

**Publisher:** Potentially TGSRTC; no separate passenger dataset was located.

**Official URL:** [TGSRTC Open Data](https://tgsrtc.telangana.gov.in/open-data) and [TGSRTC RTI](https://tgsrtc.telangana.gov.in/rti-act).

**Geographic coverage:** Not determined.

**Transport mode:** Bus.

**Time period:** Not determined.

**Demand variables:** No released field list confirmed. A future request could ask whether non-personal boardings or ticket-validation aggregates exist; this is a request specification, not a claim about source systems.

**Granularity:** Not determined.

**Access method:** Manual request to the agency; the GTFS form on Open Data is for static schedules and must not be treated as a passenger-data request.

**License/terms:** Not determined; must be agreed/documented if data is offered.

**Update frequency:** Not determined.

**Known limitations:** Dataset existence, definitions, coverage, aggregation options, privacy controls and availability are unconfirmed.

**Manual action required:** Ask TGSRTC for anonymized aggregates, a data dictionary, date range, route/depot/time dimensions, missingness/revision policies, and written license/attribution terms.

**Potential use in HYD-MOVE:** If released with appropriate definitions and rights, could provide bus passenger observations to relate to the TGSRTC schedule feed.

**Evidence status:** **Confirmed:** TGSRTC has an official static GTFS request page and RTI information page. **Unknown:** whether operational passenger aggregates are retained or releasable.

### HMRL Passenger-Count Request Target

**Publisher:** Potentially Hyderabad Metro Rail Ltd. or L&T Metro Rail (Hyderabad) Limited; ownership of any operational count data is not determined.

**Official URLs:** [HMRL Open Data](https://hmrl.co.in/open-data/), [L&T Metro Ridership](https://ltmetro.com/ridership/), and [HMRL contact page](https://hmrl.co.in/contact-us/).

**Geographic coverage:** Not determined for any undisclosed dataset.

**Transport mode:** Metro.

**Time period:** Not determined beyond the monthly values visible on the public ridership page.

**Demand variables:** The public table shows month and source-labelled ridership totals. Station entry/exit, ticket-validation, smart-card and transaction-level fields are not confirmed.

**Granularity:** Public summary is monthly network-level; any finer granularity is unknown.

**Access method:** Public summary page; request a machine-readable series from the operator/agency. The GTFS request form does not establish access to passenger data.

**License/terms:** Reuse terms for the monthly table and any requested detail are not determined; HMRL's GTFS terms are not assumed to govern a separate ridership dataset.

**Update frequency:** The public page visibly contains 12 months through June 2025; update frequency is not determined.

**Known limitations:** Metric definition, data owner, revisions, station coverage and shareable aggregation level are unknown. HMRL's GTFS documentation excludes payment information from its static feed, which does not establish whether a separate aggregate ridership product exists.

**Manual action required:** Ask HMRL/operator for the monthly series in a documented machine-readable form, definition/unit, temporal/geographic completeness, non-personal aggregation, permission and attribution.

**Potential use in HYD-MOVE:** Could support monthly system-level or (if separately authorized and provided) station-level metro demand analysis.

**Evidence status:** **Confirmed:** the operator site publishes monthly ridership figures for July 2024-June 2025. **Unknown:** data ownership, exact measure, downloadable source and more granular records.

### HMDA CTS - HMA Research Lead

**Publisher:** HMDA's public homepage lists “CTS - HMA” and links to a separate legacy HTTP host; actual dataset publisher/custodian is not confirmed.

**Official URL:** [HMDA homepage](https://www.hmda.gov.in/) (the linked target displayed there is `http://ctshma2011.finnaclle.com/index.php`).

**Geographic coverage:** “HMA” is present in the link title; exact boundary not determined.

**Transport mode:** Not determined.

**Time period:** Not determined.

**Demand variables:** No dataset fields or survey variables documented on the HMDA page.

**Granularity:** Not determined; do not assume an origin-destination survey exists based on the “CTS” title.

**Access method:** HMDA provides an external legacy HTTP link. The linked site was not treated as a verified dataset source in this assessment.

**License/terms:** Not determined.

**Update frequency:** Not determined.

**Known limitations:** Linked-domain ownership/security, current availability, publisher, data existence, source methodology, survey time period and reuse rights are all unverified.

**Manual action required:** Ask HMDA to confirm whether a travel/OD survey dataset exists, its custodian, secure official access route, data dictionary, methodology, license and permission.

**Potential use in HYD-MOVE:** If the publisher confirms a licensed survey resource, it could provide historical travel/OD proxy observations; no such use is currently substantiated.

**Evidence status:** **Confirmed:** the HMDA homepage links the title to the external host. **Unknown:** whether that host contains an official survey or reusable data.

## Search Findings and Exclusions

- The Open Data Telangana Transportation catalog shows TGSRTC GTFS, HMRL GTFS, MMTS GTFS and RTA vehicle records among the relevant visible results. Its GTFS filter lists three supply feeds; these do not contain passenger counts. The inspected catalog pages did not reveal a passenger-count dataset, but this is not proof that no such resource exists elsewhere.
- The Government of India Open Data portal describes government datasets as publisher-owned and licensed under OGL India where so marked. Its catalog/API search results and API definition were not fully inspectable in this review (client-rendered search and a mixed-content API documentation failure). No specific Hyderabad passenger-demand resource is confirmed from that portal.
- A Zenodo result titled “Travel Accessibility Criterion of Urban Commuters: Evidence from Hyderabad, Pakistan” is explicitly about Hyderabad, Pakistan, not Hyderabad, India. Zenodo describes 384 questionnaire responses, but its listed file is a journal-article PDF rather than a documented raw survey dataset. It is excluded from HYD-MOVE candidate sources despite its CC BY 4.0 article license.
- No downloadable Hyderabad bus boardings/alightings, HMRL station-entry series, AFC/smart-card aggregates, or local passenger OD table was confirmed in the pages inspected.

## Confirmed, Claimed, and Unknown

- **Confirmed:** HMRL's operator page displays a 12-row monthly ridership table (July 2024-June 2025); the TGSRTC legacy page contains the approximate daily passenger statement; Telangana's RTA record metadata and listed variables; catalog metadata and form flow for GTFS supply feeds.
- **Claimed:** TGSRTC's approximate “around 90 lakhs passengers every day” statement. It is a source-published claim, not an audited or reproducible dataset, and its date/definition/coverage are unspecified.
- **Unknown:** Whether TGSRTC or HMRL will release detailed aggregate passenger counts; whether the metro page's monthly values count journeys, entries, boardings or another measure; any station-level data; the contents/license of CTS-HMA; and any Hyderabad-specific passenger dataset not surfaced by the inspected catalog results.

## Current HYD-MOVE Demand Data Gap

The Phase 2B/2C layer currently provides scheduled routes, stops, trips, service calendars, scheduled stop times, and feed-scoped network/service relationships. It does **not** provide passengers, boardings, alightings, occupancy, ticket transactions, or validated ridership observations. `trip_count`, route count, stop count and `stop_times` are supply/network structure and must never be substituted for demand. Passenger-demand analysis remains blocked until separate, documented observations are acquired.

## Phase 2E Acquisition Candidates

### Candidate A — Direct Public Download

The Telangana RTA Vehicle Registrations Data record exposes monthly CSV resources and an API link under OGL India metadata. It could contribute motorization context only. Before use, inspect the data dictionary/resources, confirm API access requirements, identify RTA-office geography, minimize or exclude `Regn_No`, and confirm the license/attribution requirements. It cannot be treated as passenger demand.

### Candidate B — Official API

Open Data Telangana links record-level API pages for RTA and GTFS catalog resources, but no demand-specific API was confirmed. Determine whether keys/registration are required and inspect the API schema before considering integration. The Government of India OGD portal is another discovery venue; a specific Hyderabad demand resource and API requirements remain unconfirmed.

### Candidate C — Manual Request

Request non-personal aggregated bus passenger records from TGSRTC and a machine-readable definition/source for HMRL's monthly totals; separately ask whether station-level metro entries/exits are available. Request exact variable definitions, units, date range, aggregation dimensions, update/revision practices, missing-data conventions, privacy controls, license, attribution and redistribution permissions. Manual responses are not guaranteed and are not assumed to exist.

### Candidate D — Research Dataset

Ask HMDA to clarify the CTS-HMA link and whether it leads to a licensed dataset, study report, or survey instrument. Confirm custodian, city/HMA boundary, sample/collection dates, variables, methodology, access security, license and consent/privacy restrictions. Academic repository searches must confirm Hyderabad, India; the Pakistan study found in Zenodo is not applicable.

## Source References

- [TGSRTC Open Data](https://tgsrtc.telangana.gov.in/open-data) and [TGSRTC Vision & Legacy](https://tgsrtc.telangana.gov.in/about-vision-legacy)
- [HMRL Open Data](https://hmrl.co.in/open-data/), [L&T Metro Ridership](https://ltmetro.com/ridership/), and [operator home](https://ltmetro.com/)
- [Open Data Telangana Transportation catalog](https://data.telangana.gov.in/search?theme=Transportation), [RTA registrations record](https://data.telangana.gov.in/dataset/regional-transport-authority-vehicle-registrations-data), and [RTA registrations API record](https://data.telangana.gov.in/dataset/b54f1f1c-2128-4ad1-8f3c-db45ab1a0c8f/api)
- [Government Open Data License - India](https://www.data.gov.in/Godl) and [Open Data Telangana policies](https://data.telangana.gov.in/policies)
- [HMDA homepage](https://www.hmda.gov.in/) and [Zenodo Pakistan study false positive](https://zenodo.org/records/5524130)

## Phase 2E Verification and Outcome

**Checked:** 2026-10-01. Official operator pages and government catalogs were checked before any acquisition. No forms were submitted, no API credentials or access controls were bypassed, and no webpage values or datasets were downloaded. **Outcome B:** no legitimate, reusable machine-readable Hyderabad passenger-demand dataset was confirmed, so no raw demand artifact, normalized output, data dictionary, or demand-processing tests were created.

### Source Access Classification

Classifications describe the current access path. A public supply dataset or a vehicle proxy is not thereby a passenger-demand dataset.

| Source | Classification | Phase 2E finding |
| --- | --- | --- |
| [L&T Metro Rail monthly ridership page](https://ltmetro.com/ridership/) | `WEBPAGE_ONLY` | The official operator page remains accessible and shows July 2024-June 2025 monthly network-level rows. The measure definition is absent; no official download/API was linked or found. The site says all content is protected and unauthorized copying/reproduction/use may result in legal action. Do not copy the values into HYD-MOVE without written permission and a documented definition. |
| [TGSRTC Vision & Legacy](https://tgsrtc.telangana.gov.in/about-vision-legacy) | `WEBPAGE_ONLY` | Contains the approximate “around 90 lakhs passengers every day” statement in historical narrative. It has no dated observation period, method, supporting series, or disaggregation; it is not a time series. |
| TGSRTC operational passenger aggregates | `MANUAL_REQUEST` | No daily/monthly series, route/depot ridership, boarding/alighting, or ticketing aggregate was found in the official open-data or RTI pages. The open-data terms describe static GTFS supply information, not passenger counts. A request through the agency/RTI route is required. |
| HMRL/L&T machine-readable monthly or station-level observations | `MANUAL_REQUEST` | HMRL open data publishes static GTFS (schedules, routes, fares and stops), explicitly not payment or passenger personal data. The separate L&T webpage has an undefined monthly total but no machine-readable series. Request definitions, a reusable export, and written terms from the operator/data owner. |
| [Telangana RTA Vehicle Registrations Data](https://data.telangana.gov.in/dataset/regional-transport-authority-vehicle-registrations-data) | `PUBLIC_DOWNLOAD` | The official catalog lists public monthly CSV resources, RTA-level scope, and Open Government License, India. This is vehicle registration/motorization context only, not transit passenger demand. It includes `Regn_No`, so privacy/data-minimization review is required; it was not acquired. |
| HMDA “CTS - HMA” linked research lead | `MANUAL_REQUEST` | The HMDA homepage links to an external legacy host, but no dataset, custodian, methodology, secure current access, or reuse terms were confirmed. Ask HMDA to establish whether any dataset exists before considering access. |
| [Open Data Telangana transportation catalog](https://data.telangana.gov.in/search?theme=Transportation) | `NOT_AVAILABLE` | The inspected transportation listings exposed GTFS supply feeds and vehicle/transport administration records, but no Hyderabad passenger-count dataset. This catalog search is not proof that no such data exists elsewhere. |
| [Government of India OGD search](https://www.data.gov.in/search?title=Hyderabad%20Metro) | `NOT_AVAILABLE` | Title searches returned no verified Hyderabad transit demand dataset. Results included unrelated Delhi/Mumbai ridership and other metro records; those are not applicable to Hyderabad and were excluded. The OGD license applies to records carrying that license, not to unrelated operator webpage content. |
| Existing TGSRTC/HMRL GTFS records | `MANUAL_REQUEST` | Their official download paths use operator forms, but the feeds contain scheduled service/supply data only. They were not refreshed or modified for Phase 2E and cannot supply passenger counts. |

The status labels are an assessment of the official sources checked on the date above, not a guarantee that no other source exists. No official source located in this review documents a public TGSRTC daily/monthly passenger series or route/depot boarding, alighting, or ticketing aggregate.

### Manual Request Boundary

No request has been sent. The official [TGSRTC RTI page](https://tgsrtc.telangana.gov.in/rti-act) identifies its RTI information process; the [TGSRTC contact page](https://tgsrtc.telangana.gov.in/contact-us) provides general contact details. HMRL lists a Public Information Officer on its [RTI page](https://hmrl.co.in/right-to-information/); L&T provides its operator contact details at [ltmetro.com/contact-us](https://ltmetro.com/contact-us/). Contact should be initiated by a project owner manually.

Request only already-aggregated, non-personal data, and ask the agency to document:

- TGSRTC: whether daily/monthly total passengers or aggregated boardings/alightings exist; available time span; definition, unit and counting method; safe route/depot/region/network granularity; coverage gaps and revisions; schema/data dictionary; written reuse, attribution and redistribution terms.
- HMRL/L&T: the machine-readable source for the displayed monthly series; definition (for example, the operator's exact meaning of “ridership”), unit and method; period and coverage; whether safe station/month aggregates exist; revisions; schema/data dictionary; written reuse, attribution and redistribution terms.
- HMDA: whether the CTS-HMA link refers to an actual dataset; custodian, official secure access, study boundary and dates, variables/methodology, aggregation, privacy/consent conditions, and license.

Request no names, phone numbers, email addresses, card/ticket identifiers, individual journeys, or trace-level records. Reject or quarantine any response containing such data; do not ingest it. Do not convert a published statement into observations or infer passenger demand from GTFS trip, stop, stop-time, route, or service counts.

### Acquisition and Quality Status

No eligible passenger dataset was acquired. Therefore there is no source filename/format, file size, SHA-256, row/column profile, data-type or missingness report, duplicate check, observed date range, geographic granularity, or value validation to report. No transformations were performed. The operator pages and catalog metadata were inspected only; no source artifacts were saved. `data/external/manifest.json` remains unchanged because it tracks acquired GTFS archives and no demand artifact exists. See [DEMAND_DATA_PROVENANCE.md](DEMAND_DATA_PROVENANCE.md) for the Phase 2E access-attempt record.