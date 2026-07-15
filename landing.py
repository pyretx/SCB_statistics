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
import content

# Optional: the country framework (registry + access gate) — for the admin "Dev"
# preview menu and the gated framework tiles (e.g. Norway beta). Guarded so a
# framework issue can never break the landing page.
try:
    from core import registry as _registry
    from core import access as _access
except Exception:
    _registry = _access = None

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_GLOBE  = os.path.join(_ASSETS, "logo.png")
_FLAGS  = os.path.join(_ASSETS, "flags")

BLUE = "#0A63A6"

# All user-facing text for this page lives in content/home.toml + content/auth.toml
# (edit there, not here). See content.py.
C = content.load("home")
A = content.load("auth")


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
_ROUTES = {"sweden": "countries/se2/page.py", "france": "countries/fr2/page.py"}
if st.query_params.get("country") in _ROUTES:
    st.switch_page(_ROUTES[st.query_params["country"]])

# ── Email confirmation, two generations ──────────────────────────────────────
# NEW (root-cause fix): the customised Supabase email links straight to the app
# with &confirm_token={{ .TokenHash }}. Verification happens ONLY when the user
# presses the Confirm button in the dialog below — mail-scanner prefetches load
# the page but never press buttons, so the one-time token survives. On success
# the user is signed in directly.
if st.query_params.get("confirm_token"):
    st.session_state["_confirm_token"] = st.query_params["confirm_token"]
    for p in ("confirm_token", "confirmed"):
        if p in st.query_params:
            del st.query_params[p]

# LEGACY (default Supabase template): the link verified on Supabase's side and
# redirected here with ?confirmed=1 — optimistic banner + sign-in (the resend
# button covers tokens that a scanner already consumed).
elif st.query_params.get("confirmed"):
    st.session_state["_confirmed_msg"] = True
    st.session_state["_show_auth"] = True
    st.session_state["_auth_mode"] = A["form"]["mode_sign_in"]
    del st.query_params["confirmed"]

# The catalog's "free account required — Sign in →" pill is an HTML link (so it
# can carry the same lock SVG as the country rows); it lands here. Only shown
# signed-out, so the full-page reload costs no session.
if st.query_params.get("signin"):
    st.session_state["_show_auth"] = True
    st.session_state["_auth_mode"] = A["form"]["mode_sign_in"]
    del st.query_params["signin"]


def _app_base_url():
    """Public base URL of this app (for the confirmation-email redirect). Prefer
    an explicit ``[app] url`` in secrets.toml — that's rock-solid behind a reverse
    proxy — then fall back to the forwarded host/proto headers; None if unknown."""
    # 1) explicit config (recommended on the server: [app] url = "https://…")
    try:
        u = st.secrets.get("app", {}).get("url")
        if u:
            return str(u).rstrip("/")
    except Exception:
        pass
    # 2) forwarded headers (case-insensitive; Traefik/HTTP2 may lowercase them)
    try:
        h = st.context.headers
        host = (h.get("X-Forwarded-Host") or h.get("x-forwarded-host")
                or h.get("Host") or h.get("host"))
        if host:
            host = host.split(",")[0].strip()
            proto = (h.get("X-Forwarded-Proto") or h.get("x-forwarded-proto")
                     or ("http" if host.startswith(("localhost", "127.")) else "https"))
            return f"{proto}://{host}"
    except Exception:
        pass
    return None

