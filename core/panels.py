"""Shared exclusive-view panels: the User guide and the Code browser.

Both render into core.states.view_mount() and take over the main area with a
Back button. They're driven entirely by the config + provider, so every country
gets them for free: the guide from ``cfg.guide`` and the browser from
``provider.occupation_tree`` (the whole classification, all levels).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from . import hierarchy, i18n


def _back(cfg, lang, vk):
    if st.button(i18n.t(cfg, "back", lang), key=f"{cfg.slug}_back_{vk}"):
        st.session_state.pop(vk, None)
        st.rerun()


_GUIDE_CSS = """
<style>
.gd-eyebrow{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
  letter-spacing:.16em;color:#0A63A6;text-transform:uppercase;margin-bottom:10px;}
.gd-title{font-size:28px;font-weight:800;letter-spacing:-.02em;color:#0C1119;
  line-height:1.15;margin:0 0 8px;}
.gd-source{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:#98A0AC;
  margin-bottom:16px;}
.gd-intro{font-size:16px;color:#4A525F;line-height:1.6;max-width:640px;margin-bottom:8px;}
.gd-sec{margin-top:34px;}
.gd-num{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
  color:#0A63A6;margin-bottom:6px;}
.gd-h{font-size:20px;font-weight:700;color:#0C1119;margin:0 0 14px;}
.gd-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;}
.gd-card{background:#fff;border:1px solid #E7E9ED;border-radius:14px;padding:20px;}
.gd-card0{background:#fff;border:1px solid #E7E9ED;border-radius:14px;overflow:hidden;}
.gd-step-num{font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:600;
  color:#0A63A6;margin-bottom:8px;}
.gd-step-t{font-weight:700;font-size:15px;letter-spacing:-.01em;color:#0C1119;margin-bottom:7px;}
.gd-step-d{font-size:13.5px;color:#5B6472;line-height:1.5;}
.gd-row{display:flex;gap:14px;padding:14px 18px;border-top:1px solid #EEF0F3;}
.gd-row:first-child{border-top:none;}
.gd-lbl{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
  color:#0A63A6;width:150px;flex:0 0 auto;padding-top:2px;letter-spacing:.04em;
  text-transform:uppercase;}
.gd-txt{font-size:13.5px;color:#4A525F;line-height:1.5;}
.gd-chart-intro{font-size:14px;color:#4A525F;line-height:1.55;margin-bottom:14px;}
.gd-prow{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.gd-prow:last-child{margin-bottom:0;}
.gd-plbl{font-family:'JetBrains Mono',monospace;font-size:11px;color:#98A0AC;
  width:34px;flex:0 0 auto;}
.gd-track{flex:1 1 0;height:9px;border-radius:5px;background:#EEF0F3;overflow:hidden;}
.gd-fill{height:100%;border-radius:5px;background:#94AAC0;}
.gd-fill.med{background:#0A63A6;}
.gd-pdesc{font-size:12.5px;color:#5B6472;flex:0 0 auto;}
.gd-notes{list-style:none;margin:0;padding:0;}
.gd-notes li{display:flex;gap:10px;font-size:13.5px;color:#4A525F;line-height:1.5;
  margin-bottom:8px;}
.gd-notes li::before{content:'';width:5px;height:5px;border-radius:50%;background:#0A63A6;
  margin-top:8px;flex:0 0 auto;opacity:.7;}
.gd-footer{font-size:12.5px;color:#8A919D;margin-top:34px;padding-top:16px;
  border-top:1px solid #EEF0F3;}
</style>
"""


def _guide_html(cfg, g: dict, lang: str) -> str:
    """Structured guide (the approved User-Guide design): eyebrow · title ·
    source · intro, then numbered sections — step cards, label rows,
    percentile-bar explainer + good-to-know, tab rows — and a footer."""
    eyebrow = f"{i18n.t(cfg, 'user_guide', lang)} · {cfg.name}"
    h = [_GUIDE_CSS,
         f'<div class="gd-eyebrow">{eyebrow}</div>',
         f'<div class="gd-title">{g.get("title", "")}</div>']
    if g.get("source"):
        h.append(f'<div class="gd-source">{g["source"]}</div>')
    if g.get("intro"):
        h.append(f'<div class="gd-intro">{g["intro"]}</div>')

    n = 0

    def sec(title):
        nonlocal n
        n += 1
        return (f'<div class="gd-sec"><div class="gd-num">{n:02d}</div>'
                f'<div class="gd-h">{title}</div>')

    if g.get("steps"):
        h.append(sec(g.get("steps_title", "Getting started")))
        cards = "".join(
            f'<div class="gd-card"><div class="gd-step-num">{i + 1}</div>'
            f'<div class="gd-step-t">{t}</div><div class="gd-step-d">{d}</div></div>'
            for i, (t, d) in enumerate(g["steps"]))
        h.append(f'<div class="gd-steps">{cards}</div></div>')

    if g.get("find"):
        h.append(sec(g.get("find_title", "Finding the right occupation")))
        rows = "".join(f'<div class="gd-row"><div class="gd-lbl">{l}</div>'
                       f'<div class="gd-txt">{d}</div></div>' for l, d in g["find"])
        h.append(f'<div class="gd-card0">{rows}</div></div>')

    if g.get("pcts") or g.get("notes"):
        h.append(sec(g.get("charts_title", "Reading the salary charts")))
        if g.get("charts_intro"):
            h.append(f'<div class="gd-chart-intro">{g["charts_intro"]}</div>')
        if g.get("pcts"):
            prows = "".join(
                f'<div class="gd-prow"><span class="gd-plbl">{l}</span>'
                f'<div class="gd-track"><div class="gd-fill{" med" if l.upper().startswith("MED") else ""}"'
                f' style="width:{w}%"></div></div>'
                f'<span class="gd-pdesc">{d}</span></div>'
                for l, w, d in g["pcts"])
            h.append(f'<div class="gd-card" style="margin-bottom:14px;">{prows}</div>')
        if g.get("notes"):
            items = "".join(f"<li><span>{x}</span></li>" for x in g["notes"])
            h.append(f'<div class="gd-card"><div class="gd-step-t" style="margin-bottom:10px;">'
                     f'{g.get("notes_title", "Good to know")}</div>'
                     f'<ul class="gd-notes">{items}</ul></div>')
        h.append("</div>")

    if g.get("tabs"):
        h.append(sec(g.get("tabs_title", "The tabs")))
        rows = "".join(f'<div class="gd-row"><div class="gd-lbl">{l}</div>'
                       f'<div class="gd-txt">{d}</div></div>' for l, d in g["tabs"])
        h.append(f'<div class="gd-card0">{rows}</div></div>')

    if g.get("footer"):
        h.append(f'<div class="gd-footer">{g["footer"]}</div>')
    return "".join(h)


def _guide(cfg, lang, vk):
    _back(cfg, lang, vk)
    g = cfg.guide.get(lang) or cfg.guide.get("EN") or ""
    if isinstance(g, dict):                      # structured guide (the design)
        st.markdown(_guide_html(cfg, g, lang), unsafe_allow_html=True)
    elif g:                                      # legacy markdown fallback
        st.markdown(f"## {i18n.t(cfg, 'user_guide', lang)}")
        st.markdown(g)
    else:
        st.info("—")


def browsable(cfg, lang: str = "EN") -> bool:
    """Whether the classification nests enough to browse (more than one level)."""
    tree = cfg.provider.occupation_tree(lang) if cfg.provider else {}
    return len({len(c) for c in tree}) > 1


def _confirm_body(cfg, lang, query, code, name, vk):
    """The 'Use this occupation' confirm dialog: the picked occupation plus the
    country's remaining filters (sector / gender / year range, each shown only if
    the data supports it), pre-filled from the current selection. Search applies;
    Cancel just closes and returns to the browser. Only styling attributes and
    capability gates differ per country."""
    caps, slug = cfg.capabilities, cfg.slug
    st.caption(i18n.t(cfg, "confirm_intro", lang,
                      "Check the filters below, then search — or search with the "
                      "current selection."))
    st.markdown(f"**{i18n.t(cfg, 'confirm_occ', lang, 'Occupation')}:** {name} · {code}")

    sector_code = query.get("sector", "") or (caps.sectors[0] if caps.sectors else "")
    sector_label = None
    if caps.sectors:
        sec_labels = [i18n.t(cfg, f"sector_{s}", lang, s.capitalize()) for s in caps.sectors]
        idx = caps.sectors.index(sector_code) if sector_code in caps.sectors else 0
        sector_label = st.selectbox(i18n.t(cfg, "sector", lang, "Sector"), sec_labels,
                                    index=idx, key=f"{slug}_d_sector")
        sector_code = caps.sectors[sec_labels.index(sector_label)]

    sex = query.get("sex", "total") or "total"
    if caps.has_sex:
        sex = st.segmented_control(
            i18n.t(cfg, "sex", lang, "Gender"), ["total", "women", "men"],
            default=sex if sex in ("total", "women", "men") else "total",
            key=f"{slug}_d_sex",
            format_func=lambda s: i18n.t(cfg, s, lang, s.capitalize())) or "total"

    years_tuple = tuple(query.get("years", ()))
    years_value = None
    if caps.year_range:
        y0, y1 = caps.year_range
        allyears = list(range(y0, y1 + 1))
        if len(allyears) > 1:
            cur = sorted(int(y) for y in years_tuple) if years_tuple else []
            a0 = min(max(cur[0] if cur else max(y0, y1 - 2), y0), y1)
            b0 = min(max(cur[-1] if cur else y1, y0), y1)
            a, b = st.select_slider(i18n.t(cfg, "year_range", lang, "Year range"),
                                    options=allyears, value=(a0, b0),
                                    key=f"{slug}_d_years")
            years_tuple = tuple(y for y in allyears if a <= y <= b)
            years_value = (a, b)
        else:
            years_tuple = (y1,)

    c1, c2 = st.columns(2)
    if c1.button("🔍 " + i18n.t(cfg, "search", lang, "Search"), type="primary",
                 use_container_width=True, key=f"{slug}_d_go"):
        # Stage the full selection; the sidebar consumes it BEFORE its widgets
        # instantiate (so it can write their keys). App-scope rerun closes the
        # dialog and renders the results.
        st.session_state[f"{slug}_apply"] = {
            "query": {**query, "sector": sector_code, "sex": sex,
                      "years": years_tuple, "occ_codes": (code,), "scope": ""},
            "occ_label": f"{name}  ({code})",
            "sector_label": sector_label, "sex": sex if caps.has_sex else None,
            "years_value": years_value, "vk": vk}
        st.rerun()
    if c2.button(i18n.t(cfg, "cancel", lang, "Cancel"), use_container_width=True,
                 key=f"{slug}_d_cancel"):
        st.rerun()                               # close, back to the browser


def _open_confirm(cfg, lang, query, code, name, vk):
    """Open the confirm dialog on the click's OWN run (the proven st.dialog
    pattern — no persistent open flag that would resurrect it after an
    X-dismissal). In-dialog widget edits are fragment reruns, so it stays open;
    Search/Cancel do app-scope reruns, which close it."""
    title = i18n.t(cfg, "confirm_title", lang, "Confirm your search")
    st.dialog(title)(lambda: _confirm_body(cfg, lang, query, code, name, vk))()


def _browse_body(cfg, lang, query=None, vk=None):
    """The browser itself (search + cascading drill-down), reused by both the
    full-page Code-browser view and the default landing. When ``query`` is given,
    a drilled-to occupation offers a 'Use this occupation' button."""
    tree = cfg.provider.occupation_tree(lang) if cfg.provider else {}
    if not tree:
        st.info("—")
        return

    present = set(tree)
    roots, children = hierarchy.build(tree)
    col_code, col_name = i18n.t(cfg, "col_code", lang), i18n.t(cfg, "col_name", lang)

    def fmt(c):
        return f"{c} · {tree[c]}"

    def panel_for(cur):
        """Right-hand detail for the selected node: code · name, a breadcrumb of
        ancestors, and either its direct children (a group) or a leaf note + a
        'use this occupation' action."""
        if not cur:
            st.info(i18n.t(cfg, "browser_pick", lang))
            return
        st.markdown(f"#### {cur} · {tree[cur]}")
        crumbs, p = [], hierarchy.parent_of(cur, present)
        while p:
            crumbs.append(p)
            p = hierarchy.parent_of(p, present)
        if crumbs:
            st.caption(f"**{i18n.t(cfg, 'browser_hierarchy', lang)}:** "
                       + " › ".join(tree[c] for c in reversed(crumbs)))
        # Rich metadata when the provider has it (SSYK descriptions/synonyms)
        det = {}
        try:
            det = cfg.provider.occupation_details(cur, lang) or {}
        except Exception:
            det = {}
        if det.get("description"):
            st.markdown(det["description"])
        if det.get("synonyms"):
            syn = ", ".join(det["synonyms"][:15])
            st.caption(f"**{i18n.t(cfg, 'also_known', lang, 'Also known as')}:** {syn}")
        kids = sorted(children.get(cur, []))
        if kids:
            rows = [{col_code: c, col_name: tree[c]} for c in kids]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:                                    # a leaf = a detailed occupation
            st.caption(i18n.t(cfg, "browser_leaf", lang))
            if query is not None:
                if st.button(i18n.t(cfg, "use_occupation", lang), type="primary",
                             key=f"{cfg.slug}_use", use_container_width=True):
                    # fresh dialog each open (keyed widgets otherwise keep the
                    # previous edit instead of reflecting the current selection)
                    for dk in ("d_sector", "d_sex", "d_years"):
                        st.session_state.pop(f"{cfg.slug}_{dk}", None)
                    _open_confirm(cfg, lang, query, cur, tree[cur], vk)

    # ── Global search: bypass the drill-down, pick from matches ────────────────
    q = st.text_input(i18n.t(cfg, "browser_search", lang),
                      key=f"{cfg.slug}_brsearch").strip()
    if q:
        ql = q.lower()
        hits = sorted(c for c in tree if ql in c.lower() or ql in tree[c].lower())
        st.caption(f"{len(hits)} {i18n.t(cfg, 'browser_results', lang)}")
        if hits:
            sel = st.selectbox(i18n.t(cfg, "code_browser", lang), hits[:300],
                               format_func=fmt, key=f"{cfg.slug}_brres",
                               label_visibility="collapsed")
            panel_for(sel)
        return

    # ── Drill-down: one blank-able selectbox per level; the next appears once a
    # level is chosen (Sweden SSYK / France PCS pattern) ───────────────────────
    st.caption(i18n.t(cfg, "browser_intro", lang))
    BLANK = "__none__"
    nav, panel = st.columns([1, 1.3])
    with nav:
        cur, opts, level = None, sorted(roots), 0
        while opts:
            label = i18n.t(cfg, f"brlvl_{len(opts[0])}", lang, f"Level {level + 1}")
            v = st.selectbox(
                label, [BLANK] + opts, key=f"{cfg.slug}_brlvl{level}",
                format_func=lambda c: i18n.t(cfg, "browser_blank", lang) if c == BLANK else fmt(c))
            if v == BLANK:
                break
            cur, opts, level = v, sorted(children.get(v, [])), level + 1
    with panel:
        panel_for(cur)


def _browser(cfg, lang, vk, query):
    """Full-page Code-browser view (from the sidebar button): Back + heading."""
    _back(cfg, lang, vk)
    heading = i18n.t(cfg, "code_browser", lang)
    if cfg.classification:
        heading += f" · {cfg.classification}"
    st.markdown(f"## {heading}")
    _browse_body(cfg, lang, query, vk)


def default_browser(cfg, lang, query=None):
    """Inline browser shown on the empty landing (no occupation selected), under
    the prompt — the Swedish page's default start view. No Back button; the same
    drill-down as the full-page view."""
    heading = i18n.t(cfg, "browse_title", lang)
    if cfg.classification:
        heading += f" · {cfg.classification}"
    st.subheader(heading)
    _browse_body(cfg, lang, query, None)


def render(cfg, view: str, lang: str, vk: str, query=None):
    if view == "guide":
        _guide(cfg, lang, vk)
    elif view == "browser":
        _browser(cfg, lang, vk, query)
