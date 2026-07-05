"""By-sex tab — women vs men mean/median per occupation.

Fetches the women and men slices via the provider (reusing occupation_stats),
so no new provider method is needed. Gated by capabilities.has_sex.
"""
from __future__ import annotations

import streamlit as st

from .. import charts, i18n, states


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    st.subheader(i18n.t(cfg, "tab_sex", lang, "By sex"))
    occ = tuple(query.get("occ_codes", ()))
    sector = query.get("sector", "")
    years = tuple(query.get("years", ()))
    with states.loading():
        women = cfg.provider.occupation_stats(sector=sector, occ_codes=occ,
                                              sex="women", years=years, lang=lang)
        men = cfg.provider.occupation_stats(sector=sector, occ_codes=occ,
                                            sex="men", years=years, lang=lang)
    val = "mean" if cfg.capabilities.has_mean else "median"
    heading = i18n.t(cfg, "avg_salary" if val == "mean" else "median_salary", lang)
    fig = charts.grouped_sex_bar(
        women, men, cfg, val,
        women_label=i18n.t(cfg, "women", lang), men_label=i18n.t(cfg, "men", lang),
        title=f"{heading} · {cfg.currency_suffix}/mo")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