# Country catalog — content-driven (edit content/home.toml → [countries].catalog).


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
     display:flex; flex-direction:column; flex:1 0 auto; gap:0; min-height:334px;
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
  [class*="st-key-cc_"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]) {
     width:100% !important; margin:8px 0 16px; }
  /* The markdown-chip CTA (Notify me / Locked) sits tighter to the bullets than a
     real page-link button, so give it extra bottom margin — all tiles then match. */
  [class*="st-key-cc_"] [data-testid="stElementContainer"]:has(.se-cta-off) {
     width:100% !important; margin:8px 0 34px; }
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
  /* ── "Watch the demo" pitch-video button (design tokens from the export):
     white pill, blue 30px play circle (::before), mono duration chip (::after). */
  :is(.st-key-hero_video,.st-key-hero_tour,.st-key-hero_cp) button { display:inline-flex; align-items:center; gap:11px;
     margin-top:10px; font-size:14.5px; font-weight:600; color:#0C1119 !important;
     background:#fff !important; border:1px solid #DDE1E6 !important;
     padding:10px 18px 10px 12px !important; border-radius:12px !important;
     box-shadow:0 2px 8px rgba(16,21,31,.06); width:auto; }
  :is(.st-key-hero_video,.st-key-hero_tour,.st-key-hero_cp) button:hover { border-color:#C9CFD8 !important;
     box-shadow:0 4px 12px rgba(16,21,31,.10); }
  :is(.st-key-hero_video,.st-key-hero_tour,.st-key-hero_cp) button::before { content:''; width:30px; height:30px;
     border-radius:50%; flex:0 0 auto; background:#0A63A6
     url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'><path d='M7 4.5v15l13-7.5z'/></svg>")
     center/12px 12px no-repeat; }
  :is(.st-key-hero_video,.st-key-hero_tour,.st-key-hero_cp) button::after { content:'';
     font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:500;
     color:#98A0AC; }  /* content set dynamically from home.toml at render */
  :is(.st-key-hero_video,.st-key-hero_tour,.st-key-hero_cp) button p { font-size:14.5px !important; font-weight:600 !important;
     color:#0C1119 !important; white-space:nowrap; }
  /* Third button = Career Paths (beta): amber accent matching the country-tile
     beta pill (#B26A00) — play circle + label tinted so it reads as a beta link. */
  .st-key-hero_cp button::before { background-color:#B26A00 !important; }
  .st-key-hero_cp button p { color:#B26A00 !important; }
  /* Lay the two pitch buttons in a tight, LEFT-aligned row (no column gutter) with
     only a small gap between them — flush with the paragraph's left edge above.
     .st-key-hero_vids IS the vertical flex block, so flip it to row directly. */
  .st-key-hero_vids{ flex-direction:row !important; gap:10px !important;
     align-items:center; width:auto; }
  /* each element container must hug its button (max-content) so the buttons don't
     overflow and overlap — then the 10px gap sits between the two pills. */
  .st-key-hero_vids > [data-testid="stElementContainer"]{ width:max-content !important;
     flex:0 0 auto !important; }
  /* Header Admin/Log-out buttons: keep icon + label on ONE row so the two
     buttons always share the same height — without this the flex content
     wraps at narrow widths (the gear landed above "Admin"). */
  .st-key-hdr_admin button, .st-key-hdr_logout button {
    flex-wrap: nowrap !important; white-space: nowrap !important; }
  .st-key-hdr_admin button p, .st-key-hdr_logout button p {
    white-space: nowrap !important; }
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
  /* ── Header identity → profile dialog: buttons can't hold HTML, so an
     invisible button stretched over the whole chip makes name+avatar clickable.
     Explicit width/height (not inset) — Streamlit's element containers carry
     fixed emotion sizes that inset alone can't override, and the 36px avatar
     overflows the 20px-tall wrapper. */
  .st-key-hdr_idwrap{ position:relative; }
  .st-key-hdr_idwrap .st-key-hdr_profile{ position:absolute; top:0; left:0;
     width:100% !important; height:36px !important; z-index:3; }
  .st-key-hdr_idwrap .st-key-hdr_profile button{ width:100%; height:100%; min-height:0;
     opacity:0; cursor:pointer; }
  .st-key-hdr_idwrap:has(.st-key-hdr_profile button:hover) .se-hdr-nm{
     text-decoration:underline; }
  /* Profile dialog: mono field labels + value rows (admin-panel look). */
  .se-prow{ display:flex; justify-content:space-between; align-items:center; gap:18px;
            padding:11px 2px; border-bottom:1px solid #EEF0F3; }
  .se-plbl{ font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.11em;
            text-transform:uppercase; color:#98A0AC; }
  .se-pval{ font-weight:600; font-size:14px; color:#0C1119; text-align:right; min-width:0;
            overflow:hidden; text-overflow:ellipsis; }
</style>
""", unsafe_allow_html=True)


@st.dialog(A["dialog"]["title"], width="large")
def _auth_dialog():
    left, right = st.columns([0.82, 1], gap="large", vertical_alignment="center")
    _p = A["panel"]
    _checks = "".join(
        f'<div class="se-authcheck"><span class="se-tick">✓</span><span>{c}</span></div>'
        for c in _p["checks"])

    with left:
        st.markdown(f"""
        <div class="se-authpanel">
          <div class="se-blob" style="width:190px;height:190px;top:-70px;right:-60px;"></div>
          <div class="se-blob" style="width:150px;height:150px;bottom:-60px;left:-50px;"></div>
          <img src="{LOGO_URI}" alt="Salary Explorer" style="width:40px;height:40px;border-radius:10px;
               background:rgba(255,255,255,.14);padding:3px;margin-bottom:20px;position:relative;display:block;">
          <div class="se-mono" style="font-size:11px;font-weight:600;letter-spacing:.18em;
                                      color:rgba(255,255,255,.72);margin-bottom:16px;">{_p["eyebrow"]}</div>
          <div style="font-size:24px;line-height:1.18;font-weight:800;letter-spacing:-.015em;
                      margin-bottom:24px;">{_p["headline"]}</div>
          {_checks}
          <div class="se-mono" style="position:absolute;bottom:26px;left:26px;font-size:11px;
                                      color:rgba(255,255,255,.60);letter-spacing:.04em;">
            {_p["footer"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        # Just clicked the email-confirmation link → greet them (see the
        # ?confirmed=1 handling at the top of this file).
        _f, _m = A["form"], A["messages"]
        if st.session_state.get("_confirmed_msg"):
            st.success(_m["confirmed"])
        # Segmented pill toggle (mockup look). The header buttons pre-seed
        # session_state["_auth_mode"]; feed that as the default and mirror any
        # click back into it so the choice sticks across the dialog's reruns.
        _default = st.session_state.get("_auth_mode", _f["mode_sign_in"])
        _seg = st.segmented_control(
            "mode", [_f["mode_sign_in"], _f["mode_create"]], default=_default,
            key="_auth_seg", label_visibility="collapsed")
        if _seg:  # None only if the active pill is clicked again (deselect)
            st.session_state["_auth_mode"] = _seg
        mode = st.session_state.get("_auth_mode", _f["mode_sign_in"])
        _is_create = (mode == _f["mode_create"])

        st.caption(_f["intro"])

        # Fields + primary action live in a FORM. A bare st.text_input only
        # commits its value on Enter/blur, so a browser/Google-autofilled
        # password stayed "uncommitted" and the click read it as empty
        # ("password required", reported on mobile). A form commits every field
        # together when the submit button is pressed, capturing autofilled values.
        with st.form("auth_form", border=False, clear_on_submit=False):
            name = (st.text_input(_f["name_label"], key="_su_name",
                                  placeholder=_f["name_ph"]) if _is_create else "")
            email = st.text_input(_f["email_label"], key="_auth_email",
                                  placeholder=_f["email_ph"])
            pw = st.text_input(_f["password_label"], key="_auth_pw", type="password",
                               placeholder=_f["password_ph"])
            _submitted = st.form_submit_button(
                _f["create_button"] if _is_create else _f["sign_in_button"],
                type="primary", use_container_width=True)

        if _submitted and not _is_create:
            user, err = auth.sign_in(email.strip(), pw)
            if user:
                st.session_state["auth_user"] = user
                st.session_state.pop("_auth_pw", None)
                st.session_state.pop("_confirmed_msg", None)
                st.session_state.pop("_resend_for", None)
                st.session_state["_show_auth"] = False
                st.rerun()
            else:
                st.error(_m["sign_in_failed"].format(err=err))
                # 'Email not confirmed' → offer a fresh confirmation link
                # (the first one is often consumed by a mail-app preview).
                if "confirm" in str(err).lower():
                    st.session_state["_resend_for"] = email.strip()
        elif _submitted and _is_create:
            if not name.strip() or not email.strip() or not pw:
                st.error(_m["missing_fields"])
            else:
                # sign_up stores the account in Supabase as a *standard* user
                # (the public client can't set app_metadata.role, so no
                # self-registration can ever mint an admin). redirect_to brings
                # the confirmation-email link back here with ?confirmed=1.
                _base = _app_base_url()
                _redir = f"{_base}/?confirmed=1" if _base else None
                user, err = auth.sign_up(email.strip(), pw, name.strip(),
                                         redirect_to=_redir)
                if not user:
                    st.error(_m["create_failed"].format(err=err))
                else:
                    # If the project doesn't require email confirmation the
                    # account is usable immediately — sign them straight in. If
                    # it does, sign-in fails cleanly → "check your inbox".
                    signed, _ = auth.sign_in(email.strip(), pw)
                    if signed:
                        st.session_state["auth_user"] = signed
                        st.session_state.pop("_auth_pw", None)
                        st.session_state["_show_auth"] = False
                        st.rerun()
                    else:
                        st.success(_m["check_inbox"])

        # Resend confirmation (sign-in mode, after an 'email not confirmed'
        # failure) — a normal button, outside the form.
        if not _is_create and st.session_state.get("_resend_for"):
            if st.button(_m["resend_button"], key="_auth_resend", use_container_width=True):
                _base = _app_base_url()
                _redir = f"{_base}/?confirmed=1" if _base else None
                _rerr = auth.resend_confirmation(st.session_state["_resend_for"], _redir)
                if _rerr:
                    st.error(_m["resend_failed"].format(err=_rerr))
                else:
                    st.success(_m["resent"].format(email=st.session_state.pop("_resend_for")))

        st.caption(_f["terms"])
        if st.button(_f["close"], key="_auth_close"):
            st.session_state["_show_auth"] = False
            st.session_state.pop("_resend_for", None)
            st.session_state.pop("_confirmed_msg", None)
            st.rerun()


@st.dialog(A.get("confirm", {}).get("title", "Confirm your email"))
def _confirm_dialog():
    """The new-generation confirmation: the email links here with a token_hash;
    verification runs ONLY on this button press (mail scanners prefetch links
    but never press buttons), and on success the user is signed in directly."""
    Cq = A["confirm"]
    st.markdown(Cq["intro"])
    tok = st.session_state.get("_confirm_token")
    if st.button(Cq["button"], type="primary", use_container_width=True,
                 key="_confirm_go"):
        user, err = auth.confirm_email_token(tok)
        if user:
            st.session_state["auth_user"] = user
            st.session_state.pop("_confirm_token", None)
            st.session_state["_confirm_done"] = True
            st.rerun()
        else:
            st.error(Cq["failed"].format(err=err))
            st.caption(Cq["failed_hint"])
    if st.button(A["form"]["close"], key="_confirm_close"):
        st.session_state.pop("_confirm_token", None)
        st.rerun()


# White person glyph for the profile dialog's avatar circle (lucide-ish, same
# stroke style as the admin panel's KPI icons).
_PROFILE_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" '
                 'stroke-linecap="round" stroke-linejoin="round" width="30" height="30">'
                 '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
                 '<circle cx="12" cy="7" r="4"/></svg>')


@st.dialog(A["profile"]["title"])
def _profile_dialog():
    """Read-only profile (opened by clicking your name in the header): person
    icon, name / e-mail / account type, and the 'join the beta program' ask.
    No editing or password reset yet — that comes later."""
    P = A["profile"]
    u = st.session_state.get("auth_user") or {}
    email = u.get("email", "")
    name = u.get("name") or (email.split("@")[0] if email else P["no_name"])
    role = u.get("role", "standard")
    rc = "#B8863B" if role in ("admin", "master") else BLUE
    acct = P.get(f"type_{role}", role.capitalize())
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:5px;
                padding:4px 0 14px;">
      <div style="width:64px;height:64px;border-radius:50%;background:{rc};
           display:flex;align-items:center;justify-content:center;
           box-shadow:0 6px 18px {rc}55;margin-bottom:7px;">{_PROFILE_ICON}</div>
      <div style="font-weight:700;font-size:18px;color:#0C1119;">{name}</div>
      <div class="se-mono" style="font-size:10px;letter-spacing:.12em;color:{rc};
           text-transform:uppercase;font-weight:600;">{acct}</div>
    </div>
    <div class="se-prow"><span class="se-plbl">{P["f_name"]}</span>
      <span class="se-pval">{u.get("name") or P["no_name"]}</span></div>
    <div class="se-prow"><span class="se-plbl">{P["f_email"]}</span>
      <span class="se-pval">{email or P["no_name"]}</span></div>
    <div class="se-prow" style="border-bottom:none;"><span class="se-plbl">{P["f_type"]}</span>
      <span class="se-pval">{acct}</span></div>
    """, unsafe_allow_html=True)

    # ── Beta program: the one action on this page. Standard users may ask to
    # join; the request lands in the admin panel (Users → Beta requests).
    st.markdown(f'<div class="se-plbl" style="margin:16px 0 2px;">{P["beta_heading"]}</div>',
                unsafe_allow_html=True)
    st.caption(P["beta_caption"])
    if role in ("admin", "master"):
        st.caption(P["beta_admin"])
    elif role == "beta":
        st.success(P["beta_member"])
    elif u.get("beta_requested"):
        st.info(P["beta_pending"].format(date=u["beta_requested"]))
    else:
        if st.button(P["beta_button"], type="primary", use_container_width=True,
                     key="_prof_beta"):
            try:
                stamp = auth.request_beta(u["id"])
                st.session_state["auth_user"]["beta_requested"] = stamp
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(P["beta_failed"].format(err=e))
    if st.button(P["close"], key="_prof_close"):
        st.session_state["_show_profile"] = False
        st.rerun()


# ── Header ─────────────────────────────────────────────────────────────────
# Nested columns so the button pair shares its own row and doesn't get
# squeezed by the outer ratio (a flat 5-way split made "Create account" wrap
# letter-by-letter — buttons need real pixel room, not a thin slice of 12).
h_left, h_right = st.columns([2, 1], vertical_alignment="center")
with h_left:
    # Mockup logo mark: blue rounded square with a globe glyph, tight to the
    # wordmark (a single flex row — no column gap to blow the spacing out).
    _tagline = C["brand"].get("tagline", "")
    _tag_html = (f'<span class="se-mono" style="font-size:8px;font-weight:600;'
                 f'letter-spacing:.14em;color:#8A919D;line-height:1.2;">{_tagline}</span>'
                 if _tagline else "")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:11px;">
      <img src="{LOGO_URI}" alt="Salary Explorer" style="width:32px;height:32px;flex:none;
           border-radius:8px;box-shadow:0 2px 6px rgba(10,99,166,.35);">
      <div style="display:flex;flex-direction:column;gap:2px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-weight:700;font-size:16px;letter-spacing:-.01em;line-height:1.15;">{C["brand"]["name"]}</span>
          <span class="se-mono" style="font-size:10px;font-weight:600;letter-spacing:.06em;
                color:{BLUE};background:rgba(10,99,166,.10);padding:3px 7px;border-radius:5px;">{C["brand"]["badge"]}</span>
        </div>
        {_tag_html}
      </div>
    </div>
    """, unsafe_allow_html=True)
with h_right:
    _hu = st.session_state.get("auth_user")
    if _hu:
        # Logged in: show who you are (name + role + avatar initials) instead of
        # the sign-in buttons, with a Log out control.
        _email = _hu.get("email", "")
        # Prefer the real full name (sign_in carries user_metadata.full_name);
        # sessions from before that change fall back to the email prefix.
        _nm = _hu.get("name") or (_email.split("@")[0] if _email else "Account")
        _ini = ("".join(w[0] for w in _nm.replace(".", " ").replace("_", " ").split()[:2])
                or _nm[:1]).upper()
        _role = _hu.get("role", "standard")
        _rc = "#B8863B" if _role in ("admin", "master") else BLUE  # gold-ish for admins
        # Admins get a button to the full-page Admin panel (data refresh, users,
        # in-dev country previews). st.switch_page keeps the session across the
        # jump. Non-admins just see their identity + Log out.
        if _role in ("admin", "master"):
            # Identity, then Admin + Log out as two equal, adjacent buttons.
            _who, _adm, _out = st.columns([1.3, 1.1, 1], vertical_alignment="center")
            with _adm:
                if st.button(C["header"]["admin"], icon=":material/settings:",
                             use_container_width=True, key="hdr_admin"):
                    st.switch_page("admin.py")
        else:
            _who, _out = st.columns([2.4, 1], vertical_alignment="center")
        with _who, st.container(key="hdr_idwrap"):
            # The chip itself + an invisible overlay button (see the
            # .st-key-hdr_idwrap CSS) — clicking your name opens the profile.
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;justify-content:flex-end;">
              <div style="text-align:right;line-height:1.16;min-width:0;">
                <div class="se-hdr-nm" style="font-weight:600;font-size:13.5px;color:#0C1119;
                            overflow:hidden;text-overflow:ellipsis;">{_nm}</div>
                <div class="se-mono" style="font-size:10px;letter-spacing:.10em;color:{_rc};
                     text-transform:uppercase;font-weight:600;">{_role}</div>
              </div>
              <div style="width:36px;height:36px;border-radius:50%;background:{_rc};color:#fff;
                   flex:none;display:flex;align-items:center;justify-content:center;
                   font-weight:700;font-size:13px;">{_ini}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(A["profile"]["title"], key="hdr_profile",
                         help=A["profile"]["title"]):
                st.session_state["_show_profile"] = True
                st.rerun()
        with _out:
            if st.button(C["header"]["log_out"], use_container_width=True, key="hdr_logout"):
                st.session_state.pop("auth_user", None)
                st.rerun()
        # Beta feedback entry (beta users + admins only; hidden otherwise).
        import feedback as _feedback
        _feedback.feedback_entry(page="home", key="hdr_fb_open")
    else:
        hr_signin, hr_signup = st.columns(2)
        with hr_signin:
            if st.button(C["header"]["sign_in"], use_container_width=True, key="hdr_signin"):
                st.session_state["_auth_mode"] = A["form"]["mode_sign_in"]
                st.session_state["_show_auth"] = True
                st.rerun()
        with hr_signup:
            if st.button(C["header"]["create_account"], type="primary",
                         use_container_width=True, key="hdr_signup"):
                st.session_state["_auth_mode"] = A["form"]["mode_create"]
                st.session_state["_show_auth"] = True
                st.rerun()

# Dialog must be (re)invoked on every rerun while open — a Streamlit dialog
# only stays open across its own internal reruns (typing, radio clicks) if
# it's called unconditionally like this, gated by persisted state; calling it
# only inside the button's `if` block would close it the instant you type.
if st.session_state.get("_confirm_token"):
    _confirm_dialog()
elif st.session_state.get("_show_auth"):
    _auth_dialog()

if st.session_state.pop("_confirm_done", False):
    st.toast(A["confirm"]["success"])

if st.session_state.get("_show_profile"):
    _profile_dialog()


def _play_video_dialog():
    # Reset immediately: the X-dismiss triggers a rerun, and with the state
    # cleared the dialog isn't re-invoked (the video plays without reruns).
    v = st.session_state.get("_video_play")
    st.session_state["_video_play"] = None
    if v and v.get("file"):
        st.video(v["file"], autoplay=True)


# One player for either pitch video — the title follows whichever button opened it
# (dynamic-title dialog: st.dialog(title)(fn)()).
_vp = st.session_state.get("_video_play")
if _vp:
    st.dialog(_vp.get("label") or "Video", width="large")(_play_video_dialog)()

st.divider()

# ── Hero ───────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([1.05, 0.95], gap="large")
with hc1:
    _hero = C["hero"]
    _hs = _hero["stats"]
    # Counts driven by the catalogue statuses (single source of truth); roadmap
    # is the planned ("soon") count rounded to the nearest 5 as an "N+" figure.
    _cat = C["countries"]["catalog"]
    _live_n = sum(1 for c in _cat if c.get("status") == "live")
    _beta_n = sum(1 for c in _cat if c.get("status") == "beta")
    _soon_n = sum(1 for c in _cat if c.get("status") == "soon")
    _roadmap = f"{max(5, round(_soon_n / 5) * 5)}+"
    _num = ('font-family:\'JetBrains Mono\',monospace;font-size:26px;font-weight:600;'
            'color:#0C1119;letter-spacing:-.02em;')
    _lbl = 'font-size:13px;color:#7A828F;margin-top:3px;white-space:nowrap;'
    _div = '<div style="width:1px;background:#E1E4E9;align-self:stretch;"></div>'
    _dot = ('<span style="width:7px;height:7px;border-radius:50%;background:#1F9D62;'
            'display:inline-block;"></span>')
    _bbadge = ('<span class="se-mono" style="font-size:10px;font-weight:600;color:#0A63A6;'
               'background:rgba(10,99,166,.10);padding:2px 6px;border-radius:4px;">BETA</span>')

    def _stat(num, label, extra=""):
        head = (f'<div style="display:flex;align-items:baseline;gap:6px;">'
                f'<span style="{_num}">{num}</span>{extra}</div>') if extra else \
               f'<div style="{_num}">{num}</div>'
        return f'<div>{head}<div style="{_lbl}">{label}</div></div>'

    _stats_html = (
        f'{_stat(_live_n, _hs["label_live"], _dot)}{_div}'
        f'{_stat(_beta_n, _hs["label_beta"], _bbadge)}{_div}'
        f'{_stat(_roadmap, _hs["label_roadmap"])}{_div}'
        f'{_stat(_hs["official"], _hs["label_official"])}')
    st.markdown(f"""
    <div class="se-mono" style="font-size:12px;font-weight:600;letter-spacing:.16em;color:{BLUE};margin-bottom:20px;">
      {_hero["eyebrow"]}
    </div>
    <h1 style="margin:0;font-size:52px;line-height:1.06;letter-spacing:-.025em;font-weight:800;color:#0C1119;">
      {_hero["title"]}
    </h1>
    <p style="margin:20px 0 0;font-size:17px;line-height:1.55;color:#5B6472;max-width:520px;">
      {_hero["intro"]}
    </p>
    """, unsafe_allow_html=True)
    # ── Pitch-video buttons (content/home.toml → [hero.video] + [hero.video2]);
    #    each opens the SAME pop-up player, side by side.
    _vids = [(_hero.get("video", {}), "hero_video"), (_hero.get("video2", {}), "hero_tour"),
             (_hero.get("video3", {}), "hero_cp")]
    _vids = [(v, k) for v, k in _vids if v.get("file") and os.path.exists(v["file"])]
    # Duration chips injected BEFORE the row so the row holds only the two buttons
    # (the CSS below lays them left-aligned with a small gap — see .st-key-hero_vids).
    for v, k in _vids:
        if v.get("duration"):
            st.markdown(f"<style>.st-key-{k} button::after{{content:'{v['duration']}';}}</style>",
                        unsafe_allow_html=True)
    if _vids:
        with st.container(key="hero_vids"):
            for v, k in _vids:
                if st.button(v.get("label", "Watch"), key=k):
                    st.session_state["_video_play"] = {"file": v["file"], "label": v.get("label", "")}
                    st.rerun()
    st.markdown(f"""
    <div style="display:flex;gap:20px;margin-top:24px;flex-wrap:nowrap;align-items:stretch;">
      {_stats_html}
    </div>
    """, unsafe_allow_html=True)

with hc2:
    # ── Live-preview carousel: three example distributions, swipeable ──────────
    # JS-driven slide animation → rendered via components.html (an iframe), since
    # st.markdown strips JS. Self-contained HTML/CSS/JS, no Python state. Sweden
    # slides use the live SCB fetch (fallbacks embedded); France is 2023 microdata.
    _pv = C["hero"]["preview"]
    _slides_data = []
    for _s in _pv["slides"]:
        # live SCB fetch when an occ_code is given, else the stored fallback
        _v = (_fetch_preview_data(_s["occ_code"], _s["year"]) or _s["fallback"]) \
            if _s.get("occ_code") else _s["fallback"]
        _slides_data.append({"title": _s["title"], "sub": _s["sub"],
                             "iso": _s["iso"], "unit": _s["unit"],
                             "per": _s.get("per", _pv["per_month"]), "v": _v})

    def _nbsp(x):                       # 53500 -> "53 900" (nbsp so it never wraps)
        return f"{int(round(x)):,}".replace(",", " ")

    def _slide_html(s):
        v = s["v"]
        # Only the percentiles the source publishes (Norway: quartiles only).
        pres = [(lbl, key) for lbl, key in
                (("P10", "p10"), ("P25", "p25"), ("MED", "median"),
                 ("P75", "p75"), ("P90", "p90")) if v.get(key) is not None]
        lo, hi = v[pres[0][1]], (v[pres[-1][1]] or 1)
        span = (hi - lo) or 1
        rows = ""
        for lbl, key in pres:
            val = v[key]
            w = 30 + 66 * (val - lo) / span        # lowest ≈ 30% … highest ≈ 96%
            m = " med" if lbl == "MED" else ""
            rows += (f'<div class="row"><span class="lbl{m}">{lbl}</span>'
                     f'<div class="track2"><div class="fill{m}" style="width:{w:.0f}%"></div></div>'
                     f'<span class="val{m}">{_nbsp(val)}</span></div>')
        med = f'{_nbsp(v["median"])} {s["unit"]}'
        return (f'<div class="slide"><div class="head"><div>'
                f'<div class="eyebrow mono">{_pv["eyebrow"]}</div>'
                f'<div class="title">{s["title"]}</div>'
                f'<div class="sub">{s["sub"]}</div></div>'
                f'<img class="flag" src="{flag_uri(s["iso"])}" alt=""></div>'
                f'{rows}<div class="foot"><span class="foot-lbl">{_pv["foot_label"]}</span>'
                f'<span class="foot-val mono">{med}<span class="unit">{s["per"]}</span></span></div></div>')

    _slides = "".join(_slide_html(s) for s in _slides_data)
    _dots = "".join('<span class="dot"></span>' for _ in _slides_data)
    _carousel = _CAROUSEL_TPL.replace("__SLIDES__", _slides) \
        .replace("__DOTS__", _dots).replace("__N__", str(len(_slides_data)))
    components.html(_carousel, height=352)

st.write("")
st.write("")

# ── Select a country — the catalog: search + region filter + compact grid ───
# Design: "Salary Explorer Landing 40" export (r13 cards, 34×25 flag frames,
# mono source line, blue Soon pill, pill-group region filter, 12px grid gaps).
_CATALOG = C["countries"]["catalog"]
_CAT_REGIONS = C["countries"]["regions"]
_STATUS_ORDER = {"live": 0, "beta": 1, "soon": 2}

_LOCK_SVG = ('<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#0A63A6"'
             ' stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
             '<rect x="4" y="11" width="16" height="10" rx="2"/>'
             '<path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>')
_ARROW_SVG = ('<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0A63A6"'
              ' stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>')

st.markdown("""
<style>
  /* country rows — keyed containers so a full-card page_link overlay can sit on top */
  [class*="st-key-cr_"]{position:relative;background:#fff;border:1px solid #E7E9ED;
    border-radius:13px;padding:12px 16px;min-height:65px;justify-content:center;gap:0;
    transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease;}
  [class*="st-key-cr_"]:has([data-testid="stPageLink"]):hover{border-color:#C9D2DC;
    box-shadow:0 12px 26px -20px rgba(16,21,31,.40);transform:translateY(-1px);}
  .cat-row{display:flex;align-items:center;gap:10px;}
  .cat-flag{width:34px;height:25px;border-radius:5px;overflow:hidden;flex:none;
    border:1px solid rgba(0,0,0,.08);box-shadow:0 1px 3px rgba(0,0,0,.08);display:block;}
  .cat-flag img{width:100%;height:100%;object-fit:cover;display:block;}
  .cat-mid{display:flex;flex-direction:column;gap:1px;min-width:0;flex:1;}
  .cat-nm{font-size:14.5px;font-weight:600;color:#0C1119;letter-spacing:-.01em;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .cat-src{font-size:10.5px;color:#98A0AC;text-transform:uppercase;white-space:nowrap;
    overflow:hidden;text-overflow:ellipsis;}
  .cat-ic{display:flex;align-items:center;gap:6px;flex:none;}
  .cat-pill{font-size:10.5px;font-weight:600;color:#0A63A6;background:rgba(10,99,166,.10);
    border-radius:20px;padding:3px 8px;}
  .cat-pill-b{color:#B26A00;background:rgba(178,106,0,.13);}
  .cat-pill-live{color:#1B8A5A;background:rgba(27,138,90,.12);}
  /* cards keep their 1/4 width when the live filter hides row siblings
     (Streamlit columns are flexible and would stretch the survivors otherwise);
     media-scoped so Streamlit's own mobile column stacking still works */
  @media (min-width: 641px){
    [data-testid="stColumn"]:has([class*="st-key-cr_"]){
      flex:0 0 calc(25% - 12px) !important;min-width:calc(25% - 12px) !important;}
  }
  /* hover info card (live/beta rows): a gap-free wrapper (padding-top instead of
     a margin) so the pointer can travel INTO the card without losing :hover —
     the locked note at the top is a real ?signin=1 link */
  .cat-tip{display:none;position:absolute;left:0;top:100%;width:300px;
    z-index:80;padding-top:8px;pointer-events:auto;}
  .cat-tip-box{background:#fff;border:1px solid #E7E9ED;border-radius:12px;
    padding:13px 15px;box-shadow:0 18px 40px -18px rgba(16,21,31,.35);text-align:left;}
  [class*="st-key-cr_"]:hover .cat-tip{display:block;}
  [class*="st-key-cr_"]:hover{z-index:90;}
  .cat-tip ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:7px;}
  .cat-tip li{display:flex;gap:9px;font-size:12.5px;color:#4A525F;line-height:1.35;}
  .cat-tip li::before{content:"";width:5px;height:5px;border-radius:50%;
    background:#0A63A6;opacity:.7;margin-top:6px;flex:none;}
  .cat-tip-note{display:flex;align-items:center;gap:7px;margin:0 0 10px;
    padding:0 0 9px;border-bottom:1px solid #EEF0F3;font-size:12px;font-weight:600;
    color:#0A63A6 !important;text-decoration:none !important;}
  a.cat-tip-note:hover{color:#0B72C2 !important;}
  .cat-hd{display:flex;align-items:center;gap:14px;margin:26px 0 12px;
    font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
    letter-spacing:.14em;color:#8A919D;text-transform:uppercase;}
  .cat-hline{flex:1;height:1px;background:#E7E9ED;}
  .cat-count{font-weight:400;color:#B4BAC4;letter-spacing:.02em;}
  /* the page_link overlay: absolute over the card, its own layout slot removed.
     width/height forced — Streamlit sets an inline width on the element
     container, which beats inset:0 and collapsed the click area to 16px. */
  [class*="st-key-cr_"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]){
    position:absolute;inset:0;margin:0;width:100% !important;height:100% !important;}
  [class*="st-key-cr_"] [data-testid="stPageLink"]{position:absolute;inset:0;
    width:100% !important;height:100% !important;}
  [class*="st-key-cr_"] [data-testid="stPageLink"] a{position:absolute;inset:0;
    width:100% !important;height:100% !important;
    background:transparent !important;border-radius:13px;}
  [class*="st-key-cr_"] [data-testid="stPageLink"] a p,
  [class*="st-key-cr_"] [data-testid="stPageLink"] a span{display:none;}
  /* search box (design: white, r11, #DDE1E6 border, magnifier) */
  .st-key-cat_search [data-baseweb="input"]{border:1px solid #DDE1E6;border-radius:11px;
    background:#fff;}
  .st-key-cat_search input{border-radius:11px;font-size:14px;
    padding:11px 14px 11px 38px !important;
    background:#fff url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='15' height='15' viewBox='0 0 24 24' fill='none' stroke='%2398A0AC' stroke-width='2.2' stroke-linecap='round'><circle cx='11' cy='11' r='7'/><path d='M21 21l-4.3-4.3'/></svg>") no-repeat 13px center;}
  /* region pills: grey track, white active pill w/ blue text */
  .st-key-cat_region [data-testid="stButtonGroup"] > div[role="radiogroup"]{
    background:#EDEFF2;border-radius:11px;padding:4px;gap:4px;display:inline-flex;
    flex-wrap:nowrap;}
  .st-key-cat_region [data-testid="stButtonGroup"] button{border:none !important;
    background:transparent !important;border-radius:8px !important;
    padding:7px 14px !important;font-size:13px !important;font-weight:600 !important;
    color:#7A828F !important;box-shadow:none !important;white-space:nowrap !important;}
  .st-key-cat_region [data-testid="stButtonGroup"] button p{white-space:nowrap !important;
    font-size:13px !important;}
  .st-key-cat_region [data-testid="stButtonGroup"]
    button[data-testid="stBaseButton-segmented_controlActive"]{background:#fff !important;
    color:#0A63A6 !important;box-shadow:0 1px 3px rgba(16,21,31,.10) !important;}
  /* sign-in pill (right of the heading, signed-out only) — HTML link so it can
     carry the same lock SVG as the country rows; lands on ?signin=1 */
  .cat-signin{display:inline-flex;align-items:center;gap:8px;float:right;
    background:#fff;border:1px solid #DDE1E6;border-radius:10px;padding:9px 14px;
    font-size:13px;color:#5B6472 !important;text-decoration:none !important;
    white-space:nowrap;}
  .cat-signin b{color:#0A63A6;font-weight:600;}
  .cat-signin:hover{border-color:#C9D2DC;box-shadow:0 6px 16px -12px rgba(16,21,31,.35);}
</style>
""", unsafe_allow_html=True)

_hd_l, _hd_r = st.columns([1.5, 1], vertical_alignment="center")
with _hd_l:
    st.markdown(f"""
    <div class="se-mono" style="font-size:12px;font-weight:600;letter-spacing:.16em;color:{BLUE};margin-bottom:10px;">
      {C["countries"]["eyebrow"]}
    </div>
    """, unsafe_allow_html=True)
    st.subheader(C["countries"]["heading"])
with _hd_r:
    if not st.session_state.get("auth_user"):
        st.markdown(
            f'<a class="cat-signin" href="?signin=1" target="_self">{_LOCK_SVG}'
            f'<span>{C["countries"]["signin_note"]}</span>'
            f'<b>{C["countries"]["signin_cta"]}</b></a>', unsafe_allow_html=True)

_ct_l, _ct_r = st.columns([1.0, 1.6], vertical_alignment="center")
with _ct_l:
    _cat_q = (st.text_input("Search countries", key="cat_search",
                            label_visibility="collapsed",
                            placeholder=C["countries"]["search_ph"].format(n=len(_CATALOG)))
              or "").strip().lower()
with _ct_r:
    _reg_opts = ["all"] + [r["key"] for r in _CAT_REGIONS]
    _reg_lbl = {"all": C["countries"]["region_all"],
                **{r["key"]: r["label"] for r in _CAT_REGIONS}}
    _cat_reg = st.segmented_control("Region", _reg_opts,
                                    format_func=lambda k: _reg_lbl[k], default="all",
                                    key="cat_region", label_visibility="collapsed") or "all"


def _catalog_row(col, c):
    """One compact country card. live/beta + access → whole card is a page_link;
    otherwise inert (Soon pill / lock). Live/beta rows get a hover info card
    (the old tiles' bullets; locked rows add the account-required note)."""
    status = c.get("status", "soon")
    cfg = _registry.get(c["slug"]) if (c.get("slug") and _registry) else None
    openable = bool(cfg is not None and _access and _access.can_open(cfg))
    word = C["countries"]["planned" if status == "soon" else "official"]
    if status == "soon":
        right = f'<span class="cat-pill">{C["countries"]["soon_badge"]}</span>'
    else:
        pill_cls = "cat-pill-b" if status == "beta" else "cat-pill-live"
        badge = C["countries"]["beta_badge" if status == "beta" else "live_badge"]
        # openable → arrow; locked → lock only (the arrow would just crowd the name)
        right = (f'<span class="cat-pill {pill_cls}">{badge}</span>'
                 + (_ARROW_SVG if openable else _LOCK_SVG))
    tip = ""
    info = C["countries"].get("info", {}).get(c["iso"])
    if status in ("live", "beta") and info:
        lis = "".join(f"<li>{p}</li>" for p in info)
        note = ""
        if not openable:
            # note at the TOP; for live rows it's a real link into the sign-in
            # dialog (?signin=1) — beta access isn't granted by signing in, so
            # the beta note stays plain text
            note_txt = C["countries"]["beta_note" if status == "beta" else "locked_note"]
            if status == "live":
                note = (f'<a class="cat-tip-note" href="?signin=1" target="_self">'
                        f'{_LOCK_SVG}{note_txt}</a>')
            else:
                note = f'<div class="cat-tip-note">{_LOCK_SVG}{note_txt}</div>'
        tip = f'<div class="cat-tip"><div class="cat-tip-box">{note}<ul>{lis}</ul></div></div>'
    with col, st.container(key=f"cr_{c['iso']}"):
        st.markdown(
            f'<div class="cat-row">'
            f'<span class="cat-flag"><img src="{flag_uri(c["iso"])}" alt=""></span>'
            f'<span class="cat-mid"><span class="cat-nm">{c["name"]}</span>'
            f'<span class="cat-src se-mono">{c["source"]} · {word}</span></span>'
            f'<span class="cat-ic">{right}</span></div>{tip}', unsafe_allow_html=True)
        if openable:
            st.page_link(f"countries/{c['slug']}/page.py", label=c["name"])


for _r in _CAT_REGIONS:
    if _cat_reg != "all" and _r["key"] != _cat_reg:
        continue
    _rows = [c for c in _CATALOG if c["region"] == _r["key"]]
    # prefix match ("s" → all countries starting with S) — same rule as the
    # client-side live filter below, which handles keystrokes without a rerun
    _shown = sorted(
        [c for c in _rows if not _cat_q or c["name"].lower().startswith(_cat_q)],
        key=lambda c: (_STATUS_ORDER.get(c.get("status", "soon"), 3), c["name"]))
    if not _shown:
        continue
    _live_n = sum(1 for c in _rows if c.get("status") == "live")
    st.markdown(
        f'<div class="cat-hd"><span>{_r["label"]}</span><span class="cat-hline"></span>'
        f'<span class="cat-count">'
        f'{C["countries"]["live_fmt"].format(live=_live_n, total=len(_rows))}</span></div>',
        unsafe_allow_html=True)
    for _j in range(0, len(_shown), 4):
        _cat_cols = st.columns(4, gap="small")
        for _cat_col, _c in zip(_cat_cols, _shown[_j:_j + 4]):
            _catalog_row(_cat_col, _c)

# ── Live search-as-you-type ──────────────────────────────────────────────────
# Streamlit text_input only commits on Enter/blur; this small script (same-origin
# iframe → parent document) filters the rendered cards on every keystroke:
# prefix match on the country name or source, hides emptied rows and region
# headers. The committed (Enter) value then reruns with the same rule.
components.html("""
<script>
(function () {
  const doc = window.parent.document;
  let last = null;
  function apply() {
    const inp = doc.querySelector('.st-key-cat_search input');
    if (!inp) return;
    if (!inp.dataset.liveBound) { inp.dataset.liveBound = '1';
      inp.addEventListener('input', apply); }
    const q = (inp.value || '').trim().toLowerCase();
    const cards = [...doc.querySelectorAll('[class*="st-key-cr_"]')];
    if (q === last && cards.every(c => c.dataset.liveSeen)) return;
    last = q;
    cards.forEach(c => {
      c.dataset.liveSeen = '1';
      const nm = (c.querySelector('.cat-nm') || {textContent: ''}).textContent.toLowerCase();
      const show = !q || nm.startsWith(q);
      const col = c.closest('[data-testid="stColumn"]');
      if (col) col.style.display = show ? '' : 'none';
    });
    const rows = [...doc.querySelectorAll('[data-testid="stHorizontalBlock"]')]
      .filter(r => r.querySelector('[class*="st-key-cr_"]'));
    const hdrs = [...doc.querySelectorAll('.cat-hd')]
      .map(h => h.closest('[data-testid="stElementContainer"]')).filter(Boolean);
    const items = [...hdrs.map(el => ({t: 'h', el})), ...rows.map(el => ({t: 'r', el}))]
      .sort((a, b) => (a.el.compareDocumentPosition(b.el) & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1);
    let curH = null, any = false;
    items.forEach(it => {
      if (it.t === 'h') {
        if (curH) curH.style.display = any ? '' : 'none';
        curH = it.el; any = false;
      } else {
        const vis = [...it.el.querySelectorAll('[data-testid="stColumn"]')]
          .some(col => col.style.display !== 'none' && col.querySelector('[class*="st-key-cr_"]'));
        it.el.style.display = vis ? '' : 'none';
        any = any || vis;
      }
    });
    if (curH) curH.style.display = any ? '' : 'none';
  }
  setInterval(apply, 700);   // rebind + reapply after Streamlit rerenders
  apply();
})();
</script>
""", height=0)

st.write("")
st.divider()
# Footer: the copyright/source note + a small "About" dropdown linking the public
# transparency pages (Data sources & methodology · About · Disclaimers).
_ft_l, _ft_r = st.columns([3, 1], vertical_alignment="center")
with _ft_l:
    st.caption(C["footer"]["note"])
with _ft_r:
    try:
        _AB = content.load("about")["nav"]
        with st.popover(_AB["menu"], use_container_width=True):
            st.page_link("methodology.py", label=_AB["methodology"])
            st.page_link("about.py", label=_AB["about"])
            st.page_link("disclaimers.py", label=_AB["disclaimers"])
    except Exception as _e:  # never let the footer break the landing
        print(f"[landing] About nav unavailable: {_e}")
