"""Public page — About Salary Explorer. Static content from content/about.toml."""
from __future__ import annotations

import streamlit as st

import content
import pubpage

A = content.load("about")["about"]

pubpage.inject_base()
pubpage.top(active="about")

st.markdown(f'<div class="pp-eyebrow">{A["eyebrow"]}</div>'
            f'<div class="pp-h1">{A["title"]}</div>', unsafe_allow_html=True)
st.write("")

for key in ("purpose", "data", "enhanced", "coverage", "methodology", "limitations", "contact"):
    sec = A[key]
    st.markdown(f'<div class="pp-card"><div class="pp-sec-h">{sec["heading"]}</div>'
                f'<div class="pp-sec-b">{sec["body"]}</div></div>', unsafe_allow_html=True)

_q = A["qvistin"]
st.markdown(
    f'<div class="pp-card" style="background:rgba(10,99,166,.05);border-color:rgba(10,99,166,.20);">'
    f'<div class="pp-sec-b" style="font-weight:600;color:#0C1119;">{_q["line"]}</div>'
    f'<div class="pp-sec-b" style="margin-top:6px;">'
    f'<a href="{_q["link_url"]}" target="_blank" rel="noopener" '
    f'style="color:#0A63A6;text-decoration:none;font-weight:600;">{_q["link"]}</a></div></div>',
    unsafe_allow_html=True)
