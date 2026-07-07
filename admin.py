"""Full-page Admin panel — Overview · Data sources · Users.

Gated to admin/master. Reachable at /admin and from the landing top row (an
'Admin' button shown only to admins). The section UI lives in admin_ui.py (a
plain module) so it can be reused (e.g. Sweden's 'Manage users' dialog).

Visual design follows the approved Admin-panel mockup.
"""
import base64
import os

import streamlit as st

import admin_ui

_ADMIN_ROLES = ("admin", "master")
_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_u = st.session_state.get("auth_user")
_role = (_u or {}).get("role", "")


def _logo_uri() -> str:
    with open(os.path.join(_ASSETS, "logo_mark.svg"), "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")


st.markdown(admin_ui.CSS, unsafe_allow_html=True)   # so the header tab pills are styled too

# ── Brand row (logo + wordmark + ADMIN badge · Back to home) ──────────────────
# Top spacer so the right-aligned back link clears Streamlit's top toolbar.
st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
_bl, _br = st.columns([3, 1], vertical_alignment="center")
with _br:
    st.page_link("landing.py", label="Back to home", icon=":material/arrow_back:")
with _bl:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:11px;">
      <img src="{_logo_uri()}" alt="Salary Explorer" style="width:32px;height:32px;flex:none;
           border-radius:8px;box-shadow:0 2px 6px rgba(10,99,166,.35);">
      <span style="font-weight:700;font-size:16px;letter-spacing:-.01em;color:#0C1119;">Salary Explorer</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;
            letter-spacing:.08em;color:#0A63A6;background:rgba(10,99,166,.10);padding:3px 8px;
            border-radius:5px;">ADMIN</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:#E7E9ED;margin:14px 0 18px;"></div>',
            unsafe_allow_html=True)

# ── Gate ─────────────────────────────────────────────────────────────────────
if _role not in _ADMIN_ROLES:
    st.info("🔒 The admin panel is available to administrators only. "
            "Sign in with an admin account from the home page.")
    st.page_link("landing.py", label="Go to home", icon=":material/home:")
    st.stop()

# ── Title row (eyebrow + H1 · section tabs) ───────────────────────────────────
_tl, _tr = st.columns([1.5, 1], vertical_alignment="center")
with _tl:
    st.markdown(
        "<div style='font-family:\"JetBrains Mono\",monospace;font-size:11px;font-weight:600;"
        "letter-spacing:.16em;text-transform:uppercase;color:#0A63A6;margin-bottom:4px;'>"
        "Control room</div>"
        "<div style='font-size:30px;font-weight:800;letter-spacing:-.02em;color:#0C1119;'>"
        "Admin panel</div>",
        unsafe_allow_html=True)
with _tr:
    _section = admin_ui.section_selector()

st.write("")
admin_ui.render_body(_section)
