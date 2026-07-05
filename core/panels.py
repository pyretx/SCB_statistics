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

    q = st.text_input(i18n.t(cfg, "browser_search", lang), key=f"{cfg.slug}_brsearch").strip()
    col_code, col_name = i18n.t(cfg, "col_code", lang), i18n.t(cfg, "col_name", lang)

    if q:
        ql = q.lower()
        hits = {c: n for c, n in tree.items() if ql in c.lower() or ql in n.lower()}
        rows = [{col_code: c, col_name: n} for c, n in sorted(hits.items())]
        st.caption(f"{len(rows)} {i18n.t(cfg, 'browser_results', lang)}")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        return

    st.caption(i18n.t(cfg, "browser_intro", lang))
    majors = sorted((c for c in tree if len(c) == 1), key=lambda c: tree[c].lower())
    for m in majors:
        # every descendant code, sorted → codes sort into hierarchy order
        desc = sorted(c for c in tree if c.startswith(m) and len(c) > 1)
        with st.expander(f"{m} · {tree[m]}  ({sum(1 for c in desc if len(c) == 4)})"):
            rows = [{col_code: c, col_name: tree[c]} for c in desc]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render(cfg, view: str, lang: str, vk: str):
    if view == "guide":
        _guide(cfg, lang, vk)
    elif view == "browser":
        _browser(cfg, lang, vk)
