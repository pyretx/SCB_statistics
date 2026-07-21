"""Admin → AI crew — an interactive illustration of the AI agent team that
builds and maintains Salary Explorer (the six .claude/agents robots, the
built-in helpers, the terminal session, and the systems they touch).

Rendered as a single components.html iframe: an SVG scene where every figure
is clickable — clicking updates the description card below the picture with a
plain-language version of that agent's .md definition. All copy lives in
content/admin.toml [crew]; colours come from theme.py so the scene follows
the design system. The iframe loads its own Google-Fonts stylesheet (iframes
don't inherit the app's fonts — the career-map lesson).
"""
from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

import content
import theme

# ── Palette (design-system tokens + the few illustration-only shades) ────────
AC   = theme.ACCENT          # robot outlines, glyphs
SO   = theme.SOFT            # robot bodies (light blue)
SCR  = "#EAF2F9"             # robot chest screens
EYE  = "#0B3B61"             # robot eyes / smiles (dark navy on light blue)
MEAN = theme.MEAN            # the bug glyph only (red = "something's wrong")
GOLD = "#B8863B"             # humans (the admin accent gold)
HUM  = "#F3E3C3"             # human fill
GREY_F, GREY_S = "#EDEFF3", "#8A919D"     # infrastructure fill / stroke
TXT, SUB = "#0C1119", "#5B6472"           # label colours
ARR, DASH = "#98A0AC", "#D3D8E0"          # arrows / dashed container
TERM = "#101826"             # terminal window
SAGE = "#5B8A72"             # LEDs + one design swatch (theme.SERIES green)


def _robot(cx: int, y: int, did: str, glyph: str, name: str, role: str) -> str:
    """One clickable robot: antenna, head, chest screen with a specialty
    glyph, arms/legs, and its two labels. ``y`` is the antenna-ball centre."""
    return (
        f'<g class="fig" data-id="{did}">'
        f'<line x1="{cx}" y1="{y + 2}" x2="{cx}" y2="{y + 12}" stroke="{AC}" stroke-width="1.5"/>'
        f'<circle cx="{cx}" cy="{y}" r="3.5" fill="{AC}"/>'
        f'<rect x="{cx - 22}" y="{y + 12}" width="44" height="30" rx="7" fill="{SO}" stroke="{AC}" stroke-width="1.5"/>'
        f'<circle cx="{cx - 9}" cy="{y + 27}" r="4.5" fill="{EYE}"/>'
        f'<circle cx="{cx + 9}" cy="{y + 27}" r="4.5" fill="{EYE}"/>'
        f'<path d="M{cx - 6} {y + 35} Q{cx} {y + 39} {cx + 6} {y + 35}" fill="none" stroke="{EYE}" stroke-width="1.5" stroke-linecap="round"/>'
        f'<rect x="{cx - 27}" y="{y + 46}" width="54" height="36" rx="9" fill="{SO}" stroke="{AC}" stroke-width="1.5"/>'
        f'<rect x="{cx - 11}" y="{y + 54}" width="22" height="15" rx="3" fill="{SCR}" stroke="{AC}" stroke-width="1"/>'
        f"{glyph}"
        f'<line x1="{cx - 27}" y1="{y + 54}" x2="{cx - 37}" y2="{y + 66}" stroke="{AC}" stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="{cx + 27}" y1="{y + 54}" x2="{cx + 37}" y2="{y + 66}" stroke="{AC}" stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="{cx - 10}" y1="{y + 82}" x2="{cx - 10}" y2="{y + 88}" stroke="{AC}" stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="{cx + 10}" y1="{y + 82}" x2="{cx + 10}" y2="{y + 88}" stroke="{AC}" stroke-width="2" stroke-linecap="round"/>'
        f'<text class="cw-th" x="{cx}" y="{y + 106}" text-anchor="middle">{name}</text>'
        f'<text class="cw-ts" x="{cx}" y="{y + 122}" text-anchor="middle">{role}</text>'
        f"</g>"
    )


def _mini(cy: int) -> str:
    """One grey built-in mini robot (head only) at x=66, head-top ``cy``."""
    return (
        f'<line x1="66" y1="{cy - 6}" x2="66" y2="{cy}" stroke="{GREY_S}" stroke-width="1.5"/>'
        f'<circle cx="66" cy="{cy - 8}" r="2.5" fill="{GREY_S}"/>'
        f'<rect x="54" y="{cy}" width="24" height="18" rx="5" fill="{GREY_F}" stroke="{GREY_S}" stroke-width="1.2"/>'
        f'<circle cx="61" cy="{cy + 9}" r="2.5" fill="{TXT}"/>'
        f'<circle cx="71" cy="{cy + 9}" r="2.5" fill="{TXT}"/>'
    )


