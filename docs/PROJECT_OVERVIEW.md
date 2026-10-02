# HYD-MOVE Project Overview

## Problem Statement

Public transport demand and urban congestion vary over time and location and may relate to routes, service conditions, weather, and calendar effects. HYD-MOVE will provide a reproducible data analytics workflow for investigating those relationships in Hyderabad once appropriate, documented data sources are selected.

Official TGSRTC and HMRL static GTFS feeds have been manually acquired and are preserved separately in `data/external/`. The CSV in `data/raw/` is an explicitly synthetic fixture for existing pipeline tests; the GTFS test archive is generated in pytest temporary storage. GTFS is schedule/network information, not observed passenger demand.

## System Architecture

```text
TGSRTC ZIP                         HMRL ZIP
  |                                 |
  v                                 v
GTFS ingestion                  GTFS ingestion
  |                                 |
  v                                 v
Independent validation          Independent validation
  |                                 |
  v                                 v
Schedule summaries              Schedule summaries
  |                                 |
  +----------> Phase 2C feed-scoped normalized tables
                |
                v
          Future analytics / database
                |
                v
            dashboard/app.py
```

Phase 2A implemented local GTFS ZIP ingestion, validation, and schedule-derived summaries. In Phase 2B the official source archives were manually obtained, checksummed, and validated separately. They remain unchanged and unextracted. No production database has been created. GTFS is static/scheduled service data and does not contain observed passenger demand. The dashboard remains a status page and does not display analytics results.

## Data Flow

1. Preserve the two manually acquired official GTFS ZIPs unchanged under separate `data/external/` directories.
2. Record source, available retrieval metadata, file size, SHA-256, service period, terms, and attribution in the manifest/provenance document.
3. Read available TXT members directly from each ZIP and report required/optional files.
4. Validate table schemas, identifiers, foreign keys, dates/times, coordinates, and empty tables independently.
5. Produce schedule-derived summaries only; these are not demand measures.
6. In Phase 2C, normalize into feed-scoped canonical tables, derive scheduled route/stop service summaries, run quality checks, and write Parquet outputs without merging the two feed identities.

## Phase 2D: Passenger Demand Data Discovery

GTFS currently provides scheduled routes, stops, trips, calendars, stop times, and feed-scoped network relationships only. Passenger demand requires separate observed data; no passenger-demand dataset is integrated and no passenger values have been inferred. Phase 2D assesses possible official, government, and research sources, including their access paths, licenses, data definitions, and unresolved limitations. See [DEMAND_DATA_SOURCE_ASSESSMENT.md](DEMAND_DATA_SOURCE_ASSESSMENT.md) and [demand_sources.json](../data/external/demand_sources.json). No data has been downloaded for this assessment.

## Planned Modules

| Module | Responsibility |
| --- | --- |
| `src/data/` | Tabular ingestion, quality checks, cleaning, and feature preparation. |
| `src/data/gtfs_validation.py` | GTFS file/schema/key/reference/date/time/coordinate validation reports. |
| `src/data/gtfs_transform.py` | Schedule-derived transport summaries; no passenger-demand estimates. |
| `src/analysis/` | Descriptive statistics, frequency summaries, correlations, and IQR outlier detection. |
| `src/models/` | Unfitted regression, classification, clustering, and ARIMA model factories for later work. |
| `src/utils/` | Shared project paths and configuration. |
| `dashboard/` | Streamlit status page now; validated visual analytics in a later phase. |
| `tests/` | Automated checks for data utilities and future project behavior. |

## Syllabus-to-Module Mapping

| Unit | Concepts | Planned location/application |
| --- | --- | --- |
| I: Data Management | Data sources and architecture, variables, sensors/GPS, data management/quality, missing values, duplicates, inconsistencies, noise, outliers, processing. | `docs/`, `src/data/`, `data/raw/`, and `data/processed/`; future source inventory and data dictionary. |
| II: Data Visualization | Univariate visualization/statistics, distributions, bivariate and multivariate analysis, quantitative/qualitative attributes, descriptive statistics, frequencies, infographics. | `src/analysis/`, future notebooks, and the later dashboard. |
| III: Data Analysis | Analytics environment, exploratory and missing-data analysis, modelling techniques, business/problem modelling. | `src/analysis/`, future notebooks, and documented problem framing. |
| IV: Data Modelling | Correlation, linear/non-linear/logistic regression, least squares, assumptions, evaluation, model trade-offs, business analytics. | `src/analysis/correlation.py`, `src/models/regression.py`, later evaluation utilities and documentation. |
| V: Objective Segmentation | Classification, decision trees, overfitting/pruning, ensembles, unsupervised learning, clustering, time series/ARIMA, forecast accuracy, ETL, feature extraction; optional text analytics. | `src/data/`, `src/models/`, future model evaluation, and optional extension modules. |

## Future Development Phases

1. **Phase 1, foundation (complete):** Repository, minimal utilities, status dashboard, and data-pipeline tests.
2. **Phase 2A, GTFS architecture (complete):** ZIP ingestion, validation, schedule transforms, data dictionary, and normalized database proposal.
3. **Phase 2B, acquisition and validation (complete):** Official TGSRTC/HMRL ZIPs preserved, checksummed, and independently inspected.
4. **Phase 2C, ETL and unified mobility layer (complete):** Feed-aware normalized Parquet tables, schedule summaries, quality accounting, and lineage are generated. The feeds remain traceable separately; schedules do not represent passenger demand.
5. **Phase 2D, passenger-demand source assessment (complete):** Evaluate candidate direct observations/proxies, access paths, licensing, and unknowns. No demand data was integrated and no values were inferred.
6. **Phase 2E, controlled acquisition (Outcome B; access review complete):** Official checks did not confirm a reusable machine-readable Hyderabad passenger-demand dataset. No data was acquired; controlled acquisition awaits manual operator responses, documented definitions, and written reuse/privacy terms. See [DEMAND_DATA_PROVENANCE.md](DEMAND_DATA_PROVENANCE.md).
7. **Exploratory analysis and modelling:** Proceed only after suitable observations are available and quality-checked.
8. **Dashboard and academic reporting:** Present validated findings and limitations.