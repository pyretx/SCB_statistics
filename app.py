"""Salary Explorer — multi-country entrypoint.

Streamlit executes this file on every rerun, then runs the page selected in
st.navigation. Each country app is a standalone page script:
    scb_salaries.py — Sweden (Statistics Sweden / SCB)
    france.py       — France (INSEE Melodi, in development)
Global page config (page_config, logo, shared CSS) lives here, ONCE — country
pages must not call st.set_page_config / st.logo themselves.
"""
import os

import net_fix  # noqa: F401 — force IPv4 BEFORE any HTTP client loads (broken
#                  local IPv6 made every fresh API connection wait ~21s)
import streamlit as st

_ASSETS   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_ICON_PNG = os.path.join(_ASSETS, "logo.png")
_ICON_SVG = os.path.join(_ASSETS, "logo.svg")

st.set_page_config(page_title="Salary Explorer", page_icon=_ICON_PNG, layout="wide")
# NOTE: no st.logo() — each page carries its own brand mark in its header, so a
# global top-left logo would duplicate it (the "two globes" / page-in-page look).

# Global chrome tweaks (all pages):
#  • hide Streamlit's default top "decoration" gradient bar
#  • pull the content up under the (transparent) top toolbar — the default
#    ~6rem top padding left a big empty band above the header/logo, so the
#    landing needed scrolling to see everything. Trim it right down.
st.markdown("""
<style>
  [data-testid='stDecoration']{display:none;}
  [data-testid='stMainBlockContainer']{padding-top:2rem;}
  [data-testid='stSidebarUserContent']{padding-top:1.2rem;}
</style>
""", unsafe_allow_html=True)

# position="hidden" suppresses Streamlit's automatic Home/Sweden/France link
# list in the sidebar (the landing page has no sidebar content of its own, so
# it should show no sidebar at all, matching the mockup). Country pages still
# render their own filters into st.sidebar as before; each adds its own
# "← Home" link (st.page_link) at the top so users aren't stranded without
# the auto nav-list.
_pages = [
    st.Page("landing.py",      title="Home",   default=True),
    st.Page("admin.py",        title="Admin",  url_path="admin"),
    # Public "About" pages (About dropdown in the nav) — data-source transparency,
    # generated from the compliance register; see docs/compliance-framework.md.
    st.Page("methodology.py",  title="Data sources & methodology", url_path="methodology"),
    st.Page("about.py",        title="About Salary Explorer", url_path="about"),
    st.Page("disclaimers.py",  title="Disclaimers & terms", url_path="disclaimers"),
    # Legacy builds (SE_OLD / FR_OLD) — admin-only, reachable from the Admin
    # panel. The public Sweden/France pages are the framework builds below
    # (countries/se2 + countries/fr2, serving /sweden and /france).
    st.Page("scb_salaries.py", title="Sweden (legacy)", url_path="sweden-old"),
    st.Page("france.py",       title="France (legacy)", url_path="france-old"),
]

# Framework-driven country pages (docs/architecture.md) register themselves from
# the registry, ALONGSIDE the legacy Sweden/France pages above. Wrapped so a bug
# in the new framework can never take down the existing app; access is gated per
# page (in-development countries are admin-only).
try:
    from core import registry

    for _cfg in registry.all_countries():
        # File-path pages (thin loaders in countries/<slug>/page.py — the module
        # dir MUST equal the slug) so other pages can link to them client-side
        # (st.page_link keeps the session). Guard PER COUNTRY and log: one broken
        # country must not silently unregister the ones after it.
        try:
            _pages.append(st.Page(f"countries/{_cfg.slug}/page.py",
                                  title=_cfg.name,
                                  url_path=getattr(_cfg, "url_path", "") or _cfg.slug))
        except Exception as _e:
            print(f"[registry] could not register page for '{_cfg.slug}': {_e}")
except Exception as _e:
    print(f"[registry] country registry unavailable: {_e}")

pg = st.navigation(_pages, position="hidden")
pg.run()