def _glyphs(cx: int, y: int) -> dict:
    """The six chest-screen specialty glyphs, keyed by figure id."""
    return {
        "code_reviewer": (
            f'<circle cx="{cx - 2}" cy="{y + 60}" r="3.5" fill="none" stroke="{AC}" stroke-width="1.5"/>'
            f'<line x1="{cx + 1}" y1="{y + 63}" x2="{cx + 5}" y2="{y + 67}" stroke="{AC}" stroke-width="1.5" stroke-linecap="round"/>'),
        "design_i18n": (
            f'<rect x="{cx - 8}" y="{y + 58}" width="5" height="5" fill="{AC}"/>'
            f'<rect x="{cx - 2}" y="{y + 58}" width="5" height="5" fill="{GOLD}"/>'
            f'<rect x="{cx + 4}" y="{y + 58}" width="5" height="5" fill="{SAGE}"/>'),
        "data_provider": (
            f'<rect x="{cx - 7}" y="{y + 64}" width="3" height="3" fill="{AC}"/>'
            f'<rect x="{cx - 2}" y="{y + 61}" width="3" height="6" fill="{AC}"/>'
            f'<rect x="{cx + 3}" y="{y + 58}" width="3" height="9" fill="{AC}"/>'),
        "deploy_verifier": (
            f'<path d="M{cx - 6} {y + 61} l3.5 4 l7 -8" fill="none" stroke="{AC}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'),
        "career_pipeline": (
            f'<rect x="{cx - 8}" y="{y + 64}" width="5" height="3" fill="{AC}"/>'
            f'<rect x="{cx - 2}" y="{y + 61}" width="5" height="3" fill="{AC}"/>'
            f'<rect x="{cx + 4}" y="{y + 58}" width="5" height="3" fill="{AC}"/>'),
        "bug_hunter": (
            f'<ellipse cx="{cx}" cy="{y + 62}" rx="3.5" ry="4.5" fill="{MEAN}"/>'
            f'<line x1="{cx - 3}" y1="{y + 58}" x2="{cx - 5}" y2="{y + 55}" stroke="{MEAN}" stroke-width="1.2" stroke-linecap="round"/>'
            f'<line x1="{cx + 3}" y1="{y + 58}" x2="{cx + 5}" y2="{y + 55}" stroke="{MEAN}" stroke-width="1.2" stroke-linecap="round"/>'),
    }


