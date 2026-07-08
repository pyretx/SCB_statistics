"""Generic dimension-breakdown tab — By age / By education / By region.

ONE shared implementation, registered three times (ids "age" / "education" /
"region"). It asks the provider for occupation_stats(dimension=<dim>) for a
chart year and draws the shared category_bar (one trace per occupation, one bar
row per category). A country enables a dimension simply by listing the tab id
in cfg.tabs and answering the dimension in its provider — capability-driven,
like everything else.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import agg, charts, i18n, states

_TITLE_KEY = {"age": "tab_age", "education": "tab_education", "region": "tab_region"}
_FALLBACK = {"age": "By age", "education": "By education", "region": "By region"}


def _render(cfg, stats, query, dim: str):
    lang = query.get("lang", "EN")
    slug = cfg.slug
    st.subheader(i18n.t(cfg, _TITLE_KEY[dim], lang, _FALLBACK[dim]))
    occ = tuple(query.get("occ_codes", ()))
    years = [int(y) for y in query.get("years", ())] or [0]
    aggregate = bool(query.get("aggregate"))

    # Chart year — only the years in the active selection (like Distribution).
    c1, c2 = st.columns([1, 2.4], vertical_alignment="bottom")
    with c1:
        yr = st.selectbox(i18n.t(cfg, "chart_year", lang, "Chart year"),
                          sorted(set(years), reverse=True), key=f"{slug}_{dim}_year")
    # Standard sex-split (the legacy Swedish by-age view): when the whole
    # selection is "total" and the country has sex data, offer women/men traces.
    split = False
    if cfg.capabilities.has_sex and query.get("sex", "total") == "total":
        with c2:
            split = st.toggle(i18n.t(cfg, "split_sex", lang, "Split by sex"),
                              key=f"{slug}_{dim}_split")

    def fetch(sx):
        return cfg.provider.occupation_stats(
            sector=query.get("sector", ""), occ_codes=occ,
            sex=sx, dimension=dim, year=yr, lang=lang)

    val = "mean" if cfg.capabilities.has_mean else "median"
    name = agg.agg_name(cfg, lang, len(occ))

    def prep(df, suffix=""):
        d0 = df[df["dimension"] == dim] if df is not None and not df.empty else pd.DataFrame()
        if d0.empty:
            return d0
        if aggregate:
            d0 = agg.collapse_stats(d0, name)
        if suffix:
            d0 = d0.assign(occ_name=d0["occ_name"] + " — " + suffix)
        return d0

    with states.loading():
        if split:
            d = pd.concat([prep(fetch("women"), i18n.t(cfg, "women", lang)),
                           prep(fetch("men"), i18n.t(cfg, "men", lang))],
                          ignore_index=True)
        else:
            d = prep(fetch(query.get("sex", "total")))
    if d.empty or val not in d or not d[val].notna().any():
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return

    heading = i18n.t(cfg, "avg_salary" if val == "mean" else "median_salary", lang)
    fig = charts.category_bar(d, cfg, val,
                              title=f"{heading} · {cfg.currency_suffix}{cfg.per_label}")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    with st.expander(i18n.t(cfg, "raw_data", lang, "Raw data")):
        col_occ = i18n.t(cfg, "col_occupation", lang)
        col_cat = i18n.t(cfg, _TITLE_KEY[dim], lang, _FALLBACK[dim])
        raw = pd.DataFrame({col_occ: d["occ_name"].values, col_cat: d["dim_value"].values,
                            i18n.t(cfg, "col_mean" if val == "mean" else "col_median", lang):
                                d[val].values})
        if "count" in d and d["count"].notna().any():
            raw[i18n.t(cfg, "col_count", lang)] = d["count"].values
        disp = raw.copy()
        vcol = raw.columns[2]
        disp[vcol] = [charts.fmt_value(v, cfg) for v in raw[vcol].values]
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.download_button(i18n.t(cfg, "download_csv", lang, "Download CSV"),
                           raw.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{slug}_{dim}_{yr}.csv", mime="text/csv",
                           key=f"{slug}_dl_{dim}")


def render_age(cfg, stats, query):
    _render(cfg, stats, query, "age")


def render_education(cfg, stats, query):
    _render(cfg, stats, query, "education")


def render_region(cfg, stats, query):
    _render(cfg, stats, query, "region")
