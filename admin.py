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
import content

_ADMIN_ROLES = ("admin", "master")
_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_u = st.session_state.get("auth_user")
_role = (_u or {}).get("role", "")

# All static text lives in content/admin.toml (+ the brand name in home.toml).
_H = content.load("admin")["header"]
_B = content.load("home").get("brand", {})
_BRAND = _B.get("name", "Salary Explorer")
_TAGLINE = _B.get("tagline", "")


def _logo_uri() -> str:
    with open(os.path.join(_ASSETS, "logo_mark.svg"), "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")


st.markdown(admin_ui.CSS, unsafe_allow_html=True)   # so the header tab pills are styled too

# ── Brand row (logo + wordmark + ADMIN badge · Back to home) ──────────────────
# Top spacer so the right-aligned back link clears Streamlit's top toolbar.
st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
_bl, _br = st.columns([3, 1], vertical_alignment="center")
with _br:
    st.page_link("landing.py", label=_H["back"], icon=":material/arrow_back:")
with _bl:
    _tag_html = (f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:8px;'
                 f'font-weight:600;letter-spacing:.14em;color:#8A919D;line-height:1.2;">'
                 f'{_TAGLINE}</span>' if _TAGLINE else "")
    # The whole brand block (logo · wordmark · tagline) is a home link, same as
    # on the country pages: an invisible st.page_link overlaid on the HTML (a
    # raw <a href> would full-reload the browser and drop the signed-in session).
    st.markdown("""<style>
    /* min-height: the brand HTML overflows Streamlit's collapsed markdown slot
       (~18px), so without it the click overlay would only cover the top half. */
    [class*="st-key-adm_brand"]{ position:relative; width:fit-content; min-height:36px; }
    [class*="st-key-adm_brand"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]){
      position:absolute;inset:0;margin:0;width:100% !important;height:100% !important;}
    [class*="st-key-adm_brand"] [data-testid="stPageLink"]{position:absolute;inset:0;
      width:100% !important;height:100% !important;}
    [class*="st-key-adm_brand"] [data-testid="stPageLink"] a{position:absolute;inset:0;
      width:100% !important;height:100% !important;
      background:transparent !important;border-radius:8px;}
    [class*="st-key-adm_brand"] [data-testid="stPageLink"] a p,
    [class*="st-key-adm_brand"] [data-testid="stPageLink"] a span{display:none;}
    </style>""", unsafe_allow_html=True)
    with st.container(key="adm_brand"):
        st.markdown(f"""
    <div style="display:flex;align-items:center;gap:11px;">
      <img src="{_logo_uri()}" alt="{_BRAND}" style="width:32px;height:32px;flex:none;
           border-radius:8px;box-shadow:0 2px 6px rgba(10,99,166,.35);">
      <div style="display:flex;flex-direction:column;gap:2px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-weight:700;font-size:16px;letter-spacing:-.01em;color:#0C1119;
                line-height:1.15;">{_BRAND}</span>
          <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;
                letter-spacing:.08em;color:#0A63A6;background:rgba(10,99,166,.10);padding:3px 8px;
                border-radius:5px;">{_H["badge"]}</span>
        </div>
        {_tag_html}
      </div>
    </div>
    """, unsafe_allow_html=True)
        st.page_link("landing.py", label=_BRAND)

st.markdown('<div style="height:1px;background:#E7E9ED;margin:14px 0 18px;"></div>',
            unsafe_allow_html=True)

# ── Gate ─────────────────────────────────────────────────────────────────────
if _role not in _ADMIN_ROLES:
    st.info(_H["gate"])
    st.page_link("landing.py", label=_H["go_home"], icon=":material/home:")
    st.stop()

# ── Title row (eyebrow + H1 · section tabs) ───────────────────────────────────
_tl, _tr = st.columns([1.5, 1], vertical_alignment="center")
with _tl:
    st.markdown(
        "<div style='font-family:\"JetBrains Mono\",monospace;font-size:11px;font-weight:600;"
        f"letter-spacing:.16em;text-transform:uppercase;color:#0A63A6;margin-bottom:4px;'>"
        f"{_H['eyebrow']}</div>"
        "<div style='font-size:30px;font-weight:800;letter-spacing:-.02em;color:#0C1119;'>"
        f"{_H['title']}</div>",
        unsafe_allow_html=True)
with _tr:
    _section = admin_ui.section_selector()

st.write("")
admin_ui.render_body(_section)
