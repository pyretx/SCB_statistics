"""Landing page — pick a country's salary statistics, or sign in / create a
free account. Visual design follows the approved mockup (Hanken Grotesk +
JetBrains Mono, blue #0A63A6 accent) as closely as Streamlit's own widgets
allow: native st.container(border=True) cards + st.button for real navigation
(the mockup's onclick handlers can't fire through st.markdown — JS is
stripped — so every interactive element here is a real Streamlit widget;
only the decorative parts, e.g. the flag swatches, are inline-styled HTML).

Browsing stays free (confirmed 2026-07 — see project memory): country cards
open directly, no login required. Sign in / Create account are here for the
admin flow and for people who want an account; they do not gate the data —
so there are deliberately no "Locked" badges or gated-access banners here,
unlike the original mockup export (which defaults to a gated variant).
"""
import os
import base64

import requests
import streamlit as st
import streamlit.components.v1 as components

import auth

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_GLOBE  = os.path.join(_ASSETS, "logo.png")
_FLAGS  = os.path.join(_ASSETS, "flags")

BLUE = "#0A63A6"


def _svg_data_uri(path: str) -> str:
    """Base64-inline an SVG file as a data URI so it can be dropped straight into
    HTML (st.markdown strips <img src> to real files, but data URIs survive)."""
    with open(path, "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")


@st.cache_data(show_spinner=False)
def flag_uri(code: str) -> str:
    """Real high-quality country flag (assets/flags/<code>.svg) as a data URI."""
    return _svg_data_uri(os.path.join(_FLAGS, f"{code}.svg"))


# App logo mark (blue rounded square + white globe) — one asset used everywhere.
LOGO_URI = _svg_data_uri(os.path.join(_ASSETS, "logo_mark.svg"))

# Self-contained live-preview carousel (HTML/CSS/JS) rendered in an iframe via
# components.html. __SLIDES__ / __DOTS__ / __N__ are filled in per render. The
# animation is client-side only — Streamlit keeps no state for it.
_CAROUSEL_TPL = """<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  *{box-sizing:border-box;margin:0;padding:0;}
  html,body{background:transparent;font-family:'Hanken Grotesk',system-ui,sans-serif;-webkit-font-smoothing:antialiased;}
  .mono{font-family:'JetBrains Mono',monospace;}
  .panel{position:relative;background:#fff;border:1px solid #E7E9ED;border-radius:16px;
         padding:22px 22px 16px;box-shadow:0 20px 40px -26px rgba(16,21,31,.25);overflow:hidden;user-select:none;}
  .viewport{overflow:hidden;}
  .track{display:flex;transition:transform .55s cubic-bezier(.22,1,.36,1);}
  .slide{min-width:100%;flex:0 0 100%;}
  .head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:16px;}
  .eyebrow{font-size:10px;font-weight:600;letter-spacing:.14em;color:#0A63A6;}
  .title{font-weight:700;font-size:15px;margin-top:5px;color:#0C1119;}
  .sub{font-size:12px;color:#8A919D;margin-top:2px;}
  .flag{width:34px;height:24px;object-fit:cover;border-radius:5px;border:1px solid rgba(0,0,0,.08);flex:none;}
  .row{display:flex;align-items:center;gap:10px;margin-bottom:11px;}
  .lbl{font-size:11px;width:32px;flex:none;color:#98A0AC;}
  .lbl.med{color:#0A63A6;font-weight:600;}
  .track2{flex:1;height:8px;border-radius:5px;background:#EEF0F3;overflow:hidden;}
  .fill{height:100%;border-radius:5px;background:#B9C6D4;}
  .fill.med{background:#0A63A6;}
  .val{font-size:11px;width:66px;text-align:right;flex:none;color:#5B6472;white-space:nowrap;}
  .val.med{color:#0A63A6;font-weight:600;}
  .foot{display:flex;align-items:center;justify-content:space-between;margin-top:14px;
        padding-top:13px;border-top:1px solid #EEF0F3;}
  .foot-lbl{font-size:12px;color:#8A919D;}
  .foot-val{font-weight:600;font-size:14px;color:#0C1119;white-space:nowrap;}
  .unit{color:#98A0AC;font-weight:400;}
  .nav{position:absolute;top:0;bottom:52px;width:50%;cursor:pointer;z-index:2;}
  .nav.l{left:0;} .nav.r{right:0;}
  .pager{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:14px;position:relative;z-index:3;}
  .arrow{width:26px;height:26px;border:1px solid #DDE1E6;border-radius:50%;background:#fff;color:#5B6472;
         display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:15px;line-height:1;}
  .arrow:hover{background:#F4F5F7;color:#0C1119;}
  .dots{display:flex;align-items:center;gap:6px;}
  .dot{width:6px;height:6px;border-radius:3px;background:#D3D8DF;cursor:pointer;
       transition:width .4s cubic-bezier(.22,1,.36,1),background .4s;}
  .dot.active{width:20px;background:#0A63A6;}
</style></head><body>
<div class="panel">
  <div class="nav l" data-dir="-1"></div>
  <div class="nav r" data-dir="1"></div>
  <div class="viewport"><div class="track" id="tk">__SLIDES__</div></div>
  <div class="pager">
    <div class="arrow" data-dir="-1">&#8249;</div>
    <div class="dots" id="dt">__DOTS__</div>
    <div class="arrow" data-dir="1">&#8250;</div>
  </div>
</div>
<script>
(function(){
  var N=__N__, i=0, tk=document.getElementById('tk');
  var dots=[].slice.call(document.querySelectorAll('.dot'));
  function go(k){ i=((k%N)+N)%N; tk.style.transform='translateX('+(-i*100)+'%)';
    for(var j=0;j<dots.length;j++){ dots[j].className='dot'+(j===i?' active':''); } }
  var nav=document.querySelectorAll('[data-dir]');
  for(var a=0;a<nav.length;a++){ (function(el){ el.addEventListener('click',function(e){
    e.stopPropagation(); go(i+parseInt(el.getAttribute('data-dir'),10)); }); })(nav[a]); }
  for(var b=0;b<dots.length;b++){ (function(j){ dots[j].addEventListener('click',function(e){
    e.stopPropagation(); go(j); }); })(b); }
  go(0);
})();
</script></body></html>"""

