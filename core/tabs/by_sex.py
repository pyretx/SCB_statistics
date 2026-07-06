"""By-gender tab — women vs men mean/median per occupation, with a "Women as %
of men" toggle (like the Swedish page). Fetches the women/men slices via the
provider. Gated by capabilities.has_sex.
"""
from __future__ import annotations

import streamlit as st

from .. import charts, i18n, states


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    slug = cfg.slug
    st.subheader(i18n.t(cfg, "tab_sex", lang, "By gender"))
    occ = tuple(query.get("occ_codes", ()))
    sector = query.get("sector", "")
    years = tuple(query.get("years", ()))
    ratio = st.toggle(i18n.t(cfg, "show_ratio", lang, "Women as % of men"),
                      key=f"{slug}_sexratio")
    with states.loading():
        women = cfg.provider.occupation_stats(sector=sector, occ_codes=occ,
                                              sex="women", years=years, lang=lang)
        men = cfg.provider.occupation_stats(sector=sector, occ_codes=occ,
                                            sex="men", years=years, lang=lang)
    val = "mean" if cfg.capabilities.has_mean else "median"
    # Always the two bars; the toggle just annotates women-as-%-of-men at the end
    # of each row (Sweden's behaviour), rather than replacing them.
    heading = (i18n.t(cfg, "ratio_title", lang, "Women's salary as % of men's") if ratio
               else f"{i18n.t(cfg, 'avg_salary' if val == 'mean' else 'median_salary', lang)} · {cfg.currency_suffix}{cfg.per_label}")
    fig = charts.grouped_sex_bar(
        women, men, cfg, val,
        women_label=i18n.t(cfg, "women", lang), men_label=i18n.t(cfg, "men", lang),
        title=heading, show_ratio=ratio)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
