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
    n = f"{int(round(v)):,}".replace(",", " ")
    return f"{cfg.currency_suffix}{n}" if cfg.money_prefix else f"{n} {cfg.currency_suffix}"


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


# Percentile columns in canonical left→right order, with their x-axis labels.
_PCT_ORDER = [("p10", "P10"), ("p25", "P25"), ("median", "Median"),
              ("p75", "P75"), ("p90", "P90")]


def distribution_chart(stats: pd.DataFrame, cfg, *, keys=None, labels_map: dict | None = None,
                       mean_label: str = "Mean", x_title: str | None = None,
                       title: str | None = None):
    """THE standard salary-distribution chart (mirrors the Swedish page): one
    line+markers trace per occupation across the percentile points the source
    actually publishes (P10..P90, whichever exist), with the mean drawn as a
    standalone diamond (it is not a percentile). Norway's P25·median·P75 renders
    the same way as Sweden's P10–P90 — just fewer points on the line.

    ``keys`` — restrict to these measure keys (subset of p10/p25/median/p75/p90/
    mean), in canonical order; None = all present. ``labels_map`` — key→x-label.
    Horizontal legend on top, ``hovermode='x unified'``, theme-styled — identical
    look to scb_salaries.py's Percentile distribution tab."""
    d = stats[stats["dimension"] == "total"].copy()
    if d.empty:
        return None
    labels_map = labels_map or {}
    want = set(keys) if keys is not None else None
    # percentile columns to plot: canonical order, present in data, and selected
    pct = [(col, labels_map.get(col, lbl)) for col, lbl in _PCT_ORDER
           if d[col].notna().any() and (want is None or col in want)]
    labels = [lbl for _, lbl in pct]
    show_mean = bool(cfg.capabilities.has_mean and d["mean"].notna().any()
                     and (want is None or "mean" in want))
    if not pct and not show_mean:
        return None
    cats = labels + ([mean_label] if show_mean else [])

    fig = go.Figure()
    for i, (_, row) in enumerate(d.iterrows()):
        col = theme.SERIES[i % len(theme.SERIES)]
        name = str(row["occ_name"])
        ys = [row[c] for c, _ in pct]
        if not all(pd.isna(y) for y in ys):
            fig.add_trace(go.Scatter(
                x=labels, y=ys, mode="lines+markers", name=name,
                line=dict(color=col, width=2.5), marker=theme.series_marker(col)))
        # mean — standalone diamond, disconnected from the percentile line
        if show_mean and pd.notna(row["mean"]):
            fig.add_trace(go.Scatter(
                x=[mean_label], y=[row["mean"]], mode="markers", showlegend=False,
                marker=dict(size=12, symbol="diamond", color=col,
                            line=dict(width=1, color="white")),
                hovertemplate=f"{name}<br>{mean_label} %{{y:,.0f}} "
                              + cfg.currency_suffix + "<extra></extra>"))
    if not fig.data:
        return None
    fig.update_layout(
        xaxis=dict(categoryorder="array", categoryarray=cats, title=x_title),
        yaxis_title=f"{cfg.currency_suffix}{cfg.per_label}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=420, margin=dict(t=60, b=40), hovermode="x unified", title=title)
    return theme.style_fig(fig)


def grouped_sex_bar(women: pd.DataFrame, men: pd.DataFrame, cfg, value_col: str,
                    *, women_label: str, men_label: str, title: str | None = None,
                    show_ratio: bool = False):
    """Grouped horizontal bars comparing women vs men on ``value_col`` per
    occupation. When ``show_ratio`` is set, the two bars stay and a "women as %
    of men" figure is annotated at the end of each row (the Swedish behaviour)."""
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
    if show_ratio:
        for n in names:
            wv, mv = w.get(n), m.get(n)
            if wv and mv:
                fig.add_annotation(x=max(wv, mv), y=n, text=f"{wv / mv * 100:.0f}%",
                                   showarrow=False, xanchor="left", xshift=10,
                                   font=dict(color=theme.MEAN, size=13,
                                             family="JetBrains Mono, monospace"))
    fig.update_layout(height=max(240, 58 * len(names) + 90), barmode="group",
                      margin=dict(l=8, r=8, t=40 if title else 8, b=8),
                      title=title, xaxis_title=None, yaxis_title=None,
                      legend=dict(orientation="h", y=1.02, yanchor="bottom"))
    return theme.style_fig(fig, horizontal=True)


def category_bar(df: pd.DataFrame, cfg, value_col: str, *, title: str | None = None):
    """Grouped horizontal bars of ``value_col`` per category (dim_value) — the
    shared chart behind the By age / By education / By region tabs. One trace
    per occupation, categories in the order the provider returned them (age
    bands ascending, education levels 1→7, regions north→south…)."""
    d = df.dropna(subset=[value_col]).copy()
    if d.empty:
        return None
    cats = list(dict.fromkeys(d["dim_value"]))          # provider order, deduped
    fig = go.Figure()
    for i, (name, g) in enumerate(d.groupby("occ_name", sort=False)):
        col = theme.SERIES[i % len(theme.SERIES)]
        by_cat = dict(zip(g["dim_value"], g[value_col]))
        fig.add_trace(go.Bar(
            y=cats, x=[by_cat.get(c) for c in cats], orientation="h",
            name=str(name), marker_color=col,
            hovertemplate="%{y}<br>%{x:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
    if not fig.data:
        return None
    n_rows = len(cats)
    fig.update_layout(
        height=max(260, (26 + 20 * max(0, d["occ_name"].nunique() - 1)) * n_rows + 120),
        barmode="group", margin=dict(l=8, r=8, t=40 if title else 8, b=8),
        title=title, xaxis_title=None, yaxis_title=None,
        yaxis=dict(categoryorder="array", categoryarray=cats[::-1]),
        legend=dict(orientation="h", y=1.02, yanchor="bottom"))
    return theme.style_fig(fig, horizontal=True)


def position_curve(levs, vals, est, salary, cfg, *, you_label: str = "You",
                   x_title: str | None = None, title: str | None = None):
    """Percentile curve for one occupation with the user's salary marked (a star
    at the estimated percentile + a dotted salary line) — the Swedish "Where do I
    stand?" chart."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=levs, y=vals, mode="lines+markers", showlegend=False,
        line=dict(color=theme.ACCENT, width=2.5), marker=theme.series_marker(theme.ACCENT)))
    fig.add_hline(y=salary, line=dict(color=theme.MEAN, width=1, dash="dot"))
    fig.add_trace(go.Scatter(
        x=[est], y=[salary], mode="markers+text", text=[you_label],
        textposition="top center", textfont=dict(color=theme.MEAN), showlegend=False,
        marker=dict(size=17, symbol="star", color=theme.MEAN, line=dict(width=1, color="white"))))
    lo, hi = max(0, levs[0] - 10), min(100, levs[-1] + 10)
    fig.update_layout(
        xaxis=dict(tickvals=levs, ticktext=[f"P{int(l)}" for l in levs], range=[lo, hi],
                   title=x_title),
        yaxis_title=f"{cfg.currency_suffix}{cfg.per_label}", height=380, margin=dict(t=40, b=40),
        showlegend=False, title=title)
    return theme.style_fig(fig)


def leaderboard_bar(show: pd.DataFrame, cfg, *, value_col: str, value_fmt,
                    highlight: set, x_title: str | None = None, title: str | None = None):
    """Horizontal ranking bars; the user's own occupations are drawn in the accent
    colour, the rest dimmed — the Swedish Leaderboard chart."""
    colors = [theme.ACCENT if c in highlight else theme.SOFT for c in show["occ_code"]]
    fig = go.Figure(go.Bar(
        x=show[value_col], y=show["occ_name"], orientation="h", marker_color=colors,
        text=[value_fmt(v) for v in show[value_col]], textposition="auto",
        hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>"))
    fig.update_layout(height=max(360, 27 * len(show) + 80), margin=dict(t=30, b=40, l=8),
                      xaxis_title=x_title, yaxis_title=None, title=title)
    return theme.style_fig(fig, horizontal=True)


def trend_lines(df: pd.DataFrame, cfg, *, value_col: str = "value", y_title: str,
                unit: str = "", inflation=None, inflation_label: str = "Inflation",
                title: str | None = None):
    """One line+markers per occupation (series) over years — the shared trend
    chart. ``df`` has columns [year, series, <value_col>]. Optionally overlays a
    dashed inflation line (``inflation`` = list of (year, pct)), as on the Swedish
    growth-vs-inflation view."""
    if df is None or df.empty:
        return None
    fig = go.Figure()
    for i, (series, g) in enumerate(df.groupby("series", sort=False)):
        g = g.dropna(subset=[value_col]).sort_values("year")
        if g.empty:
            continue
        col = theme.SERIES[i % len(theme.SERIES)]
        fig.add_trace(go.Scatter(
            x=g["year"], y=g[value_col], mode="lines+markers", name=str(series),
            line=dict(color=col, width=2.5), marker=theme.series_marker(col),
            hovertemplate="%{x}<br>%{y:,.0f} " + unit + "<extra></extra>"))
    if inflation:
        xs = [y for y, _ in inflation]
        ys = [p for _, p in inflation]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers", name=inflation_label,
            line=dict(color=theme.MEAN, width=2, dash="dash"), marker=dict(size=6),
            hovertemplate="%{x}<br>%{y:+.1f}%<extra></extra>"))
    if not fig.data:
        return None
    fig.update_layout(height=400, margin=dict(l=8, r=8, t=40 if title else 8, b=8),
                      title=title, xaxis_title=None, yaxis_title=y_title,
                      xaxis=dict(type="category"),
                      legend=dict(orientation="h", y=1.02, yanchor="bottom"))
    return theme.style_fig(fig)
