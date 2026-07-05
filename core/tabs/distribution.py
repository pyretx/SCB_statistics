"""Distribution tab — the Swedish "Percentile distribution" tab, generalised.

Chart-year dropdown · Measures-shown multiselect (add/remove percentiles + the
average; they reappear in canonical order) · the standard distribution chart ·
a raw-data table with CSV export · and the embedded Salary-trend-over-time
section. Sweden shows P10–P90; Norway shows P25·median·P75 the same way.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, i18n, states
from . import trend as _trend

_PCT_KEYS = ["p10", "p25", "median", "p75", "p90"]


def _mlabel(cfg, lang, key: str) -> str:
    return {"p10": "P10", "p25": "P25",
            "median": i18n.t(cfg, "m_median", lang, "Median (P50)"),
            "p75": "P75", "p90": "P90",
            "mean": i18n.t(cfg, "m_average", lang, "Average")}.get(key, key)


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    slug = cfg.slug
    def k(n):
        return f"{slug}_{n}"
    st.subheader(i18n.t(cfg, "distribution_subheader", lang, "Salary distribution by percentile"))
    caps = cfg.capabilities
    occ = tuple(query.get("occ_codes", ()))
    sector, sex = query.get("sector", ""), query.get("sex", "total")

    # ── Controls: chart year + measures shown ────────────────────────────────
    c1, c2 = st.columns([1, 2.4])
    with c1:
        if caps.year_range:
            y0, y1 = caps.year_range
            chart_year = st.selectbox(i18n.t(cfg, "chart_year", lang, "Chart year"),
                                      list(range(y1, y0 - 1, -1)), key=k("dyear"))
        else:
            yy = query.get("years", ())
            chart_year = int(yy[-1]) if yy else None

    with states.loading():
        d = cfg.provider.occupation_stats(sector=sector, occ_codes=occ, sex=sex,
                                          year=chart_year, lang=lang)
    tot = d[d["dimension"] == "total"]
    if tot.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return

    avail = [key for key in _PCT_KEYS if key in tot and tot[key].notna().any()]
    if caps.has_mean and tot["mean"].notna().any():
        avail.append("mean")
    labels = {key: _mlabel(cfg, lang, key) for key in avail}
    with c2:
        chosen = st.multiselect(i18n.t(cfg, "measures_shown", lang, "Measures shown"),
                                [labels[key] for key in avail],
                                default=[labels[key] for key in avail], key=k("dmeasures"))
    # canonical order, map labels back to keys
    keys = [key for key in avail if labels[key] in chosen] or avail

    # ── Chart ────────────────────────────────────────────────────────────────
    fig = charts.distribution_chart(
        tot, cfg, keys=keys, labels_map=labels, mean_label=labels.get("mean", "Average"),
        x_title=i18n.t(cfg, "x_percentile", lang, "Percentile"),
        title=f"{i18n.t(cfg, 'distribution_title', lang)} · {cfg.currency_suffix}/mo")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    if caps.has_quartiles and not caps.has_occupation_percentiles:
        st.caption(i18n.t(cfg, "quartile_note", lang))

    # ── Raw-data table + CSV export ──────────────────────────────────────────
    with st.expander(i18n.t(cfg, "raw_data", lang, "Raw data")):
        col_code = i18n.t(cfg, "col_code", lang)
        col_occ = i18n.t(cfg, "col_occupation", lang)
        raw = pd.DataFrame({col_code: tot["occ_code"].values, col_occ: tot["occ_name"].values})
        disp = raw.copy()
        for key in keys:
            raw[labels[key]] = tot[key].values
            disp[labels[key]] = [charts.fmt_value(v, cfg) for v in tot[key].values]
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.download_button(i18n.t(cfg, "download_csv", lang, "Download CSV"),
                           raw.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{slug}_percentiles_{chart_year}.csv", mime="text/csv",
                           key=k("dl_dist"))

    # ── Salary trend over time (embedded, like Sweden) ───────────────────────
    if caps.has_trend:
        st.divider()
        _trend.trend_section(cfg, query, lang, k)
