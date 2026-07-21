"""Public page — What you get (/access): the access-level comparison table
(Visitor · Free account · Beta tester). Copy lives in content/plans.toml; the
country names and counts are generated live from the country registry
(cfg.access), so releasing or gating a country never touches this page."""
from __future__ import annotations

import html

import streamlit as st

import content
import pubpage

P = content.load("plans")["plans"]

pubpage.inject_base()
pubpage.top(active="plans")

st.markdown(f'<div class="pp-eyebrow">{P["eyebrow"]}</div>'
            f'<div class="pp-h1">{P["title"]}</div>'
            f'<div class="pp-intro">{P["intro"]}</div>', unsafe_allow_html=True)
st.write("")

# ── Country lists per access tier, straight from the registry ────────────────
_pub, _live, _beta = [], [], []
try:
    from core import registry
    for _c in registry.all_countries():
        _tier = {"public": _pub, "registered": _live, "restricted": _beta}.get(
            getattr(_c, "access", "internal"))
        if _tier is not None:
            _tier.append(_c.name)
except Exception as _e:   # the table still renders, just without name lists
    print(f"[plans] country registry unavailable: {_e}")

_T, _R, _S = P["tiers"], P["rows"], P["sections"]
_CHK = ('<span class="pl-chk" role="img" aria-label="' + _R["included"] + '">✓</span>')
_DASH = ('<span class="pl-dash" role="img" aria-label="' + _R["not_included"] + '">—</span>')


def _row(title: str, note: str, marks: tuple[bool, bool, bool]) -> str:
    cells = "".join(
        f'<td class="pl-c{" pl-hi" if i == 1 else ""}">{_CHK if m else _DASH}</td>'
        for i, m in enumerate(marks))
    note_html = f'<div class="pl-note">{note}</div>' if note else ""
    return (f'<tr><td class="pl-f"><div class="pl-t">{title}</div>{note_html}</td>'
            f'{cells}</tr>')


def _sec(label: str) -> str:
    return f'<tr><td colspan="4" class="pl-sec">{label}</td></tr>'


def _names(names: list[str]) -> str:
    return html.escape(" · ".join(sorted(names)))


_pub_title = " & ".join(sorted(_pub, reverse=True)) or "Sweden & France"
_rows = "".join([
    _sec(_S["countries"]),
    _row(_pub_title, _R["public_note"], (True, True, True)),
    _row(_R["live_title"].format(n=len(_live)), _names(_live), (False, True, True)),
    _row(_R["beta_title"].format(n=len(_beta)),
         f'{_R["beta_extra"]}<details class="pl-more">'
         f'<summary>{_R["beta_toggle"].format(n=len(_beta))}</summary>'
         f'{_names(_beta)}</details>', (False, False, True)),
    _sec(_S["features"]),
    _row(_R["tabs_title"], _R["tabs_note"], (True, True, True)),
    _row(_R["lang_title"], _R["lang_note"], (True, True, True)),
    _row(_R["career_title"], _R["career_note"], (False, False, True)),
    _row(_R["early_title"], _R["early_note"], (False, False, True)),
    _sec(_S["price"]),
    ('<tr><td class="pl-f"></td>' + "".join(
        f'<td class="pl-c pl-price{" pl-hi" if i == 1 else ""}">{_R["price_free"]}</td>'
        for i in range(3)) + "</tr>"),
])


def _tier_head(name: str, sub: str, badge: str = "", hi: bool = False) -> str:
    b = f'<div class="pl-badge">{badge}</div>' if badge else '<div class="pl-badge-sp"></div>'
    return (f'<th class="pl-th{" pl-hi" if hi else ""}">{b}'
            f'<div class="pl-tier">{name}</div><div class="pl-sub">{sub}</div></th>')


st.markdown(f"""
<style>
  .pl-table{{width:100%;border-collapse:collapse;table-layout:fixed;}}
  .pl-table th:first-child{{width:42%;}}
  .pl-th{{text-align:center;padding:10px 8px 14px;vertical-align:bottom;}}
  .pl-badge{{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:10px;
    font-weight:600;letter-spacing:.08em;color:#1B6FB0;background:rgba(10,99,166,.10);
    padding:2px 9px;border-radius:5px;margin-bottom:7px;}}
  .pl-badge-sp{{height:26px;}}
  .pl-tier{{font-size:15px;font-weight:700;color:#0C1119;}}
  .pl-sub{{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:#8A919D;
    margin-top:3px;}}
  .pl-sec{{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
    color:#0A63A6;letter-spacing:.06em;text-transform:uppercase;
    padding:20px 2px 7px;border-bottom:1px solid #EEF0F3;}}
  .pl-f{{padding:12px 14px 12px 2px;border-top:1px solid #F3F5F7;vertical-align:top;}}
  .pl-t{{font-size:14px;font-weight:600;color:#26303C;line-height:1.4;}}
  .pl-note{{font-size:12.5px;color:#7A828E;line-height:1.5;margin-top:3px;}}
  .pl-c{{text-align:center;vertical-align:middle;border-top:1px solid #F3F5F7;
    padding:12px 8px;}}
  .pl-hi{{background:rgba(10,99,166,.045);}}
  .pl-chk{{font-size:16px;font-weight:700;color:#0A63A6;}}
  .pl-dash{{font-size:14px;color:#C2C8D0;}}
  .pl-price{{font-size:13.5px;font-weight:600;color:#26303C;}}
  .pl-more{{margin-top:4px;}}
  .pl-more summary{{cursor:pointer;font-size:12px;font-weight:600;color:#0A63A6;
    list-style:none;user-select:none;}}
  .pl-more summary::-webkit-details-marker{{display:none;}}
  .pl-more summary::after{{content:" ▾";}}
  .pl-more[open] summary::after{{content:" ▴";}}
</style>
<div class="pp-card">
  <table class="pl-table">
    <thead><tr><th></th>
      {_tier_head(_T["visitor_name"], _T["visitor_sub"])}
      {_tier_head(_T["account_name"], _T["account_sub"], _T["badge_free"], hi=True)}
      {_tier_head(_T["beta_name"], _T["beta_sub"], _T["badge_invite"])}
    </tr></thead>
    <tbody>{_rows}</tbody>
  </table>
</div>
""", unsafe_allow_html=True)

_B = P["beta"]
st.markdown(f'<div class="pp-card"><div class="pp-sec-h">{_B["heading"]}</div>'
            f'<div class="pp-sec-b">{_B["body"]}</div></div>', unsafe_allow_html=True)

# CTA — signed-out visitors get a button that opens the Create-account dialog
# on the landing page (same session keys the landing header buttons set).
if st.session_state.get("auth_user") is None:
    if st.button(P["cta"]["create_account"], type="primary"):
        _AF = content.load("auth")["form"]
        st.session_state["_auth_mode"] = _AF["mode_create"]
        st.session_state["_show_auth"] = True
        st.switch_page("landing.py")
else:
    st.caption(P["cta"]["signed_in_note"])
