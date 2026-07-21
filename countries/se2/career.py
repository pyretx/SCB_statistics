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

import datetime as _dt
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


def _subcode(t):
    """Human-readable {SSYK}-{n} sub-code (e.g. 4112-1) for a role that has one;
    "" for the older curated roles that use a slug id. The official SSYK is never
    changed — this is an additive sub-index off the official code."""
    tid = str(t.get("title_id", ""))
    a, sep, b = tid.partition("-")
    return tid if (sep and len(a) == 4 and a.isdigit() and b.isdigit()) else ""


def _chips(items, color, bg):
    return " ".join(
        f'<span style="display:inline-block;padding:2px 9px;margin:2px 4px 2px 0;border-radius:20px;'
        f'background:{bg};color:{color};font-size:12px;line-height:1.7;">{_esc(x)}</span>'
        for x in items if x)


def _tile(label, value, sub=""):
    return (f'<div style="border:1px solid #E7E9ED;border-radius:16px;background:#fff;'
            f'padding:15px 17px;box-shadow:0 1px 2px rgba(16,21,31,.04);height:100%;box-sizing:border-box;">'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;letter-spacing:.05em;'
            f'text-transform:uppercase;color:#98A0AC;">{label}</div>'
            f'<div style="font-size:21px;font-weight:700;color:#0C1119;margin-top:6px;line-height:1.2;">{value}</div>'
            + (f'<div style="font-size:12px;color:#5B6472;margin-top:3px;">{sub}</div>' if sub else "")
            + '</div>')


def _chip_card(label, chips_html):
    if not chips_html:
        return ""
    return (f'<div style="border:1px solid #E7E9ED;border-radius:16px;background:#fff;'
            f'padding:15px 17px;box-shadow:0 1px 2px rgba(16,21,31,.04);margin-bottom:12px;">'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;letter-spacing:.05em;'
            f'text-transform:uppercase;color:#98A0AC;margin-bottom:9px;">{label}</div>'
            + chips_html + '</div>')


# ── Interactive career map — bidirectional Streamlit component ────────────────
# The HTML/CSS/JS lives in career_map/index.html and speaks the raw component
# protocol: payload in via streamlit:render, {title_id, kind} back to Python on
# node/member clicks (so e.g. the Live market signal picker can follow), frame
# height self-reported. See tests/career_map_harness.py for a login-free test.
_MAP_COMPONENT = None


def _map_component():
    global _MAP_COMPONENT
    if _MAP_COMPONENT is None:
        import os
        import streamlit.components.v1 as components
        _MAP_COMPONENT = components.declare_component(
            "se2_career_map", path=os.path.join(os.path.dirname(__file__), "career_map"))
    return _MAP_COMPONENT

