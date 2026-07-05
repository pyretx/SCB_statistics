"""Shared table builders — consume the normalized model."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from . import charts


def occupation_table(stats: pd.DataFrame, cfg):
    """A simple table of the selected occupations (total slice) with formatted
    salary columns. Reused by the overview tab and the leaderboard."""
    d = stats[stats["dimension"] == "total"].copy()
    if d.empty:
        st.caption("No occupations to show.")
        return
    out = pd.DataFrame({"Code": d["occ_code"], "Occupation": d["occ_name"]})
    if cfg.capabilities.has_mean and d["mean"].notna().any():
        out[f"Mean ({cfg.currency_suffix})"] = d["mean"].map(lambda v: charts.fmt_value(v, cfg))
    if cfg.capabilities.has_median and d["median"].notna().any():
        out[f"Median ({cfg.currency_suffix})"] = d["median"].map(lambda v: charts.fmt_value(v, cfg))
    if d["count"].notna().any():
        out["Count"] = d["count"].map(lambda v: "–" if pd.isna(v) else f"{int(v):,}".replace(",", " "))
    st.dataframe(out, use_container_width=True, hide_index=True)


def ranked_table(stats: pd.DataFrame, cfg, *, by: str = "mean", top: int = 20,
                 ascending: bool = False):
    """Top/bottom occupations by a salary column (leaderboard)."""
    d = stats[stats["dimension"] == "total"].dropna(subset=[by])
    d = d.sort_values(by, ascending=ascending).head(top)
    occupation_table(d, cfg)
