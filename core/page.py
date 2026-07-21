"""render_country(cfg) — the ONE shared page skeleton.

Access gate → sidebar (filters) → header → tabs, with shared empty/loading/error
states. Exclusive full-page views (User guide, Code browser) render into the
view-mount and take over the main area. Countries never write this; they supply
a config + provider.
"""
from __future__ import annotations

import streamlit as st

import theme

from . import access, agg, i18n, panels, sidebar, states, tabs


def _header(cfg, lang):
    title = i18n.t(cfg, "title", lang, cfg.name)
    caption = i18n.t(cfg, "caption", lang, cfg.caption)
    st.markdown(f"""
    <div style="margin-bottom:6px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
                  letter-spacing:.16em;color:#0A63A6;margin-bottom:10px;">{cfg.eyebrow}</div>
      <div style="display:flex;align-items:center;gap:14px;">
        <img class="se-hflag" src="{theme.flag_uri(cfg.iso)}" alt="{cfg.name} flag">
        <h1 style="margin:0;font-size:34px;font-weight:800;letter-spacing:-.025em;
                   color:#0C1119;line-height:1.05;">{title}</h1>
      </div>
      <p style="margin:8px 0 0;font-size:14px;color:#7A828F;">{caption}</p>
    </div>
    """, unsafe_allow_html=True)


_OFFICIAL_BADGE = ('<span style="display:inline-flex;align-items:center;font-family:'
                   "'JetBrains Mono',monospace;font-size:10.5px;font-weight:600;"
                   'padding:1px 7px;border-radius:5px;color:#1B6FB0;background:rgba(10,99,166,.10);">'
                   '{txt}</span>')
_DERIVED_BADGE = ('<span style="display:inline-flex;align-items:center;font-family:'
                  "'JetBrains Mono',monospace;font-size:10.5px;font-weight:600;"
                  'padding:1px 7px;border-radius:5px;color:#B26A00;background:rgba(178,106,0,.13);">'
                  '{txt}</span>')

# transform_type → default English friendly name (per-country JA/etc. inherit these)
_TF_LABEL = {
    "currency_conversion": "Currency conversion", "period_conversion": "Monthly / annual conversion",
    "inflation_adjustment": "Inflation adjustment", "aggregation": "Aggregation",
    "ranking": "Ranking", "projection": "Projection", "reclassification": "Reclassification",
    "cross_country_standardisation": "Cross-country standardisation",
}


def _sources_panel(cfg, lang):
    """Phase 4 — derived-data labelling. A compact 'Sources & methods' expander
    driven by the compliance register (single source of truth): official provider/
    dataset/licence/attribution + each Salary Explorer calculation tagged Official
    vs Salary-Explorer-calculation. When a country has SE calculations, an inline
    note under the header points to it. Fully guarded — if the country isn't in the
    register (or the DB is unreachable) nothing extra renders."""
    try:
        import html as _html
        import compliance as comp
        rec = comp.country_notes(cfg.slug)
    except Exception:
        return
    if not rec:
        return

    def esc(x):
        return _html.escape(str(x)) if x is not None else ""

    off_txt = i18n.t(cfg, "badge_official", lang, "Official")
    der_txt = i18n.t(cfg, "badge_se_calc", lang, "Salary Explorer calculation")
    transforms = rec.get("transformations") or []
    se_calcs = [t for t in transforms if t.get("origin") == "salary_explorer"]

    # Inline note under the header when there are SE calculations.
    if se_calcs:
        st.markdown(
            f'<div style="font-size:12.5px;color:#7A828F;margin:-2px 0 10px;">ⓘ '
            f'{i18n.t(cfg, "derived_note", lang, "Some figures are Salary Explorer calculations")} — '
            f'{i18n.t(cfg, "see_sources", lang, "see Sources &amp; methods below")}.</div>',
            unsafe_allow_html=True)

    with st.expander(i18n.t(cfg, "sources_methods", lang, "Sources & methods")):
        prov = esc(rec.get("provider_name"))
        ds = esc(rec.get("dataset_title"))
        if rec.get("dataset_url"):
            ds = f'[{ds}]({rec["dataset_url"]})'
        st.markdown(f"**{esc(rec.get('provider_name') or '')}** — {ds}")
        if rec.get("reference_period"):
            st.caption(esc(rec["reference_period"]))
        lic = esc(rec.get("licence_summary_plain") or rec.get("licence_name"))
        if rec.get("licence_url") and rec.get("licence_name"):
            lic += f' ([{esc(rec["licence_name"])}]({rec["licence_url"]}))'
        if lic:
            st.markdown(f"**{i18n.t(cfg, 'licence', lang, 'Licence')}:** {lic}")
        if rec.get("required_attribution_text"):
            st.markdown(f"**{i18n.t(cfg, 'attribution', lang, 'Attribution')}:** "
                        f"`{esc(rec['required_attribution_text'])}`")

        # Original values + each transformation, badged.
        rows = []
        if rec.get("displayed_original_values"):
            rows.append(f'<div style="padding:6px 0;">'
                        + _OFFICIAL_BADGE.format(txt=off_txt)
                        + f' <span style="font-size:13.5px;color:#26303C;">{esc(rec["displayed_original_values"])}</span></div>')
        for t in transforms:
            is_off = t.get("origin") == "source_provided"
            badge = (_OFFICIAL_BADGE if is_off else _DERIVED_BADGE).format(
                txt=off_txt if is_off else der_txt)
            name = i18n.t(cfg, f"tf_{t.get('transform_type')}", lang,
                          _TF_LABEL.get(t.get("transform_type"), t.get("transform_type") or ""))
            note = esc(t.get("method_note"))
            rows.append(f'<div style="padding:6px 0;border-top:1px solid #EEF0F3;">{badge} '
                        f'<span style="font-size:13.5px;font-weight:600;color:#0C1119;">{name}</span>'
                        f'<div style="font-size:12.5px;color:#5B6472;margin-top:2px;">{note}</div></div>')
        if rows:
            st.markdown("".join(rows), unsafe_allow_html=True)


