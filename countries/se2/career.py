"""Sweden "Career Paths — Beta" tab (curated v0).

Interpretation layer on top of the official SCB statistics — it never changes or
restates them. For the occupation being viewed it shows: the official percentile
curve (published points vs interpolated), a set of Qvistin-estimated career levels
positioned by *actual salary* (each computed live from its OWN SSYK's SCB curve via
core.interp), a simple career map (advance / specialist / leadership / lateral), and
a role comparison. Everything is a clearly-labelled estimate with a confidence tag.

Data: careerpaths.py (curated cp_* register). No AI, no job-ad access at runtime.
See docs/career-paths-assessment.md. Beta-gated + Sweden-only (registered in config
+ core/tabs._BETA_TABS).
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


def _year(cfg, query) -> int:
    ys = query.get("years") or ()
    if ys:
        return max(int(y) for y in ys)
    yr = cfg.capabilities.year_range
    return yr[1] if yr else 2025


def _curves(cfg, ssyks, sex, year, lang):
    """{ssyk: SalaryCurve} + the raw stats frame, from one SCB fetch."""
    from core import interp
    d = cfg.provider.occupation_stats(sector="0", occ_codes=tuple(ssyks), sex=sex,
                                      year=year, years=(year,), lang=lang)
    out = {}
    if d is not None and not d.empty:
        for _, r in d.iterrows():
            out[str(r["occ_code"]).strip()] = interp.curve_from_stats(dict(r))
    return out


def _band_for(title, curves):
    """Attach computed salary band (from the title's own SSYK curve) → dict or None."""
    c = curves.get(str(title.get("primary_ssyk")))
    if not c or not c.ok:
        return None
    return c.band(float(title["lo_pct"]), float(title["mid_pct"]), float(title["hi_pct"]))


def _esc(x):
    return html.escape(str(x)) if x is not None else ""


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
                       "Career Paths currently covers Human Resources and Software & ICT. "
                       "Open an occupation in one of those families (e.g. Software- and system "
                       "developers, or HR specialists) to explore its career map."))
        return

    titles = cp.titles_for_family(fam)
    rels = cp.relationships_for_family(fam)
    by_id = {t["title_id"]: t for t in titles}
    year, sex = _year(cfg, query), query.get("sex", "total")

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
        xs = [p / 2 for p in range(20, 181)]  # 10..90 step .5
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
                                 hovertemplate="P%{x:.0f} · %{y:,.0f} kr (published)<extra></extra>"))
        fig.update_layout(height=300, xaxis_title=i18n.t(cfg, "x_percentile", lang, "Percentile"),
                          yaxis_title=f"{cfg.currency_suffix}{cfg.per_label}", showlegend=True,
                          legend=dict(orientation="h", y=1.15, x=0))
        st.plotly_chart(theme.style_fig(fig), use_container_width=True)
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
                orientation="h", y=[t["name_en"] for t in rows],
                x=[t["_band"]["hi_salary"] - t["_band"]["lo_salary"] for t in rows],
                base=[t["_band"]["lo_salary"] for t in rows],
                marker=dict(color=_TRACK_COLOR[tr], line=dict(width=0)), opacity=0.55,
                name=_TRACK_LABEL[tr],
                customdata=[[t["primary_ssyk"], t["mid_pct"], _CONF_LABEL.get(t["confidence"], t["confidence"]),
                             t["_band"]["mid_salary"]] for t in rows],
                hovertemplate="%{y}<br>SSYK %{customdata[0]} · ~P%{customdata[1]:.0f}"
                              "<br>%{base:,.0f}–%{x:,.0f} kr (mid %{customdata[3]:,.0f})"
                              "<br>%{customdata[2]}<extra></extra>"))
        # mid markers
        fig2.add_trace(go.Scatter(
            orientation="h", y=[t["name_en"] for t in banded],
            x=[t["_band"]["mid_salary"] for t in banded], mode="markers",
            marker=dict(color="#0C1119", size=7, symbol="line-ns-open"),
            showlegend=False, hoverinfo="skip"))
        fig2.update_layout(height=90 + 26 * len(banded), barmode="overlay",
                           xaxis_title=f"{cfg.currency_suffix}{cfg.per_label}",
                           legend=dict(orientation="h", y=1.06, x=0))
        st.plotly_chart(theme.style_fig(fig2), use_container_width=True)

    # Table (accessible fallback + full detail)
    with st.expander(i18n.t(cfg, "cp_table_h", lang, "All roles — detail")):
        import pandas as pd
        rows = []
        for t in sorted(titles, key=lambda x: (mid_salary(x) or 0)):
            b = t.get("_band")
            rows.append({
                i18n.t(cfg, "cp_c_title", lang, "Role"): t["name_en"],
                i18n.t(cfg, "cp_c_level", lang, "Level"): t["level_label"],
                i18n.t(cfg, "cp_c_track", lang, "Track"): _TRACK_LABEL.get(t["track"], t["track"]),
                "SSYK": t["primary_ssyk"],
                i18n.t(cfg, "cp_c_pct", lang, "Est. percentile"): f"P{t['lo_pct']:.0f}–P{t['hi_pct']:.0f}",
                i18n.t(cfg, "cp_c_salary", lang, "Est. salary"):
                    (f"{charts.fmt_value(b['lo_salary'], cfg)}–{charts.fmt_value(b['hi_salary'], cfg)}"
                     if b else "—"),
                i18n.t(cfg, "cp_c_conf", lang, "Evidence"): _CONF_LABEL.get(t["confidence"], t["confidence"]),
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # ═══ 2b · Performance positioning — INTERNAL PREVIEW (not published) ═════
    # Shown only to admins (or if perf_config.enabled_public, which stays false
    # until evidence exists). Illustrative only — never a measure of performance.
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
                opts = {t["name_en"]: t for t in banded}
                sel = st.selectbox(i18n.t(cfg, "cp_perf_level", lang, "Career level"),
                                   list(opts), key=f"{cfg.slug}_cp_perf_sel")
                t = opts[sel]
                vcur = curves.get(str(t["primary_ssyk"]))
                lo_p, hi_p = float(t["lo_pct"]), float(t["hi_pct"])
                import pandas as pd
                # ascending performance ramp (slate → blue → green → gold → amber)
                _PERF_COLORS = ["#9AA7B4", "#6FA8C4", "#5B9E7A", "#D0A72E", "#C77E2A"]
                brows = []
                for i, band in enumerate(bands):
                    p_lo = lo_p + float(band["rel_lo"]) * (hi_p - lo_p)
                    p_hi = lo_p + float(band["rel_hi"]) * (hi_p - lo_p)
                    s_lo = vcur.value_at(p_lo).value if vcur and vcur.ok else None
                    s_hi = vcur.value_at(p_hi).value if vcur and vcur.ok else None
                    brows.append({"label": band["label"], "s_lo": s_lo, "s_hi": s_hi,
                                  "color": _PERF_COLORS[i % len(_PERF_COLORS)],
                                  "within": f"{float(band['rel_lo'])*100:.0f}–{float(band['rel_hi'])*100:.0f}%"})

                # ── Colour-coded salary bar (segment widths ∝ SEK span) ──
                valid = [b for b in brows if b["s_lo"] is not None and b["s_hi"] is not None]
                if valid and (valid[-1]["s_hi"] - valid[0]["s_lo"]) > 0:
                    total = valid[-1]["s_hi"] - valid[0]["s_lo"]
                    segs = "".join(
                        f'<div title="{b["label"]}: {charts.fmt_value(b["s_lo"], cfg)}–'
                        f'{charts.fmt_value(b["s_hi"], cfg)}" style="flex:{max((b["s_hi"]-b["s_lo"])/total*100, 5):.2f};'
                        f'background:{b["color"]};" ></div>' for b in valid)
                    legend = "".join(
                        f'<span style="display:inline-flex;align-items:center;gap:6px;margin:0 14px 4px 0;'
                        f'font-size:12px;color:#5B6472;"><span style="width:12px;height:12px;border-radius:3px;'
                        f'background:{b["color"]};display:inline-block;"></span>{b["label"]}</span>'
                        for b in valid)
                    st.markdown(
                        f'<div style="display:flex;height:44px;border-radius:9px;overflow:hidden;'
                        f'border:1px solid #E7E9ED;">{segs}</div>'
                        f'<div style="display:flex;justify-content:space-between;font-family:'
                        f"'JetBrains Mono',monospace;font-size:11px;color:#98A0AC;margin:5px 0 10px;\">"
                        f'<span>{charts.fmt_value(valid[0]["s_lo"], cfg)}</span>'
                        f'<span>{charts.fmt_value(valid[-1]["s_hi"], cfg)}</span></div>'
                        f'<div style="display:flex;flex-wrap:wrap;">{legend}</div>',
                        unsafe_allow_html=True)

                # ── Table (kept) ──
                st.dataframe(pd.DataFrame([{
                    i18n.t(cfg, "cp_perf_pos", lang, "Position"): b["label"],
                    i18n.t(cfg, "cp_perf_within", lang, "Within level"): b["within"],
                    i18n.t(cfg, "cp_perf_sal", lang, "Illustrative salary"):
                        (f"{charts.fmt_value(b['s_lo'], cfg)}–{charts.fmt_value(b['s_hi'], cfg)}"
                         if b["s_lo"] is not None else "—"),
                } for b in brows]), hide_index=True, use_container_width=True)
                st.caption(i18n.t(cfg, "cp_perf_note", lang,
                                  "Internal preview — not shown to users. Public release requires "
                                  "individual-level, consented compensation evidence we do not have."))

    # ═══ 3 · Career map from the viewed occupation ═══════════════════════════
    st.markdown(f"#### {i18n.t(cfg, 'cp_map_h', lang, 'Where can this role lead?')}")
    from_ids = {t["title_id"] for t in titles if str(t["primary_ssyk"]) == primary}
    out_rels = [r for r in rels if r["from_title"] in from_ids]
    if not out_rels:
        # fall back to the whole family's progression if the exact SSYK has no mapped moves
        out_rels = [r for r in rels if r["rel_type"] == "progression"]
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
            frm = by_id.get(r["from_title"])
            if not to:
                continue
            b = to.get("_band")
            diff = None
            if b and frm and frm.get("_band"):
                diff = b["mid_salary"] - frm["_band"]["mid_salary"]
            ssyk_badge = ("↔ same SSYK" if r["same_ssyk"] else f"→ SSYK {to['primary_ssyk']}")
            sal = (f"{charts.fmt_value(b['lo_salary'], cfg)}–{charts.fmt_value(b['hi_salary'], cfg)}"
                   if b else "—")
            diff_html = ""
            if diff is not None:
                sign = "+" if diff >= 0 else "−"
                color = "#1B8A5A" if diff >= 0 else "#C0453A"
                diff_html = (f'<div style="font-size:12px;color:{color};font-weight:600;margin-top:4px;">'
                             f'{sign}{charts.fmt_value(abs(diff), cfg)} {i18n.t(cfg,"cp_vs",lang,"vs current (indicative)")}</div>')
            gaps = ", ".join((r.get("skill_gaps") or [])[:3])
            with cols[i % len(cols)]:
                st.markdown(
                    f'<div style="border:1px solid #E7E9ED;border-radius:12px;padding:13px 15px;'
                    f'margin-bottom:10px;background:#fff;">'
                    f'<div style="font-weight:700;font-size:14.5px;color:#0C1119;">{_esc(to["name_en"])}</div>'
                    f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10.5px;color:#98A0AC;'
                    f'margin:3px 0 8px;">{_esc(to["level_label"])} · {_esc(ssyk_badge)} · '
                    f'{_esc(_CONF_LABEL.get(to["confidence"], to["confidence"]))}</div>'
                    f'<div style="font-size:13px;color:#26303C;">{sal}</div>'
                    f'{diff_html}'
                    + (f'<div style="font-size:12px;color:#5B6472;margin-top:6px;">'
                       f'{i18n.t(cfg,"cp_gaps",lang,"Typical gaps")}: {_esc(gaps)}</div>' if gaps else "")
                    + '</div>', unsafe_allow_html=True)
    if not shown_any:
        st.caption(i18n.t(cfg, "cp_no_moves", lang, "No mapped moves for this occupation yet."))

    # ═══ 4 · Compare two roles ═══════════════════════════════════════════════
    with st.expander(i18n.t(cfg, "cp_compare_h", lang, "Compare two roles")):
        names = {t["name_en"]: t for t in titles}
        c1, c2 = st.columns(2)
        a = c1.selectbox(i18n.t(cfg, "cp_current", lang, "Current role"), list(names),
                         key=f"{cfg.slug}_cp_a")
        b_name = c2.selectbox(i18n.t(cfg, "cp_next", lang, "Possible next role"), list(names),
                              index=min(1, len(names) - 1), key=f"{cfg.slug}_cp_b")
        ta, tb = names[a], names[b_name]

        def cell(t):
            bd = t.get("_band")
            return (f"SSYK {t['primary_ssyk']} · {_TRACK_LABEL.get(t['track'], t['track'])}<br>"
                    f"{t['level_label']}<br>P{t['lo_pct']:.0f}–P{t['hi_pct']:.0f}<br>"
                    + (f"{charts.fmt_value(bd['lo_salary'], cfg)}–{charts.fmt_value(bd['hi_salary'], cfg)}"
                       if bd else "—")
                    + f"<br>{_CONF_LABEL.get(t['confidence'], t['confidence'])}")
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
