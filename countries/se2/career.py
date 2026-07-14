"""Sweden "Career Paths — Beta" tab (curated v0).

Interpretation layer on top of the official SCB statistics — it never changes or
restates them. For the occupation being viewed it shows: the official percentile
curve (published points vs interpolated), a set of Qvistin-estimated career levels
positioned by *actual salary* (each computed live from its OWN SSYK's SCB curve via
core.interp), a simple career map (advance / specialist / leadership / lateral), and
a role comparison. Everything is a clearly-labelled estimate with a confidence tag.

Bilingual (EN + Svenska): all chrome via i18n (keys in countries/se2/config.py),
title/family names from name_sv, level/track/confidence via the helpers below.

Data: careerpaths.py (curated cp_* register). No AI, no job-ad access at runtime.
Beta-gated + Sweden-only (registered in config + core/tabs._BETA_TABS).
"""
from __future__ import annotations

import html

import plotly.graph_objects as go
import streamlit as st

import theme
from core import charts, i18n

_TRACK_COLOR = {"ic": "#0A63A6", "specialist": "#5B8A72", "management": "#B26A00"}
_TRACK_LABEL = {"ic": "Individual contributor", "specialist": "Specialist", "management": "Management"}
_CONF_LABEL = {"strong": "Strong evidence", "moderate": "Moderate evidence",
               "limited": "Limited evidence", "experimental": "Experimental"}
_REL_GROUPS = [
    ("progression", "Advance within this occupation"),
    ("specialist", "Move into a related specialist occupation"),
    ("leadership", "Move into leadership"),
    ("lateral", "Related lateral moves"),
]
# Swedish for the fixed set of curated level labels (level_label has no name_sv).
_LEVEL_SV = {
    "Entry / Associate": "Ingång / Junior", "Professional": "Yrkesperson",
    "Senior Professional": "Senior yrkesperson", "Lead / Advanced": "Ledande / Avancerad",
    "Principal / Staff": "Principal / Staff", "Specialist": "Specialist",
    "Management": "Ledning", "Lead / Specialist": "Ledande / specialist",
    "Senior / Specialist": "Senior / specialist",
}


def _tname(t, lang):
    """Title display name — Swedish where available."""
    return (t.get("name_sv") or t["name_en"]) if lang == "SV" else t["name_en"]


def _level(label, lang):
    return _LEVEL_SV.get(label, label) if lang == "SV" else label


def _track(cfg, lang, code):
    return i18n.t(cfg, f"cp_track_{code}", lang, _TRACK_LABEL.get(code, code))


def _conf(cfg, lang, code):
    return i18n.t(cfg, f"cp_conf_{code}", lang, _CONF_LABEL.get(code, code))


def _year(cfg, query) -> int:
    ys = query.get("years") or ()
    if ys:
        return max(int(y) for y in ys)
    yr = cfg.capabilities.year_range
    return yr[1] if yr else 2025


def _curves(cfg, ssyks, sex, year, lang):
    from core import interp
    d = cfg.provider.occupation_stats(sector="0", occ_codes=tuple(ssyks), sex=sex,
                                      year=year, years=(year,), lang=lang)
    out = {}
    if d is not None and not d.empty:
        for _, r in d.iterrows():
            out[str(r["occ_code"]).strip()] = interp.curve_from_stats(dict(r))
    return out


def _band_for(title, curves):
    c = curves.get(str(title.get("primary_ssyk")))
    if not c or not c.ok:
        return None
    return c.band(float(title["lo_pct"]), float(title["mid_pct"]), float(title["hi_pct"]))


def _esc(x):
    return html.escape(str(x)) if x is not None else ""


# ── Job-ad evidence (v1) — real Arbetsförmedlingen signal, when present ───────
_EV_STRENGTH = {"strong": "Strong signal", "moderate": "Moderate signal", "limited": "Limited signal"}


def _ev_strength(cfg, lang, code):
    return i18n.t(cfg, f"cp_ev_{code}", lang, _EV_STRENGTH.get(code, code))


def _ev_ads(cfg, lang, e):
    """"based on N ads · Arbetsförmedlingen" attribution line for an evidence row."""
    return i18n.t(cfg, "cp_ev_based", lang, "based on {n} ads · Arbetsförmedlingen").format(
        n=int(e.get("ad_count") or 0))