def _render_career_map(cfg, lang, primary, occ_name, titles, rels, by_id, curves, evidence):
    """Interactive, data-driven career map (embedded component) — replaces the old
    card list. Node = a role the viewed occupation can lead to, coloured by move
    type, positioned by estimated salary midpoint, badged with its live ad count.
    Clicking a node reveals its range, gaps and (in red) the job-ad requirements +
    Platsbanken references. Returns the last-clicked role's title_id (graph node
    or sub-cluster member) — None until something is clicked."""
    yrs = i18n.t(cfg, "cp_ms_yrs", lang, "yrs")
    bc = curves.get(primary)
    base_mid = bc.value_at(50).value if bc and bc.ok else None
    c_lo = bc.value_at(25).value if bc and bc.ok else None
    c_hi = bc.value_at(75).value if bc and bc.ok else None

    rel_color = {"progression": "#0A63A6", "specialist": "#5B8A72", "management": "#B26A00",
                 "leadership": "#B26A00", "lateral": "#8A919D", "entry": "#5B6472", "related": "#5B6472"}
    _leg_lbl = {
        "progression": i18n.t(cfg, "cp_rel_progression", lang, "Advance within this occupation"),
        "specialist": i18n.t(cfg, "cp_rel_specialist", lang, "Specialist move"),
        "management": i18n.t(cfg, "cp_rel_leadership", lang, "Move into leadership"),
        "leadership": i18n.t(cfg, "cp_rel_leadership", lang, "Move into leadership"),
        "lateral": i18n.t(cfg, "cp_rel_lateral", lang, "Related lateral moves"),
        "entry": i18n.t(cfg, "cp_rel_entry", lang, "Entry route"),
        "related": i18n.t(cfg, "cp_rel_related", lang, "Related move"),
    }

    # ── Full family graph: every role a node, every relationship an edge.
    # The component re-centres client-side on click (Option A), so we ship the
    # whole graph once — bands + ad evidence precomputed for every role. ──
    roles = {}
    for t in titles:
        b = t.get("_band")
        if not b:
            continue
        if t.get("sub_track"):
            continue  # rendered as a sub-cluster card below, not a graph node
        ev = evidence.get(t["title_id"]) or {}
        exp = (ev.get("common_experience") or [])
        ym = exp[0].get("years_median") if exp else None
        edu = (ev.get("common_education") or [])
        roles[t["title_id"]] = {
            "name": _tname(t, lang), "subcode": _subcode(t),
            "level": _level(t["level_label"], lang), "conf": _conf(cfg, lang, t["confidence"]),
            "ssyk": str(t["primary_ssyk"]),
            "lo": round(b["lo_salary"]), "mid": round(b["mid_salary"]), "hi": round(b["hi_salary"]),
            "ad_count": int(ev.get("ad_count") or 0),
            "skills": [s.get("skill") for s in (ev.get("common_skills") or [])[:8]],
            "education": (edu[0]["label"] if edu else None),
            "experience": (f"{ym}+ {yrs}" if ym is not None else None),
        }
    edges = []
    for r in rels:
        if r["from_title"] in roles and r["to_title"] in roles:
            edges.append({"from": r["from_title"], "to": r["to_title"], "rel": r["rel_type"],
                          "same_ssyk": bool(r.get("same_ssyk")), "gaps": (r.get("skill_gaps") or [])[:4],
                          "color": rel_color.get(r["rel_type"], "#5B6472")})
    # ── Specialisation sub-clusters: family titles flagged with a sub_track are
    # collapsed into one card per group (and hidden from the graph above) so the
    # promotion spine stays clean. Each member's ad count is the PER-TITLE count
    # from cp_raw_title_map (ads whose normalised title matched that role) — NOT
    # the SSYK+seniority bucket count, which is identical across every title at
    # that level and would show e.g. "240 ads" six times. The group headline is
    # then a real sum of distinct per-title counts. ──
    try:
        import careerpaths_v1 as _cpv1
        _raw = _cpv1.raw_title_map()
    except Exception:
        _raw = []
    _raw_by: dict[tuple, int] = {}
    for _r in _raw:
        _k = (str(_r.get("ssyk")), (_r.get("raw_title") or "").strip().lower())
        _raw_by[_k] = _raw_by.get(_k, 0) + int(_r.get("ad_count") or 0)

    _groups: dict[str, dict] = {}
    for t in titles:
        st_ = t.get("sub_track")
        b = t.get("_band")
        if not st_ or not b:
            continue
        ev = evidence.get(t["title_id"]) or {}
        exp = (ev.get("common_experience") or [])
        ym = exp[0].get("years_median") if exp else None
        edu = (ev.get("common_education") or [])
        _ssyk = str(t["primary_ssyk"])
        _names = {(t.get("name_en") or "").strip().lower()}
        for _v in (t.get("raw_variants") or []):
            _names.add((_v or "").strip().lower())
        _rc = sum(_raw_by.get((_ssyk, nm), 0) for nm in _names if nm)
        # A group hangs off a spine node (sub_track_anchor = its title_id) or, by
        # default, off the entry occupation (the centre). An anchor that isn't a
        # rendered graph node falls back to the centre.
        _anchor = t.get("sub_track_anchor") or "center"
        g = _groups.setdefault(st_, {"members": [], "anchor": _anchor})
        g["members"].append({
            "title_id": t["title_id"],
            "name": _tname(t, lang), "subcode": _subcode(t),
            "level": _level(t["level_label"], lang), "conf": _conf(cfg, lang, t["confidence"]),
            "ssyk": _ssyk,
            "same_ssyk": _ssyk == str(primary),
            "lo": round(b["lo_salary"]), "mid": round(b["mid_salary"]), "hi": round(b["hi_salary"]),
            "diff": (round(b["mid_salary"] - base_mid) if base_mid is not None else None),
            "ad_count": _rc,
            "skills": [s.get("skill") for s in (ev.get("common_skills") or [])[:8]],
            "education": (edu[0]["label"] if edu else None),
            "experience": (f"{ym}+ {yrs}" if ym is not None else None),
        })
    subgroups = []
    for label, gd in _groups.items():
        members = sorted(gd["members"], key=lambda m: -(m["mid"] or 0))
        anchor = gd["anchor"] if gd["anchor"] in roles else "center"
        subgroups.append({"label": label, "anchor": anchor, "count": len(members),
                          "ad_count": sum(m["ad_count"] for m in members),
                          "members": members})
    subgroups.sort(key=lambda g: -(g["members"][0]["mid"] if g["members"] else 0))

    from_ids = [t["title_id"] for t in titles
                if str(t["primary_ssyk"]) == primary and t["title_id"] in roles]

    # ── Longest-path layering over the forward sub-graph from the occupation's
    # roles → each role gets a level (min hops), so the component can show N
    # levels at once instead of click-drilling. Entry roles = layer 0 (the centre). ──
    from collections import deque
    adj = {}
    for e in edges:
        adj.setdefault(e["from"], []).append(e["to"])
    inset = set(from_ids)
    stack = list(from_ids)
    while stack:
        u = stack.pop()
        for v in adj.get(u, []):
            if v in roles and v not in inset:
                inset.add(v); stack.append(v)
    indeg = {n: 0 for n in inset}
    for e in edges:
        if e["from"] in inset and e["to"] in inset:
            indeg[e["to"]] += 1
    dq = deque([n for n in inset if indeg[n] == 0])
    indeg2 = dict(indeg); topo = []
    while dq:
        u = dq.popleft(); topo.append(u)
        for v in adj.get(u, []):
            if v in inset:
                indeg2[v] -= 1
                if indeg2[v] == 0:
                    dq.append(v)
    layer = {n: 0 for n in inset}; parent = {}
    for u in topo:
        for v in adj.get(u, []):
            if v in inset and layer[u] + 1 > layer[v]:
                layer[v] = layer[u] + 1; parent[v] = u
    center_ids = [n for n in inset if layer[n] == 0]
    node_ids = [n for n in inset if layer[n] >= 1]
    if not node_ids:
        st.markdown(f"#### {i18n.t(cfg, 'cp_map_h', lang, 'Where can this role lead?')}")
        st.caption(i18n.t(cfg, "cp_no_moves", lang, "No mapped moves for this occupation yet."))
        return
    max_layer = max(layer[n] for n in node_ids)

    present = {e["rel"] for e in edges if e["to"] in set(node_ids)}
    legend, _seen = [], set()
    for _rt in ["progression", "specialist", "management", "leadership", "lateral", "entry", "related"]:
        _lbl = _leg_lbl.get(_rt)
        if _rt in present and _lbl and _lbl not in _seen:
            legend.append({"color": rel_color.get(_rt, "#5B6472"), "label": _lbl,
                           "dashed": _rt in ("lateral", "related")})
            _seen.add(_lbl)

    payload = {
        "occupation": {"name": occ_name, "ssyk": str(primary),
                       "base_mid": (round(base_mid) if base_mid else None),
                       "lo": (round(c_lo) if c_lo else None), "hi": (round(c_hi) if c_hi else None)},
        "roles": roles, "edges": edges, "legend": legend, "rellabels": _leg_lbl,
        "layer": layer, "parent": parent, "center_ids": center_ids, "max_layer": max_layer,
        "subgroups": subgroups,
        "labels": {
            "eyebrow": "CAREER PATHS · " + i18n.t(cfg, "cp_map_h", lang, "Where can this role lead?").upper(),
            "title": i18n.t(cfg, "cp_map_from", lang, "Paths from {r}"),
            "subtitle": f"{occ_name} · SSYK {primary} · "
                        + i18n.t(cfg, "cp_map_axis", lang, "positions reflect estimated salary midpoints"),
            "you_here": i18n.t(cfg, "cp_you_here", lang, "YOU ARE HERE"),
            "levels_lbl": i18n.t(cfg, "cp_map_levels", lang, "Steps to show:"),
            "ads": i18n.t(cfg, "cp_ads", lang, "ads"),
            "sub_roles": i18n.t(cfg, "cp_sub_roles", lang, "roles"),
            "specialisations": i18n.t(cfg, "cp_specialisations", lang, "specialisations"),
            "range": i18n.t(cfg, "cp_ms_range", lang, "Estimated range"),
            "vs": i18n.t(cfg, "cp_vs", lang, "vs occupation median (indicative)"),
            "gaps": i18n.t(cfg, "cp_gaps", lang, "Typical gaps to close"),
            "same_ssyk": i18n.t(cfg, "cp_same_ssyk", lang, "↔ same SSYK"),
            "ads_header": i18n.t(cfg, "cp_ms_fromads", lang, "FROM JOB ADS"),
            "experience": i18n.t(cfg, "cp_ms_exp", lang, "Typical experience"),
            "education": i18n.t(cfg, "cp_ms_edu", lang, "Top education req."),
            "skills": i18n.t(cfg, "cp_skills", lang, "Skills"),
            "no_ads": i18n.t(cfg, "cp_ms_none", lang, "No live job-ad signal for this role yet."),
            "hint": i18n.t(cfg, "cp_map_hint3", lang,
                           "Pick how many steps to show, hover a role to trace its path, "
                           "and click one for its live job-ad requirements."),
            "pick": i18n.t(cfg, "cp_map_pick", lang, "Click a role to see its detail and job-ad requirements."),
        },
    }
    # Bidirectional component: renders the map AND returns the last-clicked
    # role ({title_id, kind}) so the caller can sync downstream sections.
    # Frame height is self-reported by the component (ResizeObserver).
    sel_val = _map_component()(data=payload, key=f"{cfg.slug}_cp_map", default=None)
    return sel_val.get("title_id") if isinstance(sel_val, dict) else None


