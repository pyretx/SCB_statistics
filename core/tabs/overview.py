"""Overview tab — a French-style KPI summary per occupation (mean · median · P25
· P75 · women · men · F/M gap · headcount), plus a comparison bar when several
occupations are selected. Every metric is capability-gated, so a country only
shows what its data has.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, i18n, states


def _num(v, suf):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    return f"{int(round(v)):,}".replace(",", " ") + (f" {suf}" if suf else "")


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    caps = cfg.capabilities
    tot = stats[stats["dimension"] == "total"]
    if tot.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return
    suf = cfg.currency_suffix
    occ = tuple(query.get("occ_codes", ()))

    # women/men means for the gap (only when the source has a sex split)
    wmean, mmean = {}, {}
    if caps.has_sex:
        with states.loading():
            w = cfg.provider.occupation_stats(sector=query.get("sector", ""), occ_codes=occ,
                                              sex="women", years=tuple(query.get("years", ())), lang=lang)
            m = cfg.provider.occupation_stats(sector=query.get("sector", ""), occ_codes=occ,
                                              sex="men", years=tuple(query.get("years", ())), lang=lang)
        wt, mt = w[w["dimension"] == "total"], m[m["dimension"] == "total"]
        wmean = dict(zip(wt["occ_code"], wt["mean"]))
        mmean = dict(zip(mt["occ_code"], mt["mean"]))

    for _, row in tot.iterrows():
        code, name = row["occ_code"], row["occ_name"]
        st.markdown(f"#### {name}  ({code})")

        r1 = []
        if caps.has_mean:
            r1.append((f"{i18n.t(cfg, 'col_mean', lang)} ({suf})", _num(row["mean"], "")))
        if caps.has_median:
            r1.append((f"{i18n.t(cfg, 'm_median', lang)} ({suf})", _num(row["median"], "")))
        if caps.has_quartiles or caps.has_occupation_percentiles:
            r1 += [(f"P25 ({suf})", _num(row["p25"], "")), (f"P75 ({suf})", _num(row["p75"], ""))]
        for c, (lbl, v) in zip(st.columns(len(r1)), r1):
            c.metric(lbl, v)

        r2 = []
        if caps.has_sex:
            wv, mv = wmean.get(code), mmean.get(code)
            r2.append((f"{i18n.t(cfg, 'women', lang)} ({suf})", _num(wv, "")))
            r2.append((f"{i18n.t(cfg, 'men', lang)} ({suf})", _num(mv, "")))
            gap = ((wv / mv - 1) * 100 if wv and mv and not pd.isna(wv) and not pd.isna(mv)
                   else None)
            r2.append((i18n.t(cfg, "m_gap", lang), f"{gap:+.1f} %" if gap is not None else "–"))
        if pd.notna(row["count"]):
            r2.append((i18n.t(cfg, "m_headcount", lang), _num(row["count"], "")))
        if r2:
            for c, (lbl, v) in zip(st.columns(len(r2)), r2):
                c.metric(lbl, v)
        st.write("")

    if len(tot) > 1:                            # comparison bar across occupations
        st.subheader(i18n.t(cfg, "compare_occ", lang, "Compare occupations"))
        val = "mean" if caps.has_mean else "median"
        heading = i18n.t(cfg, "avg_salary" if val == "mean" else "median_salary", lang)
        fig = charts.occupation_bar(stats, cfg, value_col=val,
                                    title=f"{heading} · {suf}/mo")
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
