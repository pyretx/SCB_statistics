"""Overview tab — the approved Sweden-Overview design, capability-gated.

Per occupation: a mono context line (code · headcount) + name, then a card
grid — a blue MEDIAN hero card (mean as sub-line), a salary-distribution card
with percentile bar rows, a mean-by-sex card with the F/M gap pill, and a
headcount card. Cards drop out when a country lacks the capability (no sex →
no sex card; no counts → no headcount card). Year pills refetch the slice
(instant when the provider caches locally). Compare chart (several
occupations) and the raw-data expander with CSV export stay below.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import agg, charts, i18n, states

_PCT_KEYS = ["p10", "p25", "median", "p75", "p90"]


def _num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    return f"{int(round(v)):,}".replace(",", " ")


_CSS_DONE_KEY = "_ov_css"

_CSS = """
<style>
.ov-ctx{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
  letter-spacing:.14em;color:#8A919D;text-transform:uppercase;margin-bottom:4px;}
.ov-name{font-size:22px;font-weight:700;letter-spacing:-.015em;color:#0C1119;
  margin:0 0 14px;}
.ov-grid{display:grid;gap:16px;margin-bottom:16px;}
.ov-r1{grid-template-columns:minmax(240px,3fr) 7fr;}
.ov-r2{grid-template-columns:7fr minmax(240px,3fr);}
@media (max-width:760px){.ov-r1,.ov-r2{grid-template-columns:1fr;}}
.ov-hero{background:#0A63A6;border-radius:16px;padding:24px;color:#fff;
  display:flex;flex-direction:column;justify-content:space-between;min-height:170px;}
.ov-hlbl{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;
  letter-spacing:.14em;color:rgba(255,255,255,.75);text-transform:uppercase;
  margin-bottom:8px;}
.ov-hnum{font-family:'JetBrains Mono',monospace;font-size:40px;font-weight:600;
  line-height:1.05;letter-spacing:-.01em;}
.ov-hunit{font-size:14px;color:rgba(255,255,255,.75);margin-left:4px;}
.ov-hsub{font-size:12.5px;color:rgba(255,255,255,.75);margin-top:14px;}
.ov-hsub b{font-family:'JetBrains Mono',monospace;color:#fff;font-weight:600;}
.ov-card{background:#fff;border:1px solid #E7E9ED;border-radius:16px;
  padding:22px 24px;}
.ov-chd{display:flex;align-items:center;justify-content:space-between;gap:10px;
  margin-bottom:14px;}
.ov-ct{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
  letter-spacing:.12em;color:#8A919D;text-transform:uppercase;}
.ov-csub{font-size:12px;color:#98A0AC;}
.ov-prow{display:flex;align-items:center;gap:12px;margin-bottom:9px;}
.ov-prow:last-child{margin-bottom:0;}
.ov-plbl{font-family:'JetBrains Mono',monospace;font-size:11px;color:#98A0AC;
  width:34px;flex:0 0 auto;}
.ov-plbl.med{color:#0A63A6;font-weight:600;}
.ov-track{flex:1 1 0;height:9px;border-radius:5px;background:#EEF0F3;overflow:hidden;}
.ov-fill{height:100%;border-radius:5px;background:#94AAC0;}
.ov-fill.med{background:#0A63A6;}
.ov-pval{font-family:'JetBrains Mono',monospace;font-size:12.5px;color:#0C1119;
  width:84px;flex:0 0 auto;text-align:right;}
.ov-pval.med{color:#0A63A6;font-weight:600;}
.ov-srow{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.ov-srow:last-child{margin-bottom:0;}
.ov-slbl{font-size:13px;color:#5B6472;width:64px;flex:0 0 auto;}
.ov-strack{flex:1 1 0;height:22px;border-radius:6px;background:#EEF0F3;overflow:hidden;}
.ov-sfill{height:100%;border-radius:6px;}
.ov-sval{font-family:'JetBrains Mono',monospace;font-size:14px;color:#0C1119;
  width:96px;flex:0 0 auto;text-align:right;}
.ov-gap{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
  padding:4px 10px;border-radius:20px;background:#FBF1DD;color:#8A6318;flex:0 0 auto;}
.ov-hcnum{font-family:'JetBrains Mono',monospace;font-size:30px;font-weight:600;
  color:#0C1119;letter-spacing:-.01em;}
.ov-hcword{font-size:13px;color:#98A0AC;margin-left:6px;}
.ov-hcsub{font-size:12.5px;color:#8A919D;margin-top:10px;}
</style>
"""

_YEAR_CSS = """
<style>
.st-key-{key} [data-testid="stButtonGroup"]{{background:#EDEFF2;border-radius:10px;
  padding:4px;gap:4px;display:inline-flex;}}
.st-key-{key} [data-testid="stButtonGroup"] button{{border:none!important;
  background:transparent!important;border-radius:8px!important;
  padding:7px 14px!important;font-size:13px!important;font-weight:600!important;
  color:#7A828F!important;box-shadow:none!important;}}
.st-key-{key} [data-testid="stButtonGroup"]
  button[data-testid="stBaseButton-segmented_controlActive"]{{background:#fff!important;
  color:#0A63A6!important;box-shadow:0 1px 3px rgba(16,21,31,.10)!important;}}
</style>
"""


def _pct_label(cfg, lang, key):
    return {"p10": "P10", "p25": "P25", "median": "MED", "p75": "P75", "p90": "P90"}[key]


def _fmt_money(cfg, v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    return charts.fmt_value(v, cfg)


def _hero_card(cfg, lang, row) -> str:
    caps = cfg.capabilities
    unit = f"{cfg.currency_suffix}{cfg.per_label}"
    if caps.has_median and pd.notna(row.get("median")):
        lbl, big = i18n.t(cfg, "m_median", lang, "Median (P50)"), row["median"]
        sub_lbl, sub_v = i18n.t(cfg, "m_average", lang, "Average"), row.get("mean")
    elif caps.has_mean and pd.notna(row.get("mean")):
        lbl, big = i18n.t(cfg, "m_average", lang, "Average"), row["mean"]
        sub_lbl, sub_v = i18n.t(cfg, "m_median", lang, "Median (P50)"), row.get("median")
    else:
        return ""
    sub = (f'<div class="ov-hsub">{sub_lbl} <b>{_fmt_money(cfg, sub_v)}</b></div>'
           if sub_v is not None and pd.notna(sub_v) else "")
    return (f'<div class="ov-hero"><div><div class="ov-hlbl">{lbl}</div>'
            f'<div><span class="ov-hnum">{_num(big)}</span>'
            f'<span class="ov-hunit">{unit}</span></div></div>{sub}</div>')


def _dist_card(cfg, lang, row, yr) -> str:
    pts = [(k, float(row[k])) for k in _PCT_KEYS
           if k in row and pd.notna(row[k])]
    if len(pts) < 2:
        return ""
    vmax = max(v for _, v in pts) * 1.06
    rows = "".join(
        f'<div class="ov-prow">'
        f'<span class="ov-plbl{" med" if k == "median" else ""}">{_pct_label(cfg, lang, k)}</span>'
        f'<div class="ov-track"><div class="ov-fill{" med" if k == "median" else ""}"'
        f' style="width:{max(6, v / vmax * 100):.1f}%"></div></div>'
        f'<span class="ov-pval{" med" if k == "median" else ""}">{_num(v)}</span></div>'
        for k, v in pts)
    title = i18n.t(cfg, "tab_distribution", lang, "Salary distribution")
    unit = f"{cfg.currency_suffix}{cfg.per_label}"
    return (f'<div class="ov-card"><div class="ov-chd"><span class="ov-ct">{title} · {yr}</span>'
            f'<span class="ov-csub">{unit}</span></div>{rows}</div>')


def _sex_card(cfg, lang, wv, mv, yr) -> str:
    if wv is None and mv is None:
        return ""
    vals = [v for v in (wv, mv) if v is not None and pd.notna(v)]
    if not vals:
        return ""
    vmax = max(vals) * 1.04
    gap = ((wv / mv - 1) * 100 if wv and mv and pd.notna(wv) and pd.notna(mv) else None)
    pill = (f'<span class="ov-gap">{gap:+.1f} % {i18n.t(cfg, "m_gap", lang, "F/M gap")}</span>'
            if gap is not None else "")
    def srow(label, v, color):
        if v is None or pd.isna(v):
            return ""
        return (f'<div class="ov-srow"><span class="ov-slbl">{label}</span>'
                f'<div class="ov-strack"><div class="ov-sfill" '
                f'style="width:{v / vmax * 100:.1f}%;background:{color};"></div></div>'
                f'<span class="ov-sval">{_fmt_money(cfg, v)}</span></div>')
    title = i18n.t(cfg, "ov_by_sex", lang, "Mean by sex")
    return (f'<div class="ov-card"><div class="ov-chd"><span class="ov-ct">{title} · {yr}</span>'
            f'{pill}</div>'
            + srow(i18n.t(cfg, "women", lang, "Women"), wv, "#6FA8D4")
            + srow(i18n.t(cfg, "men", lang, "Men"), mv, "#0A63A6")
            + '</div>')


def _hc_card(cfg, lang, count) -> str:
    if count is None or pd.isna(count):
        return ""
    return (f'<div class="ov-card"><div class="ov-chd"><span class="ov-ct">'
            f'{i18n.t(cfg, "m_headcount", lang, "Headcount")}</span></div>'
            f'<div><span class="ov-hcnum">{_num(count)}</span>'
            f'<span class="ov-hcword">{i18n.t(cfg, "ov_employees", lang, "employees")}</span></div>'
            f'<div class="ov-hcsub">{i18n.t(cfg, "ov_hc_sub", lang, "in this occupation & filter selection")}</div></div>')


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    caps = cfg.capabilities
    slug = cfg.slug
    tot = stats[stats["dimension"] == "total"]
    if tot.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return
    occ = tuple(query.get("occ_codes", ()))
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Year pills — newest selected year first (what the page already fetched);
    # picking another year refetches that slice (instant when cached locally).
    years = sorted({int(y) for y in query.get("years", ())}, reverse=True)
    yr = None
    if len(years) > 1:
        ykey = f"{slug}_ov_year"
        st.markdown(_YEAR_CSS.format(key=ykey), unsafe_allow_html=True)
        yr = st.segmented_control(i18n.t(cfg, "chart_year", lang, "Chart year"),
                                  years, default=years[0], key=ykey,
                                  label_visibility="collapsed") or years[0]
        cur = int(tot["year"].max()) if tot["year"].notna().any() else None
        if cur is not None and yr != cur:
            with states.loading():
                d2 = cfg.provider.occupation_stats(
                    sector=query.get("sector", ""), occ_codes=occ,
                    sex=query.get("sex", "total"),
                    years=tuple(query.get("years", ())), year=yr, lang=lang)
            if query.get("aggregate") and d2 is not None and not d2.empty:
                d2 = agg.collapse_stats(d2, agg.agg_name(cfg, lang, len(occ)))
            t2 = d2[d2["dimension"] == "total"] if d2 is not None else None
            if t2 is not None and not t2.empty:
                tot = t2
    yr_disp = yr or (int(tot["year"].max()) if tot["year"].notna().any() else "")

    # women/men means for the sex card + F/M gap
    wmean, mmean = {}, {}
    if caps.has_sex:
        with states.loading():
            w = cfg.provider.occupation_stats(sector=query.get("sector", ""), occ_codes=occ,
                                              sex="women", years=tuple(query.get("years", ())),
                                              year=yr, lang=lang)
            m = cfg.provider.occupation_stats(sector=query.get("sector", ""), occ_codes=occ,
                                              sex="men", years=tuple(query.get("years", ())),
                                              year=yr, lang=lang)
        wt, mt = w[w["dimension"] == "total"], m[m["dimension"] == "total"]
        if query.get("aggregate"):
            name = agg.agg_name(cfg, lang, len(occ))
            wt, mt = agg.collapse_stats(wt, name), agg.collapse_stats(mt, name)
        wmean = dict(zip(wt["occ_code"], wt["mean"]))
        mmean = dict(zip(mt["occ_code"], mt["mean"]))

    # ── One card block per occupation ─────────────────────────────────────────
    sel_word = i18n.t(cfg, "ov_selected", lang, "employees selected")
    for _, row in tot.iterrows():
        code, name = row["occ_code"], row["occ_name"]
        cnt = row.get("count")
        ctx_code = "" if code == agg.AGG_CODE else \
            f"{(cfg.classification.split()[0] + ' ') if cfg.classification else ''}{code}"
        ctx_parts = [p for p in (ctx_code,
                                 f"{_num(cnt)} {sel_word}" if cnt is not None and pd.notna(cnt) else "")
                     if p]
        html = ""
        if ctx_parts:
            html += f'<div class="ov-ctx">{" · ".join(ctx_parts)}</div>'
        html += f'<div class="ov-name">{name}</div>'

        hero = _hero_card(cfg, lang, row)
        dist = _dist_card(cfg, lang, row, yr_disp)
        if hero and dist:
            html += f'<div class="ov-grid ov-r1">{hero}{dist}</div>'
        elif hero or dist:
            html += f'<div class="ov-grid ov-r1">{hero or dist}</div>'

        sex = _sex_card(cfg, lang, wmean.get(code), mmean.get(code), yr_disp) \
            if caps.has_sex else ""
        hc = _hc_card(cfg, lang, cnt)
        if sex and hc:
            html += f'<div class="ov-grid ov-r2">{sex}{hc}</div>'
        elif sex or hc:
            html += f'<div class="ov-grid ov-r2">{sex or hc}</div>'
        st.markdown(html, unsafe_allow_html=True)

    # ── Compare chart (several occupations) ───────────────────────────────────
    if len(tot) > 1:
        st.subheader(i18n.t(cfg, "compare_occ", lang, "Compare occupations"))
        val = "mean" if caps.has_mean else "median"
        heading = i18n.t(cfg, "avg_salary" if val == "mean" else "median_salary", lang)
        fig = charts.occupation_bar(tot, cfg, value_col=val,
                                    title=f"{heading} · {cfg.currency_suffix}{cfg.per_label}")
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

    # ── Raw data + CSV export ─────────────────────────────────────────────────
    with st.expander(i18n.t(cfg, "raw_data", lang, "Raw data")):
        col_code = i18n.t(cfg, "col_code", lang)
        col_occ = i18n.t(cfg, "col_occupation", lang)
        cols = [("mean", i18n.t(cfg, "col_mean", lang)),
                ("p10", "P10"), ("p25", "P25"),
                ("median", i18n.t(cfg, "col_median", lang)),
                ("p75", "P75"), ("p90", "P90")]
        raw = pd.DataFrame({col_code: tot["occ_code"].values, col_occ: tot["occ_name"].values})
        disp = raw.copy()
        for key, lbl in cols:
            if key in tot and tot[key].notna().any():
                raw[lbl] = tot[key].values
                disp[lbl] = [charts.fmt_value(v, cfg) for v in tot[key].values]
        if tot["count"].notna().any():
            c_lbl = i18n.t(cfg, "col_count", lang)
            raw[c_lbl] = tot["count"].values
            disp[c_lbl] = [_num(v) for v in tot["count"].values]
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.download_button(i18n.t(cfg, "download_csv", lang, "Download CSV"),
                           raw.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{cfg.slug}_overview.csv", mime="text/csv",
                           key=f"{cfg.slug}_dl_overview")
