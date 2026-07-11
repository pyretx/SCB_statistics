"""Sweden-specific extra tab: the work-permit salary & SSYK check (Migrationsverket
rules), ported from the legacy page onto the framework's extra_tabs hook.

Rules come from the SAME wp_rules.json the legacy page's admin editor writes
(defaults below match the legacy WP_DEFAULTS), so both pages always agree.
All strings live in the config's i18n (EN + SV) under wp_* keys.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import theme
from core import i18n, states

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES_FILE = os.path.join(_ROOT, "wp_rules.json")
DEFAULTS = {
    "as_of": "2026-06-16",
    "median": 38300,
    "pct_general": 0.90,
    "pct_transition": 0.80,
    "pct_exempt": 0.75,
    "blue_card_floor": 52000,
    "transition_end": "2026-12-01",
    "bench_year": 2025,
    "exempt_ssyk": ["3115", "3215", "3511", "3512", "3513", "3514",
                    "5321", "5322", "5323", "5324", "5325", "5326", "5330",
                    "6121", "6129", "6130", "6210",
                    "7212", "7215", "7233", "7413", "7611",
                    "8161", "8169", "8199", "8341", "9210"],
    "banned_full": ["5343"],
    "banned_partial": ["9210"],
}


def load_rules() -> dict:
    rules = dict(DEFAULTS)
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, encoding="utf-8") as f:
                rules.update(json.load(f))
        except Exception:
            pass
    return rules


def save_rules(rules: dict):
    """Persist the rule set (the admin panel's Work-permit editor writes here;
    same file/shape the legacy page's editor used)."""
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


def _floor(rules, ssyk: str, permit_type: str, is_transition: bool, app_date_iso: str):
    """(floor_sek, basis_key) — the applicable salary floor (legacy wp_floor)."""
    if permit_type == "blue":
        return rules["blue_card_floor"], "blue"
    if is_transition and app_date_iso <= rules["transition_end"]:
        return round(rules["median"] * rules["pct_transition"]), "transition"
    if ssyk in set(rules["exempt_ssyk"]):
        return round(rules["median"] * rules["pct_exempt"]), "exempt"
    return round(rules["median"] * rules["pct_general"]), "general"


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    def t(key, default=None):
        return i18n.t(cfg, key, lang, default)
    rules = load_rules()

    st.subheader(t("wp_title"))
    st.info(t("wp_banner").format(as_of=rules["as_of"],
                                  today=datetime.now().strftime("%Y-%m-%d")))

    occs = cfg.provider.occupations(lang)
    codes = [c for c in query.get("occ_codes", ()) if c != "0000"]
    if not codes:
        st.info(t("wp_no_occ"))
        return

    c1, c2 = st.columns(2)
    with c1:
        pcode = st.selectbox(t("wp_occ"), codes,
                             format_func=lambda c: f"{c} – {occs.get(c, c)}",
                             key="se2_wp_occ")
        salary = st.number_input(t("wp_salary"), min_value=0, value=35000,
                                 step=500, key="se2_wp_salary")
        ptype = st.radio(t("wp_type"), [t("wp_type_regular"), t("wp_type_blue")],
                         key="se2_wp_type", horizontal=True)
        permit_type = "blue" if ptype == t("wp_type_blue") else "regular"
    with c2:
        secs = list(cfg.capabilities.sectors)
        cur = query.get("sector", secs[0])
        sec_labels = [i18n.t(cfg, f"sector_{s}", lang, s) for s in secs]
        sel = st.selectbox(t("wp_sector"), sec_labels,
                           index=secs.index(cur) if cur in secs else 0,
                           key=f"se2_wp_sector_{cur}")
        wp_sector = secs[sec_labels.index(sel)]
        is_transition = st.checkbox(t("wp_transition"), key="se2_wp_transition")
        app_date = st.date_input(t("wp_app_date"), key="se2_wp_date")
    app_date_iso = app_date.strftime("%Y-%m-%d")

    st.divider()

    # 1 · Eligibility ----------------------------------------------------------
    st.markdown(f"**{t('wp_h_elig')}**")
    if pcode in set(rules["banned_full"]):
        st.error(t("wp_banned_full").format(code=pcode))
    elif pcode in set(rules["banned_partial"]):
        st.warning(t("wp_banned_partial").format(code=pcode))
    else:
        st.success(t("wp_elig_ok").format(code=pcode))

    # 2 · Salary floor ---------------------------------------------------------
    st.markdown(f"**{t('wp_h_floor')}**")
    floor, basis = _floor(rules, pcode, permit_type, is_transition, app_date_iso)
    basis_txt = t(f"wp_basis_{basis}")
    if salary >= floor:
        st.success(t("wp_floor_pass").format(sal=salary, floor=floor,
                                             basis=basis_txt, margin=salary - floor))
    else:
        st.error(t("wp_floor_fail").format(sal=salary, floor=floor,
                                           basis=basis_txt, gap=floor - salary))

    # 3 · Market / customary pay -----------------------------------------------
    st.markdown(f"**{t('wp_h_market')}**")
    bench_year = int(rules.get("bench_year", 2025))
    with states.loading():
        mdf = cfg.provider.occupation_stats(sector=wp_sector, occ_codes=(pcode,),
                                            sex="total", year=bench_year, lang=lang)
    pts = []
    if mdf is not None and not mdf.empty:
        row = mdf.iloc[0]
        for lvl, col in [(10, "p10"), (25, "p25"), (50, "median"), (75, "p75"), (90, "p90")]:
            if col in row and pd.notna(row[col]):
                pts.append((lvl, float(row[col])))
    pts.sort(key=lambda p: p[0])
    if len(pts) < 2:
        st.info(t("wp_market_none"))
    else:
        levs = [lv for lv, _ in pts]
        vals = [v for _, v in pts]
        if salary <= vals[0]:
            est = levs[0]
        elif salary >= vals[-1]:
            est = levs[-1]
        else:
            est = levs[-1]
            for i in range(len(pts) - 1):
                if vals[i] <= salary <= vals[i + 1]:
                    frac = ((salary - vals[i]) / (vals[i + 1] - vals[i])
                            if vals[i + 1] > vals[i] else 0.0)
                    est = levs[i] + frac * (levs[i + 1] - levs[i])
                    break
        pv = dict(pts)
        st.write(t("wp_market").format(
            sal=salary, pct=est, sector=sel, year=bench_year,
            p10=int(pv.get(10, vals[0])), p50=int(pv.get(50, vals[len(vals) // 2])),
            p90=int(pv.get(90, vals[-1]))))
        if 50 in pv and salary < pv[50]:
            st.warning(t("wp_market_below"))
        else:
            st.success(t("wp_market_ok"))

        occ_median = pv.get(50) or vals[len(vals) // 2]
        v90 = round(occ_median * rules["pct_general"])
        v80 = round(occ_median * rules["pct_transition"])
        v75 = round(occ_median * rules["pct_exempt"])
        st.caption(t("wp_ref_lines").format(median=int(occ_median)))
        rc1, rc2, rc3 = st.columns(3)
        show90 = rc1.checkbox(f"90% ({v90:,})", key="se2_wp_ref90")
        show80 = rc2.checkbox(f"80% ({v80:,})", key="se2_wp_ref80")
        show75 = rc3.checkbox(f"75% ({v75:,})", key="se2_wp_ref75")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=levs, y=vals, mode="lines+markers",
                                 line=dict(color=theme.ACCENT, width=2.5),
                                 marker=theme.series_marker(theme.ACCENT)))
        fig.add_hline(y=floor, line=dict(color="#1B8A5A", width=1, dash="dash"),
                      annotation_text=f"{t('wp_plot_floor')} {int(floor):,}",
                      annotation_position="bottom left")
        for show, val, col, lbl in [(show90, v90, "#8B5FA6", "90%"),
                                    (show80, v80, "#B26A00", "80%"),
                                    (show75, v75, "#4E93C6", "75%")]:
            if show:
                fig.add_hline(y=val, line=dict(color=col, width=1, dash="dot"),
                              annotation_text=f"{lbl} {int(val):,}",
                              annotation_position="top left")
        fig.add_hline(y=salary, line=dict(color=theme.MEAN, width=1, dash="dot"))
        fig.add_trace(go.Scatter(
            x=[est], y=[salary], mode="markers+text",
            text=[f"{t('wp_plot_proposed')} ({int(salary):,})"],
            textposition="top center", textfont=dict(color=theme.MEAN),
            marker=dict(size=16, symbol="star", color=theme.MEAN,
                        line=dict(width=1, color="white"))))
        fig.update_layout(
            xaxis_title=i18n.t(cfg, "x_percentile", lang, "Percentile"),
            yaxis_title=f"{cfg.currency_suffix}{cfg.per_label}",
            xaxis=dict(tickvals=levs, ticktext=[f"P{lv}" for lv in levs], range=[5, 95]),
            height=360, margin=dict(t=30, b=40), showlegend=False)
        theme.style_fig(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(t("wp_market_note"))

    # 4 · Documentation & process ----------------------------------------------
    st.markdown(f"**{t('wp_h_docs')}**")
    st.caption(t("wp_docs_note"))
    for item in i18n.t(cfg, "wp_docs_items", lang, []) or []:
        st.checkbox(item, key=f"se2_wp_doc_{item[:20]}")

    with st.expander(t("wp_rules_expander")):
        st.markdown(
            f"- Median: **SEK {rules['median']:,}** (as of {rules['as_of']})\n"
            f"- 90% → **SEK {round(rules['median'] * rules['pct_general']):,}**\n"
            f"- 80% → **SEK {round(rules['median'] * rules['pct_transition']):,}**\n"
            f"- 75% → **SEK {round(rules['median'] * rules['pct_exempt']):,}**\n"
            f"- EU Blue Card → **SEK {rules['blue_card_floor']:,}**\n"
            f"- Transition ends: **{rules['transition_end']}**")
        st.markdown(f"**{t('wp_exempt_header')}**")
        st.dataframe(pd.DataFrame(
            [{"SSYK": c, i18n.t(cfg, "col_occupation", lang): occs.get(c, "—")}
             for c in sorted(rules["exempt_ssyk"])]),
            use_container_width=True, hide_index=True)
