"""The one shared left menu. Rendered identically for every country; which
filters appear is driven by the config's Capabilities. Every widget key is
namespaced with the country slug (all country pages share one Streamlit session,
so unprefixed keys would collide).
"""
from __future__ import annotations

import streamlit as st

import theme
import auth


def render_sidebar(cfg) -> dict:
    """Render the sidebar and return the ACTIVE query dict:
        {lang, sector, sex, years, occ_codes}
    In fetch_mode='search' the active query is the last committed one (updates on
    the Search button); in 'reactive' mode it tracks the widgets live.
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
            st.page_link("landing.py", label="Salary Explorer", icon=":material/language:")
        with sc:
            auth.country_switcher(cfg.slug)     # registry-driven in Phase 4
        auth.sidebar_identity()
        st.markdown('<div style="height:1px;background:#EEF0F3;margin:12px 0 4px;"></div>',
                    unsafe_allow_html=True)

        if caps.sectors:
            live["sector"] = st.selectbox(
                "Sector", list(caps.sectors), key=k("sector"),
                format_func=lambda s: cfg.L(f"sector_{s}", s.capitalize()))

        if caps.has_sex:
            _sex = st.segmented_control(
                "Sex", ["total", "women", "men"], default="total", key=k("sex"),
                format_func=lambda s: {"total": "Total", "women": "Women", "men": "Men"}[s])
            live["sex"] = _sex or "total"

        if caps.year_range:
            y0, y1 = caps.year_range
            years = list(range(y0, y1 + 1))
            if len(years) > 1:
                a, b = st.select_slider("Year range", options=years,
                                        value=(max(y0, y1 - 2), y1), key=k("years"))
                live["years"] = tuple(y for y in years if a <= y <= b)
            else:
                live["years"] = (y1,)

        occs = cfg.provider.occupations(live["lang"]) if cfg.provider else {}
        if occs:
            name_to_code = {v: c for c, v in occs.items()}
            picked = st.multiselect("Occupation(s)", sorted(name_to_code), key=k("occ"))
            live["occ_codes"] = tuple(name_to_code[p] for p in picked)

        if cfg.fetch_mode == "search":
            b1, b2 = st.columns(2)
            if b1.button("🔍 Search", type="primary", use_container_width=True, key=k("go")):
                st.session_state[k("committed")] = dict(live)
            if b2.button("✕ Clear", use_container_width=True, key=k("clear")):
                st.session_state.pop(k("committed"), None)

    if cfg.fetch_mode == "search":
        return st.session_state.get(k("committed")) or {**live, "occ_codes": ()}
    return live
