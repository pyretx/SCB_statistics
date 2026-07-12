"""By-region SIMULATION tab (shared).

For countries whose source has OVERALL earnings by region but not
occupation×region (Denmark, Norway): show the selected occupation's national
figures, and — on a toggle — overlay a region by applying that region's overall
pay difference (vs the nation) uniformly to the occupation. It is explicitly a
simulation; the disclaimer says so. Provider answers region_sim() (a
{display_name: factor} map); capability flag has_region_sim gates the tab.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import agg, charts, i18n, states

# Measures overlaid, in canonical order (only those the row actually has).
_MEASURES = [("mean", "m_average", "Average"), ("p25", None, "P25"),
             ("median", "m_median", "Median (P50)"), ("p75", None, "P75")]


def _label(cfg, lang, key, i18n_key, fallback):
    return i18n.t(cfg, i18n_key, lang, fallback) if i18n_key else fallback


def _metric_row(cfg, lang, row, factor, delta):
    """One horizontal band of st.metric — a measure per column. factor scales
    the money; delta (e.g. '+11.1%') is shown when simulating, else None."""
    present = [(k, ik, fb) for k, ik, fb in _MEASURES
               if k in row and pd.notna(row[k])]
    if not present:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return
    cols = st.columns(len(present))
    for col, (k, ik, fb) in zip(cols, present):
        val = float(row[k]) * factor
        col.metric(_label(cfg, lang, k, ik, fb), charts.fmt_value(val, cfg),
                   delta=delta, delta_color="off" if k in ("p25", "p75") else "normal")


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    slug = cfg.slug
    def k(n):
        return f"{slug}_{n}"

    st.subheader(i18n.t(cfg, "tab_region_sim", lang, "By region"))

    tot = stats[stats["dimension"] == "total"]
    occ = tuple(query.get("occ_codes", ()))
    if query.get("aggregate") and not tot.empty:
        tot = agg.collapse_stats(tot, agg.agg_name(cfg, lang, len(occ)))
    if tot.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return

    st.caption(i18n.t(cfg, "rs_intro", lang,
                      "Below are the national figures for the selected occupation. "
                      "Turn on the simulation to estimate them for a specific region."))

    # Region factors (one cheap, cached provider call for the shown year).
    yy = query.get("years", ())
    year = max(int(y) for y in yy) if yy else (
        cfg.capabilities.year_range[1] if cfg.capabilities.year_range else None)
    with states.loading():
        data = cfg.provider.region_sim(year=year, lang=lang) or {}
    regions = data.get("regions") or {}
    if not regions:
        st.info(i18n.t(cfg, "rs_unavailable", lang,
                       "Regional simulation isn't available for this country."))
        return

    # ── Toggle + region picker ────────────────────────────────────────────────
    sim_on = st.toggle(i18n.t(cfg, "rs_toggle", lang, "Simulate a specific region"),
                       key=k("regsim"))
    factor, delta, region_name = 1.0, None, None
    if sim_on:
        opts = sorted(regions, key=lambda r: -regions[r])   # highest-paying first

        def _fmt(r):
            return f"{r}  ({(regions[r] - 1) * 100:+.1f}%)"
        region_name = st.selectbox(i18n.t(cfg, "rs_region", lang, "Region"), opts,
                                   format_func=_fmt, key=k("regsim_pick"))
        factor = regions[region_name]
        delta = f"{(factor - 1) * 100:+.1f}%"

    # ── National (+ simulated) figures per occupation ─────────────────────────
    for _, row in tot.iterrows():
        st.markdown(f"**{row['occ_name']}**")
        st.caption(i18n.t(cfg, "rs_national", lang, "National"))
        _metric_row(cfg, lang, row, 1.0, None)
        if sim_on:
            st.markdown(f"<div style='height:6px'></div>", unsafe_allow_html=True)
            st.caption(f"{region_name} · {delta}")
            _metric_row(cfg, lang, row, factor, delta)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Basis + disclaimer ────────────────────────────────────────────────────
    if data.get("basis"):
        st.caption(i18n.t(cfg, "rs_basis", lang, "Regional difference based on {basis}.")
                   .format(basis=data["basis"]))
    st.warning(i18n.t(cfg, "rs_disclaimer", lang,
                      "Estimate only. This applies the region's overall pay "
                      "difference — measured across all occupations — to this one "
                      "occupation. The true regional gap for this specific "
                      "occupation may differ."))
