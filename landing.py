"""Country landing page — pick which country's salary statistics to explore."""
import os

import streamlit as st

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_GLOBE  = os.path.join(_ASSETS, "logo.png")
_SWEDEN = os.path.join(_ASSETS, "logo_sweden.png")
_FRANCE = os.path.join(_ASSETS, "logo_france.png")

h_logo, h_title = st.columns([1, 11], vertical_alignment="center")
with h_logo:
    st.image(_GLOBE, width=52)
with h_title:
    st.title("Salary Explorer")
st.caption("Interactive official salary statistics. Pick a country to get started.")
st.write("")

c1, c2 = st.columns(2, gap="large")

with c1:
    with st.container(border=True):
        t_logo, t_name = st.columns([1, 6], vertical_alignment="center")
        with t_logo:
            st.image(_SWEDEN, width=40)
        with t_name:
            st.subheader("Sweden · Sverige")
        st.markdown(
            "- Salary **percentiles (P10–P90)** for ~430 occupations (SSYK)\n"
            "- Sector, sex, **age, region, education** breakdowns\n"
            "- **Work-permit** salary check (Migrationsverket rules)\n"
            "- Inflation-adjusted trends · Data: **SCB**, 2014–2025"
        )
        if st.button("Open Sweden →", type="primary", use_container_width=True, key="go_se"):
            st.switch_page("scb_salaries.py")

with c2:
    with st.container(border=True):
        t_logo, t_name = st.columns([1, 6], vertical_alignment="center")
        with t_logo:
            st.image(_FRANCE, width=40)
        with t_name:
            st.subheader("France")
        st.markdown(
            "- **Mean salaries** for 361 detailed occupations (PCS)\n"
            "- Wage **distribution by socio-professional group**, series since 1951\n"
            "- Inflation-adjusted trends (IPC)\n"
            "- Data: **INSEE**"
        )
        if st.button("Open France →", use_container_width=True, key="go_fr"):
            st.switch_page("france.py")

st.write("")
st.caption("Sources: Statistics Sweden (SCB) PxWebApi · INSEE Melodi API")
