"""Shared chart theme — the single place that styles every Plotly figure to the
design system (design-system.md §3). Both country pages import this and call
``style_fig(fig)`` right before ``st.plotly_chart`` so no chart ships default
Streamlit/Plotly styling.

Colours come from §1. ``SERIES`` is a restrained, accent-derived categorical
palette used where a chart genuinely needs several distinguishable lines/bars
(e.g. several occupations, sex-split bars) — §1 says "no other hues", but the
Tableau rainbow it replaces was worse; red (``MEAN``) is reserved for the
mean / reference line and negative deltas only.
"""
from __future__ import annotations

# ── Tokens (design-system.md §1) ─────────────────────────────────────────────
ACCENT      = "#0A63A6"   # primary line / bar
ACCENT_HOV  = "#0B72C2"
MEAN        = "#C0453A"   # mean / reference line, negative deltas
TRACK       = "#EEF0F3"   # gridlines
AXIS_TITLE  = "#5B6472"   # axis titles + legend (Hanken)
TICK        = "#98A0AC"   # x tick labels (mono)
TICK_Y      = "#B4BAC4"   # y tick labels (mono)
FONT        = "Hanken Grotesk"
MONO        = "JetBrains Mono"

# Up to 8 distinguishable, on-brand series colours (blues → sage → slate).
SERIES = ["#0A63A6", "#4E93C6", "#7FB3D5", "#5B8A72",
          "#8B5FA6", "#B8863B", "#3F7CAC", "#5A6472"]

SOFT      = "#9EC2DE"   # light-blue bars (un-highlighted / secondary)
SEX_MEN   = "#0A63A6"   # men series (accent)
SEX_WOMEN = "#9EC2DE"   # women series (light blue)

# §3 marker for line charts: white fill, accent stroke.
LINE_MARKER = dict(size=8, color="#FFFFFF", line=dict(color=ACCENT, width=2.5))


def series_marker(color: str) -> dict:
    """White-fill marker stroked in the given series colour."""
    return dict(size=7, color="#FFFFFF", line=dict(color=color, width=2.5))


def style_fig(fig, horizontal: bool = False):
    """Apply the design-system chart theme to ``fig`` in place and return it.

    Sets fonts, transparent background, single-direction gridlines and mono
    tick labels — WITHOUT clobbering the chart's own titles, height, margins,
    hovermode or legend orientation (update_* calls merge). Pass
    ``horizontal=True`` for horizontal bar charts so the value gridlines run
    vertically (on the x axis) instead of horizontally.
    """
    value_axis = dict(showgrid=True, gridcolor=TRACK, gridwidth=1, zeroline=False)
    cat_axis   = dict(showgrid=False, zeroline=False)
    x_grid = value_axis if horizontal else cat_axis
    y_grid = cat_axis if horizontal else value_axis

    fig.update_layout(
        font=dict(family=FONT, color=AXIS_TITLE),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=SERIES,
        legend=dict(font=dict(family=FONT, size=12, color=AXIS_TITLE)),
    )
    fig.update_xaxes(**x_grid, linecolor=TRACK,
                     tickfont=dict(family=MONO, size=11, color=TICK),
                     title_font=dict(family=FONT, size=13, color=AXIS_TITLE))
    fig.update_yaxes(**y_grid, linecolor=TRACK,
                     tickfont=dict(family=MONO, size=11, color=TICK_Y),
                     title_font=dict(family=FONT, size=13, color=AXIS_TITLE))
    return fig
