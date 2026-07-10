"""By-gender tab — women vs men mean/median per occupation, with a "Women as %
of men" toggle (like the Swedish page). Fetches the women/men slices via the
provider. Gated by capabilities.has_sex.

Above the chart: a per-occupation KPI strip in the Overview card design (the
legacy France page's gender metrics, promoted to the standard) — mean salary,
women, men, the amber F/M-gap pill and headcount. Tiles drop out when a source
doesn't publish the figure.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import agg, charts, i18n, states
from .overview import _CSS as _OV_CSS, _num

# KPI-strip additions on top of the Overview card classes (same tokens).
_KPI_CSS = """
<style>
.ov-kgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));
  gap:16px;margin-bottom:18px;}
.ov-kdot{display:inline-block;width:9px;height:9px;border-radius:50%;
  margin-right:7px;vertical-align:1px;}
.ov-kgap{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:600;
  padding:5px 14px;border-radius:24px;background:#FBF1DD;color:#8A6318;
  display:inline-block;letter-spacing:-.01em;}
</style>
"""


def _tile(label: str, value_html: str, dot: str = "") -> str:
    d = f'<span class="ov-kdot" style="background:{dot};"></span>' if dot else ""
    return (f'<div class="ov-card"><div class="ov-chd"><span class="ov-ct">{d}{label}'
            f'</span></div><div>{value_html}</div></div>')


def _kpi_strip(cfg, lang, trow, wv, mv, val_col: str) -> str:
    """One occupation's tile row: mean/median · women · men · F/M gap · headcount."""
    unit = cfg.currency_suffix.strip()
    val_lbl = (i18n.t(cfg, "kpi_mean", lang, "Mean salary") if val_col == "mean"
               else i18n.t(cfg, "median_salary", lang, "Median salary"))
    tiles = []
    tv = trow.get(val_col) if trow is not None else None
    if tv is not None and pd.notna(tv):
        tiles.append(_tile(f"{val_lbl} ({unit})",
                           f'<span class="ov-hcnum">{_num(tv)}</span>'))
    if wv is not None and pd.notna(wv):
        tiles.append(_tile(f'{i18n.t(cfg, "women", lang, "Women")} ({unit})',
                           f'<span class="ov-hcnum">{_num(wv)}</span>', dot="#6FA8D4"))
    if mv is not None and pd.notna(mv):
        tiles.append(_tile(f'{i18n.t(cfg, "men", lang, "Men")} ({unit})',
                           f'<span class="ov-hcnum">{_num(mv)}</span>', dot="#0A63A6"))
    if (wv is not None and mv is not None and pd.notna(wv) and pd.notna(mv) and mv):
        gap = (wv / mv - 1) * 100
        tiles.append(_tile(i18n.t(cfg, "m_gap", lang, "F/M gap"),
                           f'<span class="ov-kgap">{gap:+.1f} %</span>'))
    cnt = trow.get("count") if trow is not None else None
    if cnt is not None and pd.notna(cnt):
        tiles.append(_tile(i18n.t(cfg, "m_headcount", lang, "Headcount"),
                           f'<span class="ov-hcnum">{_num(cnt)}</span>'))
    return f'<div class="ov-kgrid">{"".join(tiles)}</div>' if tiles else ""


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    slug = cfg.slug
    st.subheader(i18n.t(cfg, "tab_sex", lang, "By gender"))
    occ = tuple(query.get("occ_codes", ()))
    sector = query.get("sector", "")
    years = tuple(query.get("years", ()))
    with states.loading():
        # Total alongside women/men — the KPI strip always shows the overall
        # figure + headcount regardless of the sidebar's gender filter.
        total = cfg.provider.occupation_stats(sector=sector, occ_codes=occ,
                                              sex="total", years=years, lang=lang)
        women = cfg.provider.occupation_stats(sector=sector, occ_codes=occ,
                                              sex="women", years=years, lang=lang)
        men = cfg.provider.occupation_stats(sector=sector, occ_codes=occ,
                                            sex="men", years=years, lang=lang)
    if query.get("aggregate"):
        name = agg.agg_name(cfg, lang, len(occ))
        total = agg.collapse_stats(total, name)
        women, men = agg.collapse_stats(women, name), agg.collapse_stats(men, name)
    val = "mean" if cfg.capabilities.has_mean else "median"

    # ── KPI tiles per occupation (Overview look & feel) ──────────────────────
    ttot = total[total["dimension"] == "total"] if total is not None else None
    wtot = women[women["dimension"] == "total"]
    mtot = men[men["dimension"] == "total"]
    wmap = dict(zip(wtot["occ_code"], wtot[val]))
    mmap = dict(zip(mtot["occ_code"], mtot[val]))
    if ttot is not None and not ttot.empty:
        st.markdown(_OV_CSS + _KPI_CSS, unsafe_allow_html=True)
        for _, row in ttot.iterrows():
            code = row["occ_code"]
            strip = _kpi_strip(cfg, lang, row, wmap.get(code), mmap.get(code), val)
            if not strip:
                continue
            ctx_code = "" if code == agg.AGG_CODE else \
                f"{(cfg.classification.split()[0] + ' ') if cfg.classification else ''}{code}"
            yr = int(row["year"]) if pd.notna(row.get("year")) else ""
            ctx = " · ".join(str(p) for p in (ctx_code, yr) if p)
            html = (f'<div class="ov-ctx">{ctx}</div>' if ctx else "")
            html += f'<div class="ov-name">{row["occ_name"]}</div>{strip}'
            st.markdown(html, unsafe_allow_html=True)

    # ── Women-vs-men bars ─────────────────────────────────────────────────────
    ratio = st.toggle(i18n.t(cfg, "show_ratio", lang, "Women as % of men"),
                      key=f"{slug}_sexratio")
    # Always the two bars; the toggle just annotates women-as-%-of-men at the end
    # of each row (Sweden's behaviour), rather than replacing them.
    heading = (i18n.t(cfg, "ratio_title", lang, "Women's salary as % of men's") if ratio
               else f"{i18n.t(cfg, 'avg_salary' if val == 'mean' else 'median_salary', lang)} · {cfg.currency_suffix}{cfg.per_label}")
    fig = charts.grouped_sex_bar(
        women, men, cfg, val,
        women_label=i18n.t(cfg, "women", lang), men_label=i18n.t(cfg, "men", lang),
        title=heading, show_ratio=ratio)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
