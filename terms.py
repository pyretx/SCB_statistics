"""Public page — Terms of Service & Privacy Policy. Static content from
content/terms.toml. The Create-account dialog links here; auth.sign_up()
stamps content/terms.toml [meta] terms_version onto every new account
(user_metadata.accepted_terms_version / accepted_terms_at). The two documents
are versioned separately (see the toml header)."""
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


def _card(sec: dict):
    """One document card. Items are [heading, body] or [heading, body, anchor]
    (anchor makes the row linkable as /terms#anchor). Each document shows its
    own version + effective date under the heading."""
    rows = "".join(
        f'<div class="pp-row"{f" id=\"{item[2]}\"" if len(item) > 2 else ""}>'
        f'<div class="pp-lbl">{item[0]}</div>'
        f'<div class="pp-val">{item[1]}</div></div>'
        for item in sec["items"])
    ver = P["verline"].format(version=sec["version"], effective=sec["effective"])
    st.markdown(f'<div class="pp-card" id="{sec["anchor"]}">'
                f'<div class="pp-sec-h">{sec["heading"]}</div>'
                f'<div class="pp-mono" style="font-size:11px;color:#8A919D;'
                f'margin:-2px 0 8px;">{ver}</div>{rows}</div>',
                unsafe_allow_html=True)


_card(T["terms"])
_card(T["privacy"])

st.markdown(f'<div class="pp-foot">{P["footer_note"]}</div>', unsafe_allow_html=True)

# CTA — signed-out readers (usually here from the create-account dialog) get a
# button back to registration: reopens the dialog on the landing page (same
# session keys the landing header buttons set; pattern copied from plans.py).
if st.session_state.get("auth_user") is None:
    st.write("")
    if st.button(T["cta"]["create_account"], type="primary"):
        _AF = content.load("auth")["form"]
        st.session_state["_auth_mode"] = _AF["mode_create"]
        st.session_state["_show_auth"] = True
        st.switch_page("landing.py")
