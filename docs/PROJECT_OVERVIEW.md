# HYD-MOVE Project Overview

## Problem Statement

Public transport demand and urban congestion vary over time and location and may relate to routes, service conditions, weather, and calendar effects. HYD-MOVE will provide a reproducible data analytics workflow for investigating those relationships in Hyderabad once appropriate, documented data sources are selected.

No real Hyderabad mobility data has been integrated. The repository's single CSV is an explicitly synthetic fixture for pipeline tests, not evidence about Hyderabad.

## System Architecture

```text
Documented data sources
          |
          v
src/data/ingestion.py --> immutable data/raw/
          |
          v
src/data/cleaning.py --> src/data/preprocessing.py
          |
          v
data/processed/ --> src/analysis/ --> src/models/
                                      |
                                      v
                              dashboard/app.py
```

In Phase 1, the source and analytics modules are only foundational utilities. The dashboard is a status page; it does not load data, train models, or display analytics results.

## Data Flow

1. Record each future source's provenance, permissions, schema, and limitations.
2. Load local tabular source files and preserve the originals in `data/raw/`.
3. Validate columns and assess missingness, duplicates, inconsistencies, and outliers.
4. Create cleaned and feature-prepared outputs separately under `data/processed/`.
5. Explore and visualize suitable data, then fit and evaluate justified analytical models.
6. Publish only validated analysis and its caveats in the dashboard and reports.

## Planned Modules

| Module | Responsibility |
| --- | --- |
| `src/data/` | Tabular ingestion, quality checks, cleaning, and feature preparation. |
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

1. **Foundation:** Establish structure, rules, minimal utilities, synthetic test fixture, status dashboard, and tests. Current phase; no real data or trained models.
2. **Data discovery and acquisition:** Evaluate permitted public transport, route/stop, traffic, weather, and calendar sources; record data dictionaries, provenance, and quality criteria before integration.
3. **ETL and exploratory analysis:** Implement repeatable preparation, missing-data and quality analysis, feature extraction, descriptive statistics, and visual exploration.
4. **Modelling and evaluation:** Establish baselines and evaluate appropriate regression, classification, clustering, and ARIMA/time-series approaches with documented assumptions and accuracy metrics.
5. **Dashboard and academic reporting:** Present validated results, limitations, reproducibility details, and syllabus-aligned conclusions.