def _ev_skills(e, k=3):
    return [s.get("skill") for s in (e.get("common_skills") or [])[:k] if s.get("skill")]


def render(cfg, stats, query):
    import careerpaths as cp
    lang = query.get("lang", "EN")

    # ── Beta banner + transparency (Phase 13) ────────────────────────────────
    st.markdown(
        '<div style="border:1px solid #E7C16B;background:rgba(178,106,0,.07);border-radius:12px;'
        'padding:12px 16px;margin-bottom:8px;">'
        '<span style="font-family:\'JetBrains Mono\',monospace;font-size:10.5px;font-weight:600;'
        'letter-spacing:.06em;color:#B26A00;background:rgba(178,106,0,.13);padding:2px 8px;'
        'border-radius:5px;">CAREER PATHS · BETA</span>'
        '<div style="font-size:13px;color:#5B6472;line-height:1.55;margin-top:8px;">'
        + i18n.t(cfg, "cp_disclaimer", lang,
                 "Career levels, salary intervals, percentile positioning and career "
                 "relationships are <b>Qvistin-generated estimates</b> — not official career "
                 "structures defined by SCB or Arbetsförmedlingen. One SSYK occupation can "
                 "contain several seniority levels; levels are inferred from job titles, "
                 "responsibilities and experience. Salary intervals are estimates based on the "
                 "official SCB distribution and normally overlap. Salary does not measure "
                 "individual performance.")
        + '</div></div>', unsafe_allow_html=True)

    occ_codes = tuple(str(c) for c in query.get("occ_codes", ()))
    if not occ_codes:
        st.info(i18n.t(cfg, "cp_pick", lang, "Select an occupation in the sidebar to see its career paths."))
        return
    primary = occ_codes[0]
    fam = cp.family_for_ssyk(primary)
    if not fam:
        st.info(i18n.t(cfg, "cp_uncovered", lang,
                       "Career Paths currently covers a set of professional families "
                       "(HR, Software & ICT, Finance, Sales & Marketing, Healthcare, Legal, "
                       "Logistics and Engineering). Open an occupation in one of those to "
                       "explore its career map."))
        return

    titles = cp.titles_for_family(fam)
    rels = cp.relationships_for_family(fam)
    by_id = {t["title_id"]: t for t in titles}
    # Real job-ad evidence (v1) — {} when the pipeline hasn't run / tables absent.
    try:
        import careerpaths_v1 as cpv1
        evidence = cpv1.evidence()
    except Exception:
        evidence = {}
    year, sex = _year(cfg, query), query.get("sex", "total")

    # ── Selected occupation + its career family ──────────────────────────────
    occ_name = primary
    try:
        m = stats[stats["occ_code"].astype(str) == primary] if stats is not None else None
        occ_name = (m.iloc[0]["occ_name"] if m is not None and not m.empty
                    else cfg.provider.occupations(lang).get(primary, primary))
    except Exception:
        occ_name = cfg.provider.occupations(lang).get(primary, primary)
    _fr = cp.family_names().get(fam, {})
    fam_name = (_fr.get("sv") or _fr.get("en") or fam) if lang == "SV" else (_fr.get("en") or fam)
    st.markdown(
        f'<div style="font-size:14px;color:#26303C;margin:2px 0 14px;">'
        f'{i18n.t(cfg, "cp_selected", lang, "Selected occupation")}: '
        f'<b>{_esc(occ_name)}</b> <span style="font-family:\'JetBrains Mono\',monospace;'
        f'color:#98A0AC;font-size:12px;">SSYK {_esc(primary)}</span>'
        f' &nbsp;·&nbsp; {i18n.t(cfg, "cp_family", lang, "Career family")}: '
        f'<b>{_esc(fam_name)}</b></div>', unsafe_allow_html=True)

    with st.spinner("…"):
        curves = _curves(cfg, sorted({t["primary_ssyk"] for t in titles}), sex, year, lang)
    for t in titles:
        t["_band"] = _band_for(t, curves)

    def mid_salary(t):
        return t["_band"]["mid_salary"] if t.get("_band") else None

    # ═══ 1 · Official curve for the viewed occupation ════════════════════════
    st.markdown(f"#### {i18n.t(cfg, 'cp_curve_h', lang, 'Official salary curve')}")
    st.caption(i18n.t(cfg, "cp_curve_cap", lang,
                      "The official SCB percentile distribution for this occupation. "
                      "Dots are published percentiles (P10/P25/P50/P75/P90); the line between "
                      "them is interpolated — not published by SCB."))
    vc = curves.get(primary)
    if vc and vc.ok:
        xs = [p / 2 for p in range(20, 181)]
        ys = [vc.value_at(p).value for p in xs]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=theme.ACCENT, width=2.5),
                                 name=i18n.t(cfg, "cp_interp", lang, "Interpolated"),
                                 hovertemplate="P%{x:.0f} · %{y:,.0f} kr<extra></extra>"))
        pub_x = [10, 25, 50, 75, 90]
        pub_y = [vc.value_at(p).value for p in pub_x]
        fig.add_trace(go.Scatter(x=pub_x, y=pub_y, mode="markers",
                                 marker=dict(color=theme.ACCENT, size=9, line=dict(color="#fff", width=2)),
                                 name=i18n.t(cfg, "cp_published", lang, "Published (SCB)"),
                                 hovertemplate="P%{x:.0f} · %{y:,.0f} kr<extra></extra>"))
        fig.update_layout(height=300, xaxis_title=i18n.t(cfg, "x_percentile", lang, "Percentile"),
                          yaxis_title=f"{cfg.currency_suffix}{cfg.per_label}", showlegend=True)
        fig = theme.style_fig(fig)
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
                          margin=dict(t=44, l=10, r=10, b=44))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption(i18n.t(cfg, "cp_no_curve", lang, "No SCB distribution available for this occupation/year."))

    # ═══ 2 · Estimated career levels, positioned by salary ═══════════════════
    st.markdown(f"#### {i18n.t(cfg, 'cp_levels_h', lang, 'Estimated career levels (by salary)')}")
    st.caption(i18n.t(cfg, "cp_levels_cap", lang,
                      "Each bar is a Qvistin-estimated salary interval for a role, computed from "
                      "that role's own official SSYK distribution. Ranges normally overlap — a "
                      "strong Professional can out-earn a new Senior. Colour = career track."))
    banded = [t for t in titles if t.get("_band")]
    banded.sort(key=lambda t: t["_band"]["mid_salary"])
    if banded:
        fig2 = go.Figure()
        for tr in ("ic", "specialist", "management"):
            rows = [t for t in banded if t["track"] == tr]
            if not rows:
                continue
            fig2.add_trace(go.Bar(
                orientation="h", y=[_tname(t, lang) for t in rows],
                x=[t["_band"]["hi_salary"] - t["_band"]["lo_salary"] for t in rows],
                base=[t["_band"]["lo_salary"] for t in rows],
                marker=dict(color=_TRACK_COLOR[tr], line=dict(width=0)), opacity=0.55,
                name=_track(cfg, lang, tr),
                customdata=[[t["primary_ssyk"], t["mid_pct"], _conf(cfg, lang, t["confidence"]),
                             t["_band"]["mid_salary"]] for t in rows],
                hovertemplate="%{y}<br>SSYK %{customdata[0]} · ~P%{customdata[1]:.0f}"
                              "<br>%{base:,.0f}–%{x:,.0f} kr (~%{customdata[3]:,.0f})"
                              "<br>%{customdata[2]}<extra></extra>"))
        fig2.add_trace(go.Scatter(
            orientation="h", y=[_tname(t, lang) for t in banded],
            x=[t["_band"]["mid_salary"] for t in banded], mode="markers",
            marker=dict(color="#0C1119", size=7, symbol="line-ns-open"),
            showlegend=False, hoverinfo="skip"))
        fig2.update_layout(height=120 + 26 * len(banded), barmode="overlay",
                           xaxis_title=f"{cfg.currency_suffix}{cfg.per_label}")
        fig2 = theme.style_fig(fig2)
        fig2.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
                           margin=dict(t=54, l=10, r=10, b=44))
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander(i18n.t(cfg, "cp_table_h", lang, "All roles — detail")):
        import pandas as pd
        rows = []
        has_ev = any(evidence.get(t["title_id"]) for t in titles)
        for t in sorted(titles, key=lambda x: (mid_salary(x) or 0)):
            b = t.get("_band")
            e = evidence.get(t["title_id"])
            row = {
                i18n.t(cfg, "cp_c_title", lang, "Role"): _tname(t, lang),
                i18n.t(cfg, "cp_c_level", lang, "Level"): _level(t["level_label"], lang),
                i18n.t(cfg, "cp_c_track", lang, "Track"): _track(cfg, lang, t["track"]),
                "SSYK": t["primary_ssyk"],
                i18n.t(cfg, "cp_c_pct", lang, "Est. percentile"): f"P{t['lo_pct']:.0f}–P{t['hi_pct']:.0f}",
                i18n.t(cfg, "cp_c_salary", lang, "Est. salary"):
                    (f"{charts.fmt_value(b['lo_salary'], cfg)}–{charts.fmt_value(b['hi_salary'], cfg)}"
                     if b else "—"),
                i18n.t(cfg, "cp_c_conf", lang, "Evidence"): _conf(cfg, lang, t["confidence"]),
            }
            if has_ev:
                row[i18n.t(cfg, "cp_c_market", lang, "Market signal")] = (
                    f"{int(e.get('ad_count') or 0)} " + i18n.t(cfg, "cp_ads", lang, "ads")
                    + f" · {_ev_strength(cfg, lang, e.get('evidence_strength'))}" if e else "—")
                row[i18n.t(cfg, "cp_c_skills", lang, "Top ad skills")] = (
                    ", ".join(_ev_skills(e, 4)) if e else "—")
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        if has_ev:
            st.caption(i18n.t(cfg, "cp_ev_attr", lang,
                              "Market signal & top skills are aggregated from public job ads "
                              "(Arbetsförmedlingen / JobTech, CC BY-SA) — indicative, not official."))

    # ═══ 2b · Performance positioning — INTERNAL PREVIEW (not published) ═════
    role = (st.session_state.get("auth_user") or {}).get("role", "")
    pcfg = cp.perf_config()
    if (role in ("admin", "master") or pcfg.get("enabled_public")) and banded:
        bands = cp.perf_bands()
        if bands:
            with st.expander("🔒 " + i18n.t(cfg, "cp_perf_h", lang,
                                            "Performance positioning — internal preview (not published)")):
                st.warning(pcfg.get("disclaimer",
                           "Illustrative compensation-positioning model only — NOT a measure of "
                           "individual performance, and salary does not prove performance."))
                import pandas as pd
                # Soft palette (position 1..5): Developing=orange · Progressing=yellow
                # · Fully effective=green · Strong=light blue · Exceptional=dark blue.
                _PERF_COLORS = ["#E8A15C", "#EAC85E", "#7FBF8A", "#8CC0DE", "#3E6DA3"]
                plabels = [b["label"] for b in bands]
                all_label = i18n.t(cfg, "cp_perf_all", lang, "All levels")
                sel = st.selectbox(
                    i18n.t(cfg, "cp_perf_filter", lang, "Highlight performance level"),
                    [all_label] + plabels, key=f"{cfg.slug}_cp_perf_filter")

                roles = sorted(banded, key=lambda x: x["_band"]["mid_salary"])
                seg = {}
                for tt in roles:
                    vc = curves.get(str(tt["primary_ssyk"]))
                    lo_p, hi_p = float(tt["lo_pct"]), float(tt["hi_pct"])
                    seg[_tname(tt, lang)] = ([
                        (vc.value_at(lo_p + float(b["rel_lo"]) * (hi_p - lo_p)).value,
                         vc.value_at(lo_p + float(b["rel_hi"]) * (hi_p - lo_p)).value)
                        for b in bands] if vc and vc.ok else None)
                names = [_tname(tt, lang) for tt in roles if seg.get(_tname(tt, lang))]

                if names:
                    fig = go.Figure()
                    for i, b in enumerate(bands):
                        base = [seg[n][i][0] for n in names]
                        width = [seg[n][i][1] - seg[n][i][0] for n in names]
                        s_hi = [seg[n][i][1] for n in names]
                        op = 1.0 if sel in (all_label, b["label"]) else 0.18
                        fig.add_trace(go.Bar(
                            orientation="h", y=names, x=width, base=base,
                            marker=dict(color=_PERF_COLORS[i % 5], line=dict(width=0)),
                            opacity=op, name=b["label"], customdata=s_hi,
                            hovertemplate="%{y} · " + b["label"]
                                          + "<br>%{base:,.0f}–%{customdata:,.0f} kr<extra></extra>"))
                    fig.update_layout(barmode="overlay", height=150 + 28 * len(names),
                                      xaxis_title=f"{cfg.currency_suffix}{cfg.per_label}")
                    fig = theme.style_fig(fig)
                    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
                                      margin=dict(t=66, l=10, r=10, b=44))
                    st.plotly_chart(fig, use_container_width=True)

                    role_sel = st.selectbox(i18n.t(cfg, "cp_perf_role", lang, "Show intervals for role"),
                                            names, key=f"{cfg.slug}_cp_perf_role")
                    s = seg.get(role_sel)
                    st.dataframe(pd.DataFrame([{
                        i18n.t(cfg, "cp_perf_pos", lang, "Position"): b["label"],
                        i18n.t(cfg, "cp_perf_within", lang, "Within level"):
                            f"{float(b['rel_lo'])*100:.0f}–{float(b['rel_hi'])*100:.0f}%",
                        i18n.t(cfg, "cp_perf_sal", lang, "Illustrative salary"):
                            (f"{charts.fmt_value(s[i][0], cfg)}–{charts.fmt_value(s[i][1], cfg)}"
                             if s else "—"),
                    } for i, b in enumerate(bands)]), hide_index=True, use_container_width=True)
                st.caption(i18n.t(cfg, "cp_perf_note", lang,
                                  "Internal preview — not shown to users. Public release requires "
                                  "individual-level, consented compensation evidence we do not have."))

    # ═══ 3 · Career map from the viewed occupation ═══════════════════════════
    st.markdown(f"#### {i18n.t(cfg, 'cp_map_h', lang, 'Where can this role lead?')}")
    from_ids = {t["title_id"] for t in titles if str(t["primary_ssyk"]) == primary}
    out_rels = [r for r in rels if r["from_title"] in from_ids]
    if not out_rels:
        out_rels = [r for r in rels if r["rel_type"] == "progression"]
    # ONE consistent baseline for every "vs" figure: the median of the occupation
    # the user selected. (Using each relationship's own predecessor made the diffs
    # incomparable across cards — a higher role could show a smaller +.)
    _bc = curves.get(primary)
    base_mid = _bc.value_at(50).value if _bc and _bc.ok else None
    shown_any = False
    for rtype, heading in _REL_GROUPS:
        group = [r for r in out_rels if r["rel_type"] == rtype]
        if not group:
            continue
        shown_any = True
        st.markdown(f"**{i18n.t(cfg, f'cp_rel_{rtype}', lang, heading)}**")
        cols = st.columns(min(3, len(group)))
        for i, r in enumerate(group):
            to = by_id.get(r["to_title"])
            if not to:
                continue
            b = to.get("_band")
            diff = (b["mid_salary"] - base_mid) if (b and base_mid is not None) else None
            ssyk_badge = (i18n.t(cfg, "cp_same_ssyk", lang, "↔ same SSYK") if r["same_ssyk"]
                          else f"→ SSYK {to['primary_ssyk']}")
            sal = (f"{charts.fmt_value(b['lo_salary'], cfg)}–{charts.fmt_value(b['hi_salary'], cfg)}"
                   if b else "—")
            diff_html = ""
            if diff is not None:
                sign = "+" if diff >= 0 else "−"
                color = "#1B8A5A" if diff >= 0 else "#C0453A"
                diff_html = (f'<div style="font-size:12px;color:{color};font-weight:600;margin-top:4px;">'
                             f'{sign}{charts.fmt_value(abs(diff), cfg)} {i18n.t(cfg,"cp_vs",lang,"vs occupation median (indicative)")}</div>')
            gaps = ", ".join((r.get("skill_gaps") or [])[:3])
            ev = evidence.get(to["title_id"])
            ev_html = ""
            if ev:
                sk = _ev_skills(ev, 3)
                sk_html = (f'<div style="font-size:12px;color:#5B6472;margin-top:4px;">'
                           f'{i18n.t(cfg,"cp_ev_skills",lang,"In-demand skills")}: '
                           f'{_esc(", ".join(sk))}</div>' if sk else "")
                ev_html = (
                    f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
                    f'color:#1B8A5A;margin-top:8px;">{_esc(_ev_ads(cfg, lang, ev))}</div>' + sk_html)
            with cols[i % len(cols)]:
                st.markdown(
                    f'<div style="border:1px solid #E7E9ED;border-radius:12px;padding:13px 15px;'
                    f'margin-bottom:10px;background:#fff;">'
                    f'<div style="font-weight:700;font-size:14.5px;color:#0C1119;">{_esc(_tname(to, lang))}</div>'
                    f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10.5px;color:#98A0AC;'
                    f'margin:3px 0 8px;">{_esc(_level(to["level_label"], lang))} · {_esc(ssyk_badge)} · '
                    f'{_esc(_conf(cfg, lang, to["confidence"]))}</div>'
                    f'<div style="font-size:13px;color:#26303C;">{sal}</div>'
                    f'{diff_html}'
                    + (f'<div style="font-size:12px;color:#5B6472;margin-top:6px;">'
                       f'{i18n.t(cfg,"cp_gaps",lang,"Typical gaps")}: {_esc(gaps)}</div>' if gaps else "")
                    + ev_html
                    + '</div>', unsafe_allow_html=True)
    if not shown_any:
        st.caption(i18n.t(cfg, "cp_no_moves", lang, "No mapped moves for this occupation yet."))

    # ═══ 4 · Compare two roles ═══════════════════════════════════════════════
    with st.expander(i18n.t(cfg, "cp_compare_h", lang, "Compare two roles")):
        names = {_tname(t, lang): t for t in titles}
        c1, c2 = st.columns(2)
        a = c1.selectbox(i18n.t(cfg, "cp_current", lang, "Current role"), list(names),
                         key=f"{cfg.slug}_cp_a")
        b_name = c2.selectbox(i18n.t(cfg, "cp_next", lang, "Possible next role"), list(names),
                              index=min(1, len(names) - 1), key=f"{cfg.slug}_cp_b")
        ta, tb = names[a], names[b_name]

        def cell(t):
            bd = t.get("_band")
            return (f"SSYK {t['primary_ssyk']} · {_track(cfg, lang, t['track'])}<br>"
                    f"{_level(t['level_label'], lang)}<br>P{t['lo_pct']:.0f}–P{t['hi_pct']:.0f}<br>"
                    + (f"{charts.fmt_value(bd['lo_salary'], cfg)}–{charts.fmt_value(bd['hi_salary'], cfg)}"
                       if bd else "—")
                    + f"<br>{_conf(cfg, lang, t['confidence'])}")
        diff = None
        if ta.get("_band") and tb.get("_band"):
            diff = tb["_band"]["mid_salary"] - ta["_band"]["mid_salary"]
        st.markdown(
            f'<table style="width:100%;font-size:13px;border-collapse:collapse;">'
            f'<tr><td style="padding:8px;border-bottom:1px solid #EEF0F3;"><b>{_esc(a)}</b><br>{cell(ta)}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #EEF0F3;"><b>{_esc(b_name)}</b><br>{cell(tb)}</td></tr>'
            f'</table>'
            + (f'<div style="margin-top:8px;font-size:13px;">'
               f'{i18n.t(cfg,"cp_indic_diff",lang,"Indicative salary difference")}: '
               f'<b>{("+" if diff>=0 else "−")}{charts.fmt_value(abs(diff), cfg)}</b> '
               f'<span style="color:#8A919D;">({i18n.t(cfg,"cp_indic_note",lang,"mid-to-mid; indicative, not guaranteed")})</span></div>'
               if diff is not None else ""),
            unsafe_allow_html=True)
