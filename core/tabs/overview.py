"""Occupation overview tab — bar chart + table of the selected occupations.
The first shared tab; more (distribution, where-do-I-stand, leaderboard,
by-age/region/education, trend) follow the same signature: render(cfg, stats, query).
"""
from __future__ import annotations

import streamlit as st

from .. import charts, i18n, tables


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    st.subheader(i18n.t(cfg, "occupation_overview", lang))
    use_mean = cfg.capabilities.has_mean
    val = "mean" if use_mean else "median"
    heading = i18n.t(cfg, "avg_salary" if use_mean else "median_salary", lang)
    fig = charts.occupation_bar(stats, cfg, value_col=val,
                                title=f"{heading} · {cfg.currency_suffix}/mo")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    tables.occupation_table(stats, cfg, lang=lang)
