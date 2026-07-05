"""Shared table builders — consume the normalized model."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from . import charts, i18n


def occupation_table(stats: pd.DataFrame, cfg, lang: str = "EN"):
    """A simple table of the selected occupations (total slice) with formatted
    salary columns. Reused by the overview tab and the leaderboard."""
    d = stats[stats["dimension"] == "total"].copy()
    if d.empty:
        st.caption("—")
        return
    suf = cfg.currency_suffix
    out = pd.DataFrame({i18n.t(cfg, "col_code", lang): d["occ_code"],
                        i18n.t(cfg, "col_occupation", lang): d["occ_name"]})
    if cfg.capabilities.has_mean and d["mean"].notna().any():
        out[f"{i18n.t(cfg, 'col_mean', lang)} ({suf})"] = d["mean"].map(lambda v: charts.fmt_value(v, cfg))
    if cfg.capabilities.has_median and d["median"].notna().any():
        out[f"{i18n.t(cfg, 'col_median', lang)} ({suf})"] = d["median"].map(lambda v: charts.fmt_value(v, cfg))
    if d["count"].notna().any():
        out[i18n.t(cfg, "col_count", lang)] = d["count"].map(
            lambda v: "–" if pd.isna(v) else f"{int(v):,}".replace(",", " "))
    st.dataframe(out, use_container_width=True, hide_index=True)


def ranked_table(stats: pd.DataFrame, cfg, *, by: str = "mean", top: int = 20,
                 ascending: bool = False, lang: str = "EN"):
    """Top/bottom occupations by a salary column (leaderboard)."""
    d = stats[stats["dimension"] == "total"].dropna(subset=[by])
    d = d.sort_values(by, ascending=ascending).head(top)
    occupation_table(d, cfg, lang=lang)
