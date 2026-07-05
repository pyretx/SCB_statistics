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


def quartile_spread(stats: pd.DataFrame, cfg, *, title: str | None = None):
    """Per-occupation P25 → P75 range bar with a median marker (a box-ish spread).
    Uses the quartiles a source publishes when it has no P10/P90 (Norway/SSB)."""
    d = stats[stats["dimension"] == "total"].copy()
    d = d.dropna(subset=["p25", "p75", "median"]).sort_values("median")
    if d.empty:
        return None
    fig = go.Figure()
    # the P25→P75 span as a floating bar (base=P25), median as a diamond marker
    fig.add_trace(go.Bar(
        y=d["occ_name"], x=d["p75"] - d["p25"], base=d["p25"], orientation="h",
        marker_color="#CBD5E1", width=0.5,
        hovertemplate="%{y}<br>P25 %{base:,.0f} – P75 %{x:,.0f} "
                      + cfg.currency_suffix + "<extra></extra>", showlegend=False))
    fig.add_trace(go.Scatter(
        y=d["occ_name"], x=d["median"], mode="markers",
        marker=dict(symbol="diamond", size=11, color=theme.ACCENT,
                    line=dict(color="#fff", width=1.5)),
        name="Median",
        hovertemplate="%{y}<br>median %{x:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
    fig.update_layout(height=max(220, 46 * len(d) + 90),
                      margin=dict(l=8, r=8, t=40 if title else 8, b=8),
                      title=title, xaxis_title=None, yaxis_title=None, showlegend=False,
                      barmode="overlay")
    return theme.style_fig(fig, horizontal=True)


def grouped_sex_bar(women: pd.DataFrame, men: pd.DataFrame, cfg, value_col: str,
                    *, women_label: str, men_label: str, title: str | None = None):
    """Grouped horizontal bars comparing women vs men on ``value_col`` per
    occupation. Expects two total-slice frames keyed by occ_name."""
    def _series(df):
        d = df[df["dimension"] == "total"].dropna(subset=[value_col])
        return dict(zip(d["occ_name"], d[value_col]))
    w, m = _series(women), _series(men)
    names = [n for n in dict.fromkeys(list(w) + list(m))]
    if not names:
        return None
    fig = go.Figure()
    fig.add_trace(go.Bar(y=names, x=[w.get(n) for n in names], orientation="h",
                         name=women_label, marker_color=theme.ACCENT,
                         hovertemplate="%{y}<br>%{x:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
    fig.add_trace(go.Bar(y=names, x=[m.get(n) for n in names], orientation="h",
                         name=men_label, marker_color="#8FB4D6",
                         hovertemplate="%{y}<br>%{x:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
    fig.update_layout(height=max(240, 58 * len(names) + 90), barmode="group",
                      margin=dict(l=8, r=8, t=40 if title else 8, b=8),
                      title=title, xaxis_title=None, yaxis_title=None,
                      legend=dict(orientation="h", y=1.02, yanchor="bottom"))
    return theme.style_fig(fig, horizontal=True)


def trend_line(trend: pd.DataFrame, cfg, *, title: str | None = None):
    """Mean salary over years, one line per occupation (series). Expects the
    normalized trend frame (year, series, value_nominal)."""
    if trend is None or trend.empty:
        return None
    fig = go.Figure()
    for i, (series, g) in enumerate(trend.groupby("series", sort=False)):
        g = g.dropna(subset=["value_nominal"]).sort_values("year")
        if g.empty:
            continue
        col = theme.SERIES[i % len(theme.SERIES)]
        fig.add_trace(go.Scatter(
            x=g["year"], y=g["value_nominal"], mode="lines+markers", name=str(series),
            line=dict(color=col, width=2.5), marker=theme.series_marker(col),
            hovertemplate="%{x}<br>%{y:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
    if not fig.data:
        return None
    fig.update_layout(height=400, margin=dict(l=8, r=8, t=40 if title else 8, b=8),
                      title=title, xaxis_title=None,
                      yaxis_title=f"{cfg.currency_suffix}/mo",
                      legend=dict(orientation="h", y=1.02, yanchor="bottom"))
    return theme.style_fig(fig)
