"""Public page — Disclaimers & terms. Static content from content/about.toml."""
from __future__ import annotations

import streamlit as st

import content
import pubpage

D = content.load("about")["disclaimers"]

pubpage.inject_base()
pubpage.top(active="disclaimers")

st.markdown(f'<div class="pp-eyebrow">{D["eyebrow"]}</div>'
            f'<div class="pp-h1">{D["title"]}</div>'
            f'<div class="pp-intro">{D["intro"]}</div>', unsafe_allow_html=True)
st.write("")

rows = "".join(
    f'<div class="pp-row"><div class="pp-lbl">{heading}</div>'
    f'<div class="pp-val">{body}</div></div>'
    for heading, body in D["items"])
st.markdown(f'<div class="pp-card">{rows}</div>', unsafe_allow_html=True)