# Country-card CTAs are real <a href="?country=..."> links inside HTML (so the
# whole card can be one styled block with a scoped :hover, per design-system §6).
# JS can't call Python, so navigation rides a URL query param routed here.
_ROUTES = {"sweden": "scb_salaries.py", "france": "france.py"}
if st.query_params.get("country") in _ROUTES:
    st.switch_page(_ROUTES[st.query_params["country"]])

# Just confirmed their email? Supabase redirects the confirmation link back to
# the app with ?confirmed=1 (see auth.sign_up's redirect_to). Greet them and
# open the sign-in dialog, then drop the marker from the URL.
if st.query_params.get("confirmed"):
    st.session_state["_confirmed_msg"] = True
    st.session_state["_show_auth"] = True
    st.session_state["_auth_mode"] = "Sign in"
    del st.query_params["confirmed"]


def _app_base_url():
    """Best-effort public base URL of this app (for the confirmation-email
    redirect). Reads the forwarded host/proto behind Traefik; None if unknown."""
    try:
        h = st.context.headers
    except Exception:
        return None
    host = h.get("X-Forwarded-Host") or h.get("Host")
    if not host:
        return None
    proto = h.get("X-Forwarded-Proto") or ("http" if host.startswith(("localhost", "127.")) else "https")
    return f"{proto}://{host}"

