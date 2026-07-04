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
# NOTE: no st.logo() — each page carries its own brand mark in its header, so a
# global top-left logo would duplicate it (the "two globes" / page-in-page look).

# Global chrome tweaks (all pages):
#  • hide Streamlit's default top "decoration" gradient bar
#  • pull the content up under the (transparent) top toolbar — the default
#    ~6rem top padding left a big empty band above the header/logo, so the
#    landing needed scrolling to see everything. Trim it right down.
st.markdown("""
<style>
  [data-testid='stDecoration']{display:none;}
  [data-testid='stMainBlockContainer']{padding-top:2rem;}
  [data-testid='stSidebarUserContent']{padding-top:1.2rem;}
</style>
""", unsafe_allow_html=True)

# position="hidden" suppresses Streamlit's automatic Home/Sweden/France link
# list in the sidebar (the landing page has no sidebar content of its own, so
# it should show no sidebar at all, matching the mockup). Country pages still
# render their own filters into st.sidebar as before; each adds its own
# "← Home" link (st.page_link) at the top so users aren't stranded without
# the auto nav-list.
pg = st.navigation([
    st.Page("landing.py",      title="Home",   default=True),
    st.Page("scb_salaries.py", title="Sweden", url_path="sweden"),
    st.Page("france.py",       title="France", url_path="france"),
], position="hidden")
pg.run()
