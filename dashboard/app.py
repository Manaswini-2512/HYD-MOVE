"""Phase 1 status page for the HYD-MOVE project."""

import streamlit as st


st.set_page_config(page_title="HYD-MOVE")
st.title("HYD-MOVE")
st.subheader("Hyderabad Urban Mobility Intelligence System")
st.write(
    "An academic data analytics project for exploring public transport demand "
    "and urban mobility patterns."
)

st.header("Current Development Phase")
st.write("Phase 1: Project Foundation")

st.header("Planned Analytics Modules")
st.markdown(
    """
- Data ingestion, quality, and preprocessing
- Exploratory statistics, correlation, and visualization
- Regression and classification
- Clustering and time-series forecasting
"""
)

st.info(
    "Real Hyderabad mobility datasets have not yet been integrated. "
    "No real-world analytics results are available."
)