# Single source of truth for the country grid — add a country here only.
COUNTRIES = [
    {
        "num": "01", "name": "Sweden", "native": "Sverige", "source": "SCB · official",
        "iso": "se",
        "flag_css": ("background-color:#006AA7;"
                     "background-image:linear-gradient(90deg,transparent 26%,#FECC00 26% 40%,transparent 40%),"
                     "linear-gradient(0deg,transparent 40%,#FECC00 40% 60%,transparent 60%);"),
        "points": [
            "Salary percentiles P10–P90 · ~430 occupations (SSYK)",
            "Sector, sex, age, region &amp; education breakdowns",
            "Work-permit salary check · Migrationsverket rules",
        ],
        "page": "scb_salaries.py", "live": True,
    },
    {
        "num": "02", "name": "France", "native": "République française", "source": "INSEE · official",
        "iso": "fr",
        "flag_css": ("background-image:linear-gradient(90deg,#0055A4 33.33%,#ffffff 33.33% 66.66%,"
                     "#EF4135 66.66%);"),
        "points": [
            "Mean salaries · 361 detailed occupations (PCS)",
            "Wage distribution by socio-professional group",
            "Inflation-adjusted trends, series since 1951",
        ],
        "page": "france.py", "live": True,
    },
    {
        "num": "03", "name": "United States", "native": "United States",
        "source": "BLS Public Data API · planned", "iso": "us",
        "flag_css": ("background-color:#B22234;"
                     "background-image:linear-gradient(#3C3B6E,#3C3B6E),"
                     "repeating-linear-gradient(180deg,#B22234 0 7.7%,#ffffff 7.7% 15.4%);"
                     "background-size:40% 53.85%,100% 100%;"
                     "background-position:top left,top left;background-repeat:no-repeat,no-repeat;"),
        "points": [
            "Salary benchmarks by occupation &amp; location",
            "Mean, median, P10/P25/P75/P90 wage data",
            "Labour market indicators &amp; compensation trends",
        ],
        "page": None, "live": False,
    },
]
N_OCCUPATIONS = "790+"  # ~430 SSYK (Sweden) + 361 PCS (France)


@st.cache_data(show_spinner=False, persist="disk", ttl=86400)
def _fetch_preview_data(occ_code: str, year: str):
    """Real SCB percentile data for the hero's live-preview card. Same table/
    codes/dims as Sweden's own percentile tab (AM0110A, LoneSpridSektYrk4AN),
    queried directly here since importing scb_salaries.py would execute its
    whole page script rather than just its functions."""
    url = "https://api.scb.se/OV0104/v1/doris/en/ssd/AM/AM0110/AM0110A/LoneSpridSektYrk4AN"
    body = {"query": [
        {"code": "Sektor",       "selection": {"filter": "item", "values": ["0"]}},
        {"code": "Yrke2012",     "selection": {"filter": "item", "values": [occ_code]}},
        {"code": "Kon",          "selection": {"filter": "item", "values": ["1+2"]}},
        {"code": "ContentsCode", "selection": {"filter": "item",
         "values": ["000007CD", "000007CE", "000007CF", "000007CG", "000007CH", "000007CI"]}},
        {"code": "Tid",          "selection": {"filter": "item", "values": [year]}},
    ], "response": {"format": "json"}}
    try:
        r = requests.post(url, json=body, timeout=20)
        r.raise_for_status()
        vals = r.json()["data"][0]["values"]
        avg, med, p10, p25, p75, p90 = (float(v) for v in vals)
        return {"avg": avg, "median": med, "p10": p10, "p25": p25, "p75": p75, "p90": p90}
    except Exception:
        return None


