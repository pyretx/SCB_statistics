"""Shared chart builders — consume the normalized model, styled via theme.py.

Every country reuses these; nothing here knows about any specific API. The look
matches the existing Sweden/France charts (theme.style_fig, theme colours).
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

import theme


def fmt_value(v, cfg) -> str:
    """Group digits with a non-breaking space + the country's currency suffix,
    e.g. 53500 -> '53 500 kr'. '–' for missing."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    return f"{int(round(v)):,}".replace(",", " ") + f" {cfg.currency_suffix}"


def occupation_bar(stats: pd.DataFrame, cfg, value_col: str = "mean", *,
                   title: str | None = None):
    """Horizontal bar of the selected occupations by ``value_col`` (mean/median).
    Expects OccupationStat rows for dimension == 'total'."""
    d = stats[stats["dimension"] == "total"].copy()
    d = d.dropna(subset=[value_col]).sort_values(value_col)
    if d.empty:
        return None
    fig = go.Figure(go.Bar(
        x=d[value_col], y=d["occ_name"], orientation="h",
        marker_color=theme.ACCENT,
        hovertemplate="%{y}<br>%{x:,.0f} " + cfg.currency_suffix + "<extra></extra>",
    ))
    fig.update_layout(height=max(220, 46 * len(d) + 90),
                      margin=dict(l=8, r=8, t=40 if title else 8, b=8),
                      title=title, xaxis_title=None, yaxis_title=None)
    return theme.style_fig(fig, horizontal=True)


def percentile_line(stats: pd.DataFrame, cfg, *, title: str | None = None):
    """Per-occupation percentile curve (P10..P90) — Sweden-style. One trace per
    occupation. Only meaningful when capabilities.has_occupation_percentiles."""
    order = [("P10", "p10"), ("P25", "p25"), ("MED", "median"),
             ("P75", "p75"), ("P90", "p90")]
    d = stats[stats["dimension"] == "total"]
    fig = go.Figure()
    for i, (_, row) in enumerate(d.iterrows()):
        ys = [row[k] for _, k in order]
        if all(pd.isna(y) for y in ys):
            continue
        col = theme.SERIES[i % len(theme.SERIES)]
        fig.add_trace(go.Scatter(
            x=[lbl for lbl, _ in order], y=ys, mode="lines+markers",
            name=str(row["occ_name"]), line=dict(color=col, width=2.5),
            marker=theme.series_marker(col)))
    if not fig.data:
        return None
    fig.update_layout(height=380, margin=dict(l=8, r=8, t=40 if title else 8, b=8),
                      title=title, xaxis_title="Percentile",
                      yaxis_title=f"Salary ({cfg.currency_suffix}/mo)")
    return theme.style_fig(fig)