def _svg(figs: dict) -> str:
    """The full scene. Figure labels come from [crew.figures.*] name/tag so
    the picture and the description cards can never drift apart."""

    def nm(k):  # split "name" for the two label lines under each robot
        return figs[k]["name"]

    robots = []
    for cx, y, did in [
        (140, 352, "code_reviewer"), (340, 352, "design_i18n"),
        (540, 352, "data_provider"), (140, 492, "deploy_verifier"),
        (340, 492, "career_pipeline"), (540, 492, "bug_hunter"),
    ]:
        g = _glyphs(cx, y)[did]
        robots.append(_robot(cx, y, did, g, nm(did), figs[did]["tag"].lower()))

    return (
        f'<svg width="100%" viewBox="0 0 680 870" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The AI crew">'
        f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M2 1L8 5L2 9" fill="none" stroke="{ARR}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>'
        # owner
        f'<g class="fig" data-id="owner">'
        f'<circle cx="340" cy="56" r="13" fill="{HUM}" stroke="{GOLD}" stroke-width="1.5"/>'
        f'<rect x="322" y="72" width="36" height="26" rx="11" fill="{HUM}" stroke="{GOLD}" stroke-width="1.5"/>'
        f'<text class="cw-th" x="340" y="118" text-anchor="middle">{nm("owner")}</text>'
        f'<text class="cw-ts" x="340" y="134" text-anchor="middle">asks · reviews · signs off</text></g>'
        f'<line class="cw-arr" x1="327" y1="142" x2="327" y2="162" marker-end="url(#arrow)"/>'
        f'<line class="cw-arr" x1="353" y1="162" x2="353" y2="142" marker-end="url(#arrow)"/>'
        # terminal
        f'<g class="fig" data-id="terminal">'
        f'<rect x="200" y="170" width="280" height="90" rx="10" fill="{TERM}"/>'
        f'<circle cx="218" cy="184" r="4" fill="{MEAN}"/><circle cx="232" cy="184" r="4" fill="{GOLD}"/><circle cx="246" cy="184" r="4" fill="{SAGE}"/>'
        f'<text class="cw-mono" x="218" y="216">&gt; review the diff</text>'
        f'<text class="cw-mono" x="218" y="236">&gt; deploy dev + verify</text>'
        f'<text class="cw-th" x="340" y="282" text-anchor="middle">{nm("terminal")}</text>'
        f'<text class="cw-ts" x="340" y="298" text-anchor="middle">your terminal · edits · delegates</text></g>'
        # built-ins (one clickable group)
        f'<g class="fig" data-id="builtins">'
        f'<text class="cw-th" x="48" y="145">{nm("builtins")}</text>'
        f"{_mini(158)}{_mini(194)}{_mini(230)}"
        f'<text class="cw-ts" x="86" y="171">Explore</text>'
        f'<text class="cw-ts" x="86" y="207">Plan</text>'
        f'<text class="cw-ts" x="86" y="243">/code-review</text></g>'
        f'<line class="cw-arr" x1="196" y1="205" x2="174" y2="205" marker-end="url(#arrow)"/>'
        f'<line class="cw-arr" x1="340" y1="304" x2="340" y2="314" marker-end="url(#arrow)"/>'
        # the six robots in their dashed home
        f'<rect x="40" y="318" width="600" height="304" rx="8" fill="none" stroke="{DASH}" stroke-width="1" stroke-dasharray="5 4"/>'
        f'<text class="cw-label" x="52" y="340">PROJECT SUB-AGENTS · .CLAUDE/AGENTS</text>'
        f'{"".join(robots)}'
        # flows down to the systems
        f'<line class="cw-arr" x1="140" y1="626" x2="140" y2="734" marker-end="url(#arrow)"/>'
        f'<path class="cw-arr" fill="none" d="M522 626 L522 660 L360 660 L360 734" marker-end="url(#arrow)"/>'
        f'<line class="cw-arr" x1="552" y1="626" x2="552" y2="730" marker-end="url(#arrow)"/>'
        # VPS
        f'<g class="fig" data-id="vps">'
        f'<rect x="100" y="738" width="80" height="58" rx="6" fill="{GREY_F}" stroke="{GREY_S}" stroke-width="1.2"/>'
        f'<rect x="108" y="746" width="64" height="10" rx="2" fill="#FFFFFF"/><circle cx="166" cy="751" r="2.5" fill="{SAGE}"/>'
        f'<rect x="108" y="764" width="64" height="10" rx="2" fill="#FFFFFF"/><circle cx="166" cy="769" r="2.5" fill="{SAGE}"/>'
        f'<rect x="108" y="782" width="64" height="10" rx="2" fill="#FFFFFF"/><circle cx="166" cy="787" r="2.5" fill="{SAGE}"/>'
        f'<text class="cw-th" x="140" y="820" text-anchor="middle">{nm("vps")}</text>'
        f'<text class="cw-ts" x="140" y="836" text-anchor="middle">dev · test · prod</text></g>'
        # the app
        f'<g class="fig" data-id="app">'
        f'<rect x="300" y="738" width="80" height="58" rx="6" fill="{GREY_F}" stroke="{GREY_S}" stroke-width="1.2"/>'
        f'<rect x="306" y="744" width="68" height="8" rx="3" fill="#FFFFFF"/>'
        f'<rect x="312" y="772" width="9" height="18" fill="{AC}"/><rect x="325" y="764" width="9" height="26" fill="{AC}"/>'
        f'<rect x="338" y="776" width="9" height="14" fill="{AC}"/><rect x="351" y="758" width="9" height="32" fill="{AC}"/>'
        f'<text class="cw-th" x="340" y="820" text-anchor="middle">{nm("app")}</text>'
        f'<text class="cw-ts" x="340" y="836" text-anchor="middle">review server · dev env</text></g>'
        # Supabase
        f'<g class="fig" data-id="supabase">'
        f'<ellipse cx="540" cy="790" rx="36" ry="8" fill="{GREY_F}" stroke="{GREY_S}" stroke-width="1.2"/>'
        f'<rect x="504" y="744" width="72" height="46" fill="{GREY_F}"/>'
        f'<line x1="504" y1="744" x2="504" y2="790" stroke="{GREY_S}" stroke-width="1.2"/>'
        f'<line x1="576" y1="744" x2="576" y2="790" stroke="{GREY_S}" stroke-width="1.2"/>'
        f'<ellipse cx="540" cy="744" rx="36" ry="8" fill="#FFFFFF" stroke="{GREY_S}" stroke-width="1.2"/>'
        f'<text class="cw-th" x="540" y="820" text-anchor="middle">{nm("supabase")}</text>'
        f'<text class="cw-ts" x="540" y="836" text-anchor="middle">shared DB · feedback</text></g>'
        # users
        f'<g class="fig" data-id="users">'
        f'<circle cx="612" cy="752" r="6" fill="{HUM}" stroke="{GOLD}" stroke-width="1.2"/>'
        f'<rect x="604" y="760" width="16" height="13" rx="6" fill="{HUM}" stroke="{GOLD}" stroke-width="1.2"/>'
        f'<circle cx="632" cy="757" r="6" fill="{HUM}" stroke="{GOLD}" stroke-width="1.2"/>'
        f'<rect x="624" y="765" width="16" height="13" rx="6" fill="{HUM}" stroke="{GOLD}" stroke-width="1.2"/>'
        f'<text class="cw-ts" x="622" y="796" text-anchor="middle">users</text></g>'
        f'<line class="cw-arr" x1="600" y1="764" x2="582" y2="764" marker-end="url(#arrow)"/>'
        f"</svg>"
    )


