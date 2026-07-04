"""Salary Explorer — multi-country entrypoint.

Streamlit executes this file on every rerun, then runs the page selected in
st.navigation. Each country app is a standalone page script:
    scb_salaries.py — Sweden (Statistics Sweden / SCB)
    france.py       — France (INSEE Melodi, in development)
Global page config (page_config, logo, shared CSS) lives here, ONCE — country
pages must not call st.set_page_config / st.logo themselves.
"""
import os
import streamlit as st

_ASSETS   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_ICON_PNG = os.path.join(_ASSETS, "logo.png")
_ICON_SVG = os.path.join(_ASSETS, "logo.svg")

st.set_page_config(page_title="Salary Explorer", page_icon=_ICON_PNG, layout="wide")
if os.path.exists(_ICON_SVG):
    st.logo(_ICON_SVG, size="large")

# Hide Streamlit's default top "decoration" gradient bar (applies to all pages).
st.markdown("<style>[data-testid='stDecoration']{display:none;}</style>",
            unsafe_allow_html=True)

pg = st.navigation([
    st.Page("landing.py",      title="Home",       default=True),
    st.Page("scb_salaries.py", title="🇸🇪 Sweden",  url_path="sweden"),
    st.Page("france.py",       title="🇫🇷 France",  url_path="france"),
])
pg.run()