def _render_role_cards(cfg, lang, primary, titles, rels, by_id, curves, evidence):
    """Grouped role cards (Advance within / Specialist / Leadership / Lateral) —
    the classic list view, kept just above the compare section for a scannable
    text breakdown alongside the interactive map above."""
    st.markdown(f"#### {i18n.t(cfg, 'cp_cards_h', lang, 'Roles this can lead to')}")
    from_ids = {t["title_id"] for t in titles if str(t["primary_ssyk"]) == primary}
    out_rels = [r for r in rels if r["from_title"] in from_ids] or \
               [r for r in rels if r["rel_type"] == "progression"]
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
                             f'{sign}{charts.fmt_value(abs(diff), cfg)} '
                             f'{i18n.t(cfg,"cp_vs",lang,"vs occupation median (indicative)")}</div>')
            gaps = ", ".join((r.get("skill_gaps") or [])[:3])
            ev = evidence.get(to["title_id"])
            ev_html = ""
            if ev:
                sk = _ev_skills(ev, 3)
                sk_html = (f'<div style="font-size:12px;color:#5B6472;margin-top:4px;">'
                           f'{i18n.t(cfg,"cp_ev_skills",lang,"In-demand skills")}: '
                           f'{_esc(", ".join(sk))}</div>' if sk else "")
                ev_html = (f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
                           f'color:#1B8A5A;margin-top:8px;">{_esc(_ev_ads(cfg, lang, ev))}</div>' + sk_html)
            sc = _subcode(to)
            code_badge = (f'<span style="color:#0A63A6;font-weight:600;">{_esc(sc)}</span> · ' if sc else "")
            with cols[i % len(cols)]:
                st.markdown(
                    f'<div style="border:1px solid #E7E9ED;border-radius:12px;padding:13px 15px;'
                    f'margin-bottom:10px;background:#fff;">'
                    f'<div style="font-weight:700;font-size:14.5px;color:#0C1119;">{_esc(_tname(to, lang))}</div>'
                    f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10.5px;color:#98A0AC;'
                    f'margin:3px 0 8px;">{code_badge}{_esc(_level(to["level_label"], lang))} · {_esc(ssyk_badge)} · '
                    f'{_esc(_conf(cfg, lang, to["confidence"]))}</div>'
                    f'<div style="font-size:13px;color:#26303C;">{sal}</div>'
                    f'{diff_html}'
                    + (f'<div style="font-size:12px;color:#5B6472;margin-top:6px;">'
                       f'{i18n.t(cfg,"cp_gaps",lang,"Typical gaps")}: {_esc(gaps)}</div>' if gaps else "")
                    + ev_html + '</div>', unsafe_allow_html=True)
    if not shown_any:
        st.caption(i18n.t(cfg, "cp_no_moves", lang, "No mapped moves for this occupation yet."))


