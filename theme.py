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

import os
import base64

import content as _content

# App logo mark (blue rounded square + white globe) as a data URI, so the sidebar
# brand link can render the real logo image rather than a material glyph.
_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _svg_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")


def flag_uri(code: str) -> str:
    """Real country flag (assets/flags/<code>.svg) as a data URI — shared by the
    country pages so the header can show the right flag."""
    return _svg_uri(os.path.join(_ASSETS, "flags", f"{code}.svg"))


LOGO_URI = _svg_uri(os.path.join(_ASSETS, "logo_mark.svg"))

# Brand tagline ("POWERED BY QVISTIN") — lives in content/home.toml [brand] and
# renders as a second line under the wordmark wherever the brand mark appears.
TAGLINE = _content.load("home").get("brand", {}).get("tagline", "")

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

# Shared sidebar styling for the country pages (mockup look): trimmed top space,
# mono uppercase section labels, full-width segmented toggles, and the brand logo
# rendered from the single sidebar page-link (which navigates Home on click).
SIDEBAR_CSS = """
<style>
  /* Trim the blank band above the logo: shrink the header (collapse-button row)
     and the content's top padding. Extra specificity so these win over app.py's
     global sidebar padding regardless of DOM order. */
  [data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    height:auto !important; min-height:0 !important; padding:.45rem .6rem 0 !important; }
  [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top:.35rem !important; }
  [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    font-family:'JetBrains Mono',monospace !important; text-transform:uppercase;
    letter-spacing:.11em; font-size:11px !important; font-weight:600; color:#8A919D !important; }
  /* Segmented toggles (Language, Sex): the widget LABEL and the radiogroup are
     both children of stButtonGroup, so the grey track goes on the RADIOGROUP
     (not the whole group — that would tint the label too). White active pill +
     soft shadow per the mockup. Force the element container + radiogroup to full
     width (Streamlit sizes them to content otherwise). */
  [data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stButtonGroup"]) {
     width:100% !important; }
  [data-testid="stSidebar"] [data-testid="stButtonGroup"] { width:100%; }
  [data-testid="stSidebar"] [data-testid="stButtonGroup"] > div[role="radiogroup"] {
     display:flex !important; flex-wrap:nowrap !important; gap:4px !important;
     width:100% !important; min-width:100% !important; box-sizing:border-box !important;
     background:#EDEFF2; padding:4px; border-radius:10px; }
  [data-testid="stSidebar"] [data-testid="stButtonGroup"] button {
     flex:1 1 0 !important; min-width:0 !important; min-height:0; border:0 !important;
     border-radius:7px !important; box-shadow:none; font-weight:600 !important;
     font-size:13px !important; padding:7px 0 !important; }
  [data-testid="stSidebar"] [data-testid="stBaseButton-segmented_control"] {
     background:transparent !important; color:#8A919D !important; }
  [data-testid="stSidebar"] [data-testid="stBaseButton-segmented_control"]:hover {
     background:rgba(255,255,255,.55) !important; color:#5B6472 !important; }
  [data-testid="stSidebar"] [data-testid="stBaseButton-segmented_controlActive"] {
     background:#fff !important; color:#0C1119 !important;
     box-shadow:0 1px 3px rgba(16,21,31,.12) !important; }
  [data-testid="stSidebar"] [data-testid="stBaseButton-segmented_controlActive"]:hover {
     background:#fff !important; color:#0C1119 !important; }
  /* Country switcher rows: real flag + greyed 'coming soon' US. */
  .cc-flag { width:22px; height:15px; object-fit:cover !important; border-radius:3px;
             border:1px solid rgba(0,0,0,.10); display:block; }
  .cc-soon { font-size:14px; color:#B4BAC4; cursor:not-allowed; padding-top:2px; }
  /* Compact switcher trigger, right-aligned next to the logo — ONLY the first
     child (the trigger). Targeting all children re-showed the (normally hidden)
     popover-content div, so the options were visible all the time. */
  [data-testid="stSidebar"] [data-testid="stPopover"] > div:first-child {
    display:flex; justify-content:flex-end; }
  [data-testid="stSidebar"] [data-testid="stPopover"] > div:first-child button {
    padding:5px 8px !important; min-height:0 !important; border-radius:9px !important;
    font-size:13px !important; color:#3A4250 !important; white-space:nowrap !important; }
  [data-testid="stSidebar"] [data-testid="stPopover"] > div:first-child button p {
    white-space:nowrap !important; }
  /* Tighten the option rows in the open popover. */
  [data-testid="stSidebar"] [data-testid="stPopover"] [data-testid="stPageLink"] a {
    padding:4px 4px !important; }
  /* Header flag next to the country H1 (object-fit:cover !important beats
     Streamlit's global img rule, which would letterbox it). */
  .se-hflag { width:44px !important; height:31px !important; object-fit:cover !important;
    border-radius:6px; border:1px solid rgba(0,0,0,.10); display:block;
    box-shadow:0 1px 3px rgba(0,0,0,.08); }
  /* Brand logo = the only sidebar page-link (click → Home). The material icon
     span becomes the real logo image (blue square + globe SVG); hide the glyph. */
  [data-testid="stSidebar"] [data-testid="stPageLink"] a { padding:2px; gap:13px;
    background:transparent !important; }
  [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover { background:transparent !important; }
  [data-testid="stSidebar"] [data-testid="stPageLink"] span[data-testid="stIconMaterial"] {
    width:30px !important; min-width:30px !important; height:30px !important; flex:none; margin:0;
    background:url("__LOGO_URI__") center/contain no-repeat;
    color:transparent !important; font-size:0 !important; box-sizing:border-box; }
  [data-testid="stSidebar"] [data-testid="stPageLink"] p {
    font-weight:700 !important; font-size:16px !important; color:#0C1119 !important;
    letter-spacing:-.01em; line-height:1.15 !important; }
  /* Brand tagline — second line under the wordmark, inside the same link. */
  [data-testid="stSidebar"] [data-testid="stPageLink"] p::after {
    content:"__TAGLINE__"; display:block; font-family:'JetBrains Mono',monospace;
    font-size:8px; font-weight:600; letter-spacing:.14em; color:#8A919D;
    line-height:1.2; margin-top:2px; }
</style>
""".replace("__LOGO_URI__", LOGO_URI).replace("__TAGLINE__", TAGLINE)


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
    # Title + horizontal top legend both live in the top margin and overlap when
    # the margin is a single strip. Give each its own band: the title pinned to
    # the very top of the figure, the legend just above the plot area, and a top
    # margin tall enough for both.
    if (fig.layout.title and fig.layout.title.text
            and fig.layout.legend and fig.layout.legend.orientation == "h"):
        cur_t = fig.layout.margin.t if fig.layout.margin.t is not None else 80
        fig.update_layout(
            title=dict(yref="container", yanchor="top", y=1, pad=dict(t=10)),
            legend=dict(yanchor="bottom", y=1.0),
            margin=dict(t=max(cur_t, 96)),
        )
    fig.update_xaxes(**x_grid, linecolor=TRACK,
                     tickfont=dict(family=MONO, size=11, color=TICK),
                     title_font=dict(family=FONT, size=13, color=AXIS_TITLE))
    fig.update_yaxes(**y_grid, linecolor=TRACK,
                     tickfont=dict(family=MONO, size=11, color=TICK_Y),
                     title_font=dict(family=FONT, size=13, color=AXIS_TITLE))
    return fig
