"""Standard tab registry. A country's cfg.tabs picks which appear, in order.
Each tab module exposes render(cfg, stats, query).
"""
from __future__ import annotations

import streamlit as st

from . import overview

# id -> (label, render_fn). More tabs land here in later phases.
TABS = {
    "overview": ("Overview", overview.render),
}


def render_tabs(cfg, stats, query):
    enabled = [t for t in cfg.tabs if t in TABS] or ["overview"]
    if len(enabled) == 1:
        TABS[enabled[0]][1](cfg, stats, query)
        return
    objs = st.tabs([TABS[t][0] for t in enabled])
    for obj, tid in zip(objs, enabled):
        with obj:
            TABS[tid][1](cfg, stats, query)
