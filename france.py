"""France — Salary Explorer (INSEE Melodi). Placeholder while the data layer is built.

IMPORTANT (session-state rule): the Swedish and French pages share one Streamlit
session. Every France widget/session key MUST be prefixed "fr_" so it can never
collide with the Swedish app's keys (e.g. "query", "occ_selection", "trend_view").

Planned v1 (validated against the live Melodi API on 2026-07-04):
  - DS_DERA_PRIVE_ANNUEL   : mean net FTE monthly salary for 361 detailed PCS
                             occupations × sex × age bands (+ public mirror)
  - DS_DERA_*_SERIES_LONGUES: wage distribution (C10…C99) for the 5 broad
                             socio-professional groups, series back to 1951
  - DS_BTS_SAL_EQTP_*      : regional means by sex × group / age
  - DS_IPC_PRINC           : monthly CPI for inflation-adjusted views
"""
import streamlit as st

st.title("🇫🇷 Explorateur de salaires — France")
st.caption("Données : INSEE (API Melodi) · Data: INSEE (Melodi API)")

st.info(
    "🚧 **En construction / Under construction**\n\n"
    "The French edition is being built on INSEE's open Melodi API. Planned for v1:\n"
    "- Mean net salaries for **361 detailed occupations** (PCS), by sex and age\n"
    "- Wage **distribution (deciles, P95/P99)** by socio-professional group — series since **1951**\n"
    "- **Inflation-adjusted** trends using the IPC\n"
    "- Regional comparisons"
)

if st.button("← Back / Retour", key="fr_back"):
    st.switch_page("landing.py")
