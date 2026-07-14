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


# ── Interactive career map (embedded, self-contained SVG/JS component) ────────
_MAP_TEMPLATE = r"""
<style>
 * { box-sizing: border-box; }
 .cpwrap { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; color:#0C1119; }
 .cpeyebrow { font-family:'JetBrains Mono',ui-monospace,monospace; font-size:10.5px; font-weight:600;
   letter-spacing:.08em; text-transform:uppercase; color:#0A63A6; }
 .cptitle { font-size:22px; font-weight:800; margin:3px 0 2px; }
 .cpsub { font-size:12.5px; color:#5B6472; margin-bottom:10px; }
 .cplegend { display:flex; gap:16px; flex-wrap:wrap; font-size:12px; color:#5B6472; margin-bottom:8px; }
 .cplegend span { display:inline-flex; align-items:center; gap:6px; }
 .cpdot { width:9px; height:9px; border-radius:50%; display:inline-block; }
 .cpmap { position:relative; width:100%; border:1px solid #E7E9ED; border-radius:14px; background:#fff;
   overflow:hidden; }
 .cpwires { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }
 .cpcenter { position:absolute; left:60px; top:50%; transform:translateY(-50%); background:#0A63A6;
   color:#fff; border-radius:12px; padding:10px 14px; max-width:210px; box-shadow:0 3px 10px rgba(10,99,166,.28); z-index:2; }
 .cpcenter .lbl { font-family:'JetBrains Mono',monospace; font-size:9.5px; letter-spacing:.06em; opacity:.85; }
 .cpcenter .cname { font-weight:700; font-size:14px; margin-top:2px; }
 .cpcenter .crange { font-size:11.5px; opacity:.9; margin-top:2px; }
 .cpnode { position:absolute; right:14px; display:flex; align-items:center; gap:8px; background:#fff;
   border:1px solid #E7E9ED; border-radius:22px; padding:7px 13px; cursor:pointer; z-index:2;
   box-shadow:0 1px 2px rgba(16,21,31,.05); transition:box-shadow .12s, border-color .12s; white-space:nowrap; }
 .cpnode:hover { box-shadow:0 3px 10px rgba(16,21,31,.12); }
 .cpnode.active { border-color:#0A63A6; box-shadow:0 0 0 3px rgba(10,99,166,.14); }
 .cpnode .nname { font-weight:600; font-size:13px; }
 .cpnode .ndiff { font-weight:700; font-size:12px; }
 .cpnode .nads { font-family:'JetBrains Mono',monospace; font-size:10.5px; color:#98A0AC; }
 .cpdetail { border:1px solid #E7E9ED; border-radius:14px; background:#fff; padding:16px 18px; margin-top:12px;
   max-height:360px; overflow:auto; }
 .drel { font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:600; letter-spacing:.06em;
   text-transform:uppercase; color:#5B6472; }
 .dname { font-size:17px; font-weight:800; margin:2px 0; }
 .dmeta { font-family:'JetBrains Mono',monospace; font-size:11px; color:#98A0AC; margin-bottom:10px; }
 .drow { display:flex; gap:34px; flex-wrap:wrap; margin-bottom:8px; }
 .dlabel { font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.05em; text-transform:uppercase; color:#98A0AC; }
 .dval { font-size:19px; font-weight:700; }
 .chip { display:inline-block; padding:2px 9px; margin:2px 4px 2px 0; border-radius:20px; font-size:12px; line-height:1.7; }
 .adsblk { border-left:3px solid #C0453A; background:rgba(192,69,58,.05); border-radius:8px; padding:11px 14px; margin-top:13px; }
 .adshdr { font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; letter-spacing:.06em; color:#C0453A; }
 .adsline { font-size:12.5px; color:#26303C; margin-top:6px; }
 .adslist { margin:6px 0 0; padding-left:18px; }
 .adslist li { margin-bottom:7px; }
 .adslist a { color:#0A63A6; text-decoration:none; font-weight:600; font-size:13px; }
 .admeta { font-size:11px; color:#98A0AC; }
 .noads { font-size:12.5px; color:#98A0AC; margin-top:12px; font-style:italic; }
 .mtiles { display:flex; gap:10px; flex-wrap:wrap; margin-top:13px; }
 .mtile { border:1px solid #E7E9ED; border-radius:12px; background:#fff; padding:10px 14px; min-width:118px; box-shadow:0 1px 2px rgba(16,21,31,.04); }
 .mtile.red { border-left:3px solid #C0453A; }
 .mtl { font-family:'JetBrains Mono',monospace; font-size:9.5px; letter-spacing:.05em; text-transform:uppercase; color:#98A0AC; }
 .mtv { font-size:16px; font-weight:700; margin-top:4px; }
 .mskills { border:1px solid #E7E9ED; border-radius:12px; background:#fff; padding:11px 14px; margin-top:10px; box-shadow:0 1px 2px rgba(16,21,31,.04); }
 .cphint { font-size:11px; color:#98A0AC; margin-top:8px; }
</style>
<div class="cpwrap">
  <div class="cpeyebrow" id="cpeyebrow"></div>
  <div class="cptitle" id="cptitle"></div>
  <div class="cpsub" id="cpsub"></div>
  <div class="cplegend" id="cplegend"></div>
  <div class="cpmap" id="cpmap"><svg class="cpwires" id="cpwires"></svg></div>
  <div class="cpdetail" id="cpdetail"></div>
  <div class="cphint" id="cphint"></div>
</div>
<script>
const D = __DATA__;
const L = D.labels;
const num = n => (n==null? '—' : Number(n).toLocaleString('sv-SE'));
const money = n => num(n) + ' kr';
const diffStr = d => (d==null? '' : (d>=0?'+':'−') + num(Math.abs(d)) + ' kr');
const esc = s => (s==null?'':String(s)).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
document.getElementById('cpeyebrow').textContent = L.eyebrow;
document.getElementById('cptitle').textContent = L.title;
document.getElementById('cpsub').textContent = L.subtitle;
document.getElementById('cphint').textContent = L.hint;
document.getElementById('cplegend').innerHTML =
  [['#0A63A6',L.leg_within],['#5B8A72',L.leg_spec],['#B26A00',L.leg_lead]]
  .map(([c,t])=>`<span><span class="cpdot" style="background:${c}"></span>${esc(t)}</span>`).join('');

const mapEl = document.getElementById('cpmap');
const svg = document.getElementById('cpwires');
const rowH = 54, padY = 26;
const H = Math.max(D.nodes.length*rowH + padY*2, 300);
mapEl.style.height = H + 'px';

const center = document.createElement('div');
center.className = 'cpcenter';
center.innerHTML = `<div class="lbl">${esc(L.you_here)}</div><div class="cname">${esc(D.center.name)}</div>`
  + (D.center.lo!=null? `<div class="crange">${money(D.center.lo)}–${money(D.center.hi)}</div>`:'');
mapEl.appendChild(center);

let sel = 0;
D.nodes.forEach((n,i)=>{ if(n.rel==='progression' && sel===0) sel=i; });
D.nodes.forEach((n,i)=>{
  const d = document.createElement('div');
  d.className = 'cpnode'; d.dataset.i = i; d.dataset.color = n.color;
  d.style.top = (padY + i*rowH) + 'px';
  d.innerHTML = `<span class="cpdot" style="background:${n.color}"></span>`
    + `<span class="nname">${esc(n.name)}</span>`
    + (n.diff!=null? `<span class="ndiff" style="color:${n.diff>=0?'#1B8A5A':'#C0453A'}">${diffStr(n.diff)}</span>`:'')
    + (n.ad_count? `<span class="nads">· ${n.ad_count} ${esc(L.ads)}</span>`:'');
  d.onclick = () => select(i);
  mapEl.appendChild(d);
});

function drawWires(){
  const mr = mapEl.getBoundingClientRect();
  const cr = center.getBoundingClientRect();
  const cx = cr.right - mr.left, cy = cr.top - mr.top + cr.height/2;
  let p = '';
  mapEl.querySelectorAll('.cpnode').forEach(node=>{
    const i = +node.dataset.i;
    const r = node.getBoundingClientRect();
    const nx = r.left - mr.left, ny = r.top - mr.top + r.height/2;
    const mx = (cx+nx)/2;
    const on = (i===sel);
    p += `<path d="M ${cx} ${cy} C ${mx} ${cy}, ${mx} ${ny}, ${nx} ${ny}" fill="none" `
      + `stroke="${node.dataset.color}" stroke-width="${on?3:1.5}" stroke-opacity="${on?0.9:0.35}"/>`;
  });
  svg.setAttribute('viewBox', `0 0 ${mr.width} ${mr.height}`);
  svg.setAttribute('width', mr.width); svg.setAttribute('height', mr.height);
  svg.innerHTML = p;
}

function renderDetail(n){
  const skills = (n.skills||[]).filter(Boolean).slice(0,8)
    .map(s=>`<span class="chip" style="background:rgba(192,69,58,.08);color:#C0453A">${esc(s)}</span>`).join('');
  const gaps = (n.gaps||[]).filter(Boolean)
    .map(s=>`<span class="chip" style="background:rgba(10,99,166,.08);color:#0A63A6">${esc(s)}</span>`).join('');
  let ads;
  if(n.ad_count){
    ads = `<div class="mtiles">`
      + `<div class="mtile red"><div class="mtl" style="color:#C0453A">${esc(L.ads_header)}</div><div class="mtv">${n.ad_count} ${esc(L.ads)}</div></div>`
      + (n.experience? `<div class="mtile"><div class="mtl">${esc(L.experience)}</div><div class="mtv">${esc(n.experience)}</div></div>`:'')
      + (n.education? `<div class="mtile"><div class="mtl">${esc(L.education)}</div><div class="mtv">${esc(n.education)}</div></div>`:'')
      + `</div>`
      + (skills? `<div class="mskills"><div class="mtl">${esc(L.skills)}</div><div style="margin-top:7px;">${skills}</div></div>`:'');
  } else {
    ads = `<div class="noads">${esc(L.no_ads)}</div>`;
  }
  document.getElementById('cpdetail').innerHTML =
    `<div class="drel"><span class="cpdot" style="background:${n.color}"></span> ${esc(n.rel_label)}</div>`
    + `<div class="dname">${n.subcode? esc(n.subcode)+' · ':''}${esc(n.name)}</div>`
    + `<div class="dmeta">${esc(n.level)} · ${n.same_ssyk? esc(L.same_ssyk):('→ SSYK '+esc(n.ssyk))} · ${esc(n.conf)}</div>`
    + `<div class="drow"><div><div class="dlabel">${esc(L.range)}</div><div class="dval">${money(n.lo)}–${money(n.hi)}</div></div>`
    + `<div><div class="dlabel">${esc(L.vs)}</div><div class="dval" style="color:${n.diff>=0?'#1B8A5A':'#C0453A'}">${diffStr(n.diff)}<span style="font-size:12px;font-weight:400;color:#8A919D"> /mo</span></div></div></div>`
    + (gaps? `<div class="dlabel" style="margin-top:4px;">${esc(L.gaps)}</div><div style="margin-top:3px;">${gaps}</div>`:'')
    + ads;
}

function positionNodes(){
  const W = mapEl.clientWidth;
  center.style.left = Math.max(56, W*0.13) + 'px';
  const maxD = Math.max(1, ...D.nodes.map(n=>Math.abs(n.diff||0)));
  const pull = Math.min(W*0.40, 440);           // horizontal spread by leap size
  mapEl.querySelectorAll('.cpnode').forEach(nd=>{
    const i=+nd.dataset.i, n=D.nodes[i];
    nd.style.top = (padY + i*rowH) + 'px';
    const ratio = Math.abs(n.diff||0)/maxD;      // 1 = biggest leap → furthest right
    nd.style.right = (16 + (1-ratio)*pull) + 'px';
  });
}
function select(i){
  sel = i;
  mapEl.querySelectorAll('.cpnode').forEach(nd=> nd.classList.toggle('active', +nd.dataset.i===i));
  renderDetail(D.nodes[i]);
  positionNodes(); drawWires();
}
function relayout(){ positionNodes(); drawWires(); }
window.addEventListener('resize', relayout);
requestAnimationFrame(()=>{ positionNodes(); select(sel); });
</script>
"""


