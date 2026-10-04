"""HYD-MOVE project status dashboard."""

import streamlit as st


st.set_page_config(
    page_title="HYD-MOVE",
    page_icon="🚌",
    layout="wide",
)

st.title("HYD-MOVE")
st.subheader("Hyderabad Urban Mobility Intelligence System")

st.write(
    "An academic data analytics project for building a reproducible "
    "urban mobility data workflow for Hyderabad."
)

st.header("Current Development Status")

st.success("Phase 3C completed — Service and accessibility analytics")

st.markdown(
    """
### Completed phases

- **Phase 1 — Project foundation:** Complete
- **Phase 2A — GTFS architecture:** Complete
- **Phase 2B — Official data acquisition and validation:** Complete
- **Phase 2C — ETL and unified mobility layer:** Complete
- **Phase 2D — Passenger-demand source assessment:** Complete
- **Phase 2E — Controlled acquisition / access review:** Complete
- **Phase 3A — GTFS exploratory analysis:** Complete
- **Phase 3B — Network and temporal analysis:** Complete
- **Phase 3C — Service and accessibility analytics:** Complete
"""
)

st.header("Current Data Sources")

st.markdown(
    """
- **TGSRTC:** Official static GTFS feed
- **HMRL:** Official static GTFS feed
- Both feeds are preserved separately and processed through feed-aware
  validation and normalization.
"""
)

st.warning(
    "GTFS represents scheduled public transport service and network "
    "information. It is not observed passenger-demand data."
)

st.header("Passenger Demand Status")

st.info(
    "No passenger-demand dataset has been integrated. No passenger-demand "
    "values have been inferred from GTFS. Controlled acquisition remains "
    "dependent on suitable documented data access, definitions, and reuse "
    "terms."
)

st.header("Dashboard Scope")

st.write(
    "This dashboard is currently a project status page. It does not "
    "present passenger-demand results or unsupported analytics claims."
)

st.header("Next Development Stage")

st.markdown(
    """
Exploratory analysis and modelling will proceed when suitable observed
mobility or passenger-demand observations are available and quality-checked.

Future dashboard work will present only validated findings together with
their data limitations.
"""
)