# CSS/JS are plain strings (no f-strings) so braces need no escaping.
_CSS = """
  body { margin:0; font-family:'Hanken Grotesk',sans-serif; background:transparent; }
  .wrap { max-width:680px; margin:0 auto; }
  .fig { cursor:pointer; transition:opacity .15s ease; }
  .fig:hover { opacity:.7; }
  .fig.dim { opacity:.35; }
  svg text { user-select:none; }
  .cw-th { font-family:'Hanken Grotesk',sans-serif; font-size:13px; font-weight:600; fill:__TXT__; }
  .cw-ts { font-family:'Hanken Grotesk',sans-serif; font-size:11.5px; font-weight:500; fill:__SUB__; }
  .cw-mono { font-family:'JetBrains Mono',monospace; font-size:11px; fill:#9EC2DE; }
  .cw-label { font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:600;
              letter-spacing:.11em; fill:#8A919D; }
  .cw-arr { stroke:__ARR__; stroke-width:1.5; }
  #panel { border:1px solid #E7E9ED; border-radius:14px; background:#fff;
           padding:16px 20px; margin:14px auto 0; max-width:640px; }
  #p-tag { font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:600;
           letter-spacing:.12em; color:__AC__; margin-bottom:4px; }
  #p-name { font-size:15.5px; font-weight:700; color:__TXT__; margin-bottom:6px; }
  #p-desc { font-size:13.5px; line-height:1.6; color:#3A4250; }
  #p-hint { font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.08em;
            color:#8A919D; margin-top:10px; text-transform:uppercase; }
"""

_JS = """
  const figs = document.querySelectorAll('.fig');
  figs.forEach(g => g.addEventListener('click', () => {
    const id = g.dataset.id, f = FIGS[id];
    if (!f) return;
    figs.forEach(o => o.classList.toggle('dim', o.dataset.id !== id));
    document.getElementById('p-tag').textContent = f.tag;
    document.getElementById('p-name').textContent = f.name;
    document.getElementById('p-desc').textContent = f.desc;
    document.getElementById('p-hint').textContent = HINT;
  }));
"""


def render() -> None:
    C = content.load("admin").get("crew", {})
    figs = C.get("figures", {})
    if not figs:
        st.error("content/admin.toml is missing the [crew] section.")
        return

    st.caption(C.get("intro", ""))
    css = (_CSS.replace("__TXT__", TXT).replace("__SUB__", SUB)
               .replace("__ARR__", ARR).replace("__AC__", AC))
    html = (
        "<html><head>"
        '<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700'
        '&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">'
        f"<style>{css}</style></head><body><div class='wrap'>"
        f"{_svg(figs)}"
        f"<div id='panel'>"
        f"<div id='p-tag'>{C.get('default_tag', '')}</div>"
        f"<div id='p-name'>{C.get('default_name', '')}</div>"
        f"<div id='p-desc'>{C.get('default_desc', '')}</div>"
        f"<div id='p-hint'>{C.get('hint', '')}</div>"
        f"</div></div>"
        f"<script>const FIGS = {json.dumps(figs)}; "
        f"const HINT = {json.dumps(C.get('hint', ''))};{_JS}</script>"
        "</body></html>"
    )
    components.html(html, height=1120, scrolling=False)