def _render_career_map(cfg, lang, primary, occ_name, titles, rels, by_id, curves, evidence):
    """Interactive, data-driven career map (embedded component) — replaces the old
    card list. Node = a role the viewed occupation can lead to, coloured by move
    type, positioned by estimated salary midpoint, badged with its live ad count.
    Clicking a node reveals its range, gaps and (in red) the job-ad requirements +
    Platsbanken references."""
    import json
    import streamlit.components.v1 as components

    from_ids = {t["title_id"] for t in titles if str(t["primary_ssyk"]) == primary}
    out_rels = [r for r in rels if r["from_title"] in from_ids] or \
               [r for r in rels if r["rel_type"] == "progression"]
    bc = curves.get(primary)
    base_mid = bc.value_at(50).value if bc and bc.ok else None
    c_lo = bc.value_at(25).value if bc and bc.ok else None
    c_hi = bc.value_at(75).value if bc and bc.ok else None

    rel_color = {"progression": "#0A63A6", "specialist": "#5B8A72", "management": "#B26A00",
                 "leadership": "#B26A00", "lateral": "#8A919D", "entry": "#5B6472", "related": "#5B6472"}
    rel_label = {rt: i18n.t(cfg, f"cp_rel_{rt}", lang, h) for rt, h in _REL_GROUPS}

    nodes, seen = [], set()
    for r in out_rels:
        to = by_id.get(r["to_title"])
        if not to or to["title_id"] in seen:
            continue
        b = to.get("_band")
        if not b:
            continue
        seen.add(to["title_id"])
        ev = evidence.get(to["title_id"]) or {}
        exp = (ev.get("common_experience") or [])
        ym = exp[0].get("years_median") if exp else None
        edu = (ev.get("common_education") or [])
        nodes.append({
            "id": to["title_id"], "name": _tname(to, lang), "subcode": _subcode(to),
            "rel": r["rel_type"], "rel_label": rel_label.get(r["rel_type"], r["rel_type"]),
            "color": rel_color.get(r["rel_type"], "#5B6472"),
            "level": _level(to["level_label"], lang), "conf": _conf(cfg, lang, to["confidence"]),
            "same_ssyk": bool(r.get("same_ssyk")), "ssyk": str(to["primary_ssyk"]),
            "lo": round(b["lo_salary"]), "mid": round(b["mid_salary"]), "hi": round(b["hi_salary"]),
            "diff": (round(b["mid_salary"] - base_mid) if base_mid is not None else None),
            "gaps": (r.get("skill_gaps") or [])[:4],
            "ad_count": int(ev.get("ad_count") or 0),
            "skills": [s.get("skill") for s in (ev.get("common_skills") or [])[:8]],
            "education": (edu[0]["label"] if edu else None),
            "experience": (f"{ym}+ {i18n.t(cfg, 'cp_ms_yrs', lang, 'yrs')}" if ym is not None else None),
            "examples": [{"headline": a.get("headline"), "employer": a.get("employer"),
                          "deadline": a.get("deadline"), "region": a.get("region"),
                          "url": a.get("url"), "ref": a.get("id")} for a in (ev.get("example_ads") or [])],
        })
    if not nodes:
        st.markdown(f"#### {i18n.t(cfg, 'cp_map_h', lang, 'Where can this role lead?')}")
        st.caption(i18n.t(cfg, "cp_no_moves", lang, "No mapped moves for this occupation yet."))
        return
    nodes.sort(key=lambda n: -(n["mid"] or 0))

    payload = {
        "center": {"name": occ_name, "ssyk": str(primary),
                   "lo": (round(c_lo) if c_lo else None), "hi": (round(c_hi) if c_hi else None)},
        "nodes": nodes,
        "labels": {
            "eyebrow": "CAREER PATHS · " + i18n.t(cfg, "cp_map_h", lang, "Where can this role lead?").upper(),
            "title": i18n.t(cfg, "cp_map_from", lang, "Paths from {r}").format(r=occ_name),
            "subtitle": f"{occ_name} · SSYK {primary} · "
                        + i18n.t(cfg, "cp_map_axis", lang, "positions reflect estimated salary midpoints"),
            "leg_within": i18n.t(cfg, "cp_rel_progression", lang, "Advance within this occupation"),
            "leg_spec": i18n.t(cfg, "cp_rel_specialist", lang, "Specialist move"),
            "leg_lead": i18n.t(cfg, "cp_rel_leadership", lang, "Move into leadership"),
            "you_here": i18n.t(cfg, "cp_you_here", lang, "YOU ARE HERE"),
            "ads": i18n.t(cfg, "cp_ads", lang, "ads"),
            "range": i18n.t(cfg, "cp_ms_range", lang, "Estimated range"),
            "vs": i18n.t(cfg, "cp_vs_short", lang, "vs current (indicative)"),
            "gaps": i18n.t(cfg, "cp_gaps", lang, "Typical gaps to close"),
            "same_ssyk": i18n.t(cfg, "cp_same_ssyk", lang, "↔ same SSYK"),
            "ads_header": i18n.t(cfg, "cp_ms_fromads", lang, "FROM JOB ADS"),
            "experience": i18n.t(cfg, "cp_ms_exp", lang, "Typical experience"),
            "education": i18n.t(cfg, "cp_ms_edu", lang, "Top education req."),
            "skills": i18n.t(cfg, "cp_skills", lang, "Skills"),
            "examples": i18n.t(cfg, "cp_ms_ex", lang, "Example ads · Platsbanken references"),
            "apply_by": i18n.t(cfg, "cp_ms_dl", lang, "apply by {d}"),
            "ref": i18n.t(cfg, "cp_ms_ref", lang, "ref"),
            "expire": i18n.t(cfg, "cp_ms_expire", lang,
                             "Links open the ad on Platsbanken and expire after the deadline."),
            "no_ads": i18n.t(cfg, "cp_ms_none", lang, "No live job-ad signal for this role yet."),
            "hint": i18n.t(cfg, "cp_map_hint", lang,
                           "Click a role to see its salary range, gaps and live job-ad requirements."),
        },
    }
    html = _MAP_TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    map_h = max(len(nodes) * 54 + 52, 300)
    components.html(html, height=140 + map_h + 300, scrolling=True)


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