# ── Fonts + base type (scoped to this page — each Streamlit page is its own
# script run, so this never bleeds into Sweden's / France's own styling) ──────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  .se-mono { font-family:'JetBrains Mono',monospace; }
  /* Constrain + centre the landing to the mockup's editorial width. The wide
     layout is only needed for the data-explorer pages; here it made everything
     stretch ("page within a page") on big monitors. This <style> is injected by
     the landing script only, so it never touches Sweden/France. */
  [data-testid="stMainBlockContainer"] { max-width: 1180px; margin: 0 auto; }
  /* Country cards are native st.container(border, key="cc_…") so the CTA can be
     a real st.page_link (client-side nav that keeps the session/login) instead
     of an <a href> that reloads the app. Streamlit tags keyed containers with
     .st-key-cc_… — style that to reproduce the card look + scoped hover. */
  [class*="st-key-cc_"] { background:#fff; border:1px solid #E7E9ED !important;
     border-radius:16px !important; padding:22px 22px 18px !important;
     display:flex; flex-direction:column; flex:1 0 auto; gap:0;
     transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
  [class*="st-key-cc_"]:hover { transform: translateY(-3px);
     box-shadow: 0 18px 40px -24px rgba(16,21,31,.30); border-color:#D3D8DF !important; }
  /* Equal-height tiles: a flex chain from the column down to the card, so a short
     tile (US) grows to match the tallest in the row. (Plain height:100% collapses
     here — the column's height is content-driven, so it's circular.) The source
     line is pinned to the foot, so the slack lands after the last bullet and every
     tile shares the same top and bottom edge. */
  [data-testid="stColumn"]:has([class*="st-key-cc_"]) {
     align-self:stretch; display:flex; flex-direction:column; }
  [data-testid="stColumn"]:has([class*="st-key-cc_"]) > [data-testid="stVerticalBlock"],
  [data-testid="stLayoutWrapper"]:has(> [class*="st-key-cc_"]) {
     display:flex; flex-direction:column; flex:1 0 auto; }
  /* Full-width CTA button under the header — space above (off the header) + below
     (before the bullets), and a slightly reduced height. */
  [class*="st-key-cc_"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]),
  [class*="st-key-cc_"] [data-testid="stElementContainer"]:has(.se-cta-off) {
     width:100% !important; margin:8px 0 16px; }
  [class*="st-key-cc_"] [data-testid="stPageLink"] { width:100%; }
  [class*="st-key-cc_"] [data-testid="stPageLink"] a { width:100%; background:#0A63A6;
     border-radius:9px; padding:8px 14px; justify-content:center;
     box-shadow:0 2px 8px rgba(10,99,166,.24); transition: background .15s ease; }
  [class*="st-key-cc_"] [data-testid="stPageLink"] a:hover { background:#0B72C2; }
  [class*="st-key-cc_"] [data-testid="stPageLink"] a p,
  [class*="st-key-cc_"] [data-testid="stPageLink"] a span { color:#fff !important;
     font-weight:600; font-size:14px; }
  /* Bullets: breathing room before the pinned source line (never let the rule
     touch the last bullet). */
  [class*="st-key-cc_"] [data-testid="stElementContainer"]:has(ul) { margin-bottom:22px; }
  /* Source line pinned to the card foot with a rule. */
  [class*="st-key-cc_"] [data-testid="stElementContainer"]:has(.se-source) { margin-top:auto; }
  .se-source { padding-top:14px; border-top:1px solid #EEF0F3;
               font-family:'JetBrains Mono',monospace; font-size:11px; color:#98A0AC; }
  /* Real flag image — fixed size; object-fit:cover !important so it FILLS the
     swatch (Streamlit's global img rule forces scale-down, which letterboxes the
     wider flags, e.g. the US one). Class-based rule beats the inline default. */
  .se-flag { width:46px !important; height:33px !important; border-radius:7px; flex:none;
             object-fit:cover !important; display:block; border:1px solid rgba(0,0,0,.08);
             box-shadow:0 1px 3px rgba(0,0,0,.08); }
  /* Small flag in the live-preview card — same cover fix. */
  .se-flag-sm { width:34px !important; height:24px !important; border-radius:5px;
                object-fit:cover !important; display:block; border:1px solid rgba(0,0,0,.08); }
  .se-cta-off { display:flex; width:100%; align-items:center; justify-content:center;
                background:#F4F5F7; color:#8A919D; font-weight:600; font-size:14px; padding:10px;
                border-radius:9px; border:1px solid #E7E9ED; white-space:nowrap; }
  /* ── Auth dialog: match-height blue panel + full-width segmented toggle ── */
  [data-testid="stDialog"] div[role="dialog"]{ max-width: 720px; }
  [data-testid="stDialog"] [data-testid="stDialogContent"]{ padding-top: .25rem; }
  /* Full-width segmented "Sign in / Create account" pill toggle. */
  [data-testid="stDialog"] [data-testid="stSegmentedControl"]{ width:100%; margin-bottom:6px; }
  [data-testid="stDialog"] [data-testid="stSegmentedControl"] > div{ width:100%; display:flex; }
  [data-testid="stDialog"] [data-testid="stSegmentedControl"] label{ flex:1; justify-content:center; }
  /* Blue panel: rounded, decorative, fills its column height. */
  .se-authpanel{ position:relative; overflow:hidden; background:#0A63A6; color:#fff;
                 border-radius:14px; padding:28px 26px; min-height:466px;
                 box-shadow:0 10px 30px rgba(10,99,166,.28); }
  .se-authpanel .se-blob{ position:absolute; border-radius:50%;
                          background:rgba(255,255,255,.08); pointer-events:none; }
  .se-authcheck{ display:flex; align-items:center; gap:11px; font-size:13.5px;
                 color:rgba(255,255,255,.94); margin-bottom:14px; }
  .se-authcheck .se-tick{ flex:none; width:22px; height:22px; border-radius:50%;
                          background:rgba(255,255,255,.16); display:flex; align-items:center;
                          justify-content:center; font-size:12px; }
</style>
""", unsafe_allow_html=True)


@st.dialog("Welcome to Salary Explorer", width="large")
def _auth_dialog():
    left, right = st.columns([0.82, 1], gap="large", vertical_alignment="center")

    with left:
        st.markdown(f"""
        <div class="se-authpanel">
          <div class="se-blob" style="width:190px;height:190px;top:-70px;right:-60px;"></div>
          <div class="se-blob" style="width:150px;height:150px;bottom:-60px;left:-50px;"></div>
          <img src="{LOGO_URI}" alt="Salary Explorer" style="width:40px;height:40px;border-radius:10px;
               background:rgba(255,255,255,.14);padding:3px;margin-bottom:20px;position:relative;display:block;">
          <div class="se-mono" style="font-size:11px;font-weight:600;letter-spacing:.18em;
                                      color:rgba(255,255,255,.72);margin-bottom:16px;">SECURE ACCESS</div>
          <div style="font-size:24px;line-height:1.18;font-weight:800;letter-spacing:-.015em;
                      margin-bottom:24px;">Official salary data,<br>always free to browse.</div>
          <div class="se-authcheck"><span class="se-tick">✓</span>
            <span>Explore Sweden &amp; France right now - no account needed</span></div>
          <div class="se-authcheck"><span class="se-tick">✓</span>
            <span>An account is only needed for admin tools today</span></div>
          <div class="se-authcheck"><span class="se-tick">✓</span>
            <span>Free while in beta</span></div>
          <div class="se-mono" style="position:absolute;bottom:26px;left:26px;font-size:11px;
                                      color:rgba(255,255,255,.60);letter-spacing:.04em;">
            SCB · INSEE · official statistics only</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        # Just clicked the email-confirmation link → greet them (see the
        # ?confirmed=1 handling at the top of this file).
        if st.session_state.get("_confirmed_msg"):
            st.success("✅ Thanks for confirming your registration — "
                       "please sign in below.")
        # Segmented pill toggle (mockup look). The header buttons pre-seed
        # session_state["_auth_mode"]; feed that as the default and mirror any
        # click back into it so the choice sticks across the dialog's reruns.
        _default = st.session_state.get("_auth_mode", "Sign in")
        _seg = st.segmented_control(
            "mode", ["Sign in", "Create account"], default=_default,
            key="_auth_seg", label_visibility="collapsed")
        if _seg:  # None only if the active pill is clicked again (deselect)
            st.session_state["_auth_mode"] = _seg
        mode = st.session_state.get("_auth_mode", "Sign in")

        st.caption("Create a free account or explore without sign in. Browsing salary data never requires "
                  "one - sign in required for admin access.")

        if mode == "Create account":
            name = st.text_input("Full name", key="_su_name", placeholder="Jane Andersson")
        email = st.text_input("Email", key="_auth_email", placeholder="you@example.com")
        pw = st.text_input("Password", key="_auth_pw", type="password", placeholder="••••••••")

        if mode == "Sign in":
            if st.button("Sign in", type="primary", use_container_width=True):
                user, err = auth.sign_in(email.strip(), pw)
                if user:
                    st.session_state["auth_user"] = user
                    st.session_state.pop("_auth_pw", None)
                    st.session_state.pop("_confirmed_msg", None)
                    st.session_state["_show_auth"] = False
                    st.rerun()
                else:
                    st.error(f"Sign-in failed: {err}")
        else:
            if st.button("Create account", type="primary", use_container_width=True):
                if not email.strip() or not pw:
                    st.error("Email and password are required.")
                else:
                    # sign_up stores the account in Supabase as a *standard*
                    # user (the public client can't set app_metadata.role, so
                    # no self-registration can ever mint an admin). redirect_to
                    # brings the confirmation-email link back here with
                    # ?confirmed=1 so we can greet them.
                    _base = _app_base_url()
                    _redir = f"{_base}/?confirmed=1" if _base else None
                    user, err = auth.sign_up(email.strip(), pw, name.strip(),
                                             redirect_to=_redir)
                    if not user:
                        st.error(f"Could not create account: {err}")
                    else:
                        st.session_state.pop("_auth_pw", None)
                        # If the project doesn't require email confirmation the
                        # account is usable immediately — sign them straight in
                        # so they don't have to re-enter credentials. If it does
                        # require confirmation, sign-in fails cleanly and we fall
                        # back to the "check your inbox" message.
                        signed, _ = auth.sign_in(email.strip(), pw)
                        if signed:
                            st.session_state["auth_user"] = signed
                            st.session_state["_show_auth"] = False
                            st.rerun()
                        else:
                            st.success("Account created — check your inbox to confirm "
                                      "your email, then sign in.")

        st.caption("By continuing you agree to the Terms and acknowledge the Privacy Policy.")
        if st.button("Close", key="_auth_close"):
            st.session_state["_show_auth"] = False
            st.session_state.pop("_confirmed_msg", None)
            st.rerun()


# ── Header ─────────────────────────────────────────────────────────────────
# Nested columns so the button pair shares its own row and doesn't get
# squeezed by the outer ratio (a flat 5-way split made "Create account" wrap
# letter-by-letter — buttons need real pixel room, not a thin slice of 12).
h_left, h_right = st.columns([2, 1], vertical_alignment="center")
with h_left:
    # Mockup logo mark: blue rounded square with a globe glyph, tight to the
    # wordmark (a single flex row — no column gap to blow the spacing out).
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:11px;">
      <img src="{LOGO_URI}" alt="Salary Explorer" style="width:32px;height:32px;flex:none;
           border-radius:8px;box-shadow:0 2px 6px rgba(10,99,166,.35);">
      <span style="font-weight:700;font-size:16px;letter-spacing:-.01em;">Salary Explorer</span>
      <span class="se-mono" style="font-size:10px;font-weight:600;letter-spacing:.06em;
            color:{BLUE};background:rgba(10,99,166,.10);padding:3px 7px;border-radius:5px;">BETA</span>
    </div>
    """, unsafe_allow_html=True)
with h_right:
    _hu = st.session_state.get("auth_user")
    if _hu:
        # Logged in: show who you are (name + role + avatar initials) instead of
        # the sign-in buttons, with a Log out control.
        _email = _hu.get("email", "")
        _nm = _email.split("@")[0] if _email else "Account"
        _ini = ("".join(w[0] for w in _nm.replace(".", " ").replace("_", " ").split()[:2])
                or _nm[:1]).upper()
        _role = _hu.get("role", "standard")
        _rc = "#B8863B" if _role in ("admin", "master") else BLUE  # gold-ish for admins
        _who, _out = st.columns([2.4, 1], vertical_alignment="center")
        with _who:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;justify-content:flex-end;">
              <div style="text-align:right;line-height:1.16;min-width:0;">
                <div style="font-weight:600;font-size:13.5px;color:#0C1119;overflow:hidden;
                            text-overflow:ellipsis;">{_nm}</div>
                <div class="se-mono" style="font-size:10px;letter-spacing:.10em;color:{_rc};
                     text-transform:uppercase;font-weight:600;">{_role}</div>
              </div>
              <div style="width:36px;height:36px;border-radius:50%;background:{_rc};color:#fff;
                   flex:none;display:flex;align-items:center;justify-content:center;
                   font-weight:700;font-size:13px;">{_ini}</div>
            </div>
            """, unsafe_allow_html=True)
        with _out:
            if st.button("Log out", use_container_width=True, key="hdr_logout"):
                st.session_state.pop("auth_user", None)
                st.rerun()
    else:
        hr_signin, hr_signup = st.columns(2)
        with hr_signin:
            if st.button("Sign in", use_container_width=True, key="hdr_signin"):
                st.session_state["_auth_mode"] = "Sign in"
                st.session_state["_show_auth"] = True
                st.rerun()
        with hr_signup:
            if st.button("Create account", type="primary", use_container_width=True, key="hdr_signup"):
                st.session_state["_auth_mode"] = "Create account"
                st.session_state["_show_auth"] = True
                st.rerun()

# Dialog must be (re)invoked on every rerun while open — a Streamlit dialog
# only stays open across its own internal reruns (typing, radio clicks) if
# it's called unconditionally like this, gated by persisted state; calling it
# only inside the button's `if` block would close it the instant you type.
if st.session_state.get("_show_auth"):
    _auth_dialog()

st.divider()

# ── Hero ───────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([1.05, 0.95], gap="large")
with hc1:
    st.markdown(f"""
    <div class="se-mono" style="font-size:12px;font-weight:600;letter-spacing:.16em;color:{BLUE};margin-bottom:20px;">
      OFFICIAL STATISTICS · GLOBAL
    </div>
    <h1 style="margin:0;font-size:52px;line-height:1.06;letter-spacing:-.025em;font-weight:800;color:#0C1119;">
      Salary data from national agencies, made explorable.
    </h1>
    <p style="margin:20px 0 0;font-size:17px;line-height:1.55;color:#5B6472;max-width:520px;">
      One clean interface over official government statistics - percentiles, breakdowns
      and trends, standardised so you can compare occupations within and across countries.
    </p>
    <div style="display:flex;gap:0;margin-top:34px;flex-wrap:wrap;align-items:stretch;">
      <div style="padding-right:28px;">
        <div class="se-mono" style="font-size:26px;font-weight:600;color:#0C1119;letter-spacing:-.02em;">2</div>
        <div style="font-size:13px;color:#7A828F;margin-top:3px;">countries live</div>
      </div>
      <div style="width:1px;background:#E1E4E9;margin:0 28px 0 0;"></div>
      <div style="padding-right:28px;">
        <div class="se-mono" style="font-size:26px;font-weight:600;color:#0C1119;letter-spacing:-.02em;">{N_OCCUPATIONS}</div>
        <div style="font-size:13px;color:#7A828F;margin-top:3px;">occupations</div>
      </div>
      <div style="width:1px;background:#E1E4E9;margin:0 28px 0 0;"></div>
      <div>
        <div class="se-mono" style="font-size:26px;font-weight:600;color:#0C1119;letter-spacing:-.02em;">100%</div>
        <div style="font-size:13px;color:#7A828F;margin-top:3px;">official sources</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with hc2:
    # ── Live-preview carousel: three example distributions, swipeable ──────────
    # JS-driven slide animation → rendered via components.html (an iframe), since
    # st.markdown strips JS. Self-contained HTML/CSS/JS, no Python state. Sweden
    # slides use the live SCB fetch (fallbacks embedded); France is 2023 microdata.
    _se_dev = _fetch_preview_data("2512", "2025") or \
        {"p10": 39600, "p25": 46200, "median": 53500, "p75": 62600, "p90": 72600}
    _se_mech = _fetch_preview_data("2144", "2025") or \
        {"p10": 40200, "p25": 45300, "median": 51800, "p75": 60000, "p90": 69900}
    _slides_data = [
        {"title": "Software developers", "sub": "Sweden · SCB 2025 · monthly, SEK",
         "iso": "se", "unit": "kr", "v": _se_dev},
        {"title": "Psychiatric nurses", "sub": "France · INSEE 2023 · monthly, EUR",
         "iso": "fr", "unit": "€",
         "v": {"p10": 2070, "p25": 2470, "median": 2950, "p75": 3280, "p90": 3830}},
        {"title": "Mechanical engineers", "sub": "Sweden · SCB 2025 · monthly, SEK",
         "iso": "se", "unit": "kr", "v": _se_mech},
    ]

    def _nbsp(x):                       # 53500 -> "53 900" (nbsp so it never wraps)
        return f"{int(round(x)):,}".replace(",", " ")

    def _slide_html(s):
        v = s["v"]
        lo, hi = v["p10"], (v["p90"] or 1)
        span = (hi - lo) or 1
        rows = ""
        for lbl, key in (("P10", "p10"), ("P25", "p25"), ("MED", "median"),
                         ("P75", "p75"), ("P90", "p90")):
            val = v[key]
            w = 30 + 66 * (val - lo) / span        # P10 ≈ 30% … P90 ≈ 96%
            m = " med" if lbl == "MED" else ""
            rows += (f'<div class="row"><span class="lbl{m}">{lbl}</span>'
                     f'<div class="track2"><div class="fill{m}" style="width:{w:.0f}%"></div></div>'
                     f'<span class="val{m}">{_nbsp(val)}</span></div>')
        med = f'{_nbsp(v["median"])} {s["unit"]}'
        return (f'<div class="slide"><div class="head"><div>'
                f'<div class="eyebrow mono">LIVE PREVIEW</div>'
                f'<div class="title">{s["title"]}</div>'
                f'<div class="sub">{s["sub"]}</div></div>'
                f'<img class="flag" src="{flag_uri(s["iso"])}" alt=""></div>'
                f'{rows}<div class="foot"><span class="foot-lbl">Median gross salary</span>'
                f'<span class="foot-val mono">{med}<span class="unit">/mo</span></span></div></div>')

    _slides = "".join(_slide_html(s) for s in _slides_data)
    _dots = "".join('<span class="dot"></span>' for _ in _slides_data)
    _carousel = _CAROUSEL_TPL.replace("__SLIDES__", _slides) \
        .replace("__DOTS__", _dots).replace("__N__", str(len(_slides_data)))
    components.html(_carousel, height=352)

st.write("")
st.write("")

# ── Select a country ───────────────────────────────────────────────────────
st.markdown(f"""
<div class="se-mono" style="font-size:12px;font-weight:600;letter-spacing:.16em;color:{BLUE};margin-bottom:10px;">
  SELECT A COUNTRY
</div>
""", unsafe_allow_html=True)
st.subheader("Where do you want to look?")
st.write("")

# Native columns + a keyed st.container per card so the CTA can be a real
# st.page_link. That navigates *client-side* (no full-page reload), which keeps
# st.session_state — so an admin who signed in here stays signed in on Sweden /
# France. (A raw <a href> reloads the app and silently drops the session.)
_cols = st.columns(len(COUNTRIES), gap="medium")
for _col, c in zip(_cols, COUNTRIES):
    with _col, st.container(border=True, key=f"cc_{c['num']}"):
        badge = ('<div style="background:rgba(10,99,166,.10);color:#0A63A6;font-size:11px;'
                 'font-weight:600;padding:4px 10px;border-radius:20px;flex:none;">Coming soon</div>'
                 if not c["live"] else "")
        bullets = "".join(
            '<li style="display:flex;gap:10px;font-size:13.5px;color:#4A525F;line-height:1.4;">'
            '<span style="width:5px;height:5px;border-radius:50%;background:#0A63A6;margin-top:7px;'
            f'flex:none;opacity:.7;"></span><span>{p}</span></li>' for p in c["points"])
        header = f"""
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">
          <img class="se-flag" src="{flag_uri(c['iso'])}" alt="{c['name']} flag">
          <div style="flex:1;min-width:0;">
            <div style="white-space:nowrap;">
              <span class="se-mono" style="font-size:11px;color:#B4BAC4;margin-right:7px;">{c['num']}</span>
              <span style="font-weight:700;font-size:17px;">{c['name']}</span></div>
            <div style="font-size:12px;color:#8A919D;margin-top:1px;">{c['native']}</div>
          </div>
          {badge}
        </div>"""
        st.markdown("".join(l.strip() for l in header.splitlines()), unsafe_allow_html=True)
        # Full-width CTA directly under the header (mockup layout).
        if c["live"]:
            st.page_link(c["page"], label=f"Open {c['name']} →")
        else:
            st.markdown('<div class="se-cta-off">Notify me</div>', unsafe_allow_html=True)
        # Bullets, then the source line pinned to the card foot.
        st.markdown(
            '<ul style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px;">'
            + bullets + '</ul>', unsafe_allow_html=True)
        st.markdown(f'<div class="se-source">{c["source"]}</div>', unsafe_allow_html=True)

st.write("")
st.divider()
st.caption("Data sourced directly from national statistics agencies · SCB (Sweden) · INSEE (France)")
