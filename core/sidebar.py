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

from . import hierarchy, i18n


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


def _group_select(cfg, k, lang, depth: int, codes: list, tree: dict) -> str | None:
    """One blank-able group selectbox for cascade level ``depth`` (1-indexed).
    Translated labels are the options (so the shown value re-translates on a
    language switch); options are sorted by code. Returns the selected group
    code, or None for the blank/"all" option."""
    name = i18n.t(cfg, f"grp_{depth}", lang, i18n.t(cfg, "group_generic", lang))
    none_lbl = i18n.t(cfg, f"all_grp_{depth}", lang, i18n.t(cfg, "all_generic", lang))
    ordered = sorted(codes)                  # by code (0,1,2,…), not by name
    labels = [none_lbl] + [f"{c} · {tree[c]}" for c in ordered]
    chosen = st.selectbox(f"{depth}. {name}", labels, key=k(f"grp{depth}"))
    i = labels.index(chosen)
    return ordered[i - 1] if i > 0 else None


def occ_label(name: str, code: str) -> str:
    """Multiselect option text: name + code, e.g. 'Ambulance workers  (3258)'."""
    return f"{name}  ({code})"


def _occupation_picker(cfg, k, lang) -> tuple[tuple[str, ...], str]:
    """Sweden-style occupation section, but showing EVERY group level the
    classification has: 1. Major group → 2. Sub-group → 3. Minor group → … (each
    appears once its parent is picked) → an occupation search box → the final
    numbered Occupation(s) multiselect. Returns (occ_codes, scope) where scope is
    the deepest drilled-into group code ("" if none) — used to scope the
    Leaderboard. A flat classification skips the levels."""
    prov = cfg.provider
    if not prov:
        return (), ""
    leaves = prov.occupations(lang)          # {code: name}, detailed occupations
    if not leaves:
        return (), ""

    pool = leaves                            # occupations offered in the multiselect
    n_levels = 0                             # number of group levels (for numbering)
    scope = ""                               # deepest drilled-into group code
    if cfg.capabilities.has_occupation_hierarchy:
        tree = prov.occupation_tree(lang)
        roots, children = hierarchy.build(tree)
        leaf_len = max(len(c) for c in leaves)
        n_levels = len(hierarchy.group_lengths(tree, leaf_len))
        opts = sorted(c for c in roots if len(c) < leaf_len)
        depth = 0
        while opts and len(opts[0]) < leaf_len:
            depth += 1
            grp = _group_select(cfg, k, lang, depth, opts, tree)
            if grp is None:
                break
            scope = grp
            opts = sorted(children.get(grp, []))
        if scope:
            pool = {c: n for c, n in leaves.items() if c.startswith(scope)}

    # Free-text occupation search — overrides the drill-down, searching every
    # occupation by name, code or synonym (Sweden's "Search occupations…";
    # synonyms come from the provider when the classification has them).
    q = st.text_input(i18n.t(cfg, "occ_search", lang), key=k("occsearch"),
                      placeholder=i18n.t(cfg, "occ_search", lang), label_visibility="collapsed")
    if q.strip():
        s = q.strip().lower()
        try:
            syn = prov.occupation_synonyms(lang) or {}
        except Exception:
            syn = {}
        pool = {c: n for c, n in leaves.items()
                if s in n.lower() or s in c.lower() or s in syn.get(c, "")}
        st.caption(i18n.t(cfg, "found_n", lang).format(n=len(pool)) if pool
                   else i18n.t(cfg, "no_match", lang))

    label = f"{n_levels + 1}. {i18n.t(cfg, 'occupations', lang)}" if n_levels \
        else i18n.t(cfg, "occupations", lang)
    opt_to_code = {occ_label(name, code): code for code, name in pool.items()}
    # Order options by occupation CODE (1, 2, 3, … / hierarchy order), not by the
    # translated name — so "Managers (1)" precedes "Professionals (2)" etc.
    picked = st.multiselect(
        label, sorted(opt_to_code, key=lambda lbl: opt_to_code[lbl]), key=k("occ"),
        placeholder=i18n.t(cfg, "occ_placeholder", lang), max_selections=8)
    return tuple(opt_to_code[p] for p in picked), scope