def _market_from_ads(t, ad_rows):
    """Per-ROLE market-signal aggregate from the ads whose normalised title
    matches this role (name_en + raw_variants) in its SSYK — NOT the SSYK+
    seniority bucket, which is identical across every title at that level. This
    is what makes 'Recruiter' show recruiter ads and a recruiter-specific count.
    Returns None when no ad matches the role."""
    from collections import Counter
    names = {(t.get("name_en") or "").strip().lower()}
    for v in (t.get("raw_variants") or []):
        names.add((v or "").strip().lower())
    m = [a for a in ad_rows if (a.get("norm_title") or "").strip().lower() in names]
    if not m:
        return None
    skills = Counter(x for a in m for x in (a.get("skills") or []))
    certs = Counter(x for a in m for x in (a.get("certs") or []))
    langs = Counter(x for a in m for x in (a.get("languages") or []))
    edu = Counter(a.get("education") for a in m if a.get("education"))
    emp = Counter(a.get("employer") for a in m if a.get("employer"))
    yrs = sorted(a["years"] for a in m if isinstance(a.get("years"), int))
    n = len(m)
    ex = sorted(m, key=lambda a: (a.get("publication_date") or ""), reverse=True)[:12]
    return {
        "ad_count": n,
        "evidence_strength": "strong" if n >= 20 else "moderate" if n >= 8 else "limited",
        "mgmt_freq": sum(1 for a in m if a.get("mgmt")) / n,
        "common_experience": ([{"years_median": yrs[len(yrs) // 2]}] if yrs else []),
        "common_education": [{"label": l, "freq": c} for l, c in edu.most_common(6)],
        "common_skills": [{"skill": s, "freq": c} for s, c in skills.most_common(12)],
        "common_certs": [{"label": l, "freq": c} for l, c in certs.most_common(6)],
        "common_languages": [{"label": l, "freq": c} for l, c in langs.most_common(6)],
        "top_employers": [{"name": e, "freq": c} for e, c in emp.most_common(8)],
        "example_ads": [{"headline": a.get("headline"), "employer": a.get("employer"),
                         "region": a.get("region"), "deadline": a.get("deadline"),
                         "url": a.get("url"), "id": a.get("ad_id")} for a in ex],
    }


def _render_market_signal_section(cfg, lang, titles, evidence, primary, preselect=None):
    """Bottom-of-page 'Live market signal' — tiled (app card style) with a regional
    slicer on the example ads. Per-role signal is aggregated from the ads whose
    normalised title actually matches that role (see _market_from_ads), so the
    count and example ads are role-specific. A segmented-control pills row
    scopes the role dropdown to one specialisation cluster at a time."""
    from collections import Counter, defaultdict
    import careerpaths_v1 as cpv1

    ads_by_ssyk = {s: cpv1.ad_class_for_ssyk(s) for s in {str(t["primary_ssyk"]) for t in titles}}
    mkt = {}
    for t in titles:
        m = _market_from_ads(t, ads_by_ssyk.get(str(t["primary_ssyk"]), []))
        if m:
            mkt[t["title_id"]] = m
    ev_titles = [t for t in titles if mkt.get(t["title_id"])]
    if not ev_titles:
        return
    st.markdown("---")
    st.markdown(f"#### {i18n.t(cfg, 'cp_ms_h', lang, 'Live market signal (from current job ads)')}")
    st.caption(i18n.t(cfg, "cp_ms_cap", lang,
                      "What current Swedish job ads for these roles actually ask for. Aggregated from "
                      "public ads (Arbetsförmedlingen / JobTech, CC BY-SA) — indicative, not official, "
                      "and it does not change the SCB salary figures above."))

    # ── Group scoping: a pills row (the app's segmented-control style) narrows
    # the role dropdown to one cluster at a time, so option labels are just
    # "Role · N ads" — no category prefixes, no internal subcodes. "Main roles"
    # = the ungrouped spine; each sub_track cluster gets its own pill. Families
    # without clusters render no pills row at all. ──
    _n = lambda t: mkt[t["title_id"]]["ad_count"]
    ungrouped = sorted([t for t in ev_titles if not t.get("sub_track")], key=lambda t: -_n(t))
    cats: dict = defaultdict(list)
    for t in ev_titles:
        if t.get("sub_track"):
            cats[t["sub_track"]].append(t)
    groups = []
    if ungrouped:
        groups.append((i18n.t(cfg, "cp_ms_main", lang, "Main roles"), ungrouped))
    for c in sorted(cats, key=lambda c: -max(_n(x) for x in cats[c])):
        groups.append((c, sorted(cats[c], key=lambda t: -_n(t))))
    by_pill = {f"{lbl} · {len(ts)}": ts for lbl, ts in groups}
    pills = list(by_pill)
    grp_key = f"{cfg.slug}_cp_ms_grp"

    # ── Map-click sync: when the career map above reports a newly clicked role,
    # point the pill + role dropdown at it ONCE (tracked via _synced) — after
    # that the user browses freely until the next map click. Widget state is
    # seeded via session_state before instantiation (no default/index params),
    # which is the warning-free way to drive Streamlit widgets. ──
    if preselect and st.session_state.get(f"{grp_key}_synced") != preselect:
        for pill, ts in by_pill.items():
            idx = next((i for i, x in enumerate(ts) if x["title_id"] == preselect), None)
            if idx is not None:
                st.session_state[f"{grp_key}_synced"] = preselect
                st.session_state[grp_key] = pill
                st.session_state[f"{cfg.slug}_cp_ms_role_{pill}"] = idx
                break

    if len(pills) > 1:
        if st.session_state.get(grp_key) not in by_pill:
            st.session_state[grp_key] = pills[0]
        pick = st.segmented_control(
            i18n.t(cfg, "cp_ms_grp", lang, "Role group"), pills,
            key=grp_key, label_visibility="collapsed")
        pick = pick if pick in by_pill else pills[0]   # deselect → back to default
    else:
        pick = pills[0]
    scoped = by_pill[pick]

    ads_word = i18n.t(cfg, "cp_ads", lang, "ads")
    role_key = f"{cfg.slug}_cp_ms_role_{pick}"
    if st.session_state.get(role_key) not in range(len(scoped)):
        # first visit to this pill → default to the viewed occupation's own role
        st.session_state[role_key] = next(
            (i for i, x in enumerate(scoped)
             if str(x.get("primary_ssyk")) == primary and not x.get("sub_track")), 0)
    c_role, c_reg = st.columns([2, 1])
    # per-group widget key → each pill remembers its own role selection
    sel_i = c_role.selectbox(
        i18n.t(cfg, "cp_ms_role", lang, "Show role"), list(range(len(scoped))),
        format_func=lambda i: f"{_tname(scoped[i], lang)} · {_n(scoped[i])} {ads_word}",
        key=role_key)
    t = scoped[sel_i]
    e = mkt[t["title_id"]]
    # Show only still-open ads: once the application deadline passes the
    # Platsbanken link dies, so we hide the ad from users (it stays in our own
    # store for history). Ads without a deadline are treated as open.
    _today = _dt.date.today().isoformat()
    exa = [a for a in (e.get("example_ads") or [])
           if (not a.get("deadline")) or str(a.get("deadline"))[:10] >= _today]

    # regional slicer — options from this role's example ads (region mix)
    reg_counts = Counter(a.get("region") for a in exa if a.get("region"))
    all_reg = i18n.t(cfg, "cp_ms_allreg", lang, "All regions")
    reg_opts = [all_reg] + [r for r, _ in reg_counts.most_common()]
    reg_sel = c_reg.selectbox(i18n.t(cfg, "cp_ms_region", lang, "Region"), reg_opts,
                              key=f"{cfg.slug}_cp_ms_region")

    exp = (e.get("common_experience") or [])
    ym = exp[0].get("years_median") if exp else None
    edu_top = (e.get("common_education") or [])
    # ── Stat tiles (app card style, equal height via a stretch grid) ──
    tiles_html = (
        _tile(i18n.t(cfg, "cp_ms_ads_t", lang, "Live ads"), f"{int(e.get('ad_count') or 0)}",
              _ev_strength(cfg, lang, e.get("evidence_strength")))
        + _tile(i18n.t(cfg, "cp_ms_exp", lang, "Typical experience"),
                (f"{ym}+ {i18n.t(cfg, 'cp_ms_yrs', lang, 'yrs')}" if ym is not None else "—"))
        + _tile(i18n.t(cfg, "cp_ms_edu", lang, "Top education req."),
                (edu_top[0]["label"] if edu_top else "—"))
        + _tile(i18n.t(cfg, "cp_ms_mgmt", lang, "People management"),
                f"{round((e.get('mgmt_freq') or 0) * 100)}%"))
    st.markdown('<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;'
                'align-items:stretch;margin-bottom:12px;">' + tiles_html + '</div>',
                unsafe_allow_html=True)

    def chips(items, color, bg):
        return _chips([x for x in items if x], color, bg)

    st.markdown(_chip_card(
        i18n.t(cfg, "cp_ev_skills", lang, "In-demand skills"),
        chips([s.get("skill") for s in (e.get("common_skills") or [])[:12]], "#0A63A6", "rgba(10,99,166,.08)")),
        unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    cc1.markdown(_chip_card(
        i18n.t(cfg, "cp_ms_certs", lang, "Certifications / licences"),
        chips([s.get("label") for s in (e.get("common_certs") or [])[:6]], "#7A4FB0", "rgba(122,79,176,.08)")
        or f'<span style="font-size:12px;color:#98A0AC;">—</span>'), unsafe_allow_html=True)
    cc2.markdown(_chip_card(
        i18n.t(cfg, "cp_ms_langs", lang, "Languages"),
        chips([s.get("label") for s in (e.get("common_languages") or [])[:6]], "#1B8A5A", "rgba(27,138,90,.08)")
        or f'<span style="font-size:12px;color:#98A0AC;">—</span>'), unsafe_allow_html=True)
    st.markdown(_chip_card(
        i18n.t(cfg, "cp_ms_emp", lang, "Recent hiring employers"),
        chips([s.get("name") for s in (e.get("top_employers") or [])[:8]], "#5B6472", "rgba(91,100,114,.08)")),
        unsafe_allow_html=True)

    # ── Example ads (region-filtered; `exa` is already open-only) ──
    shown = [a for a in exa if reg_sel == all_reg or a.get("region") == reg_sel]
    reg_mix = " · ".join(f"{r} ({n})" for r, n in reg_counts.most_common()) if reg_counts else ""
    li = ""
    for a in shown:
        dl = a.get("deadline")
        meta = " · ".join(x for x in [
            _esc(a.get("employer")) if a.get("employer") else None,
            _esc(a.get("region")) if a.get("region") else None,
            (i18n.t(cfg, "cp_ms_dl", lang, "apply by {d}").format(d=_esc(dl)) if dl else None),
            f'{i18n.t(cfg, "cp_ms_ref", lang, "ref")} {_esc(a.get("id"))}'] if x)
        href = a.get("url") or "#"
        li += (f'<li style="margin-bottom:8px;"><a href="{_esc(href)}" target="_blank" '
               f'style="color:#0A63A6;text-decoration:none;font-weight:600;">'
               f'{_esc(a.get("headline") or href)}</a>'
               f'<div style="font-size:11px;color:#98A0AC;">{meta}</div></li>')
    body = (f'<ul style="margin:2px 0 0;padding-left:18px;">{li}</ul>'
            if li else f'<span style="font-size:12px;color:#98A0AC;">'
                       f'{i18n.t(cfg, "cp_ms_noreg", lang, "No example ads for this region.")}</span>')
    label = i18n.t(cfg, "cp_ms_ex", lang, "Example ads · Platsbanken references")
    if reg_mix:
        label += f'  <span style="text-transform:none;letter-spacing:0;color:#98A0AC;">· {_esc(reg_mix)}</span>'
    st.markdown(_chip_card(label, body), unsafe_allow_html=True)
    st.caption(i18n.t(cfg, "cp_ms_expire", lang,
                      "Links open the ad on Platsbanken and expire after the application deadline."))


def quick_access(cfg, lang, query):
    """Quick access to a career path (empty landing + the tab's empty states):
    pick a published career family, then jump straight into its map via the
    standard confirm dialog — pre-seeded with the family's core SSYK (changeable,
    but limited to the family so the landing occupation is always covered), all
    sectors and both genders. Beta-gated exactly like the tab itself."""
    import careerpaths as cp
    from core import access, panels
    if not access.is_beta_or_admin(cfg):
        return
    titles = cp.public_titles()
    fam_ids = sorted({t.get("family_id") for t in titles if t.get("family_id")})
    if not fam_ids:
        return
    names = cp.family_names()

    def fname(fid):
        r = names.get(fid, {})
        return ((r.get("sv") or r.get("en") or fid) if lang == "SV"
                else (r.get("en") or r.get("sv") or fid))

    st.markdown(
        '<div style="margin:2px 0 4px;">'
        '<span style="font-family:\'JetBrains Mono\',monospace;font-size:10.5px;font-weight:600;'
        'letter-spacing:.06em;color:#B26A00;background:rgba(178,106,0,.13);padding:2px 8px;'
        'border-radius:5px;">CAREER PATHS · BETA</span></div>', unsafe_allow_html=True)
    st.subheader(i18n.t(cfg, "cpqa_h", lang, "Quick access to a career path"))
    st.caption(i18n.t(cfg, "cpqa_cap", lang,
                      "Pick a career family and jump straight into its career map — "
                      "we suggest a typical occupation (changeable), across all "
                      "sectors and both genders."))
    c1, c2 = st.columns([2.2, 1], vertical_alignment="bottom")
    fam = c1.selectbox(i18n.t(cfg, "cpqa_family", lang, "Career path"), fam_ids,
                       format_func=fname, key=f"{cfg.slug}_cpqa_fam")
    if c2.button(i18n.t(cfg, "cpqa_btn", lang, "Explore career path"), type="primary",
                 use_container_width=True, key=f"{cfg.slug}_cpqa_go"):
        ft = sorted([t for t in titles
                     if t.get("family_id") == fam and t.get("primary_ssyk")],
                    key=lambda t: t.get("level_index") or 0)
        if not ft:
            return
        try:
            occ_names = cfg.provider.occupations(lang) or {}
        except Exception:
            occ_names = {}
        options = {c: occ_names.get(c, c)
                   for c in sorted({str(t["primary_ssyk"]) for t in ft})}
        # Suggested SSYK: the middle rung of the family's IC ladder — a
        # mid-career "Professional" core occupation, not an entry/aide code
        # (count-based picks land on aides: one SSYK holds many junior rungs).
        core = [t for t in ft if t.get("track") == "ic"] or ft
        suggested = str(core[len(core) // 2]["primary_ssyk"])
        caps = cfg.capabilities
        qa_query = {**query, "sector": (caps.sectors[0] if caps.sectors else ""),
                    "sex": "total"}                 # all sectors + both genders
        panels.open_confirm(cfg, lang, qa_query, suggested, options[suggested],
                            occ_options=options, target_tab="career")


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
        quick_access(cfg, lang, query)           # one-click way in, not a dead end
        return
    primary = occ_codes[0]
    fam = cp.family_for_ssyk(primary)
    if not fam:
        _names = cp.family_names()
        _covered = sorted(filter(None, {
            ((_names.get(fid, {}).get("sv") or _names.get(fid, {}).get("en")) if lang == "SV"
             else (_names.get(fid, {}).get("en") or _names.get(fid, {}).get("sv")))
            for fid in {t.get("family_id") for t in cp.public_titles()}}))
        st.info(i18n.t(cfg, "cp_uncovered", lang,
                       "Career Paths currently covers {n} professional families: {list}. "
                       "Open an occupation in one of those to explore its career map.")
                .format(n=len(_covered), list=", ".join(_covered)))
        quick_access(cfg, lang, query)           # one-click way in, not a dead end
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

    _has_code = any(_subcode(t) for t in titles)
    with st.expander(i18n.t(cfg, "cp_table_h", lang, "All roles — detail")):
        import pandas as pd
        rows = []
        for t in sorted(titles, key=lambda x: (mid_salary(x) or 0)):
            b = t.get("_band")
            rows.append({
                i18n.t(cfg, "cp_c_title", lang, "Role"): _tname(t, lang),
                **({i18n.t(cfg, "cp_c_code", lang, "Code"): (_subcode(t) or "—")} if _has_code else {}),
                i18n.t(cfg, "cp_c_level", lang, "Level"): _level(t["level_label"], lang),
                i18n.t(cfg, "cp_c_track", lang, "Track"): _track(cfg, lang, t["track"]),
                "SSYK": t["primary_ssyk"],
                i18n.t(cfg, "cp_c_pct", lang, "Est. percentile"): f"P{t['lo_pct']:.0f}–P{t['hi_pct']:.0f}",
                i18n.t(cfg, "cp_c_salary", lang, "Est. salary"):
                    (f"{charts.fmt_value(b['lo_salary'], cfg)}–{charts.fmt_value(b['hi_salary'], cfg)}"
                     if b else "—"),
                i18n.t(cfg, "cp_c_conf", lang, "Evidence"): _conf(cfg, lang, t["confidence"]),
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

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

    # ═══ 3 · Interactive career map from the viewed occupation ═══════════════
    map_sel = _render_career_map(cfg, lang, primary, occ_name, titles, rels, by_id, curves, evidence)

    # ═══ 3b · Grouped role cards (classic view) — just above compare ═════════
    _render_role_cards(cfg, lang, primary, titles, rels, by_id, curves, evidence)

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

    # ═══ 5 · Live market signal (tiled) — at the absolute bottom ══════════════
    _render_market_signal_section(cfg, lang, titles, evidence, primary, preselect=map_sel)
