# HYD-MOVE: Hyderabad Urban Mobility Intelligence System

HYD-MOVE is an academic data analytics project for studying public transport demand and urban mobility in Hyderabad. It is intended to bring transport, traffic, weather, calendar, and location/time patterns into a reproducible analysis workflow.

> **Data status:** The official TGSRTC and HMRL GTFS archives were manually acquired and are preserved unchanged under `data/external/`. GTFS describes scheduled transit service, not passenger demand. The separate synthetic CSV is used only by the original data-pipeline tests; no ridership or passenger-demand data has been integrated.

## Problem Statement

Urban mobility decisions depend on how demand and congestion vary across routes, times, and locations, and on how those patterns relate to conditions such as weather and holidays. The project will establish a consistent workflow for managing and analyzing those data sources before drawing evidence-based conclusions.

## Motivation

This project applies the data analytics syllabus to a practical urban mobility problem. Its staged development emphasizes data quality, exploratory analysis, visualization, model evaluation, and clear separation between observed data and synthetic test fixtures.

## Objectives

- Prepare a reproducible foundation for ingesting, validating, cleaning, and preprocessing tabular mobility data.
- Explore public transport demand, traffic conditions, weather, calendar effects, and mobility patterns by route, time, and location when suitable data becomes available.
- Use visual and statistical analysis to describe distributions, relationships, and data quality.
- Later evaluate regression, classification, clustering, and time-series methods, including demand forecasts.
- Communicate analysis and its limitations through a dashboard without presenting unsupported results.

## Planned Analytics Pipeline

1. Identify and document data sources, permissions, schemas, and provenance.
2. Preserve the manually acquired source archives unchanged and track their provenance/checksums.
3. Ingest each GTFS ZIP independently and validate files, schemas, identifiers, coordinates, dates, times, and relationships.
4. Review feed-specific quality findings before normalizing schedules into feed-scoped transport tables.
5. Acquire separate observed passenger data before performing passenger-demand analysis.
6. Conduct exploratory analysis and evaluate models only after suitable data is acquired and prepared.
7. Present validated results and limitations in the Streamlit dashboard.

## Phase 2A: GTFS Ingestion and Transport Data Architecture

Phase 2A established GTFS ZIP ingestion, structural validation, schedule-only transformations, provenance documentation, and a proposed normalized SQLite schema. No database or models were created.

The TGSRTC and HMRL feeds were inspected independently in Phase 2B. GTFS represents scheduled/static transit information and does **not** directly represent passenger demand.

```text
TGSRTC + HMRL
			|
			v
		GTFS
			|
			v
		 ETL
			|
			v
	Validation
			|
			v
Normalized transport tables
			|
			v
	Analytics
```

See [DATA_SOURCES.md](docs/DATA_SOURCES.md), [GTFS_DATA_DICTIONARY.md](docs/GTFS_DATA_DICTIONARY.md), and [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) for planned source, field, and storage details.

## Phase 2B: Real GTFS Acquisition and Data Provenance

The TGSRTC and HMRL feeds were manually acquired through their official data-request mechanisms. Their original ZIPs are preserved unchanged in separate `data/external/tgsrtc/` and `data/external/hmrl/` directories. SHA-256 checksums, observed service periods, and source details are recorded in [DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) and [manifest.json](data/external/manifest.json).

Each feed was independently read and validated; they have not been combined. Validation results and optional-file/blank-field observations are documented in [REAL_GTFS_QUALITY_REPORT.md](docs/REAL_GTFS_QUALITY_REPORT.md). GTFS schedule counts are not passenger-demand measurements; demand analysis requires separate observed passenger data.

## Planned Technology Stack

- Python, Pandas, NumPy, SciPy
- Scikit-learn and Statsmodels
- Matplotlib, Seaborn, and Plotly
- Streamlit
- SQLite for an initial local database
- Git and GitHub for version control
- Pytest for automated tests

## Planned Datasets

Acquired static schedule feeds: TGSRTC and HMRL GTFS, recorded in the provenance manifest. No passenger-demand dataset has been integrated. [DEMAND_DATA_SOURCE_ASSESSMENT.md](docs/DEMAND_DATA_SOURCE_ASSESSMENT.md) records current source leads, access/licensing status, and unknowns. Any future passenger counts, traffic observations, weather observations, calendars, GPS, or sensor data require a separate provenance and permissions review. No external API has been connected for data acquisition.

