"""Occupation overview tab — bar chart + table of the selected occupations.
The first shared tab; more (distribution, where-do-I-stand, leaderboard,
by-age/region/education, trend) follow the same signature: render(cfg, stats, query).
"""
from __future__ import annotations

import streamlit as st

from .. import charts, tables


def render(cfg, stats, query):
    st.subheader("Occupation overview")
    val = "mean" if cfg.capabilities.has_mean else "median"
    fig = charts.occupation_bar(stats, cfg, value_col=val,
                                title=f"Average salary · {cfg.currency_suffix}/mo")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    tables.occupation_table(stats, cfg)
