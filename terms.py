"""Public page — Terms of Service & Privacy Policy. Static content from
content/terms.toml. The Create-account dialog links here; auth.sign_up()
stamps content/terms.toml [meta] version onto every new account
(user_metadata.accepted_terms_version / accepted_terms_at)."""
from __future__ import annotations

import streamlit as st

import content
import pubpage

T = content.load("terms")

pubpage.inject_base()
pubpage.top(active="terms")

P = T["page"]
st.markdown(f'<div class="pp-eyebrow">{P["eyebrow"]}</div>'
            f'<div class="pp-h1">{P["title"]}</div>'
            f'<div class="pp-intro">{P["intro"]}</div>', unsafe_allow_html=True)
st.write("")


def _card(sec: dict, anchor: str = ""):
    rows = "".join(
        f'<div class="pp-row"><div class="pp-lbl">{heading}</div>'
        f'<div class="pp-val">{body}</div></div>'
        for heading, body in sec["items"])
    aid = f' id="{anchor}"' if anchor else ""
    st.markdown(f'<div class="pp-card"{aid}>'
                f'<div class="pp-sec-h">{sec["heading"]}</div>{rows}</div>',
                unsafe_allow_html=True)


_card(T["terms"])
_card(T["privacy"], anchor="privacy")

st.markdown(f'<div class="pp-foot">{P["updated"].format(version=T["meta"]["version"])}</div>',
            unsafe_allow_html=True)
