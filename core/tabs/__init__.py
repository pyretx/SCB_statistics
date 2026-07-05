"""Standard tab registry. A country's cfg.tabs picks which appear, in order.
Each tab module exposes render(cfg, stats, query); labels come from i18n
(tab_<id>), so they translate with the language toggle.
"""
from __future__ import annotations

import streamlit as st

from .. import i18n
from . import by_sex, distribution, leaderboard, overview, stats, trend, where

# id -> render_fn. cfg.tabs lists which to enable, in order.
TABS = {
    "overview": overview.render,
    "distribution": distribution.render,
    "sex": by_sex.render,
    "trend": trend.render,
    "where": where.render,
    "leaderboard": leaderboard.render,
    "stats": stats.render,
}
# Canonical framework tab names (the single standard; see docs/architecture.md).
_FALLBACK = {"overview": "Overview", "distribution": "Salary distribution",
             "sex": "By gender", "trend": "Trend", "where": "Where do I stand?",
             "leaderboard": "Leaderboard", "stats": "Basic statistics"}


_TAB_CSS = """
<style>
/* Lazy tab bar: a segmented control styled as Sweden's underlined tabs, so ONLY
   the open tab renders (and only it fetches). */
.st-key-{key} [data-testid="stButtonGroup"] > div[role="radiogroup"] {{
  background:transparent !important; padding:0 !important; gap:2px !important;
  border-bottom:1px solid #E7E9ED; border-radius:0 !important; flex-wrap:wrap; }}
.st-key-{key} [data-testid="stButtonGroup"] button {{
  background:transparent !important; border:0 !important; border-radius:0 !important;
  box-shadow:none !important; color:#5B6472 !important; font-weight:600 !important;
  font-size:15px !important; padding:8px 14px !important;
  border-bottom:2px solid transparent !important; margin-bottom:-1px !important; }}
.st-key-{key} [data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_control"]:hover {{
  color:#0C1119 !important; }}
/* active tab: must out-specify the base `button` rule above (both !important),
   so include `button[testid]` — the underline was being overridden otherwise. */
.st-key-{key} [data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"] {{
  color:#0A63A6 !important; background:transparent !important;
  border-bottom:2px solid #0A63A6 !important; }}
</style>
"""


def render_tabs(cfg, stats, query):
    lang = query.get("lang", "EN")
    enabled = [t for t in cfg.tabs if t in TABS] or ["overview"]
    if len(enabled) == 1:
        TABS[enabled[0]](cfg, stats, query)
        return
    labels = {t: i18n.t(cfg, f"tab_{t}", lang, _FALLBACK.get(t, t)) for t in enabled}
    key = f"{cfg.slug}_activetab"
    st.markdown(_TAB_CSS.format(key=key), unsafe_allow_html=True)
    active = st.segmented_control(key, enabled, default=enabled[0],
                                  format_func=lambda t: labels[t],
                                  key=key, label_visibility="collapsed") or enabled[0]
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    TABS[active](cfg, stats, query)          # render ONLY the open tab (lazy)
