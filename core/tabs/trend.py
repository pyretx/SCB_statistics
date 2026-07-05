"""Trend tab — mean salary over the selected years, one line per occupation.

Uses the provider's trend() method (normalized trend frame). Gated by
capabilities.has_trend.
"""
from __future__ import annotations

import streamlit as st

from .. import charts, i18n, states


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    st.subheader(i18n.t(cfg, "tab_trend", lang, "Trend"))
    with states.loading():
        tr = cfg.provider.trend(
            sector=query.get("sector", ""), occ_codes=tuple(query.get("occ_codes", ())),
            sex=query.get("sex", "total"), years=tuple(query.get("years", ())), lang=lang)
    fig = charts.trend_line(
        tr, cfg, title=f"{i18n.t(cfg, 'avg_salary', lang)} · {cfg.currency_suffix}/mo")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
