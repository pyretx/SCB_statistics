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


def _guide(cfg, lang, vk):
    _back(cfg, lang, vk)
    st.markdown(f"## {i18n.t(cfg, 'user_guide', lang)}")
    md = cfg.guide.get(lang) or cfg.guide.get("EN") or ""
    if md:
        st.markdown(md)
    else:
        st.info("—")


def browsable(cfg, lang: str = "EN") -> bool:
    """Whether the classification nests enough to browse (more than one level)."""
    tree = cfg.provider.occupation_tree(lang) if cfg.provider else {}
    return len({len(c) for c in tree}) > 1


def _use_occupation(cfg, code, name, query, vk):
    """Pick a drilled-to occupation: commit it as the active query (so its data
    renders), mirror it into the sidebar, and close the browser view. Runs as a
    button on_click callback — i.e. BEFORE the next run instantiates the sidebar
    widgets — so it may safely write their keys (slug_occ / slug_grp*)."""
    slug = cfg.slug
    st.session_state[f"{slug}_committed"] = {**query, "occ_codes": (code,), "scope": ""}
    for gkey in [key for key in st.session_state if key.startswith(f"{slug}_grp")]:
        st.session_state.pop(gkey, None)        # clear the sidebar drill-down
    st.session_state.pop(f"{slug}_occsearch", None)
    st.session_state[f"{slug}_occ"] = [f"{name}  ({code})"]   # reflect in the multiselect
    if vk:
        st.session_state.pop(vk, None)           # close the code-browser view


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
        kids = sorted(children.get(cur, []))
        if kids:
            rows = [{col_code: c, col_name: tree[c]} for c in kids]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:                                    # a leaf = a detailed occupation
            st.caption(i18n.t(cfg, "browser_leaf", lang))
            if query is not None:
                st.button(i18n.t(cfg, "use_occupation", lang), type="primary",
                          key=f"{cfg.slug}_use", use_container_width=True,
                          on_click=_use_occupation, args=(cfg, cur, tree[cur], query, vk))

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
