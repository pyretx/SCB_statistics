"""Where do I stand? tab — a salary calculator: enter a monthly salary and see
its estimated percentile position for an occupation (piecewise-linear between the
published percentile points). Mirrors the Swedish calculator; works on whatever
percentiles a source has (Norway: P25·median·P75).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, i18n

_PCTS = [(10, "p10"), (25, "p25"), (50, "median"), (75, "p75"), (90, "p90")]


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    slug = cfg.slug
    def k(n):
        return f"{slug}_{n}"
    st.subheader(i18n.t(cfg, "tab_where", lang, "Where do I stand?"))
    tot = stats[stats["dimension"] == "total"]
    if tot.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return

    codes = list(tot["occ_code"])
    name_by = dict(zip(tot["occ_code"], tot["occ_name"]))
    if len(codes) > 1:
        code = st.selectbox(i18n.t(cfg, "calc_occ", lang, "Occupation"), codes,
                            format_func=lambda c: name_by[c], key=k("wocc"))
    else:
        code = codes[0]
        st.markdown(f"**{name_by[code]}**")
    row = tot[tot["occ_code"] == code].iloc[0]

    points = sorted((lvl, float(row[col])) for lvl, col in _PCTS
                    if col in row and pd.notna(row[col]))
    if len(points) < 2:
        st.info(i18n.t(cfg, "calc_no_pct", lang, "Not enough percentile points."))
        return
    levs = [lvl for lvl, _ in points]
    vals = [v for _, v in points]

    salary = st.number_input(i18n.t(cfg, "calc_input", lang, "Your monthly salary"),
                             min_value=0, value=int(round(vals[len(vals) // 2])),
                             step=500, key=k("wsal"))

    if salary <= vals[0]:
        est, pos = levs[0], "below"
    elif salary >= vals[-1]:
        est, pos = levs[-1], "above"
    else:
        est, pos = levs[-1], "in"
        for i in range(len(points) - 1):
            if vals[i] <= salary <= vals[i + 1]:
                frac = (salary - vals[i]) / (vals[i + 1] - vals[i]) if vals[i + 1] > vals[i] else 0.0
                est = levs[i] + frac * (levs[i + 1] - levs[i])
                break

    m1, m2 = st.columns([1, 2])
    m1.metric(i18n.t(cfg, "calc_rank", lang, "Estimated position"), f"P{est:.0f}")
    with m2:
        if pos == "below":
            st.warning(i18n.t(cfg, "calc_below", lang, "Below the lowest published percentile."))
        elif pos == "above":
            st.success(i18n.t(cfg, "calc_above", lang, "Above the highest published percentile."))
        else:
            st.info(i18n.t(cfg, "calc_more_than", lang,
                           "Earns more than ~{p}% (top {top}%).").format(
                               p=f"{est:.0f}", top=f"{100 - est:.0f}"))

    fig = charts.position_curve(levs, vals, est, salary, cfg,
                                you_label=i18n.t(cfg, "calc_you", lang, "You"),
                                x_title=i18n.t(cfg, "x_percentile", lang, "Percentile"))
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
