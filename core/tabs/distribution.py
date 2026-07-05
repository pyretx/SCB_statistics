"""Distribution tab — per-occupation quartile spread (P25 · median · P75).

For sources that publish quartiles but not P10/P90 (e.g. Norway/SSB), gated by
capabilities.has_quartiles. Reads the same stats frame as the overview.
"""
from __future__ import annotations

import streamlit as st

from .. import charts, i18n


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    st.subheader(i18n.t(cfg, "tab_distribution", lang, "Distribution"))
    fig = charts.quartile_spread(
        stats, cfg,
        title=f"{i18n.t(cfg, 'quartile_title', lang)} · {cfg.currency_suffix}/mo")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
        st.caption(i18n.t(cfg, "quartile_note", lang))
    else:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
