"""Shared forward-projection ("aging") controls — one compounded %-increase
slider per year between a reference data year and today.

Official statistics lag by a year or more; this lets the user lift a published
curve to the current year under an assumed yearly salary increase. Used by the
import-overlay tab and the Salary-distribution tab (identical widget block and
i18n keys, so the two stay in lockstep). Sliders are 0–15%, default 3%, and the
factors COMPOUND: base×(1+p₁)×(1+p₂)… across every projected year.
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from .. import i18n


def years_to_project(ref_year) -> list[int]:
    """Calendar years between the reference data year (exclusive) and today
    (inclusive). Empty when the data is already current."""
    if not ref_year:
        return []
    return list(range(int(ref_year) + 1, date.today().year + 1))


def toggle(cfg, lang, key, container=None) -> bool:
    """The standard 'Projection (aged to <current year>)' show/hide toggle."""
    host = container if container is not None else st
    return host.toggle(
        i18n.t(cfg, "io_show_proj", lang, "Projection (aged to {year})")
        .format(year=date.today().year),
        value=False, key=key)


def slider_block(cfg, lang, key_fn, ref_year, *, expanded=False) -> float:
    """Expander with the per-year sliders. Returns the cumulative uplift factor
    (1.0 when there is nothing to project). ``key_fn(name)`` must namespace
    widget keys for the calling tab."""
    yrs = years_to_project(ref_year)
    if not yrs:
        return 1.0
    this_year = yrs[-1]
    factor = 1.0
    with st.expander(i18n.t(cfg, "io_project_header", lang,
                            "Project the reference forward"), expanded=expanded):
        st.caption(i18n.t(cfg, "io_project_caption", lang,
                          "Assumed % salary increase per year from {a} to {b}, "
                          "compounded year-on-year (e.g. +3% then +4% → ×1.03×1.04). "
                          "Applied to every percentile and the average.")
                   .format(a=ref_year, b=this_year))
        sc = st.columns(len(yrs))
        for c, y in zip(sc, yrs):
            p = c.slider(f"{y} (%)", min_value=0.0, max_value=15.0, value=3.0,
                         step=0.5, key=key_fn(f"age_{y}"))
            factor *= 1 + p / 100
        st.caption(i18n.t(cfg, "io_uplift", lang,
                          "Cumulative uplift {a}→{b}: {pct:+.1f}% (×{f:.3f})")
                   .format(a=ref_year, b=this_year, pct=(factor - 1) * 100, f=factor))
    return factor
