# HYD-MOVE: Hyderabad Urban Mobility Intelligence System

HYD-MOVE is an academic data analytics project for studying public transport demand and urban mobility in Hyderabad. It is intended to bring transport, traffic, weather, calendar, and location/time patterns into a reproducible analysis workflow.

> **Data status:** Real Hyderabad mobility datasets have **not** been integrated. The only data file currently provided is a small, explicitly synthetic fixture for testing the data pipeline. No dashboard analytics or real-world findings are presented.

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

1. Identify and document data sources, schemas, permissions, and provenance.
2. Ingest source data while preserving immutable raw inputs.
3. Assess missing values, duplicates, inconsistent values, noise, and outliers.
4. Clean and preprocess validated copies; derive time, route, location, and other relevant features.
5. Perform exploratory, statistical, correlation, and visual analysis.
6. Fit and evaluate appropriate analytical models using reproducible splits and documented metrics.
7. Present validated results and limitations in the Streamlit dashboard.

## Planned Technology Stack

- Python, Pandas, NumPy, SciPy
- Scikit-learn and Statsmodels
- Matplotlib, Seaborn, and Plotly
- Streamlit
- SQLite for an initial local database
- Git and GitHub for version control
- Pytest for automated tests

## Planned Datasets

Potential sources, subject to availability, permissions, and documented provenance, include public transport ridership and service records, route and stop reference data, traffic observations, weather observations, and public holiday/calendar records. GPS- or sensor-derived data may be considered where access and privacy requirements allow. No external API has been connected and no real dataset has been downloaded or integrated in Phase 1.

`data/raw/synthetic_traffic_sample.csv` is a tiny synthetic test fixture. Its locations and values are illustrative only and must not be treated as Hyderabad observations or used to support findings.

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

1. **Foundation (current):** Repository structure, documented rules, synthetic pipeline fixture, minimal utilities, dashboard shell, and tests. No real data or trained models.
2. **Data discovery and acquisition:** Select permitted data sources, document provenance and schemas, and define a data dictionary and validation rules before integration.
3. **Data preparation and exploration:** Build reproducible ETL, data-quality reporting, feature preparation, exploratory analysis, and visualizations.
4. **Modelling and evaluation:** Establish baselines, evaluate suitable regression/classification/clustering/forecasting approaches, and document assumptions and limitations.
5. **Dashboard and reporting:** Present validated findings and model performance, then prepare academic reporting and reproducibility materials.

## Getting Started

Install the dependencies with `python -m pip install -r requirements.txt`, then run the tests with `python -m pytest -q`. To view the Phase 1 status page, run `streamlit run dashboard/app.py`.