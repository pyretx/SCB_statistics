"""Distribution tab — the standard salary-distribution chart (Swedish-style):
a line across the percentile points the source publishes, plus the mean as a
diamond. Sweden shows P10–P90; Norway shows P25·median·P75 the same way.

Gated by capabilities.has_occupation_percentiles OR has_quartiles.
"""
from __future__ import annotations

import streamlit as st

from .. import charts, i18n


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    st.subheader(i18n.t(cfg, "tab_distribution", lang, "Distribution"))
    fig = charts.distribution_chart(
        stats, cfg,
        mean_label=i18n.t(cfg, "col_mean", lang, "Mean"),
        x_title=i18n.t(cfg, "x_percentile", lang, "Percentile"),
        title=f"{i18n.t(cfg, 'distribution_title', lang)} · {cfg.currency_suffix}/mo")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
        # only quartile sources need the "no P10/P90" note
        if cfg.capabilities.has_quartiles and not cfg.capabilities.has_occupation_percentiles:
            st.caption(i18n.t(cfg, "quartile_note", lang))
    else:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
