"""Aggregate-selection helpers — collapse several picked occupations into ONE
headcount-weighted series (the legacy Swedish page's collapse_df, standardised).

The page offers the toggle whenever more than one occupation is selected; tabs
read query["aggregate"] and pass their fetched frames through these helpers.
Weighted means of medians/percentiles are an approximation (same as the legacy
page) — the toggle label says "weighted" so nobody mistakes it for a published
figure.
"""
from __future__ import annotations

import pandas as pd

from . import model

AGG_CODE = "__agg__"
_VALS = ["mean", "median", "p10", "p25", "p75", "p90"]


def _wmean(vals: pd.Series, weights: pd.Series):
    vals = pd.to_numeric(vals, errors="coerce")
    w = pd.to_numeric(weights, errors="coerce").fillna(0)
    w = w.where(vals.notna(), 0)
    tot = w.sum()
    if tot > 0:
        return float((vals.fillna(0) * w).sum() / tot)
    v = vals.dropna()
    return float(v.mean()) if not v.empty else None


def collapse_stats(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """One synthetic row per (dimension, dim_value): headcount-weighted mean of
    every value column, counts summed. Falls back to a simple mean when the
    source has no counts."""
    if df is None or df.empty:
        return df
    rows = []
    for (dim, dv), g in df.groupby(["dimension", "dim_value"], sort=False):
        rec = g.iloc[0].to_dict()
        rec.update({"occ_code": AGG_CODE, "occ_name": name, "occ_group": ""})
        for c in _VALS:
            if c in g:
                rec[c] = _wmean(g[c], g["count"] if "count" in g else pd.Series(dtype=float))
        cnt = pd.to_numeric(g.get("count"), errors="coerce")
        rec["count"] = float(cnt.sum()) if cnt is not None and cnt.notna().any() else None
        rows.append(rec)
    return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)


def collapse_trend(tr: pd.DataFrame, weights: dict, name: str) -> pd.DataFrame:
    """Collapse per-occupation trend series into one weighted series per year.
    ``weights`` maps series name → headcount (from the current stats frame) —
    constant across years, an approximation the toggle label owns."""
    if tr is None or tr.empty:
        return tr
    rows = []
    for (yr, sex), g in tr.groupby(["year", "sex"], sort=True):
        w = g["series"].map(lambda s: weights.get(s) or 0)
        val = _wmean(g["value_nominal"], w)
        rows.append({"country": g.iloc[0]["country"], "year": int(yr), "series": name,
                     "sex": sex, "value_nominal": val, "value_real": None})
    return pd.DataFrame(rows, columns=model.TREND_COLS)


def agg_name(cfg, lang: str, n: int) -> str:
    from . import i18n
    return i18n.t(cfg, "agg_name", lang, "Selection · {n} occupations").format(n=n)
