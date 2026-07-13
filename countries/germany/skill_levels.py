"""Germany-specific "Skill levels" tab.

KldB 2010 encodes the requirement level (Anforderungsniveau) in the 5th digit of
an occupation code, so the same occupation appears at up to four levels:
  …1 un-/semiskilled (Helfer) · …2 skilled (Fachkraft) ·
  …3 complex specialist (Spezialist) · …4 highly complex (Experte)
This tab groups those levels under their 4-digit base occupation and charts the
mean + median PROGRESSION across levels — the pay premium for higher
qualification within one occupation. Unique to Germany; wired via
cfg.extra_tabs, so it never touches the shared tabs.
"""
from __future__ import annotations

from collections import defaultdict

import plotly.graph_objects as go
import streamlit as st

import theme
from core import charts, i18n

# 5th-digit requirement level → (sort order, EN label, DE label)
_LEVELS = {
    "1": ("Un-/semiskilled", "Helfer"),
    "2": ("Skilled", "Fachkraft"),
    "3": ("Complex specialist", "Spezialist"),
    "4": ("Highly complex", "Experte"),
}
_ORDER = ["1", "2", "3", "4"]

_T = {
    "EN": {"pick": "Occupation", "level": "Skill level", "mean": "Mean",
           "median": "Median", "step": "Median step-up",
           "axis": "Gross monthly",
           "intro": "How pay rises across skill levels within one occupation — the "
                    "5th KldB digit is the requirement level (Anforderungsniveau).",
           "premium": "**Pay premium:** {hi} earns **{pct}% more** than {lo} (median).",
           "one": "Only one skill level is published for this occupation.",
           "selnote": "Showing figures for: {sex}."},
    "DE": {"pick": "Beruf", "level": "Anforderungsniveau", "mean": "Mittel",
           "median": "Median", "step": "Median-Steigerung",
           "axis": "Brutto monatlich",
           "intro": "Wie der Verdienst mit dem Anforderungsniveau steigt — die "
                    "5. KldB-Stelle ist das Anforderungsniveau.",
           "premium": "**Verdienstprämie:** {hi} verdient **{pct}% mehr** als {lo} (Median).",
           "one": "Für diesen Beruf ist nur ein Anforderungsniveau veröffentlicht.",
           "selnote": "Angezeigt für: {sex}."},
}


def _lvl_label(digit: str, lang: str) -> str:
    en, de = _LEVELS.get(digit, (digit, digit))
    return de if lang == "DE" else en


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    sex = query.get("sex", "total")
    T = _T.get(lang, _T["EN"])
    slug = cfg.slug
    st.subheader(i18n.t(cfg, "tab_skill_levels", lang, "Skill levels"))
    st.caption(T["intro"])

    tree = cfg.provider.occupation_tree(lang)
    children = defaultdict(list)
    for c in tree:
        if len(c) == 5:
            children[c[:4]].append(c)
    multi = {b for b, ch in children.items() if len(ch) >= 2}      # ≥2 levels
    if not multi:
        st.caption(i18n.no_data(cfg, lang))
        return

    # Default to the base(s) of the sidebar selection; else the first base.
    occ = tuple(query.get("occ_codes", ()))
    sel_bases = [c[:4] for c in occ if len(c) >= 4 and c[:4] in multi]
    options = sorted(multi, key=lambda b: tree.get(b, b).lower())
    default = sel_bases[0] if sel_bases else options[0]
    base = st.selectbox(T["pick"], options,
                        index=options.index(default) if default in options else 0,
                        format_func=lambda b: f"{tree.get(b, b)}  ({b})",
                        key=f"{slug}_skl_base")

    kids = sorted(children[base], key=lambda c: _ORDER.index(c[-1]) if c[-1] in _ORDER else 9)
    df = cfg.provider.occupation_stats(occ_codes=tuple(kids), sex=sex, lang=lang)
    df = df[df["dimension"] == "total"]
    rows = []
    for c in kids:
        r = df[df["occ_code"] == c]
        if r.empty:
            continue
        rr = r.iloc[0]
        rows.append((c[-1], rr["mean"], rr["median"]))
    rows = [r for r in rows if r[1] is not None or r[2] is not None]
    if not rows:
        st.caption(i18n.no_data(cfg, lang))
        return
    if sex != "total":
        st.caption(T["selnote"].format(sex=i18n.t(cfg, sex, lang, sex)))

    xlabels = [_lvl_label(d, lang) for d, _, _ in rows]
    means = [m for _, m, _ in rows]
    medians = [md for _, _, md in rows]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xlabels, y=medians, mode="lines+markers+text", name=T["median"],
        line=dict(color=theme.ACCENT, width=3), marker=theme.LINE_MARKER,
        text=[charts.fmt_value(v, cfg) for v in medians], textposition="top center",
        textfont=dict(family=theme.MONO, size=11, color=theme.ACCENT),
        hovertemplate="%{x}<br>%{y:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
    if any(m is not None for m in means):
        fig.add_trace(go.Scatter(
            x=xlabels, y=means, mode="lines+markers", name=T["mean"],
            line=dict(color=theme.MEAN, width=2, dash="dot"),
            marker=theme.series_marker(theme.MEAN),
            hovertemplate="%{x}<br>%{y:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
    fig.update_layout(
        title=f"{tree.get(base, base)} · {cfg.currency_suffix}{cfg.per_label}",
        height=430, hovermode="x unified", yaxis_title=T["axis"], xaxis_title=None,
        legend=dict(orientation="h"), margin=dict(l=8, r=8, t=96, b=8))
    st.plotly_chart(theme.style_fig(fig), use_container_width=True)

    # Pay-premium line (top vs bottom level, median).
    lo_md, hi_md = medians[0], medians[-1]
    if len(rows) >= 2 and lo_md and hi_md:
        st.markdown(T["premium"].format(hi=xlabels[-1], lo=xlabels[0],
                                        pct=f"{(hi_md / lo_md - 1) * 100:+.0f}"))
    elif len(rows) == 1:
        st.caption(T["one"])

    # Table: level · mean · median · median step-up vs the previous level.
    import pandas as pd
    trows = []
    prev = None
    for (d, mean, md), lbl in zip(rows, xlabels):
        step = "–"
        if prev and md:
            step = f"{(md / prev - 1) * 100:+.0f} %"
        trows.append({T["level"]: lbl, T["mean"]: charts.fmt_value(mean, cfg),
                      T["median"]: charts.fmt_value(md, cfg), T["step"]: step})
        prev = md or prev
    st.dataframe(pd.DataFrame(trows), use_container_width=True, hide_index=True)
