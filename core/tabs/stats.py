"""Basic statistics tab — headcount + a per-occupation summary table (mean,
median, quartiles, count) with CSV export. Mirrors the Swedish Basic-statistics
tab; uses the stats already fetched.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, i18n


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    st.subheader(i18n.t(cfg, "tab_stats", lang, "Basic statistics"))
    tot = stats[stats["dimension"] == "total"]
    if tot.empty:
        st.caption(i18n.no_data(cfg, lang))
        return

    if tot["count"].notna().any():
        total = int(tot["count"].dropna().sum())
        st.metric(i18n.t(cfg, "stat_total", lang, "Employees (selected)"),
                  f"{total:,}".replace(",", " "))

    col_code = i18n.t(cfg, "col_code", lang)
    col_occ = i18n.t(cfg, "col_occupation", lang)
    cols = [("mean", i18n.t(cfg, "col_mean", lang)),
            ("median", i18n.t(cfg, "col_median", lang)),
            ("p25", "P25"), ("p75", "P75")]
    raw = pd.DataFrame({col_code: tot["occ_code"].values, col_occ: tot["occ_name"].values})
    disp = raw.copy()
    for key, lbl in cols:
        if key in tot and tot[key].notna().any():
            raw[lbl] = tot[key].values
            disp[lbl] = [charts.fmt_value(v, cfg) for v in tot[key].values]
    if tot["count"].notna().any():
        c_lbl = i18n.t(cfg, "col_count", lang)
        raw[c_lbl] = tot["count"].values
        disp[c_lbl] = [("–" if pd.isna(v) else f"{int(v):,}".replace(",", " "))
                       for v in tot["count"].values]
    st.dataframe(disp, use_container_width=True, hide_index=True)
    st.download_button(i18n.t(cfg, "download_csv", lang, "Download CSV"),
                       raw.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{cfg.slug}_stats.csv", mime="text/csv",
                       key=f"{cfg.slug}_dl_stats")
