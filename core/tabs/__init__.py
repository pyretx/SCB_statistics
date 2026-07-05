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
_FALLBACK = {"overview": "Overview", "distribution": "Distribution",
             "sex": "By sex", "trend": "Trend", "where": "Where do I stand?",
             "leaderboard": "Leaderboard", "stats": "Basic statistics"}


def render_tabs(cfg, stats, query):
    lang = query.get("lang", "EN")
    enabled = [t for t in cfg.tabs if t in TABS] or ["overview"]
    if len(enabled) == 1:
        TABS[enabled[0]](cfg, stats, query)
        return
    labels = [i18n.t(cfg, f"tab_{t}", lang, _FALLBACK.get(t, t)) for t in enabled]
    for obj, tid in zip(st.tabs(labels), enabled):
        with obj:
            TABS[tid](cfg, stats, query)
