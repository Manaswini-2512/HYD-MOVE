# HYD-MOVE Project Overview

## Problem Statement

Public transport demand and urban congestion vary over time and location and may relate to routes, service conditions, weather, and calendar effects. HYD-MOVE will provide a reproducible data analytics workflow for investigating those relationships in Hyderabad once appropriate, documented data sources are selected.

No real Hyderabad mobility data has been integrated. The CSV in `data/raw/` is an explicitly synthetic fixture for existing pipeline tests; the GTFS test archive is generated in pytest temporary storage. Neither is evidence about Hyderabad.

## System Architecture

```text
Planned TGSRTC + HMRL sources
          |
          v
GTFS ZIP --> src/data/ingestion.py
          |
          v
src/data/gtfs_validation.py
          |
          v
src/data/gtfs_transform.py
          |
          v
normalized transport tables
          |
          v
future analytics / database
                                      |
                                      v
                              dashboard/app.py
```

Phase 2A implements local GTFS ZIP ingestion, validation, and schedule-derived summaries. Feeds are not downloaded, extracted to disk, or written to a production database. GTFS is static/scheduled service data and does not contain observed passenger demand. The dashboard remains a status page and does not display analytics results.

## Data Flow

1. Document planned source pages, permissions, expected schemas, and retrieval metadata.
2. After an approved controlled acquisition, preserve source GTFS ZIP archives unchanged in `data/raw/`.
3. Read available TXT members directly from ZIP files and report required/optional files.
4. Validate table schemas, identifiers, foreign keys, dates/times, coordinates, and empty tables.
5. Produce schedule-derived route, stop, trip, service-frequency, and route-stop summaries.
6. Later, load validated data into a normalized database and conduct analytics only with appropriate data.

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
2. **Phase 2A, GTFS architecture (current):** ZIP ingestion, validation, schedule transforms, provenance plan, data dictionary, and normalized database proposal. No feed acquisition.
3. **Phase 2B, controlled acquisition (next):** Review terms, retrieve approved TGSRTC/HMRL feeds, record checksums and retrieval dates, and validate actual contents.
4. **ETL and exploratory analysis:** Implement repeatable preparation, quality reporting, features, statistics, and visualization using suitable acquired data.
5. **Modelling, dashboard, and academic reporting:** Evaluate justified methods and publish only validated results and limitations.