`data/raw/synthetic_traffic_sample.csv` is a tiny synthetic test fixture. Its locations and values are illustrative only and must not be treated as Hyderabad observations or used to support findings. The synthetic GTFS ZIP is generated in pytest temporary storage only and is never a real-feed substitute.

## Expected Outputs

- Documented and quality-checked processed datasets, with raw inputs preserved.
- Exploratory summaries, visualizations, and reproducible analytical notebooks.
- Evaluated models for demand estimation/forecasting and mobility segmentation where data supports them.
- A dashboard presenting evidence, model performance, and limitations.
- Academic documentation mapping methods and deliverables to the syllabus.

## Syllabus Mapping

| Syllabus area | Planned project application |
| --- | --- |
| Unit I: Data Management | Source inventory, schemas and variable types, sensor/GPS considerations, ingestion, data quality, missing values, duplicates, inconsistencies, noise, outliers, and processing. |
| Unit II: Data Visualization | Univariate distributions and statistics, frequencies, quantitative/qualitative comparisons, bivariate and multivariate analysis, and visual summaries/infographics. |
| Unit III: Data Analysis | Analytics environment, business/problem framing, exploratory analysis, missing-data analysis, and modelling approach selection. |
| Unit IV: Data Modelling | Correlation, linear/non-linear and logistic regression, least squares, assumptions, evaluation, trade-offs, and business analytics interpretation. |
| Unit V: Objective Segmentation | Classification and decision trees (including overfitting/pruning and ensembles), clustering, time-series/ARIMA forecasting, forecast accuracy, ETL, and feature extraction. Text analytics is an optional extension. |

## Development Phases

1. **Phase 1, foundation (complete):** Repository structure, rules, basic utilities, dashboard shell, and tests.
2. **Phase 2A, GTFS architecture (complete):** ZIP ingestion, validation, schedule transformations, data dictionary, and database-schema proposal.
3. **Phase 2B, real-feed acquisition and validation (complete):** Official TGSRTC/HMRL feeds manually acquired, checksummed, preserved, and validated separately.
4. **Phase 2C, ETL and unified mobility layer (complete):** Feed-scoped canonical Parquet tables, schedule summaries, quality reporting, and lineage.
5. **Phase 2D, passenger-demand data discovery (current):** Assess candidate sources, access routes, licensing, and limitations. No demand data is integrated and no passenger values are inferred.
6. **Phase 2E, controlled acquisition (next):** Acquire only approved, defined, reusable passenger observations after source terms and provenance are confirmed.
7. **Exploratory analysis and modelling:** Begin only after appropriate observations are acquired and quality-checked.

Phase 2C produces standardized schedules and network relationships only. Passenger demand is **not included**; trip, stop-time, route, and service counts must not be interpreted as ridership. See [UNIFIED_SCHEMA.md](docs/UNIFIED_SCHEMA.md) for field mappings and limitations.

### Phase 2C: ETL and Unified Mobility Layer

```text
Immutable raw GTFS ZIPs
	-> source-specific validation
	-> feed-scoped normalized tables
	-> scheduled route/stop service summaries
	-> Parquet datasets with lineage and quality reporting
```

TGSRTC and HMRL share canonical table schemas but remain traceable as separate feeds through `feed_id` and feed-prefixed IDs. Original source IDs are retained, raw ZIPs remain unchanged, and passenger demand is not included.

## Phase 2D: Passenger Demand Data Discovery

The existing GTFS layer represents scheduled service and network structure; passenger demand requires separate observations. Phase 2D evaluates official operator summaries, government open-data resources, manual-request candidates, and a research lead. It does not download or integrate demand data, create passenger values, or infer demand from trips, routes, stops, or stop times. See [DEMAND_DATA_SOURCE_ASSESSMENT.md](docs/DEMAND_DATA_SOURCE_ASSESSMENT.md) and [demand_sources.json](data/external/demand_sources.json).

## Getting Started

Install the dependencies with `python -m pip install -r requirements.txt`, then run the tests with `python -m pytest -q`. To view the Phase 1 status page, run `streamlit run dashboard/app.py`.