def _clear_all(slug: str) -> None:
    """Clear-all for the Search/Clear row (on_click, so it runs before the
    next script run). Drops the committed query and any open panel, then bumps
    the filter-widget GENERATION: the gen-suffixed keys change, so every
    filter widget REMOUNTS with its default. Merely popping a mounted widget's
    key does not reset it — the browser still holds the widget's state and
    resends the old value on the next interaction (verified). The language
    toggle keeps a plain key on purpose and survives the clear."""
    st.session_state.pop(f"{slug}_committed", None)
    st.session_state.pop(f"{slug}_view", None)
    gen = st.session_state.get(f"{slug}_fltgen", 0)
    st.session_state[f"{slug}_fltgen"] = gen + 1
    for key in [key for key in st.session_state
                if str(key).startswith(f"{slug}_")
                and str(key).endswith(f"_g{gen}")]:
        st.session_state.pop(key, None)      # orphaned old-generation state


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

    # Filter widgets use a GENERATION-suffixed key: Clear-all resets them by
    # bumping the generation (see _clear_all), which changes the keys and
    # remounts the widgets with their defaults. Non-filter state (lang, view,
    # committed, apply, activetab, the buttons) keeps plain k() keys.
    gen = st.session_state.get(k("fltgen"), 0)
    def fk(name):                      # generation-scoped filter-widget key
        return f"{cfg.slug}_{name}_g{gen}"

    live = {"lang": "EN", "sector": (caps.sectors[0] if caps.sectors else ""),
            "sex": "total", "years": (), "occ_codes": (), "scope": ""}

    # A staged selection from the Code-browser confirm dialog (its Search button).
    # Consumed HERE, before the widgets below instantiate, so it may safely write
    # their keys (the documented "set a widget value from outside" pattern) —
    # committing the query, mirroring the chosen filters into the sidebar, and
    # closing the browser view so the results render.
    _apply = st.session_state.pop(k("apply"), None)
    if _apply:
        st.session_state[k("committed")] = _apply["query"]
        st.session_state[fk("occ")] = [_apply["occ_label"]]
        if _apply.get("sector_label") is not None:
            st.session_state[fk("sector")] = _apply["sector_label"]
        if _apply.get("sex") is not None:
            st.session_state[fk("sex")] = _apply["sex"]
        if _apply.get("years_value") is not None:
            st.session_state[fk("years")] = _apply["years_value"]
        for gkey in [key for key in st.session_state
                     if str(key).startswith(f"{cfg.slug}_grp")]:
            st.session_state.pop(gkey, None)     # clear the drill-down
        st.session_state.pop(fk("occsearch"), None)
        st.session_state.pop(_apply.get("vk") or k("view"), None)   # close the view
        if _apply.get("activetab"):              # land on a specific tab (quick access)
            st.session_state[k("activetab")] = _apply["activetab"]

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
        # Beta feedback entry (beta users + admins only; hidden otherwise).
        import feedback as _feedback
        _feedback.feedback_entry(page=cfg.slug, country=cfg.name, cfg=cfg,
                                 key=k("fb_open"))
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
            chosen = st.selectbox(i18n.t(cfg, "sector", lang), sec_labels, key=fk("sector"))
            live["sector"] = caps.sectors[sec_labels.index(chosen)]

        if caps.has_sex:
            # Pass default= only on the first render; once the key exists (incl.
            # a value staged by the confirm dialog) omit it, else Streamlit warns
            # about "default value + Session State API" on every run.
            _sex_kw = {} if fk("sex") in st.session_state else {"default": "total"}
            _sex = st.segmented_control(
                i18n.t(cfg, "sex", lang), ["total", "women", "men"], key=fk("sex"),
                format_func=lambda s: i18n.t(cfg, s, lang, s.capitalize()), **_sex_kw)
            live["sex"] = _sex or "total"

        if caps.year_range:
            y0, y1 = caps.year_range
            years = list(range(y0, y1 + 1))
            if len(years) > 1:
                # value= must ALWAYS be a 2-tuple: it is what puts select_slider
                # in range mode. Omitting it (value=None) registers a SINGLE-value
                # widget, and once the browser echoes the two-handle state back,
                # deserializing it bails out to options[0] — a bare int — and the
                # `a, b =` unpack crashes ("cannot unpack non-iterable int").
                # Seeding from the key's current state keeps a confirm-dialog
                # staged value winning; value never affects the widget identity
                # (select_slider registers with key_as_main_identity).
                _cur = st.session_state.get(fk("years"))
                _val = (tuple(_cur) if isinstance(_cur, (list, tuple)) and len(_cur) == 2
                        else (max(y0, y1 - 2), y1))
                a, b = st.select_slider(i18n.t(cfg, "year_range", lang), options=years,
                                        value=_val, key=fk("years"))
                live["years"] = tuple(y for y in years if a <= y <= b)
            else:
                live["years"] = (y1,)

        # fk, not k: the picker's widgets (drill-down, search text, multiselect)
        # are all filter widgets and must remount on Clear-all.
        live["occ_codes"], live["scope"] = _occupation_picker(cfg, fk, lang)

        if cfg.fetch_mode == "search":
            b1, b2 = st.columns(2)
            if b1.button("🔍 " + i18n.t(cfg, "search", lang), type="primary",
                         use_container_width=True, key=k("go")):
                st.session_state[k("committed")] = dict(live)
                # Close any open exclusive view (User guide / Code browser) so
                # the results render instead of the panel swallowing the run —
                # the legacy Swedish page's behaviour.
                st.session_state.pop(k("view"), None)
            b2.button("✕ " + i18n.t(cfg, "clear", lang),
                      use_container_width=True, key=k("clear"),
                      on_click=_clear_all, args=(cfg.slug,))

    if cfg.fetch_mode == "search":
        committed = st.session_state.get(k("committed"))
        if committed:
            # language is always live so the toggle re-labels without re-searching
            return {**committed, "lang": live["lang"]}
        return {**live, "occ_codes": ()}
    return live
