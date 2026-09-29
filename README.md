# HYD-MOVE: Hyderabad Urban Mobility Intelligence System

HYD-MOVE is an academic data analytics project for studying public transport demand and urban mobility in Hyderabad. It is intended to bring transport, traffic, weather, calendar, and location/time patterns into a reproducible analysis workflow.

> **Data status:** No real Hyderabad mobility datasets have been integrated. The repository contains a small synthetic CSV for existing pipeline tests; Phase 2A GTFS test content is generated only in temporary pytest storage. Neither is real transit or Hyderabad data, and no real-world findings are presented.

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

1. Identify and document intended data sources, schemas, permissions, and provenance.
2. In a later controlled acquisition, retrieve approved source archives and preserve them as immutable raw inputs.
3. Ingest GTFS ZIP tables, then validate required files, schemas, identifiers, coordinates, times, and relationships.
4. Transform validated schedules into normalized transport tables and schedule-derived summaries.
5. In later phases, combine suitable sources for exploratory, statistical, and visual analysis.
6. Evaluate appropriate analytical models only after suitable data is acquired and prepared.
7. Present validated results and limitations in the Streamlit dashboard.

## Phase 2A: GTFS Ingestion and Transport Data Architecture

Phase 2A establishes GTFS ZIP ingestion, structural validation, schedule-only transformations, provenance documentation, and a proposed normalized SQLite schema. It does not download feeds, create a database, or perform modelling or forecasting.

The intended sources are TGSRTC and HMRL. Their feeds have not been downloaded or inspected. GTFS represents scheduled/static transit information and does **not** directly represent passenger demand.

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

## Planned Technology Stack

- Python, Pandas, NumPy, SciPy
- Scikit-learn and Statsmodels
- Matplotlib, Seaborn, and Plotly
- Streamlit
- SQLite for an initial local database
- Git and GitHub for version control
- Pytest for automated tests

## Planned Datasets

Potential future sources, subject to availability, permissions, and documented provenance, include TGSRTC and HMRL GTFS schedules, separate public transport ridership records, traffic observations, weather observations, and public holiday/calendar records. GPS- or sensor-derived data may be considered where access and privacy requirements allow. No external API has been connected and no real dataset has been downloaded or integrated.

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

1. **Phase 1, foundation (complete):** Repository structure, rules, basic utilities, dashboard shell, and tests. No real data or trained models.
2. **Phase 2A, GTFS architecture (current):** ZIP ingestion, validation, schedule transformations, data dictionary, source provenance plan, and proposed database schema without acquiring feeds.
3. **Phase 2B, controlled acquisition (next):** Review source terms, retrieve approved TGSRTC/HMRL GTFS files, record provenance/checksums/retrieval dates, and validate actual feed contents.
4. **Data preparation and exploration:** Build reproducible ETL and exploratory analysis using documented real data.
5. **Modelling, evaluation, dashboard, and reporting:** Proceed only after suitable data is available and quality-checked; document assumptions and limitations.

## Getting Started

Install the dependencies with `python -m pip install -r requirements.txt`, then run the tests with `python -m pytest -q`. To view the Phase 1 status page, run `streamlit run dashboard/app.py`.