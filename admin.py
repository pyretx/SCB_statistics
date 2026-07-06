"""Full-page Admin panel — Overview · Data sources · Users.

Gated to admin/master. Reachable at /admin and from the landing top row (an
'Admin' button shown only to admins). The section UI lives in admin_ui.py (a
plain module) so it can be reused (e.g. Sweden's 'Manage users' dialog).
"""
import streamlit as st

import admin_ui

_ADMIN_ROLES = ("admin", "master")
_u = st.session_state.get("auth_user")
_role = (_u or {}).get("role", "")

# ── Header ───────────────────────────────────────────────────────────────────
# Top spacer so the right-aligned back link clears Streamlit's top-right toolbar
# (Deploy / menu), which otherwise clips it.
st.markdown("<div style='height:2.2rem'></div>", unsafe_allow_html=True)
_bl, _br = st.columns([3, 1], vertical_alignment="center")
with _br:
    st.page_link("landing.py", label="Back to home", icon=":material/arrow_back:")
with _bl:
    st.markdown(
        "<div style='display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;'>"
        "<span style='font-size:26px;font-weight:800;letter-spacing:-.02em;color:#0C1119;'>"
        "Admin panel</span>"
        "<span style='font-family:\"JetBrains Mono\",monospace;font-size:11px;letter-spacing:.12em;"
        "text-transform:uppercase;color:#8A919D;'>Salary Explorer · control room</span></div>",
        unsafe_allow_html=True)

st.divider()

# ── Gate ─────────────────────────────────────────────────────────────────────
if _role not in _ADMIN_ROLES:
    st.info("🔒 The admin panel is available to administrators only. "
            "Sign in with an admin account from the home page.")
    st.page_link("landing.py", label="Go to home", icon=":material/home:")
    st.stop()

admin_ui.render()