def _render_market_signal_section(cfg, lang, titles, evidence, primary):
    """Bottom-of-page 'Live market signal' — tiled (app card style) with a regional
    slicer on the example ads. Nothing shows if no evidence exists."""
    from collections import Counter
    ev_titles = [t for t in titles if evidence.get(t["title_id"])]
    if not ev_titles:
        return
    st.markdown("---")
    st.markdown(f"#### {i18n.t(cfg, 'cp_ms_h', lang, 'Live market signal (from current job ads)')}")
    st.caption(i18n.t(cfg, "cp_ms_cap", lang,
                      "What current Swedish job ads for these roles actually ask for. Aggregated from "
                      "public ads (Arbetsförmedlingen / JobTech, CC BY-SA) — indicative, not official, "
                      "and it does not change the SCB salary figures above."))

    ev_titles.sort(key=lambda t: -(evidence.get(t["title_id"], {}).get("ad_count") or 0))
    default_i = next((i for i, t in enumerate(ev_titles) if str(t.get("primary_ssyk")) == primary), 0)
    c_role, c_reg = st.columns([2, 1])
    sel_i = c_role.selectbox(
        i18n.t(cfg, "cp_ms_role", lang, "Show role"), list(range(len(ev_titles))), index=default_i,
        format_func=lambda i: ((_subcode(ev_titles[i]) + " · ") if _subcode(ev_titles[i]) else "")
        + _tname(ev_titles[i], lang) + f"  ({evidence.get(ev_titles[i]['title_id'], {}).get('ad_count', 0)} "
        + i18n.t(cfg, "cp_ads", lang, "ads") + ")",
        key=f"{cfg.slug}_cp_ms_role")
    t = ev_titles[sel_i]
    e = evidence.get(t["title_id"], {})
    exa = e.get("example_ads") or []

    # regional slicer — options from this role's example ads (region mix)
    reg_counts = Counter(a.get("region") for a in exa if a.get("region"))
    all_reg = i18n.t(cfg, "cp_ms_allreg", lang, "All regions")
    reg_opts = [all_reg] + [r for r, _ in reg_counts.most_common()]
    reg_sel = c_reg.selectbox(i18n.t(cfg, "cp_ms_region", lang, "Region"), reg_opts,
                              key=f"{cfg.slug}_cp_ms_region")

    exp = (e.get("common_experience") or [])
    ym = exp[0].get("years_median") if exp else None
    edu_top = (e.get("common_education") or [])
    # ── Stat tiles (app card style) ──
    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(_tile(i18n.t(cfg, "cp_ms_ads_t", lang, "Live ads"),
                      f"{int(e.get('ad_count') or 0)}",
                      _ev_strength(cfg, lang, e.get("evidence_strength"))), unsafe_allow_html=True)
    s2.markdown(_tile(i18n.t(cfg, "cp_ms_exp", lang, "Typical experience"),
                      (f"{ym}+ {i18n.t(cfg, 'cp_ms_yrs', lang, 'yrs')}" if ym is not None else "—")),
                unsafe_allow_html=True)
    s3.markdown(_tile(i18n.t(cfg, "cp_ms_edu", lang, "Top education req."),
                      (edu_top[0]["label"] if edu_top else "—")), unsafe_allow_html=True)
    s4.markdown(_tile(i18n.t(cfg, "cp_ms_mgmt", lang, "People management"),
                      f"{round((e.get('mgmt_freq') or 0) * 100)}%"), unsafe_allow_html=True)
    st.write("")

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

    # ── Example ads (region-filtered) ──
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
    _render_career_map(cfg, lang, primary, occ_name, titles, rels, by_id, curves, evidence)

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
    _render_market_signal_section(cfg, lang, titles, evidence, primary)