def render_country(cfg):
    """Entry point used by app.py: render one country page from its config."""
    query = sidebar.render_sidebar(cfg)   # always render the sidebar/switcher
    access.require_access(cfg)            # …then gate the main area (stops if denied)
    lang = query.get("lang", "EN")

    _header(cfg, lang)                   # header ALWAYS first, at the top of the page
    _sources_panel(cfg, lang)            # Phase 4: source + derived-data labelling

    view = states.view_mount()           # exclusive-view mount (guides/browsers)
    vk = f"{cfg.slug}_view"
    if st.session_state.get(vk) in ("guide", "browser"):
        with view.container():
            panels.render(cfg, st.session_state[vk], lang, vk, query)
        return

    occ_codes = tuple(query.get("occ_codes", ()))
    if not occ_codes:
        # Default start page: the prompt + the code browser inline (Sweden-style),
        # so the empty state is useful rather than blank.
        with view.container():
            states.prompt(i18n.t(cfg, "prompt_select", lang))
            if cfg.landing_extra:
                cfg.landing_extra(cfg, lang, query)
            if panels.browsable(cfg, lang):
                panels.default_browser(cfg, lang, query)
        return

    with states.loading():
        stats = cfg.provider.occupation_stats(
            sector=query.get("sector", ""), occ_codes=occ_codes,
            sex=query.get("sex", "total"), years=tuple(query.get("years", ())),
            lang=lang)

    if stats is None or stats.empty:
        states.no_data()
        return

    # Aggregate-selection toggle (standard, Sweden-style): collapse several
    # picked occupations into one headcount-weighted series across all tabs.
    if len(occ_codes) > 1:
        if st.toggle(i18n.t(cfg, "agg_toggle", lang,
                            "Aggregate selection (headcount-weighted)"),
                     key=f"{cfg.slug}_agg"):
            query = {**query, "aggregate": True}
            tot0 = stats[stats["dimension"] == "total"]
            # current headcounts by series name — the trend tab's weights
            st.session_state[f"{cfg.slug}_aggweights"] = {
                str(r["occ_name"]): (float(r["count"]) if r["count"] == r["count"]
                                     and r["count"] is not None else 0)
                for _, r in tot0.iterrows()}
            stats = agg.collapse_stats(stats, agg.agg_name(cfg, lang, len(occ_codes)))

    # A source can return rows with every salary cell null — e.g. an
    # occupation×sector combo the agency suppresses (SSB has no private-sector
    # figure for ambulance workers). Show a clear message, not a bare table.
    tot = stats[stats["dimension"] == "total"]
    vcols = [c for c in ("mean", "median", "p10", "p25", "p75", "p90") if c in tot]
    if tot.empty or not tot[vcols].notna().to_numpy().any():
        states.no_data(i18n.no_data(cfg, lang))
        return

    tabs.render_tabs(cfg, stats, query)
