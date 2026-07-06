"""Full-page Admin panel — Overview · Data sources · Users.

Gated to admin/master. Reachable at /admin and from the landing top row (an
'Admin' button shown only to admins). The section UI lives in admin_ui.py (a
plain module) so it can be reused (e.g. Sweden's 'Manage users' dialog).
"""
import base64
import os

import streamlit as st

import admin_ui
import content

_ADMIN_ROLES = ("admin", "master")
_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_u = st.session_state.get("auth_user")
_role = (_u or {}).get("role", "")


def _logo_uri() -> str:
    with open(os.path.join(_ASSETS, "logo_mark.svg"), "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")


_BRAND = content.load("home").get("brand", {"name": "Salary Explorer", "badge": "BETA"})

# ── Header ───────────────────────────────────────────────────────────────────
# Top spacer so the right-aligned back link clears Streamlit's top-right toolbar
# (Deploy / menu), which otherwise clips it.
st.markdown("<div style='height:2.2rem'></div>", unsafe_allow_html=True)
_bl, _br = st.columns([3, 1], vertical_alignment="center")
with _br:
    st.page_link("landing.py", label="Back to home", icon=":material/arrow_back:")
with _bl:
    # Brand mark (logo + wordmark + BETA), shown once, matching the landing.
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:11px;">
      <img src="{_logo_uri()}" alt="Salary Explorer" style="width:32px;height:32px;flex:none;
           border-radius:8px;box-shadow:0 2px 6px rgba(10,99,166,.35);">
      <span style="font-weight:700;font-size:16px;letter-spacing:-.01em;color:#0C1119;">{_BRAND["name"]}</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;
            letter-spacing:.06em;color:#0A63A6;background:rgba(10,99,166,.10);padding:3px 7px;
            border-radius:5px;">{_BRAND["badge"]}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown(
    "<div style='display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-top:12px;'>"
    "<span style='font-size:26px;font-weight:800;letter-spacing:-.02em;color:#0C1119;'>"
    "Admin panel</span>"
    "<span style='font-family:\"JetBrains Mono\",monospace;font-size:11px;letter-spacing:.12em;"
    "text-transform:uppercase;color:#8A919D;'>control room</span></div>",
    unsafe_allow_html=True)

st.divider()

# ── Gate ─────────────────────────────────────────────────────────────────────
if _role not in _ADMIN_ROLES:
    st.info("🔒 The admin panel is available to administrators only. "
            "Sign in with an admin account from the home page.")
    st.page_link("landing.py", label="Go to home", icon=":material/home:")
    st.stop()

admin_ui.render()
