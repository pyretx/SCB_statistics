"""Shared exclusive-view panels: the User guide and the Code browser.

Both render into core.states.view_mount() and take over the main area with a
Back button. They're driven entirely by the config + provider, so every country
gets them for free: the guide from ``cfg.guide`` and the browser from
``provider.occupation_tree`` (the whole classification, all levels).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from . import i18n


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


def _parent_of(code: str, present: set) -> str | None:
    """Longest present code that is a proper prefix of ``code`` (its direct
    parent). Prefix-based, so it copes with level gaps — e.g. France PCS goes
    1→2→4 digit, STYRK/SSYK 1→2→3→4."""
    for L in range(len(code) - 1, 0, -1):
        if code[:L] in present:
            return code[:L]
    return None


def _browser(cfg, lang, vk):
    _back(cfg, lang, vk)
    heading = i18n.t(cfg, "code_browser", lang)
    if cfg.classification:
        heading += f" · {cfg.classification}"
    st.markdown(f"## {heading}")

    tree = cfg.provider.occupation_tree(lang) if cfg.provider else {}
    if not tree:
        st.info("—")
        return

    present = set(tree)
    children: dict[str, list] = {}
    roots: list[str] = []
    for c in tree:
        p = _parent_of(c, present)
        (roots if p is None else children.setdefault(p, [])).append(c)

    col_code, col_name = i18n.t(cfg, "col_code", lang), i18n.t(cfg, "col_name", lang)

    def fmt(c):
        return f"{c} · {tree[c]}"

    def panel_for(cur):
        """Right-hand detail for the selected node: code · name, a breadcrumb of
        ancestors, and either its direct children (a group) or a leaf note."""
        if not cur:
            st.info(i18n.t(cfg, "browser_pick", lang))
            return
        st.markdown(f"#### {cur} · {tree[cur]}")
        crumbs, p = [], _parent_of(cur, present)
        while p:
            crumbs.append(p)
            p = _parent_of(p, present)
        if crumbs:
            st.caption(f"**{i18n.t(cfg, 'browser_hierarchy', lang)}:** "
                       + " › ".join(tree[c] for c in reversed(crumbs)))
        kids = sorted(children.get(cur, []))
        if kids:
            rows = [{col_code: c, col_name: tree[c]} for c in kids]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption(i18n.t(cfg, "browser_leaf", lang))

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


def render(cfg, view: str, lang: str, vk: str):
    if view == "guide":
        _guide(cfg, lang, vk)
    elif view == "browser":
        _browser(cfg, lang, vk)
