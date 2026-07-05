"""Overview tab — a French-style KPI summary per occupation (mean + the
percentiles in ascending order with the median in the middle · women · men ·
F/M gap · headcount), a comparison bar for several occupations, and (merged in
from the old Basic-statistics tab) a per-occupation summary table with CSV
export. Every metric is capability-gated.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, i18n, states

_PCT_KEYS = ["p10", "p25", "median", "p75", "p90"]     # ascending → median centred


def _num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    return f"{int(round(v)):,}".replace(",", " ")


def _pct_label(cfg, lang, key):
    return {"p10": "P10", "p25": "P25", "median": i18n.t(cfg, "m_median", lang, "Median (P50)"),
            "p75": "P75", "p90": "P90"}[key]


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    caps = cfg.capabilities
    tot = stats[stats["dimension"] == "total"]
    if tot.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return
    suf = cfg.currency_suffix
    occ = tuple(query.get("occ_codes", ()))

    wmean, mmean = {}, {}                          # women/men means for the F/M gap
    if caps.has_sex:
        with states.loading():
            w = cfg.provider.occupation_stats(sector=query.get("sector", ""), occ_codes=occ,
                                              sex="women", years=tuple(query.get("years", ())), lang=lang)
            m = cfg.provider.occupation_stats(sector=query.get("sector", ""), occ_codes=occ,
                                              sex="men", years=tuple(query.get("years", ())), lang=lang)
        wt, mt = w[w["dimension"] == "total"], m[m["dimension"] == "total"]
        wmean = dict(zip(wt["occ_code"], wt["mean"]))
        mmean = dict(zip(mt["occ_code"], mt["mean"]))

    if tot["count"].notna().any():
        st.metric(i18n.t(cfg, "stat_total", lang, "Employees (selected)"),
                  _num(tot["count"].dropna().sum()))

    for _, row in tot.iterrows():
        code, name = row["occ_code"], row["occ_name"]
        st.markdown(f"#### {name}  ({code})")

        r1 = []
        if caps.has_mean and pd.notna(row["mean"]):
            r1.append((f"{i18n.t(cfg, 'col_mean', lang)} ({suf})", _num(row["mean"])))
        for key in _PCT_KEYS:                      # ascending → P25 · Median · P75 (or P10..P90)
            if key in row and pd.notna(row[key]):
                r1.append((f"{_pct_label(cfg, lang, key)} ({suf})", _num(row[key])))
        for c, (lbl, v) in zip(st.columns(len(r1) or 1), r1):
            c.metric(lbl, v)

        r2 = []
        if caps.has_sex:
            wv, mv = wmean.get(code), mmean.get(code)
            r2.append((f"{i18n.t(cfg, 'women', lang)} ({suf})", _num(wv)))
            r2.append((f"{i18n.t(cfg, 'men', lang)} ({suf})", _num(mv)))
            gap = ((wv / mv - 1) * 100 if wv and mv and not pd.isna(wv) and not pd.isna(mv) else None)
            r2.append((i18n.t(cfg, "m_gap", lang), f"{gap:+.1f} %" if gap is not None else "–"))
        if pd.notna(row["count"]):
            r2.append((i18n.t(cfg, "m_headcount", lang), _num(row["count"])))
        if r2:
            for c, (lbl, v) in zip(st.columns(len(r2)), r2):
                c.metric(lbl, v)
        st.write("")

    if len(tot) > 1:
        st.subheader(i18n.t(cfg, "compare_occ", lang, "Compare occupations"))
        val = "mean" if caps.has_mean else "median"
        heading = i18n.t(cfg, "avg_salary" if val == "mean" else "median_salary", lang)
        fig = charts.occupation_bar(stats, cfg, value_col=val, title=f"{heading} · {suf}/mo")
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

    # ── Summary table + CSV export (merged from Basic statistics) ─────────────
    with st.expander(i18n.t(cfg, "raw_data", lang, "Raw data")):
        col_code = i18n.t(cfg, "col_code", lang)
        col_occ = i18n.t(cfg, "col_occupation", lang)
        cols = [("mean", i18n.t(cfg, "col_mean", lang)),
                ("p25", "P25"), ("median", i18n.t(cfg, "col_median", lang)), ("p75", "P75")]
        raw = pd.DataFrame({col_code: tot["occ_code"].values, col_occ: tot["occ_name"].values})
        disp = raw.copy()
        for key, lbl in cols:
            if key in tot and tot[key].notna().any():
                raw[lbl] = tot[key].values
                disp[lbl] = [charts.fmt_value(v, cfg) for v in tot[key].values]
        if tot["count"].notna().any():
            c_lbl = i18n.t(cfg, "col_count", lang)
            raw[c_lbl] = tot["count"].values
            disp[c_lbl] = [_num(v) for v in tot["count"].values]
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.download_button(i18n.t(cfg, "download_csv", lang, "Download CSV"),
                           raw.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{cfg.slug}_overview.csv", mime="text/csv",
                           key=f"{cfg.slug}_dl_overview")
