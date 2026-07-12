"""By-region SIMULATION tab (shared).

For countries whose source has OVERALL earnings by region but not
occupation×region (Denmark, Norway): show the selected occupation's national
figures, and — on a toggle — overlay a region by applying that region's overall
pay difference (vs the nation) uniformly to the occupation. It is explicitly a
simulation; the disclaimer says so. Provider answers region_sim() (a
{display_name: factor} map); capability flag has_region_sim gates the tab.

Look & feel mirrors the other tabs: the standard distribution chart (national
line + a dotted region line when simulating) plus branded stat cards.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import theme

from .. import agg, i18n, states

# Measures shown, canonical order (only those the row actually has).
# All measures in canonical order; each renderer keeps only the ones the row
# actually has, so quartile countries (DK/NO/IS) show P25·MED·P75 and decile
# countries (FI: P10·MED·P90) show their deciles — no measure is hardcoded away.
_MEASURES = [("mean", "m_average", "Average"), ("p10", None, "P10"),
             ("p25", None, "P25"), ("median", "m_median", "Median (P50)"),
             ("p75", None, "P75"), ("p90", None, "P90")]
_PCTS = [("p10", None, "P10"), ("p25", None, "P25"),
         ("median", "m_median", "Median (P50)"),
         ("p75", None, "P75"), ("p90", None, "P90")]

_CSS = """
<style>
.rs-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:2px 0 4px;}
@media(max-width:760px){.rs-grid{grid-template-columns:repeat(2,1fr);}}
.rs-card{background:#fff;border:1px solid #E7E9ED;border-radius:14px;padding:16px 18px;}
.rs-lbl{font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:600;
  letter-spacing:.12em;color:#8A919D;text-transform:uppercase;margin-bottom:9px;}
.rs-val{font-family:'JetBrains Mono',monospace;font-size:23px;font-weight:600;
  color:#0C1119;letter-spacing:-.01em;line-height:1;}
.rs-unit{font-size:12px;color:#98A0AC;font-weight:400;margin-left:3px;}
.rs-pill{display:inline-block;margin-top:10px;font-family:'JetBrains Mono',monospace;
  font-size:11px;font-weight:600;padding:3px 9px;border-radius:20px;}
.rs-up{color:#1B8A5A;background:rgba(27,138,90,.12);}
.rs-dn{color:#B23A3A;background:rgba(178,58,58,.10);}
.rs-flat{color:#8A919D;background:#F1F3F6;}
.rs-rowlbl{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
  letter-spacing:.1em;color:#8A919D;text-transform:uppercase;margin:12px 0 6px;}
.rs-occ{font-size:17px;font-weight:700;letter-spacing:-.01em;color:#0C1119;margin:6px 0 2px;}
</style>
"""


def _label(cfg, lang, i18n_key, fallback):
    return i18n.t(cfg, i18n_key, lang, fallback) if i18n_key else fallback


def _num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    return f"{int(round(v)):,}".replace(",", " ")


def _cards(cfg, lang, row, factor, delta):
    """A row of branded stat cards — a measure per card; delta pill when set."""
    unit = f'<span class="rs-unit">{cfg.currency_suffix}{cfg.per_label}</span>'
    pill = ""
    if delta is not None:
        cls = "rs-up" if factor > 1 else ("rs-dn" if factor < 1 else "rs-flat")
        arrow = "↑ " if factor > 1 else ("↓ " if factor < 1 else "")
        pill = f'<div class="rs-pill {cls}">{arrow}{delta}</div>'
    cells = ""
    for key, ik, fb in _MEASURES:
        if key not in row or pd.isna(row[key]):
            continue
        cells += (f'<div class="rs-card"><div class="rs-lbl">'
                  f'{_label(cfg, lang, ik, fb)}</div>'
                  f'<div class="rs-val">{_num(float(row[key]) * factor)}{unit}</div>'
                  f'{pill}</div>')
    st.markdown(f'<div class="rs-grid">{cells}</div>', unsafe_allow_html=True)


def _chart(cfg, lang, tot, factor, region_name, year, sim_on, region_rows=None):
    """The standard distribution line chart: a national line + mean diamond per
    occupation, and (when a region is active) a dotted region line + diamond.
    ``region_rows`` {occ_code: row} gives REAL per-region values (US); when None
    the region line is national × ``factor`` (the simulation)."""
    pct = [(k, _label(cfg, lang, ik, fb)) for k, ik, fb in _PCTS
           if k in tot and tot[k].notna().any()]
    if not pct:
        return None
    xlabels = [lbl for _, lbl in pct]
    mean_label = i18n.t(cfg, "m_average", lang, "Average")
    show_mean = bool(cfg.capabilities.has_mean and tot["mean"].notna().any())
    cats = xlabels + ([mean_label] if show_mean else [])
    unit = cfg.currency_suffix
    nat_lbl = f'{i18n.t(cfg, "rs_national", lang, "National")} ({year})'
    multi = len(tot) > 1
    fig = go.Figure()
    for i, (_, row) in enumerate(tot.iterrows()):
        occ = str(row["occ_name"])
        col = theme.SERIES[i % len(theme.SERIES)]
        ys = [row[c] for c, _ in pct]
        n_name = f"{occ} · {nat_lbl}" if multi else nat_lbl
        fig.add_trace(go.Scatter(x=xlabels, y=ys, mode="lines+markers", name=n_name,
                                 line=dict(color=col, width=2.5),
                                 marker=theme.series_marker(col)))
        if show_mean and pd.notna(row["mean"]):
            fig.add_trace(go.Scatter(
                x=[mean_label], y=[row["mean"]], mode="markers", showlegend=False,
                marker=dict(size=12, symbol="diamond", color=col,
                            line=dict(width=1, color="white")),
                hovertemplate=f"{n_name}<br>{mean_label} %{{y:,.0f}} {unit}<extra></extra>"))
        if sim_on and region_name:
            rc = theme.MEAN if not multi else col
            r_name = f"{occ} · {region_name}" if multi else region_name
            rr = region_rows.get(row["occ_code"]) if region_rows is not None else None
            if region_rows is not None:      # real per-region values
                r_ys = [rr[c] if (rr is not None and pd.notna(rr[c])) else None
                        for c, _ in pct]
                r_mean = rr["mean"] if (rr is not None and pd.notna(rr["mean"])) else None
            else:                            # simulation: national × factor
                r_ys = [y * factor if pd.notna(y) else y for y in ys]
                r_mean = row["mean"] * factor if pd.notna(row["mean"]) else None
            fig.add_trace(go.Scatter(
                x=xlabels, y=r_ys, mode="lines+markers", name=r_name,
                line=dict(color=rc, width=2, dash="dot"),
                marker=dict(size=7, color=rc)))
            if show_mean and r_mean is not None:
                fig.add_trace(go.Scatter(
                    x=[mean_label], y=[r_mean], mode="markers", showlegend=False,
                    marker=dict(size=12, symbol="diamond", color=rc,
                                line=dict(width=1, color="white")),
                    hovertemplate=f"{r_name}<br>{mean_label} %{{y:,.0f}} {unit}<extra></extra>"))
    fig.update_layout(
        xaxis=dict(categoryorder="array", categoryarray=cats,
                   title=i18n.t(cfg, "x_percentile", lang, "Percentile")),
        yaxis_title=f"{unit}{cfg.per_label}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=420, margin=dict(t=60, b=40), hovermode="x unified")
    return theme.style_fig(fig)


def _real_state_cards(cfg, lang, nat_row, state_row):
    """Cards for a real region: each measure's actual regional value + its own
    %-vs-national delta (suppressed cells show '–', no pill)."""
    unit = f'<span class="rs-unit">{cfg.currency_suffix}{cfg.per_label}</span>'
    cells = ""
    for key, ik, fb in _MEASURES:
        if key not in nat_row or pd.isna(nat_row[key]):
            continue
        sv = state_row[key] if (state_row is not None and key in state_row) else None
        if sv is None or pd.isna(sv):
            val_html, pill = '<div class="rs-val">–</div>', ""
        else:
            money = (f'{"$" if cfg.money_prefix else ""}{_num(sv)}'
                     f'{"" if cfg.money_prefix else unit}')
            val_html = f'<div class="rs-val">{money}</div>'
            nv = nat_row[key]
            pct = ((sv / nv - 1) * 100) if (nv and pd.notna(nv)) else None
            if pct is None:
                pill = ""
            else:
                cls = "rs-up" if pct > 0.05 else ("rs-dn" if pct < -0.05 else "rs-flat")
                arr = "↑ " if pct > 0.05 else ("↓ " if pct < -0.05 else "")
                pill = f'<div class="rs-pill {cls}">{arr}{pct:+.1f}%</div>'
        cells += (f'<div class="rs-card"><div class="rs-lbl">'
                  f'{_label(cfg, lang, ik, fb)}</div>{val_html}{pill}</div>')
    st.markdown(f'<div class="rs-grid">{cells}</div>', unsafe_allow_html=True)


def _money_cards(cfg, lang, row):
    """National cards honouring money_prefix ($ before the number for the US)."""
    unit = f'<span class="rs-unit">{cfg.currency_suffix}{cfg.per_label}</span>'
    cells = ""
    for key, ik, fb in _MEASURES:
        if key not in row or pd.isna(row[key]):
            continue
        money = (f'{"$" if cfg.money_prefix else ""}{_num(row[key])}'
                 f'{"" if cfg.money_prefix else unit}')
        cells += (f'<div class="rs-card"><div class="rs-lbl">'
                  f'{_label(cfg, lang, ik, fb)}</div><div class="rs-val">{money}</div></div>')
    st.markdown(f'<div class="rs-grid">{cells}</div>', unsafe_allow_html=True)


def _render_real(cfg, query, lang):
    """REAL occupation×region mode (US OEWS per-state): national baseline vs a
    chosen state's ACTUAL figures — not a simulation. Region is always the
    national/all-industries geography (OEWS has no industry × state)."""
    slug = cfg.slug
    def k(n):
        return f"{slug}_{n}"
    occ = tuple(query.get("occ_codes", ()))
    year = cfg.capabilities.year_range[1] if cfg.capabilities.year_range else None
    sex = query.get("sex", "total")
    nat_code = cfg.provider.region_national_code()
    with states.loading():
        nat = cfg.provider.occupation_stats(sector=nat_code, occ_codes=occ,
                                            sex=sex, year=year, lang=lang)
    nat_tot = nat[nat["dimension"] == "total"] if nat is not None else nat
    if query.get("aggregate") and nat_tot is not None and not nat_tot.empty:
        nat_tot = agg.collapse_stats(nat_tot, agg.agg_name(cfg, lang, len(occ)))
    if nat_tot is None or nat_tot.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return

    st.caption(i18n.t(cfg, "rs_real_intro", lang,
                      "Below are the national figures for the selected occupation. "
                      "Choose a state to see its actual regional wages."))

    choices = cfg.provider.region_choices(lang) or []
    code_by_name = {n: c for c, n in choices}
    show = st.toggle(i18n.t(cfg, "rs_real_toggle", lang, "Show a specific state"),
                     key=k("regsim"))
    region_name, region_rows = None, None
    if show and choices:
        region_name = st.selectbox(i18n.t(cfg, "rs_state", lang, "State"),
                                   [n for _, n in choices], key=k("regsim_pick"))
        with states.loading():
            st_stats = cfg.provider.occupation_stats(sector=code_by_name[region_name],
                                                     occ_codes=occ, sex=sex, year=year,
                                                     lang=lang)
        st_tot = st_stats[st_stats["dimension"] == "total"]
        if query.get("aggregate") and not st_tot.empty:
            st_tot = agg.collapse_stats(st_tot, agg.agg_name(cfg, lang, len(occ)))
        region_rows = {r["occ_code"]: r for _, r in st_tot.iterrows()}

    fig = _chart(cfg, lang, nat_tot, 1.0, region_name, year, bool(show), region_rows)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    for _, row in nat_tot.iterrows():
        st.markdown(f'<div class="rs-occ">{row["occ_name"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rs-rowlbl">{i18n.t(cfg, "rs_national", lang, "National")}</div>',
                    unsafe_allow_html=True)
        _money_cards(cfg, lang, row)
        if show and region_name:
            st.markdown(f'<div class="rs-rowlbl">{region_name}</div>', unsafe_allow_html=True)
            _real_state_cards(cfg, lang, row,
                              region_rows.get(row["occ_code"]) if region_rows else None)

    st.caption(i18n.t(cfg, "rs_real_note", lang,
                      "Actual BLS OEWS wages by state (all industries). BLS does not "
                      "publish wages by occupation × industry × state, so an industry "
                      "selection does not apply here; blank cells are figures BLS "
                      "suppresses for that state."))


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    slug = cfg.slug
    def k(n):
        return f"{slug}_{n}"

    st.subheader(i18n.t(cfg, "tab_region_sim", lang, "By region"))
    st.markdown(_CSS, unsafe_allow_html=True)

    # US-style REAL per-region data → its own renderer (not a simulation).
    if getattr(cfg.capabilities, "has_region_data", False):
        _render_real(cfg, query, lang)
        return

    tot = stats[stats["dimension"] == "total"]
    occ = tuple(query.get("occ_codes", ()))
    if query.get("aggregate") and not tot.empty:
        tot = agg.collapse_stats(tot, agg.agg_name(cfg, lang, len(occ)))
    if tot.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return

    st.caption(i18n.t(cfg, "rs_intro", lang,
                      "Below are the national figures for the selected occupation. "
                      "Turn on the simulation to estimate them for a specific region."))

    yy = query.get("years", ())
    year = max(int(y) for y in yy) if yy else (
        cfg.capabilities.year_range[1] if cfg.capabilities.year_range else None)
    with states.loading():
        data = cfg.provider.region_sim(year=year, lang=lang) or {}
    regions = data.get("regions") or {}
    if not regions:
        st.info(i18n.t(cfg, "rs_unavailable", lang,
                       "Regional simulation isn't available for this country."))
        return

    # ── Toggle + region picker ────────────────────────────────────────────────
    sim_on = st.toggle(i18n.t(cfg, "rs_toggle", lang, "Simulate a specific region"),
                       key=k("regsim"))
    factor, delta, region_name = 1.0, None, None
    if sim_on:
        opts = sorted(regions, key=lambda r: -regions[r])   # highest-paying first

        def _fmt(r):
            return f"{r}  ({(regions[r] - 1) * 100:+.1f}%)"
        region_name = st.selectbox(i18n.t(cfg, "rs_region", lang, "Region"), opts,
                                   format_func=_fmt, key=k("regsim_pick"))
        factor = regions[region_name]
        delta = f"{(factor - 1) * 100:+.1f}%"

    # ── Chart: national line + (simulated) region line ────────────────────────
    fig = _chart(cfg, lang, tot, factor, region_name, year, sim_on)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    # ── National (+ simulated) stat cards, per occupation ─────────────────────
    for _, row in tot.iterrows():
        st.markdown(f'<div class="rs-occ">{row["occ_name"]}</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="rs-rowlbl">{i18n.t(cfg, "rs_national", lang, "National")}</div>',
                    unsafe_allow_html=True)
        _cards(cfg, lang, row, 1.0, None)
        if sim_on:
            st.markdown(f'<div class="rs-rowlbl">{region_name} · {delta}</div>',
                        unsafe_allow_html=True)
            _cards(cfg, lang, row, factor, delta)

    # ── Basis + disclaimer ────────────────────────────────────────────────────
    if data.get("basis"):
        st.caption(i18n.t(cfg, "rs_basis", lang, "Regional difference based on {basis}.")
                   .format(basis=data["basis"]))
    st.warning(i18n.t(cfg, "rs_disclaimer", lang,
                      "Estimate only. This applies the region's overall pay "
                      "difference — measured across all occupations — to this one "
                      "occupation. The true regional gap for this specific "
                      "occupation may differ."))
