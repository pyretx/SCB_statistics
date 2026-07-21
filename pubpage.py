"""Shared chrome for the public "About" pages (Data sources & methodology,
About Salary Explorer, Disclaimers & terms).

Each of those is a standalone Streamlit page script (registered in app.py). They
all call ``pubpage.inject_base()`` then ``pubpage.top(active=...)`` so the brand
row, fonts, card styling and the little cross-page nav are defined once here.

No st.set_page_config / st.logo (app.py owns those). Text lives in
content/about.toml (nav section) + each page's own section.
"""
from __future__ import annotations

import base64
import os

import streamlit as st

import content

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
BLUE = "#0A63A6"

_PAGES = {
    "methodology": ("methodology.py", "methodology"),
    "about": ("about.py", "about"),
    "plans": ("plans.py", "plans"),
    "disclaimers": ("disclaimers.py", "disclaimers"),
}


def nav_text() -> dict:
    return content.load("about")["nav"]


def _logo_uri() -> str:
    with open(os.path.join(_ASSETS, "logo_mark.svg"), "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")


def inject_base():
    """Fonts + base type + the card/label styling shared by the About pages.
    Scoped per page run (each Streamlit page is its own script), so it never
    bleeds into the data-explorer pages."""
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
      [data-testid="stMainBlockContainer"]{max-width:1000px;margin:0 auto;}
      .pp-mono{font-family:'JetBrains Mono',monospace;}
      .pp-eyebrow{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;
        letter-spacing:.16em;color:#0A63A6;margin-bottom:10px;}
      .pp-h1{font-size:38px;font-weight:800;letter-spacing:-.025em;color:#0C1119;
        line-height:1.08;margin:0 0 10px;}
      .pp-intro{font-size:16px;color:#4A525F;line-height:1.6;max-width:680px;margin-bottom:6px;}
      .pp-principle{font-size:14.5px;color:#0C1119;line-height:1.55;background:rgba(10,99,166,.06);
        border-left:3px solid #0A63A6;border-radius:0 10px 10px 0;padding:14px 18px;
        margin:18px 0 4px;max-width:720px;}
      .pp-card{background:#fff;border:1px solid #E7E9ED;border-radius:14px;padding:22px 24px;
        margin-bottom:16px;}
      .pp-sec-h{font-size:19px;font-weight:700;color:#0C1119;margin:0 0 8px;}
      .pp-sec-b{font-size:14.5px;color:#4A525F;line-height:1.6;}
      .pp-row{display:flex;gap:16px;padding:13px 2px;border-top:1px solid #EEF0F3;}
      .pp-row:first-child{border-top:none;}
      .pp-lbl{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
        color:#0A63A6;letter-spacing:.04em;text-transform:uppercase;width:180px;flex:0 0 auto;
        padding-top:2px;}
      .pp-val{font-size:14px;color:#26303C;line-height:1.55;min-width:0;}
      .pp-val a{color:#0A63A6;text-decoration:none;}
      .pp-val a:hover{text-decoration:underline;}
      .pp-badge{display:inline-flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;
        font-size:10.5px;font-weight:600;letter-spacing:.03em;padding:2px 8px;border-radius:5px;
        white-space:nowrap;}
      .pp-badge-off{color:#1B6FB0;background:rgba(10,99,166,.10);}
      .pp-badge-der{color:#B26A00;background:rgba(178,106,0,.13);}
      .pp-tf{padding:11px 0;border-top:1px solid #EEF0F3;}
      .pp-tf:first-child{border-top:none;}
      .pp-tf-h{display:flex;align-items:center;gap:9px;margin-bottom:3px;}
      .pp-tf-name{font-weight:600;font-size:14px;color:#0C1119;}
      .pp-tf-note{font-size:13px;color:#5B6472;line-height:1.5;}
      .pp-foot{margin-top:30px;padding-top:16px;border-top:1px solid #EEF0F3;
        font-size:12.5px;color:#8A919D;}
    </style>
    """, unsafe_allow_html=True)


def top(active: str):
    """Brand row + a compact cross-page nav (Home · the three About pages).
    ``active`` is one of _PAGES keys (or '' for none). The brand block (logo +
    wordmark + POWERED-BY tagline) is a clickable Home link — same invisible
    page_link overlay pattern as admin.py."""
    N = nav_text()
    B = content.load("home").get("brand", {})
    brand = B.get("name", "Salary Explorer")
    tagline = B.get("tagline", "")

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    # Invisible page_link stretched over the brand HTML → the whole logo+wordmark
    # block is a Home link (a raw <a> would full-reload and drop the session).
    st.markdown("""<style>
    [class*="st-key-pp_brand"]{ position:relative; width:fit-content; min-height:34px; }
    [class*="st-key-pp_brand"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]){
      position:absolute;inset:0;margin:0;width:100% !important;height:100% !important;}
    [class*="st-key-pp_brand"] [data-testid="stPageLink"]{position:absolute;inset:0;
      width:100% !important;height:100% !important;}
    [class*="st-key-pp_brand"] [data-testid="stPageLink"] a{position:absolute;inset:0;
      width:100% !important;height:100% !important;background:transparent !important;border-radius:8px;}
    [class*="st-key-pp_brand"] [data-testid="stPageLink"] a p,
    [class*="st-key-pp_brand"] [data-testid="stPageLink"] a span{display:none;}
    </style>""", unsafe_allow_html=True)

    left, right = st.columns([1.5, 2.5], vertical_alignment="center")
    with left:
        _tag = (f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:8px;'
                f'font-weight:600;letter-spacing:.14em;color:#8A919D;line-height:1.2;">'
                f'{tagline}</span>' if tagline else "")
        with st.container(key="pp_brand"):
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:11px;">
              <img src="{_logo_uri()}" alt="{brand}" style="width:32px;height:32px;flex:none;
                   border-radius:8px;box-shadow:0 2px 6px rgba(10,99,166,.35);">
              <div style="display:flex;flex-direction:column;gap:2px;">
                <span style="font-weight:700;font-size:16px;letter-spacing:-.01em;color:#0C1119;
                      line-height:1.15;">{brand}</span>
                {_tag}
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("landing.py", label=brand)
    with right:
        # Right-aligned, non-truncating nav (small leading spacer pushes links
        # right; short labels from content/about.toml + generous columns keep each
        # on one line — a too-narrow column made "Home" truncate to "H").
        st.markdown("<style>[data-testid='stPageLink'] a p{white-space:nowrap;}</style>",
                    unsafe_allow_html=True)
        cols = st.columns([0.1, 1.1, 1.5, 1.0, 1.0, 1.4])
        cols[1].page_link("landing.py", label=N["home"], icon=":material/home:")
        cols[2].page_link("methodology.py", label=N.get("methodology_short", N["methodology"]))
        cols[3].page_link("about.py", label=N.get("about_short", N["about"]))
        cols[4].page_link("plans.py", label=N.get("plans_short", N.get("plans", "What you get")))
        cols[5].page_link("disclaimers.py", label=N.get("disclaimers_short", N["disclaimers"]))
    st.markdown('<div style="height:1px;background:#E7E9ED;margin:14px 0 22px;"></div>',
                unsafe_allow_html=True)
