"""The one shared left menu. Rendered identically for every country; which
filters appear is driven by the config's Capabilities + languages. Every widget
key is namespaced with the country slug (all country pages share one Streamlit
session, so unprefixed keys would collide).

Layout mirrors the Swedish page: brand + switcher, identity, language toggle,
User-guide / Code-browser buttons, then the data filters (sector, sex, years,
occupation drill-down) and Search/Clear.
"""
from __future__ import annotations

import streamlit as st

import theme
import auth

from . import i18n


def _language_toggle(cfg, k) -> str:
    """Segmented EN / local-language switch. Returns the active language code
    (falls back to the sole language when a country offers only one)."""
    langs = list(cfg.languages) or [("EN", "English")]
    if len(langs) == 1:
        return langs[0][0]
    codes = [c for c, _ in langs]
    names = {c: n for c, n in langs}
    en_word = i18n.UI["EN"]["language"]
    local_word = i18n.t(cfg, "language", codes[-1])
    label = f"{en_word} / {local_word}" if local_word != en_word else en_word
    sel = st.segmented_control(
        label, codes, default=codes[0], key=k("lang"),
        format_func=lambda c: names.get(c, c))
    return sel or codes[0]


def _guide_browser_buttons(cfg, k, lang, has_tree):
    """Row of exclusive-view launchers (User guide / Code browser). Sets the
    view flag read by core.page; the panel renders and offers a Back button."""
    want_guide = bool(cfg.guide)
    want_browser = has_tree
    if not (want_guide or want_browser):
        return
    cols = st.columns(2 if (want_guide and want_browser) else 1)
    i = 0
    if want_guide:
        if cols[i].button(i18n.t(cfg, "user_guide", lang), use_container_width=True,
                          key=k("open_guide")):
            st.session_state[k("view")] = "guide"
            st.rerun()
        i += 1
    if want_browser:
        if cols[i].button(i18n.t(cfg, "code_browser", lang), use_container_width=True,
                          key=k("open_browser")):
            st.session_state[k("view")] = "browser"
            st.rerun()


def _occupation_picker(cfg, k, lang) -> tuple[str, ...]:
    """Optional major-group drill-down (leveling) + occupation multiselect.
    The drill-down appears only when the classification actually nests."""
    prov = cfg.provider
    if not prov:
        return ()
    leaves = prov.occupations(lang)          # {code: name}, detailed occupations
    if not leaves:
        return ()

    if cfg.capabilities.has_occupation_hierarchy:
        tree = prov.occupation_tree(lang)
        majors = {c: n for c, n in tree.items() if len(c) == 1}
        if majors:
            # translated labels as options (see the sector note above)
            none_lbl = i18n.t(cfg, "all_groups", lang)
            ordered = sorted(majors, key=lambda c: majors[c].lower())
            labels = [none_lbl] + [f"{c} · {majors[c]}" for c in ordered]
            chosen = st.selectbox(i18n.t(cfg, "major_group", lang), labels, key=k("major"))
            i = labels.index(chosen)
            if i > 0:
                sel_major = ordered[i - 1]
                leaves = {c: n for c, n in leaves.items() if c[:1] == sel_major}

    name_to_code = {v: c for c, v in leaves.items()}
    picked = st.multiselect(
        i18n.t(cfg, "occupations", lang), sorted(name_to_code), key=k("occ"),
        placeholder=i18n.t(cfg, "occ_placeholder", lang))
    return tuple(name_to_code[p] for p in picked)


def render_sidebar(cfg) -> dict:
    """Render the sidebar and return the ACTIVE query dict:
        {lang, sector, sex, years, occ_codes}
    In fetch_mode='search' the active query is the last committed one (updates on
    the Search button); in 'reactive' mode it tracks the widgets live. The active
    language is always live, so the toggle re-labels immediately.
    """
    caps = cfg.capabilities
    def k(name):                       # namespaced widget key
        return f"{cfg.slug}_{name}"

    live = {"lang": "EN", "sector": (caps.sectors[0] if caps.sectors else ""),
            "sex": "total", "years": (), "occ_codes": ()}

    with st.sidebar:
        st.markdown(theme.SIDEBAR_CSS, unsafe_allow_html=True)
        lc, sc = st.columns([1.7, 1], vertical_alignment="center")
        with lc:
            st.page_link("landing.py", label=i18n.t(cfg, "brand", "EN"),
                         icon=":material/language:")
        with sc:
            auth.country_switcher(cfg.slug)
        auth.sidebar_identity()
        st.markdown('<div style="height:1px;background:#EEF0F3;margin:12px 0 4px;"></div>',
                    unsafe_allow_html=True)

        lang = _language_toggle(cfg, k)
        live["lang"] = lang

        tree = cfg.provider.occupation_tree(lang) if cfg.provider else {}
        has_tree = caps.has_occupation_hierarchy and any(len(c) < 4 for c in tree)
        _guide_browser_buttons(cfg, k, lang, has_tree)
        st.markdown('<div style="height:1px;background:#EEF0F3;margin:12px 0 4px;"></div>',
                    unsafe_allow_html=True)

        if caps.sectors:
            # Options are the TRANSLATED labels (not stable keys + format_func):
            # a single-value selectbox memoizes its collapsed display by option
            # value, so with stable keys the shown value wouldn't re-translate on
            # a language switch. Changing the options list forces the refresh —
            # the Swedish page's approach (selection resets to default on switch).
            sec_labels = [i18n.t(cfg, f"sector_{s}", lang, s.capitalize())
                          for s in caps.sectors]
            chosen = st.selectbox(i18n.t(cfg, "sector", lang), sec_labels, key=k("sector"))
            live["sector"] = caps.sectors[sec_labels.index(chosen)]

        if caps.has_sex:
            _sex = st.segmented_control(
                i18n.t(cfg, "sex", lang), ["total", "women", "men"], default="total",
                key=k("sex"),
                format_func=lambda s: i18n.t(cfg, s, lang, s.capitalize()))
            live["sex"] = _sex or "total"

        if caps.year_range:
            y0, y1 = caps.year_range
            years = list(range(y0, y1 + 1))
            if len(years) > 1:
                a, b = st.select_slider(i18n.t(cfg, "year_range", lang), options=years,
                                        value=(max(y0, y1 - 2), y1), key=k("years"))
                live["years"] = tuple(y for y in years if a <= y <= b)
            else:
                live["years"] = (y1,)

        live["occ_codes"] = _occupation_picker(cfg, k, lang)

        if cfg.fetch_mode == "search":
            b1, b2 = st.columns(2)
            if b1.button("🔍 " + i18n.t(cfg, "search", lang), type="primary",
                         use_container_width=True, key=k("go")):
                st.session_state[k("committed")] = dict(live)
            if b2.button("✕ " + i18n.t(cfg, "clear", lang),
                         use_container_width=True, key=k("clear")):
                st.session_state.pop(k("committed"), None)

    if cfg.fetch_mode == "search":
        committed = st.session_state.get(k("committed"))
        if committed:
            # language is always live so the toggle re-labels without re-searching
            return {**committed, "lang": live["lang"]}
        return {**live, "occ_codes": ()}
    return live
