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

import requests
import streamlit as st

import auth

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_GLOBE  = os.path.join(_ASSETS, "logo.png")

BLUE = "#0A63A6"

# Country-card CTAs are real <a href="?country=..."> links inside HTML (so the
# whole card can be one styled block with a scoped :hover, per design-system §6).
# JS can't call Python, so navigation rides a URL query param routed here.
_ROUTES = {"sweden": "scb_salaries.py", "france": "france.py"}
if st.query_params.get("country") in _ROUTES:
    st.switch_page(_ROUTES[st.query_params["country"]])

# Single source of truth for the country grid — add a country here only.
COUNTRIES = [
    {
        "num": "01", "name": "Sweden", "native": "Sverige", "source": "SCB · official",
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
        "source": "BLS Public Data API · planned",
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
     border-radius:16px !important; padding:22px 22px 18px !important; height:100%;
     transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
  [class*="st-key-cc_"]:hover { transform: translateY(-3px);
     box-shadow: 0 18px 40px -24px rgba(16,21,31,.30); border-color:#D3D8DF !important; }
  /* Equal-height tiles: stretch each column to the tallest in the row, then make
     EVERY wrapper between the column and the card full-height so a shorter card
     (e.g. the US tile) stretches up to match. The source line is pinned to the
     foot (margin-top:auto), so the slack lands after the last bullet and all
     tiles share the same top and bottom edge. */
  [data-testid="stColumn"]:has([class*="st-key-cc_"]) { align-self: stretch; }
  [data-testid="stColumn"]:has([class*="st-key-cc_"]) > [data-testid="stVerticalBlock"],
  [data-testid="stLayoutWrapper"]:has(> [class*="st-key-cc_"]) { height:100% !important; }
  [class*="st-key-cc_"] { gap:0; }
  /* Full-width CTA button, directly under the card header (mockup). Force the
     element container + page-link to full width (Streamlit sizes to content),
     and add space before the bullets. */
  [class*="st-key-cc_"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]),
  [class*="st-key-cc_"] [data-testid="stElementContainer"]:has(.se-cta-off) {
     width:100% !important; margin-bottom:16px; }
  [class*="st-key-cc_"] [data-testid="stPageLink"] { width:100%; }
  [class*="st-key-cc_"] [data-testid="stPageLink"] a { width:100%; background:#0A63A6;
     border-radius:9px; padding:10px 14px; justify-content:center;
     box-shadow:0 2px 8px rgba(10,99,166,.24); transition: background .15s ease; }
  [class*="st-key-cc_"] [data-testid="stPageLink"] a:hover { background:#0B72C2; }
  [class*="st-key-cc_"] [data-testid="stPageLink"] a p,
  [class*="st-key-cc_"] [data-testid="stPageLink"] a span { color:#fff !important;
     font-weight:600; font-size:14px; }
  /* Source line pinned to the card foot with a rule. */
  [class*="st-key-cc_"] [data-testid="stElementContainer"]:has(.se-source) { margin-top:auto; }
  .se-source { padding-top:14px; border-top:1px solid #EEF0F3;
               font-family:'JetBrains Mono',monospace; font-size:11px; color:#98A0AC; }
  /* Fixed-size flag swatch so it never stretches with the card width. */
  .se-flag { width: 46px; height: 33px; border-radius: 7px; flex: none; overflow: hidden;
             border: 1px solid rgba(0,0,0,.08); box-shadow: 0 1px 3px rgba(0,0,0,.08); }
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
        st.markdown("""
        <div class="se-authpanel">
          <div class="se-blob" style="width:190px;height:190px;top:-70px;right:-60px;"></div>
          <div class="se-blob" style="width:150px;height:150px;bottom:-60px;left:-50px;"></div>
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
                    # no self-registration can ever mint an admin).
                    user, err = auth.sign_up(email.strip(), pw, name.strip())
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
      <div style="width:30px;height:30px;border-radius:8px;background:{BLUE};flex:none;
                  display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(10,99,166,.35);">
        <div style="width:13px;height:13px;border-radius:50%;border:2px solid #fff;position:relative;">
          <div style="position:absolute;top:50%;left:-2px;right:-2px;height:2px;background:#fff;transform:translateY(-50%);"></div>
        </div>
      </div>
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
      and trends, standardised so you can compare occupations across countries.
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
    _preview = _fetch_preview_data("2512", "2025")
    if _preview:
        _rows = [
            ("P10", _preview["p10"]), ("P25", _preview["p25"]), ("MED", _preview["median"]),
            ("P75", _preview["p75"]), ("P90", _preview["p90"]),
        ]
        _max = _preview["p90"] or 1
        _bar_html = "".join(f'''
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:11px;">
        <span class="se-mono" style="font-size:11px;color:{'#0A63A6' if lbl=='MED' else '#98A0AC'};
                                     font-weight:{'600' if lbl=='MED' else '400'};width:32px;flex:none;">{lbl}</span>
        <div style="flex:1;height:8px;border-radius:5px;background:#EEF0F3;overflow:hidden;">
          <div style="width:{val/_max*96:.0f}%;height:100%;background:{'#0A63A6' if lbl=='MED' else '#B9C6D4'};"></div>
        </div>
        <span class="se-mono" style="font-size:11px;color:#5B6472;width:56px;text-align:right;flex:none;">{val:,.0f}</span>
      </div>''' for lbl, val in _rows)
        _median_fmt = f"{_preview['median']:,.0f}"
    else:
        _bar_html = "<div style='font-size:13px;color:#9AA1AC;'>Live data unavailable right now.</div>"
        _median_fmt = "—"

    st.markdown(f"""
    <div style="background:#fff;border:1px solid #E7E9ED;border-radius:16px;padding:22px;
                box-shadow:0 20px 40px -26px rgba(16,21,31,.25);">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
        <div>
          <div class="se-mono" style="font-size:10px;font-weight:600;letter-spacing:.14em;color:{BLUE};">LIVE PREVIEW</div>
          <div style="font-weight:700;font-size:15px;margin-top:5px;">Software developers</div>
          <div style="font-size:12px;color:#8A919D;margin-top:2px;">Sweden · SCB 2025 · monthly, SEK</div>
        </div>
        <div style="width:34px;height:24px;border-radius:5px;border:1px solid rgba(0,0,0,.08);
                    background:#006AA7;background-image:linear-gradient(90deg,transparent 26%,#FECC00 26% 40%,transparent 40%),
                    linear-gradient(0deg,transparent 40%,#FECC00 40% 60%,transparent 60%);"></div>
      </div>
      {_bar_html}
      <div style="margin-top:14px;padding-top:13px;border-top:1px solid #EEF0F3;
                  display:flex;justify-content:space-between;">
        <span style="font-size:12px;color:#8A919D;">Median gross salary</span>
        <span class="se-mono" style="font-weight:600;font-size:14px;">{_median_fmt} kr<span style="color:#98A0AC;font-weight:400;">/mo</span></span>
      </div>
    </div>
    """, unsafe_allow_html=True)

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
          <div class="se-flag" style="{c['flag_css']}"></div>
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
