"""Trend tab — salary over the selected years, mirroring the Swedish page's
nominal / growth-vs-inflation / real (constant-prices) views.

Nominal: raw mean salary per occupation. Growth: each occupation's % change from
the base year, with the CPI (inflation) as a dashed line. Real: salary deflated
to base-year prices. Growth/Real need the provider's cpi_annual(); without it,
only Nominal is shown. Gated by capabilities.has_trend.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, i18n, states


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    st.subheader(i18n.t(cfg, "tab_trend", lang, "Trend"))
    occ = tuple(query.get("occ_codes", ()))
    years = tuple(query.get("years", ()))
    with states.loading():
        tr = cfg.provider.trend(sector=query.get("sector", ""), occ_codes=occ,
                                sex=query.get("sex", "total"), years=years, lang=lang)
    if tr is None or tr.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return
    tr = tr.copy()
    tr["year"] = tr["year"].astype(int)

    v_nom = i18n.t(cfg, "trend_nominal", lang)
    v_grow = i18n.t(cfg, "trend_growth", lang)
    v_real = i18n.t(cfg, "trend_real", lang)
    cpi = cfg.provider.cpi_annual(years)
    base = int(tr["year"].min())
    cpi_base = cpi.get(base)
    # only offer growth/real when we actually have CPI
    views = [v_nom] + ([v_grow, v_real] if cpi_base else [])
    view = st.radio(i18n.t(cfg, "trend_view", lang), views, horizontal=True,
                    key=f"{cfg.slug}_trendview") if len(views) > 1 else v_nom
    suf = cfg.currency_suffix

    if view == v_grow and cpi_base:
        rows = []
        for series, g in tr.groupby("series", sort=False):
            g = g.dropna(subset=["value_nominal"]).sort_values("year")
            if g.empty:
                continue
            b0 = g.iloc[0]["value_nominal"]
            for _, r in g.iterrows():
                rows.append({"year": int(r["year"]), "series": series,
                             "value": (r["value_nominal"] / b0 - 1) * 100})
        infl = [(y, (cpi[y] / cpi_base - 1) * 100)
                for y in sorted(tr["year"].unique()) if cpi.get(int(y))]
        fig = charts.trend_lines(
            pd.DataFrame(rows), cfg, unit="%",
            y_title=i18n.t(cfg, "trend_growth_axis", lang).format(base=base),
            inflation=infl, inflation_label=i18n.t(cfg, "trend_inflation", lang),
            title=f"{v_grow} · %")
    elif view == v_real and cpi_base:
        rows = []
        for _, r in tr.iterrows():
            y, v = int(r["year"]), r["value_nominal"]
            rows.append({"year": y, "series": r["series"],
                         "value": v * cpi_base / cpi[y] if (cpi.get(y) and pd.notna(v)) else None})
        fig = charts.trend_lines(
            pd.DataFrame(rows), cfg, unit=suf,
            y_title=i18n.t(cfg, "trend_real_axis", lang).format(base=base),
            title=f"{v_real} · {suf}/mo")
    else:
        df = tr.rename(columns={"value_nominal": "value"})[["year", "series", "value"]]
        fig = charts.trend_lines(df, cfg, unit=suf, y_title=f"{suf}/mo",
                                 title=f"{i18n.t(cfg, 'avg_salary', lang)} · {suf}/mo")

    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption(i18n.t(cfg, "no_data_combo", lang))

    # salary-vs-inflation summary per occupation (base → last year)
    if cpi_base:
        for series, g in tr.groupby("series", sort=False):
            g = g.dropna(subset=["value_nominal"]).sort_values("year")
            last_y = int(g.iloc[-1]["year"]) if len(g) else base
            if len(g) < 2 or not cpi.get(last_y):
                continue
            sal = (g.iloc[-1]["value_nominal"] / g.iloc[0]["value_nominal"] - 1) * 100
            inflp = (cpi[last_y] / cpi_base - 1) * 100
            real = ((1 + sal / 100) / (1 + inflp / 100) - 1) * 100
            st.caption(f"**{series}** — " + i18n.t(cfg, "trend_summary", lang).format(
                base=base, last=last_y, sal=sal, infl=inflp, real=real))
