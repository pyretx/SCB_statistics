"""Salary-trend-over-time section (mirrors the Swedish page). Rendered inside the
Distribution tab: a Measure selector (which percentile/mean to track) + a
Nominal / Growth-vs-inflation / Real view toggle, a summary line, and an
exportable per-year table. CPI comes from provider.cpi_annual().
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, i18n, states


def _measure_keys(cfg) -> list[str]:
    """Measures that can be tracked over time, in canonical order."""
    caps = cfg.capabilities
    ks: list[str] = []
    if caps.has_occupation_percentiles:
        ks += ["p10", "p25", "median", "p75", "p90"]
    elif caps.has_quartiles:
        ks += ["p25", "median", "p75"] if caps.has_median else ["p25", "p75"]
    elif caps.has_median:
        ks += ["median"]
    if caps.has_mean:
        ks.append("mean")
    return ks


def _mlabel(cfg, lang, key: str) -> str:
    return {"p10": "P10", "p25": "P25",
            "median": i18n.t(cfg, "m_median", lang, "Median (P50)"),
            "p75": "P75", "p90": "P90",
            "mean": i18n.t(cfg, "m_average", lang, "Average")}.get(key, key)


def trend_section(cfg, query, lang, k):
    st.subheader(i18n.t(cfg, "trend_over_time", lang, "Salary trend over time"))
    occ = tuple(query.get("occ_codes", ()))
    years = tuple(query.get("years", ()))
    ms = _measure_keys(cfg)
    if not ms:
        return

    c1, c2 = st.columns([2, 3])
    with c1:
        di = ms.index("median") if "median" in ms else 0
        mkey = st.selectbox(i18n.t(cfg, "measure", lang, "Measure"), ms, index=di,
                            format_func=lambda kk: _mlabel(cfg, lang, kk), key=k("tmeasure"))
    cpi = cfg.provider.cpi_annual(years)
    with states.loading():
        tr = cfg.provider.trend(sector=query.get("sector", ""), occ_codes=occ,
                                sex=query.get("sex", "total"), years=years, lang=lang, measure=mkey)
    if tr is None or tr.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return
    tr = tr.copy()
    tr["year"] = tr["year"].astype(int)
    base = int(tr["year"].min())
    cpi_base = cpi.get(base)
    suf = cfg.currency_suffix
    v_nom = i18n.t(cfg, "trend_nominal", lang)
    v_grow = i18n.t(cfg, "trend_growth", lang)
    v_real = i18n.t(cfg, "trend_real", lang)
    views = [v_nom] + ([v_grow, v_real] if cpi_base else [])
    with c2:
        view = (st.radio(i18n.t(cfg, "trend_view", lang), views, horizontal=True,
                         key=k("trendview")) if len(views) > 1 else v_nom)

    if view == v_grow and cpi_base:
        rows = []
        for s, g in tr.groupby("series", sort=False):
            g = g.dropna(subset=["value_nominal"]).sort_values("year")
            if g.empty:
                continue
            b0 = g.iloc[0]["value_nominal"]
            for _, r in g.iterrows():
                rows.append({"year": int(r["year"]), "series": s,
                             "value": (r["value_nominal"] / b0 - 1) * 100})
        infl = [(y, (cpi[y] / cpi_base - 1) * 100)
                for y in sorted(tr["year"].unique()) if cpi.get(int(y))]
        fig = charts.trend_lines(pd.DataFrame(rows), cfg, unit="%",
                                 y_title=i18n.t(cfg, "trend_growth_axis", lang).format(base=base),
                                 inflation=infl, inflation_label=i18n.t(cfg, "trend_inflation", lang),
                                 title=f"{v_grow} · %")
    elif view == v_real and cpi_base:
        rows = [{"year": int(r["year"]), "series": r["series"],
                 "value": (r["value_nominal"] * cpi_base / cpi[int(r["year"])]
                           if cpi.get(int(r["year"])) and pd.notna(r["value_nominal"]) else None)}
                for _, r in tr.iterrows()]
        fig = charts.trend_lines(pd.DataFrame(rows), cfg, unit=suf,
                                 y_title=i18n.t(cfg, "trend_real_axis", lang).format(base=base),
                                 title=f"{v_real} · {suf}{cfg.per_label}")
    else:
        df = tr.rename(columns={"value_nominal": "value"})[["year", "series", "value"]]
        fig = charts.trend_lines(df, cfg, unit=suf, y_title=f"{suf}{cfg.per_label}",
                                 title=f"{_mlabel(cfg, lang, mkey)} · {suf}{cfg.per_label}")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    if cpi_base:                                    # salary-vs-inflation summary per occupation
        for s, g in tr.groupby("series", sort=False):
            g = g.dropna(subset=["value_nominal"]).sort_values("year")
            if len(g) < 2:
                continue
            ly = int(g.iloc[-1]["year"])
            if not cpi.get(ly):
                continue
            sal = (g.iloc[-1]["value_nominal"] / g.iloc[0]["value_nominal"] - 1) * 100
            inflp = (cpi[ly] / cpi_base - 1) * 100
            real = ((1 + sal / 100) / (1 + inflp / 100) - 1) * 100
            st.caption(f"**{s}** — " + i18n.t(cfg, "trend_summary", lang).format(
                base=base, last=ly, sal=sal, infl=inflp, real=real))

    with st.expander(i18n.t(cfg, "raw_data", lang, "Raw data")):
        col_occ = i18n.t(cfg, "col_occupation", lang)
        col_yr = i18n.t(cfg, "x_year", lang, "Year")
        c_nom = i18n.t(cfg, "trend_col_nominal", lang, "Nominal")
        c_grow = i18n.t(cfg, "trend_col_growth", lang, "Growth %")
        c_real = i18n.t(cfg, "trend_col_real", lang, "Real ({base})").format(base=base)
        rows = []
        for s, g in tr.groupby("series", sort=False):
            g = g.dropna(subset=["value_nominal"]).sort_values("year")
            if g.empty:
                continue
            b0 = g.iloc[0]["value_nominal"]
            for _, r in g.iterrows():
                y, v = int(r["year"]), r["value_nominal"]
                row = {col_occ: s, col_yr: y, c_nom: round(v)}
                if cpi_base:
                    row[c_grow] = round((v / b0 - 1) * 100, 1)
                    if cpi.get(y):
                        row[c_real] = round(v * cpi_base / cpi[y])
                rows.append(row)
        ttbl = pd.DataFrame(rows)
        st.dataframe(ttbl, use_container_width=True, hide_index=True)
        st.download_button(i18n.t(cfg, "download_csv", lang, "Download CSV"),
                           ttbl.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{cfg.slug}_trend_{mkey}.csv", mime="text/csv",
                           key=k("dl_trend"))


def render(cfg, stats, query):
    """Standalone-tab wrapper (kept for flexibility); the Distribution tab embeds
    trend_section directly."""
    lang = query.get("lang", "EN")
    trend_section(cfg, query, lang, lambda n: f"{cfg.slug}_{n}")
