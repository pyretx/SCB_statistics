"""render_country(cfg) — the ONE shared page skeleton.

Access gate → sidebar (filters) → header → tabs, with shared empty/loading/error
states. Countries never write this; they supply a config + provider.
"""
from __future__ import annotations

import streamlit as st

import theme

from . import access, sidebar, states, tabs


def _header(cfg):
    st.markdown(f"""
    <div style="margin-bottom:6px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
                  letter-spacing:.16em;color:#0A63A6;margin-bottom:10px;">{cfg.eyebrow}</div>
      <div style="display:flex;align-items:center;gap:14px;">
        <img class="se-hflag" src="{theme.flag_uri(cfg.iso)}" alt="{cfg.name} flag">
        <h1 style="margin:0;font-size:34px;font-weight:800;letter-spacing:-.025em;
                   color:#0C1119;line-height:1.05;">{cfg.L('title', cfg.name)}</h1>
      </div>
      <p style="margin:8px 0 0;font-size:14px;color:#7A828F;">{cfg.caption}</p>
    </div>
    """, unsafe_allow_html=True)


def render_country(cfg):
    """Entry point used by app.py: render one country page from its config."""
    query = sidebar.render_sidebar(cfg)   # always render the sidebar/switcher
    access.require_access(cfg)            # …then gate the main area (stops if denied)
    _header(cfg)

    view = states.view_mount()           # exclusive-view mount (guides/browsers later)
    occ_codes = tuple(query.get("occ_codes", ()))
    if not occ_codes:
        with view.container():
            states.prompt("Select at least one occupation in the sidebar to get started.")
        return

    with states.loading():
        stats = cfg.provider.occupation_stats(
            sector=query.get("sector", ""), occ_codes=occ_codes,
            sex=query.get("sex", "total"), years=tuple(query.get("years", ())))

    if stats is None or stats.empty:
        states.no_data()
        return

    # A source can return rows with every salary cell null — e.g. an
    # occupation×sector combo the agency suppresses (SSB has no private-sector
    # figure for ambulance workers). Show a clear message, not a bare table.
    tot = stats[stats["dimension"] == "total"]
    vcols = [c for c in ("mean", "median", "p10", "p25", "p75", "p90") if c in tot]
    if tot.empty or not tot[vcols].notna().to_numpy().any():
        states.no_data(
            "No figures are published for this combination of occupation, "
            "sector, sex and year. Try “All sectors” or adjust the selection.")
        return

    tabs.render_tabs(cfg, stats, query)
