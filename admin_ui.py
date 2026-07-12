"""Shared, full-page Admin panel UI (rendered by admin.py).

Plain module — NO top-level Streamlit calls — so its section functions can be
reused elsewhere (e.g. Sweden's 'Manage users' dialog calls users_section()).
Access is gated to admin/master by admin.py before any of this renders.

Sections: Overview · Data sources · Users. The visual design (card tiles, status
pills, mono stat grids, compact button rows) follows the approved Admin-panel
mockup. All static text lives in content/admin.toml (see content.py) — edit
there, not here.
"""
from __future__ import annotations

import gzip
import json
import os
from collections import Counter

import streamlit as st

import auth
import content
import theme

_ADMIN_ROLES = ("admin", "master")
_ROOT = os.path.dirname(os.path.abspath(__file__))   # repo root (admin_ui.py lives here)


def _A() -> dict:
    """All admin-panel text (content/admin.toml). Uncached — edits show live."""
    return content.load("admin")


# ── shared styling ───────────────────────────────────────────────────────────
CSS = """
<style>
/* Section tab bar (segmented control) → pill toggle */
.st-key-_admin_section [data-testid="stButtonGroup"]{ background:#EDEFF3; border-radius:11px;
  padding:3px; gap:2px; display:inline-flex; }
.st-key-_admin_section [data-testid="stButtonGroup"] button{ border:none!important;
  background:transparent!important; border-radius:8px!important; padding:5px 18px!important;
  color:#5B6472!important; font-weight:600!important; }
.st-key-_admin_section [data-testid="stButtonGroup"]
  button[data-testid="stBaseButton-segmented_controlActive"]{ background:#fff!important;
  color:#0A63A6!important; box-shadow:0 1px 3px rgba(16,21,31,.14); }

/* Cards (any keyed container starting adcard_) */
[class*="st-key-adcard_"]{ background:#fff; border:1px solid #E7E9ED!important;
  border-radius:16px!important; padding:22px 24px!important; box-shadow:0 1px 2px rgba(16,21,31,.04); }
[class*="st-key-adkpi_"]{ background:#fff; border:1px solid #E7E9ED!important;
  border-radius:16px!important; padding:18px 20px!important; }

/* Inputs inside cards — the design's visible 1px bordered, rounded fields.
   (On the white card the theme's default input border washed out entirely.) */
[class*="st-key-adcard_"] [data-baseweb="input"],
[class*="st-key-adcard_"] [data-baseweb="select"] > div{
  border:1px solid #DDE1E6 !important; border-radius:10px !important;
  background-color:#fff !important; }
[class*="st-key-adcard_"] [data-baseweb="input"] input{ background:transparent !important; }
[class*="st-key-adcard_"] [data-baseweb="input"]:focus-within,
[class*="st-key-adcard_"] [data-baseweb="select"] > div:focus-within{
  border-color:#0A63A6 !important; box-shadow:0 0 0 3px rgba(10,99,166,.12) !important; }

/* Card header (flag · name · source · type … status pill) */
.ad-hd{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:16px; }
.ad-hdL{ display:flex; align-items:center; gap:12px; min-width:0; }
.ad-flag{ width:34px; height:24px; border-radius:5px; object-fit:cover;
  border:1px solid rgba(0,0,0,.08); flex:none; }
.ad-name{ font-weight:700; font-size:16px; color:#0C1119; }
.ad-src{ font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:600;
  letter-spacing:.04em; color:#0A63A6; margin-left:9px; }
.ad-type{ font-size:13px; color:#8A919D; margin-left:6px; }

/* Status pills */
.ad-pill{ display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600;
  padding:4px 11px; border-radius:20px; white-space:nowrap; flex:none; }
.ad-pill::before{ content:''; width:7px; height:7px; border-radius:50%; background:currentColor; }
.ad-green{ color:#1B8A5A; background:rgba(27,138,90,.12); }
.ad-amber{ color:#B26A00; background:rgba(178,106,0,.14); }
.ad-grey{ color:#8A919D; background:#F1F3F6; }
.ad-grey::before{ background:#B4BAC4; }

/* Mono stat grid */
.ad-stats{ display:flex; flex-wrap:wrap; gap:14px 42px; margin-bottom:12px; }
.ad-lbl{ font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.11em;
  text-transform:uppercase; color:#98A0AC; margin-bottom:5px; }
.ad-val{ font-family:'JetBrains Mono',monospace; font-size:22px; font-weight:600;
  color:#0C1119; letter-spacing:-.01em; }
.ad-cap{ font-size:13px; color:#8A919D; line-height:1.5; }

/* Amber "update available" alert */
.ad-alert{ display:flex; align-items:center; gap:9px; background:rgba(178,106,0,.09);
  border:1px solid rgba(178,106,0,.18); color:#8A6A2A; font-size:13px; padding:10px 13px;
  border-radius:10px; margin:14px 0 2px; }

/* Compact button rows inside cards — buttons keep their content width */
[class*="st-key-adcard_"] .stButton button{ padding:7px 16px; border-radius:9px;
  font-weight:600; font-size:13.5px; }

/* KPI cards (Overview) */
.ad-kico{ width:36px; height:36px; border-radius:10px; display:flex; align-items:center;
  justify-content:center; margin-bottom:14px; }
.ad-knum{ font-size:30px; font-weight:800; color:#0C1119; letter-spacing:-.02em; line-height:1; }
.ad-klbl{ font-size:13px; color:#7A828F; margin-top:5px; }

/* Country tiles (Overview → Open a country): styled page-links with a flag */
[class*="st-key-adtile_"] [data-testid="stPageLink"]{ width:100%; }
[class*="st-key-adtile_"] [data-testid="stPageLink"] a{ width:100%; border:1px solid #E7E9ED;
  border-radius:10px; background-color:#fff; padding:10px 32px 10px 48px; position:relative;
  background-repeat:no-repeat; background-position:13px center; background-size:24px 17px;
  transition:border-color .15s ease, background-color .15s ease; justify-content:flex-start; }
[class*="st-key-adtile_"] [data-testid="stPageLink"] a:hover{ border-color:#C9CFD8;
  background-color:#F9FAFB; }
[class*="st-key-adtile_"] [data-testid="stPageLink"] a p,
[class*="st-key-adtile_"] [data-testid="stPageLink"] a span{ font-weight:600; font-size:13.5px;
  color:#0C1119!important; }
[class*="st-key-adtile_"] [data-testid="stPageLink"] a::after{ content:'↗'; position:absolute;
  right:13px; top:50%; transform:translateY(-50%); color:#98A0AC; font-size:13px; }

/* Field label (mono uppercase, above inputs) */
.ad-flbl{ font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.10em;
  text-transform:uppercase; color:#98A0AC; margin:2px 0 4px; }

/* Users table */
.ad-th{ font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.09em;
  text-transform:uppercase; color:#98A0AC; }
.ad-user{ display:flex; align-items:center; gap:10px; }
.ad-av{ width:30px; height:30px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; color:#fff; font-weight:700; font-size:11px; flex:none; }
.ad-uname{ font-weight:600; font-size:13.5px; color:#0C1119; }
.ad-email{ color:#0A63A6; font-size:13.5px; }
.ad-badge{ display:inline-block; font-size:12px; font-weight:600; padding:3px 11px; border-radius:14px; }
.ad-access{ font-size:13px; color:#5B6472; }
</style>
"""

# lucide-ish icons for the Overview KPI cards
_IC_USERS = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" width="18" height="18">'
             '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
             '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>')
_IC_GLOBE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" width="18" height="18">'
             '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>'
             '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>')
_IC_ZAP = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round" stroke-linejoin="round" width="18" height="18">'
           '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>')
_IC_ALERT = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" width="18" height="18">'
             '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
             '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>')


# ── small helpers ────────────────────────────────────────────────────────────
def _file_meta(name: str) -> dict:
    """Read a repo-root data file (plain or .gz JSON) → {exists, size, data}."""
    p = os.path.join(_ROOT, name)
    if not os.path.exists(p):
        return {"exists": False, "size": 0, "data": None}
    out = {"exists": True, "size": os.path.getsize(p), "data": None}
    try:
        opener = gzip.open if name.endswith(".gz") else open
        with opener(p, "rt", encoding="utf-8") as f:
            out["data"] = json.load(f)
    except Exception:
        pass
    return out


def _fmt_bytes(n) -> str:
    return f"{n / 1e6:.2f} MB" if n else "—"


def _n(v) -> str:
    """1402 → '1 402' (design's mono thin-space grouping)."""
    try:
        return f"{int(v):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(v)


def _country_options() -> dict:
    opts = {"sweden": "Sweden", "france": "France"}
    try:
        from core import registry
        for c in registry.all_countries():
            if c.slug != "demo":
                opts[c.slug] = c.name
    except Exception:
        pass
    return opts


def _load_users(force: bool = False):
    if force or "_admin_users" not in st.session_state:
        with st.spinner(_A()["users"]["loading"]):
            try:
                st.session_state["_admin_users"] = (auth.list_users(), None)
            except Exception as e:  # noqa: BLE001
                st.session_state["_admin_users"] = (None, str(e))
    return st.session_state["_admin_users"]


def _invalidate_users():
    st.session_state.pop("_admin_users", None)
    # Also drop the per-user edit-widget states (role dropdown / country grant
    # multiselect). Streamlit keeps a keyed widget's value across reruns and
    # ignores its index/default afterwards — so after e.g. a beta-request
    # accept, the ✏️ popover would still SHOW the pre-change role even though
    # the row badge (fresh data) is correct. Fresh data ⇒ fresh defaults.
    for k in [k for k in st.session_state
              if str(k).startswith(("role_", "cty_"))]:
        st.session_state.pop(k, None)


def _match(query: str, *texts) -> bool:
    q = (query or "").strip().lower()
    return (not q) or any(q in (t or "").lower() for t in texts)


def _pill(kind: str, text: str) -> str:
    return f'<span class="ad-pill ad-{kind}">{text}</span>'


def _stats(pairs) -> str:
    items = "".join(f'<div><div class="ad-lbl">{l}</div><div class="ad-val">{v}</div></div>'
                    for l, v in pairs)
    return f'<div class="ad-stats">{items}</div>'


def _extras_html(T: dict) -> str:
    """'Beyond the framework standard' feature list for a country card — every
    country-specific addition (extra tabs, hooks) is declared here (admin.toml)."""
    items = T.get("extras") or []
    if not items:
        return ""
    lis = "".join(f'<li style="margin:3px 0;">{x}</li>' for x in items)
    return (f'<div class="ad-cap" style="margin-top:12px;">'
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
            f'letter-spacing:.1em;text-transform:uppercase;color:#98A0AC;">'
            f'{T.get("extras_title", "Beyond the standard")}</span>'
            f'<ul style="margin:6px 0 0;padding-left:18px;">{lis}</ul></div>')


def _hdr(iso: str, name: str, src: str, typ: str, pill_html: str) -> str:
    return (f'<div class="ad-hd"><div class="ad-hdL">'
            f'<img class="ad-flag" src="{theme.flag_uri(iso)}" alt="">'
            f'<span><span class="ad-name">{name}</span>'
            f'<span class="ad-src">{src}</span><span class="ad-type">· {typ}</span></span>'
            f'</div>{pill_html}</div>')


def _btnrow():
    """Horizontal, content-width button row (design's compact side-by-side pair).
    Falls back to a plain (vertical) container on older Streamlit."""
    try:
        return st.container(horizontal=True, gap="small")
    except TypeError:
        return st.container()


# ── Section: Overview ────────────────────────────────────────────────────────
def _kpi(col, key, icon, color, tint, num, label):
    with col, st.container(border=True, key=f"adkpi_{key}"):
        st.markdown(
            f'<div class="ad-kico" style="background:{tint};color:{color};">{icon}</div>'
            f'<div class="ad-knum">{num}</div><div class="ad-klbl">{label}</div>',
            unsafe_allow_html=True)


def _country_links() -> list[tuple[str, str, str, str]]:
    """[(slug, name, iso, page)] — framework countries, registry order (the
    public Sweden/France first)."""
    links = []
    try:
        from core import registry
        for c in registry.all_countries():
            if c.slug != "demo":
                links.append((c.slug, c.name, c.iso, f"countries/{c.slug}/page.py"))
    except Exception:
        pass
    return links


# Decommissioned builds — admin-only reference pages, shown in their own card.
_LEGACY_LINKS = [("sweden_old", "Sweden (legacy)", "se", "scb_salaries.py"),
                 ("france_old", "France (legacy)", "fr", "france.py")]


def _catalog_counts():
    """(total, live, beta, planned) from the landing catalog (home.toml) — the
    single source of truth for country statuses."""
    try:
        import content
        cat = content.load("home").get("countries", {}).get("catalog", [])
        live = sum(1 for c in cat if c.get("status") == "live")
        beta = sum(1 for c in cat if c.get("status") == "beta")
        return len(cat), live, beta, len(cat) - live - beta
    except Exception:
        return "—", "—", "—", "—"


def _run_update_check():
    """Probe every source via the shared service (updates.check_all — the same
    functions the per-source card buttons call) and mirror the results into the
    session flags the Data-sources card pills derive from. Runs only when the
    admin presses the button — never on page load, so entering the panel stays
    instant no matter how many countries exist."""
    import updates as upd
    results = upd.check_all()
    upd.record_check(results)              # persist "last checked" across restarts
    st.session_state["_upd_results"] = results   # cards + table read this
    import datetime as _dt
    st.session_state["_upd_checked_at"] = _dt.datetime.now().strftime("%H:%M")


def _updates_card():
    """The global update table: one row per source (country · source · current ·
    latest · update available · status · select), then Update-selected with an
    explicit confirmation. Rendered only after a check has run this session."""
    results = st.session_state.get("_upd_results")
    if not results:
        return
    import pandas as pd
    import updates as upd
    U = _A()["updates"]
    by_key = {s.key: s for s in results}
    st.write("")
    with st.container(border=True, key="adcard_updates"):
        st.markdown(f"#### {U['heading']}")
        st.caption(U["caption"].format(t=st.session_state.get("_upd_checked_at", "—")))
        # Only rows that need attention: an update available, or a failed probe.
        # Everything current stays out of the way (a green all-clear instead).
        shown = [s for s in results if s.update_available or s.error]
        if not shown:
            st.success(U["all_ok"])
            return
        rows = []
        for s in shown:
            rows.append({
                U["col_select"]: False,
                U["col_country"]: s.country,
                U["col_source"]: s.source,
                U["col_current"]: s.current,
                U["col_latest"]: s.latest or "—",
                U["col_upd"]: (U["v_manual"] if s.update_available and not s.can_auto
                               else U["v_yes"] if s.update_available
                               else U["v_no"] if s.update_available is False
                               else U["v_na"]),
                U["col_status"]: (U["o_unavailable"] + " — " + s.error if s.error
                                  else s.note),
            })
        df = pd.DataFrame(rows)
        other_cols = [c for c in df.columns if c != U["col_select"]]
        edited = st.data_editor(
            df, hide_index=True, use_container_width=True, key="adm_upd_table",
            column_config={U["col_select"]: st.column_config.CheckboxColumn(
                U["col_select"], help=U["none_selected"])},
            disabled=other_cols)
        sel_keys = [shown[i].key for i, v in enumerate(edited[U["col_select"]]) if v]

        if st.button(U["btn_update"], type="primary", key="adm_upd_go"):
            if sel_keys:
                st.session_state["_upd_confirm"] = sel_keys
            else:
                st.info(U["none_selected"])
        pending = st.session_state.get("_upd_confirm")
        if pending:
            names = ", ".join(by_key[k].country for k in pending if k in by_key)
            st.warning(U["confirm"].format(names=names))
            with _btnrow():
                yes = st.button(U["btn_confirm"], type="primary", key="adm_upd_yes")
                no = st.button(U["btn_cancel"], key="adm_upd_no")
            if yes:
                st.session_state.pop("_upd_confirm", None)
                with st.status(U["running"], expanded=True) as box:
                    outcomes = upd.update_many(pending, by_key, log=box.write)
                    box.update(state="complete")
                st.session_state["_upd_outcomes"] = outcomes
                if any(o.outcome == upd.OUT_UPDATED for o in outcomes):
                    st.cache_data.clear()          # serve the fresh data everywhere
                _run_update_check()                # re-probe so the table is honest
                st.rerun()
            if no:
                st.session_state.pop("_upd_confirm", None)
                st.rerun()
        for o in st.session_state.get("_upd_outcomes", []):
            lbl = U.get(f"o_{o.outcome}", o.outcome)
            country = by_key[o.key].country if o.key in by_key else o.key
            line = f"{lbl} — **{country}**" + (f" · {o.message}" if o.message else "")
            if o.outcome == "updated":
                st.success(line)
            elif o.outcome in ("failed", "validation_failed", "unavailable"):
                st.error(line)
            else:
                st.info(line)


def overview_section():
    O = _A()["overview"]
    users, uerr = _load_users()
    n_users = len(users) if users is not None else "—"
    links = _country_links()
    n_total, n_live, n_beta, n_plan = _catalog_counts()
    # Last PERSISTED full check (run from Data sources) — survives restarts.
    import updates as upd
    rec = upd.last_check()
    updates = len(rec["updates_available"]) if rec else 0
    # Pending beta-program requests (users ask from their profile dialog;
    # accepted/declined in Users → Beta requests).
    n_betareq = sum(1 for u in (users or []) if u.get("beta_requested"))

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    _kpi(c1, "users", _IC_USERS, "#0A63A6", "rgba(10,99,166,.10)", n_users, O["kpi_users"])
    _kpi(c2, "countries", _IC_GLOBE, "#0A63A6", "rgba(10,99,166,.10)", n_total, O["kpi_countries"])
    _kpi(c3, "live", _IC_ZAP, "#1B8A5A", "rgba(27,138,90,.12)", n_live, O["kpi_live"])
    _kpi(c4, "beta", _IC_ZAP, "#B26A00", "rgba(178,106,0,.13)", n_beta, O["kpi_beta"])
    _kpi(c5, "planned", _IC_GLOBE, "#5B6472", "rgba(91,100,114,.10)", n_plan, O["kpi_planned"])
    _kpi(c6, "betareq", _IC_USERS, "#B26A00", "rgba(178,106,0,.13)", n_betareq,
         O["kpi_beta_req"])
    _kpi(c7, "updates", _IC_ALERT, "#C0453A", "rgba(192,69,58,.12)", updates, O["kpi_updates"])
    with c7:
        st.caption(O["upd_checked"].format(t=rec["checked_at"]) if rec
                   else O["upd_never"])
    if uerr:
        st.caption(O["users_error"].format(err=uerr))

    st.write("")
    flag_css = ""
    with st.container(border=True, key="adcard_open"):
        st.markdown(f"#### {O['open_heading']}")
        st.caption(O["open_caption"])
        cols = st.columns(4)
        for i, (slug, name, iso, page) in enumerate(links):
            with cols[i % 4], st.container(key=f"adtile_{slug}"):
                st.page_link(page, label=name)
            flag_css += (f".st-key-adtile_{slug} [data-testid='stPageLink'] a"
                         f"{{background-image:url('{theme.flag_uri(iso)}');}}\n")

    st.write("")
    with st.container(border=True, key="adcard_legacy"):
        st.markdown(f"#### {O['legacy_heading']}")
        st.caption(O["legacy_caption"])
        cols = st.columns(4)
        for i, (slug, name, iso, page) in enumerate(_LEGACY_LINKS):
            with cols[i % 4], st.container(key=f"adtile_{slug}"):
                st.page_link(page, label=name)
            flag_css += (f".st-key-adtile_{slug} [data-testid='stPageLink'] a"
                         f"{{background-image:url('{theme.flag_uri(iso)}');}}\n")
    st.markdown(f"<style>{flag_css}</style>", unsafe_allow_html=True)


# ── Section: Data sources ────────────────────────────────────────────────────
# One consistent model on every country card: a single "Check for updates"
# button that probes the country's sub-sources and merges the results into the
# global update table — the table is the ONLY place updates run.
def _upd_results_map() -> dict:
    return {s.key: s for s in st.session_state.get("_upd_results", [])}


def _country_check(keys):
    """Probe this country's sub-sources and merge them into the global table
    results (keeping SOURCE_ORDER), so the table shows anything actionable."""
    import updates as upd
    merged = _upd_results_map()
    for k in keys:
        merged[k] = upd.check(k)
    st.session_state["_upd_results"] = [merged[k] for k in upd.SOURCE_ORDER
                                        if k in merged]


def _country_newer(keys) -> bool:
    res = _upd_results_map()
    return any(res[k].update_available for k in keys if k in res)


def _country_pill(D, keys) -> str:
    """Green/amber status pill from the latest check results (green until a
    check has found something)."""
    return (_pill("amber", D["pill_update"]) if _country_newer(keys)
            else _pill("green", D["pill_ok"]))


def _flt_skip(flt, keys) -> bool:
    """Whether the status filter hides this card."""
    if flt == "ok":
        return _country_newer(keys)
    if flt == "upd":
        return not _country_newer(keys)
    return False


def _country_update_counts():
    """(countries up to date, countries with an update) from the freshest check
    (session results, else the persisted log). (None, None) before any check."""
    import updates as upd
    sources = None
    if st.session_state.get("_upd_results"):
        sources = {s.key: bool(s.update_available)
                   for s in st.session_state["_upd_results"]}
    else:
        rec = upd.last_check()
        if rec:
            sources = {k: bool(v.get("update_available"))
                       for k, v in rec.get("sources", {}).items()}
    if not sources:
        return None, None
    by_country: dict = {}
    for k, has_upd in sources.items():
        c = k.split("_")[0]
        by_country[c] = by_country.get(c, False) or has_upd
    upd_n = sum(1 for v in by_country.values() if v)
    return len(by_country) - upd_n, upd_n


def _check_lines(D, keys):
    """Per-sub-source result lines under the card's Check button."""
    res = _upd_results_map()
    for k in keys:
        s = res.get(k)
        if s is None:
            continue
        if s.error:
            st.error(D["chk_err"].format(source=s.source, err=s.error))
        elif s.update_available:
            note = f" {s.note}" if s.note else ""
            st.warning(D["chk_upd"].format(source=s.source, current=s.current,
                                           latest=s.latest) + note)
        elif s.update_available is None and s.note:
            st.info(f"{s.source} — {s.note}")   # e.g. BLS blocks this server
        else:
            line = D["chk_ok"].format(source=s.source, current=s.current)
            st.caption(line + (f" · {s.note}" if s.note else ""))


def _check_button(D, iso, keys):
    """The standard card action: 🔍 Check for updates + result lines."""
    with _btnrow():
        chk = st.button(D["btn_check"], key=f"{iso}_check")
    if chk:
        with st.spinner("…"):
            _country_check(keys)
        st.rerun()
    _check_lines(D, keys)


_US_KEYS = ["us_data"]


def _us_card(query, D, flt="all"):
    from countries.us import build as usbuild
    T = D["us"]
    if not _match(query, T["name"], "us", T["source"], T["type"], "soc") \
            or _flt_skip(flt, _US_KEYS):
        return
    info = usbuild.bundled_info()
    c = info.get("counts", {})
    with st.container(border=True, key="adcard_us"):
        html = _hdr("us", T["name"], T["source"], T["type"],
                    _country_pill(D, _US_KEYS))
        # Standard stat row (same headings/order on every card): year ·
        # occupations · built · size — plus the US-only Scopes column.
        html += _stats([(D["s_year"], f"May {info.get('year', '—')}"),
                        (D["s_occ"], _n(c.get("occupations", "—"))),
                        (D["s_scopes"], _n(c.get("scopes", "—"))),
                        (D["s_built"], info.get("built_at", "—")),
                        (D["s_size"], _fmt_bytes(info.get("size")))])
        html += f'<div class="ad-cap">{T["desc"]}</div>'
        st.markdown(html, unsafe_allow_html=True)
        _check_button(D, "us", _US_KEYS)


_UK_KEYS = ["uk_data"]


def _uk_card(query, D, flt="all"):
    from countries.uk import build as ukbuild
    from countries.uk.provider import _leaves as _uk_leaves
    T = D["uk"]
    if not _match(query, T["name"], "uk", "gb", T["source"], T["type"], "ashe", "soc") \
            or _flt_skip(flt, _UK_KEYS):
        return
    info = ukbuild.bundled_info()
    yrs = info.get("years") or []
    span = f"{min(yrs)}–{max(yrs)}" if yrs else str(info.get("year", "—"))
    try:
        n = len(_uk_leaves())
    except Exception:
        n = None
    with st.container(border=True, key="adcard_gb"):
        st.markdown(
            _hdr("gb", T["name"], T["source"], T["type"], _country_pill(D, _UK_KEYS))
            + _stats([(D["s_year"], span),
                      (D["s_occ"], _n(n) if n else "—"),
                      (D["s_built"], info.get("built_at", "—")),
                      (D["s_size"], _fmt_bytes(info.get("size")))])
            + f'<div class="ad-cap">{T["desc"]}</div>',
            unsafe_allow_html=True)
        _check_button(D, "gb", _UK_KEYS)


_DE_KEYS = ["germany_data"]


def _germany_card(query, D, flt="all"):
    from countries.germany import build as debuild
    from countries.germany.provider import _leaves as _de_leaves
    T = D["germany"]
    if not _match(query, T["name"], "germany", "de", T["source"], T["type"], "kldb") \
            or _flt_skip(flt, _DE_KEYS):
        return
    info = debuild.bundled_info()
    try:
        n = len(_de_leaves())
    except Exception:
        n = None
    with st.container(border=True, key="adcard_de"):
        st.markdown(
            _hdr("de", T["name"], T["source"], T["type"], _country_pill(D, _DE_KEYS))
            + _stats([(D["s_year"], info.get("year", "—")),
                      (D["s_occ"], _n(n) if n else "—"),
                      (D["s_built"], info.get("built_at", "—")),
                      (D["s_size"], _fmt_bytes(info.get("size")))])
            + f'<div class="ad-cap">{T["desc"]}</div>',
            unsafe_allow_html=True)
        _check_button(D, "de", _DE_KEYS)


_NO_KEYS = ["norway_data", "norway_labels"]


def _norway_card(query, D, flt="all"):
    T = D["norway"]
    if not _match(query, T["name"], T["source"], "styrk", T["type"]) \
            or _flt_skip(flt, _NO_KEYS):
        return
    from countries.norway.build import latest_year as _no_year
    styrk_meta = _file_meta("styrk_labels.json")
    styrk = styrk_meta.get("data") or {}
    codes = (styrk.get("codes") or {}).get("EN", {})
    leaves = sum(1 for c in codes if len(c) == 4)
    with st.container(border=True, key="adcard_no"):
        st.markdown(
            _hdr("no", T["name"], T["source"], T["type"], _country_pill(D, _NO_KEYS))
            + _stats([(D["s_year"], _no_year()),
                      (D["s_occ"], _n(leaves) if leaves else "—"),
                      (D["s_built"], styrk.get("built_at", "—")),
                      (D["s_size"], _fmt_bytes(styrk_meta.get("size")))])
            + f'<div class="ad-cap">{T["desc"]}</div>',
            unsafe_allow_html=True)
        _check_button(D, "no", _NO_KEYS)


def _labels_card(query, D, flt, *, iso, keys, tkey, file, year_fn, kw):
    """Generic 'live API + bundled ISCO labels' card (Norway/Denmark/Iceland/
    Finland share this shape): one Check button, uniform stat row."""
    T = D[tkey]
    if not _match(query, T["name"], T["source"], *kw, T["type"]) \
            or _flt_skip(flt, keys):
        return
    meta = _file_meta(file)
    data = meta.get("data") or {}
    codes = (data.get("codes") or {}).get("EN", {})
    leaves = sum(1 for c in codes if len(c) == 4)
    with st.container(border=True, key=f"adcard_{iso}"):
        st.markdown(
            _hdr(iso, T["name"], T["source"], T["type"], _country_pill(D, keys))
            + _stats([(D["s_year"], year_fn()),
                      (D["s_occ"], _n(leaves) if leaves else "—"),
                      (D["s_built"], data.get("built_at", "—")),
                      (D["s_size"], _fmt_bytes(meta.get("size")))])
            + f'<div class="ad-cap">{T["desc"]}</div>',
            unsafe_allow_html=True)
        _check_button(D, iso, keys)


_DK_KEYS = ["denmark_data", "denmark_labels"]


def _denmark_card(query, D, flt="all"):
    from countries.denmark.build import latest_year as yr
    _labels_card(query, D, flt, iso="dk", keys=_DK_KEYS, tkey="denmark",
                 file="disco_labels.json", year_fn=yr, kw=("disco",))


_IS_KEYS = ["iceland_data", "iceland_labels"]


def _iceland_card(query, D, flt="all"):
    from countries.iceland.build import latest_year as yr
    _labels_card(query, D, flt, iso="is", keys=_IS_KEYS, tkey="iceland",
                 file="iceland_labels.json", year_fn=yr, kw=("isco", "hagstofa"))


_FI_KEYS = ["finland_data", "finland_labels"]


def _finland_card(query, D, flt="all"):
    from countries.finland.build import latest_year as yr
    _labels_card(query, D, flt, iso="fi", keys=_FI_KEYS, tkey="finland",
                 file="finland_labels.json", year_fn=yr, kw=("isco", "statfin"))


_EE_KEYS = ["estonia_data", "estonia_labels"]


def _estonia_card(query, D, flt="all"):
    from countries.estonia.build import latest_year as yr
    _labels_card(query, D, flt, iso="ee", keys=_EE_KEYS, tkey="estonia",
                 file="estonia_labels.json", year_fn=yr, kw=("isco", "stat.ee"))


_NL_KEYS = ["netherlands_data", "netherlands_labels"]


def _netherlands_card(query, D, flt="all"):
    from countries.netherlands.build import latest_year as yr
    _labels_card(query, D, flt, iso="nl", keys=_NL_KEYS, tkey="netherlands",
                 file="netherlands_labels.json", year_fn=yr, kw=("brc", "cbs"))


_SE_KEYS = ["sweden_data", "sweden_labels"]


def _sweden_card(query, D, flt="all"):
    T = D["sweden"]
    if not _match(query, T["name"], T["source"], "ssyk", T["type"]) \
            or _flt_skip(flt, _SE_KEYS):
        return
    occ = (_file_meta("occupations_cache.json").get("data") or {})
    ssyk_meta = _file_meta("ssyk_descriptions.json")
    appset = (_file_meta("app_settings.json").get("data") or {})
    n_occ = len(occ.get("EN", {}) or {})
    with st.container(border=True, key="adcard_se"):
        st.markdown(
            _hdr("se", T["name"], T["source"], T["type"], _country_pill(D, _SE_KEYS))
            + _stats([(D["s_year"], appset.get("latest_data_year", 2025)),
                      (D["s_occ"], _n(n_occ) if n_occ else "—"),
                      (D["s_built"], (occ.get("cached_at") or "—")[:10]),
                      (D["s_size"], _fmt_bytes(ssyk_meta.get("size")))])
            + f'<div class="ad-cap">{T["desc"]}</div>'
            + _extras_html(T),
            unsafe_allow_html=True)
        _check_button(D, "se", _SE_KEYS)

        # ── Country-specific admin (beyond the standard check/update) ─────────
        st.markdown(f'<div class="ad-lbl" style="margin-top:12px;">'
                    f'{D["specific_heading"]}</div>', unsafe_allow_html=True)
        with _btnrow():
            if st.button(T["btn_wp"], key="se_wp_open"):
                st.session_state["_show_wp_editor"] = True
                st.rerun()


_FR_KEYS = ["france_api", "france_micro"]


def _france_card(query, D, flt="all"):
    T = D["france"]
    if not _match(query, T["name"], T["source"], "melodi", "microdata", "pcs",
                  T["type"]) or _flt_skip(flt, _FR_KEYS):
        return
    lbl = (_file_meta("pcs_labels.json").get("data") or {})
    micro_meta = _file_meta("pcs_microdata_percentiles.json")
    micro = micro_meta.get("data") or {}
    micro_year = micro.get("year", "—")
    n_occ = len(micro.get("occupations", {}) or {})
    with st.container(border=True, key="adcard_fr"):
        html = _hdr("fr", T["name"], T["source"], T["type"],
                    _country_pill(D, _FR_KEYS))
        html += _stats([(D["s_year"], micro_year),
                        (D["s_occ"], _n(n_occ) if n_occ else "—"),
                        (D["s_built"], micro.get("built_at")
                         or lbl.get("built_at", "—")),
                        (D["s_size"], _fmt_bytes(micro_meta.get("size")))])
        html += f'<div class="ad-cap">{T["desc"]}</div>'
        html += _extras_html(T)
        st.markdown(html, unsafe_allow_html=True)
        _check_button(D, "fr", _FR_KEYS)

        # ── Country-specific admin: import a new FD_SALAAN microdata vintage.
        # INSEE distributes it per publication page (no stable URL), so the
        # admin pastes the parquet link (downloaded server-side) or uploads the
        # file; the shipped build validates before the atomic swap. ───────────
        from countries.fr2 import build as frbuild
        st.markdown(f'<div class="ad-lbl" style="margin-top:12px;">'
                    f'{D["specific_heading"]}</div>', unsafe_allow_html=True)
        st.caption(T["imp_caption"])
        url = st.text_input(T["imp_url_label"], key="fr_micro_url",
                            placeholder=T["imp_url_ph"])
        up = st.file_uploader(T["imp_file_label"], type=["parquet"],
                              key="fr_micro_file")
        _src = up if up is not None else (url.strip() or None)
        _guess = frbuild.infer_year(getattr(up, "name", "") or url or "")
        try:
            _my = int(str(micro_year)[:4])
        except (TypeError, ValueError):
            _my = 0
        ycol, bcol = st.columns([1, 2.4], vertical_alignment="bottom")
        yr_in = ycol.number_input(T["imp_year_label"], min_value=2001,
                                  max_value=2099,
                                  value=int(_guess or (_my + 1 if _my else 2024)),
                                  step=1, key="fr_micro_year")
        if bcol.button(T["imp_btn"], key="fr_micro_go", type="primary"):
            if _src is None:
                st.session_state["_fr_micro_nosrc"] = True
            else:
                st.session_state["_fr_micro_confirm"] = True
                st.session_state.pop("_fr_micro_nosrc", None)
        if st.session_state.pop("_fr_micro_nosrc", False):
            st.info(T["imp_need_src"])
        if st.session_state.get("_fr_micro_confirm"):
            st.warning(T["imp_confirm"].format(cur=micro_year, new=int(yr_in)))
            with _btnrow():
                yes = st.button(T["btn_confirm"], type="primary", key="fr_micro_yes")
                no = st.button(T["btn_cancel"], key="fr_micro_no")
            if yes:
                st.session_state.pop("_fr_micro_confirm", None)
                with st.status(T["imp_running"], expanded=True) as box:
                    try:
                        res = frbuild.build(_src, year=int(yr_in), log=box.write)
                        st.cache_data.clear()      # serve the new estimates now
                        st.session_state["_fr_micro_result"] = res
                        # refresh the France rows so pill + table reflect the import
                        _country_check(_FR_KEYS)
                        box.update(label=f"{res['year']} ✓", state="complete")
                    except Exception as e:  # noqa: BLE001
                        box.update(label="✗", state="error")
                        st.session_state["_fr_micro_err"] = str(e)
                st.rerun()
            if no:
                st.session_state.pop("_fr_micro_confirm", None)
                st.rerun()
        if st.session_state.get("_fr_micro_err"):
            st.error(T["imp_failed"].format(err=st.session_state.pop("_fr_micro_err")))
        res = st.session_state.get("_fr_micro_result")
        if res:
            st.success(T["imp_done"].format(year=res["year"],
                                            occ=_n(res["occupations"]),
                                            censored=res["censored"]))


def _caches_card(query, D):
    if not _match(query, D["caches_title"], "clear", D["caches_type"]):
        return
    with st.container(border=True, key="adcard_caches"):
        lc, rc = st.columns([3, 1.2], vertical_alignment="center")
        lc.markdown(
            f'<div class="ad-hdL"><span><span class="ad-name">{D["caches_title"]}</span>'
            f'<span class="ad-type">· {D["caches_type"]}</span></span></div>'
            f'<div class="ad-cap" style="margin-top:8px;">{D["caches_caption"]}</div>',
            unsafe_allow_html=True)
        if rc.button(D["clear_btn"], key="clear_caches"):
            st.cache_data.clear()
            st.success(D["cleared"])


def data_section():
    st.markdown(CSS, unsafe_allow_html=True)
    D = _A()["data"]

    # Country-specific editor opened from a source card (e.g. Sweden's
    # Work-permit rules) takes over the section until Back is pressed.
    if st.session_state.get("_show_wp_editor"):
        if st.button(_A()["wp"]["back"], key="wp_back"):
            st.session_state.pop("_show_wp_editor", None)
            st.rerun()
        wp_section()
        return

    tl, tr = st.columns([2.4, 1], vertical_alignment="center")
    tl.caption(D["caption"])
    tr.markdown('<div style="text-align:right;font-size:12px;color:#7A828F;">'
                f'<span class="ad-pill ad-green" style="padding:2px 8px;">{D["pill_ok"]}</span>&nbsp;'
                f'<span class="ad-pill ad-amber" style="padding:2px 8px;">{D["pill_update"]}</span></div>',
                unsafe_allow_html=True)

    # ── Global update check (the shared service) + the results table ─────────
    U = _A()["updates"]
    if st.button(U["btn_check"], key="adm_check_updates", help=U["check_help"]):
        with st.spinner(U["checking"]):
            _run_update_check()
        st.session_state.pop("_upd_outcomes", None)
        st.rerun()
    _updates_card()
    st.write("")

    # ── Status KPIs (like the Overview tiles): countries up to date vs with an
    # update — from the freshest check (session, else the persisted log). ─────
    ok_n, upd_n = _country_update_counts()
    kc = st.columns(6)
    _kpi(kc[0], "ds_ok", _IC_ZAP, "#1B8A5A", "rgba(27,138,90,.12)",
         ok_n if ok_n is not None else "—", D["kpi_ok"])
    _kpi(kc[1], "ds_upd", _IC_ALERT, "#B26A00", "rgba(178,106,0,.13)",
         upd_n if upd_n is not None else "—", D["kpi_upd"])
    st.write("")

    # ── Search + status filter ────────────────────────────────────────────────
    sc1, sc2 = st.columns([2, 1.1], vertical_alignment="center")
    query = sc1.text_input("Search data sources", key="ds_search",
                           placeholder=D["search_ph"], label_visibility="collapsed")
    _flbl = {"all": D["flt_all"], "ok": D["flt_ok"], "upd": D["flt_upd"]}
    flt = sc2.segmented_control("Status filter", list(_flbl),
                                format_func=lambda k: _flbl[k], default="all",
                                key="ds_filter", label_visibility="collapsed") or "all"

    # Cards in the same order as the update table (SOURCE_ORDER).
    _sweden_card(query, D, flt)
    _france_card(query, D, flt)
    _norway_card(query, D, flt)
    _us_card(query, D, flt)
    _denmark_card(query, D, flt)
    _iceland_card(query, D, flt)
    _finland_card(query, D, flt)
    _estonia_card(query, D, flt)
    _netherlands_card(query, D, flt)
    _uk_card(query, D, flt)
    _germany_card(query, D, flt)
    if flt == "all":
        _caches_card(query, D)

    # Live search-as-you-type (same behaviour as the landing catalog): a
    # same-origin iframe script prefix-matches the card's country name on every
    # keystroke — no Enter needed. The committed value still reruns server-side
    # (keyword matching, e.g. "melodi"/"oews").
    import streamlit.components.v1 as _components
    _components.html("""
    <script>
    (function () {
      const doc = window.parent.document;
      let last = null;
      function apply() {
        const inp = doc.querySelector('.st-key-ds_search input');
        if (!inp) return;
        if (!inp.dataset.liveBound) { inp.dataset.liveBound = '1';
          inp.addEventListener('input', apply); }
        const q = (inp.value || '').trim().toLowerCase();
        const cards = [...doc.querySelectorAll('[class*="st-key-adcard_"]')]
          .filter(c => c.querySelector('.ad-name'));
        if (q === last && cards.every(c => c.dataset.liveSeen)) return;
        last = q;
        cards.forEach(c => {
          c.dataset.liveSeen = '1';
          const nm = c.querySelector('.ad-name').textContent.trim().toLowerCase();
          c.style.display = (!q || nm.startsWith(q)) ? '' : 'none';
        });
      }
      setInterval(apply, 700);
      apply();
    })();
    </script>
    """, height=0)
    if query.strip() and not any(_match(query, *t) for t in (
            (D["us"]["name"], "us", D["us"]["source"], D["us"]["type"], "soc"),
            (D["norway"]["name"], D["norway"]["source"], "styrk", D["norway"]["type"]),
            (D["sweden"]["name"], D["sweden"]["source"], "ssyk", D["sweden"]["type"]),
            (D["france"]["name"], D["france"]["source"], "melodi", "microdata", "pcs",
             D["france"]["type"]),
            (D["caches_title"], "clear", D["caches_type"]))):
        st.caption(D["no_match"].format(q=query))


# ── Section: Users ───────────────────────────────────────────────────────────
def _initials(name, email):
    base = (name or (email.split("@")[0] if email else "?")).strip()
    parts = base.replace(".", " ").replace("_", " ").split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    b = parts[0] if parts else "?"
    if len(b) > 1 and b[-1].isdigit():          # "kristoffer2" → "K2"
        return (b[0] + b[-1]).upper()
    return b[:2].upper()


def _role_badge_map(U):
    return {"master": (U["role_master"], "#8A6A2A", "rgba(184,134,59,.16)"),
            "admin": (U["role_admin"], "#0A63A6", "rgba(10,99,166,.10)"),
            "beta": (U.get("role_beta", "Beta"), "#166534", "rgba(22,163,74,.12)"),
            "standard": (U["role_standard"], "#5B6472", "#EEF0F3")}


def _delete_dialog():
    """Confirmation before deleting a user: their profile card + an explicit
    Delete / Cancel choice — no more one-click deletions."""
    U = _A()["users"]
    u = st.session_state.get("_del_user") or {}
    txt, fg, bg = _role_badge_map(U).get(u.get("role"),
                                         (u.get("role", "—"), "#5B6472", "#EEF0F3"))
    country_opts = _country_options()
    acc = (U["all_countries"] if u.get("role") in _ADMIN_ROLES
           else ", ".join(country_opts.get(s, s) for s in u.get("countries", []))
           or "—")
    av = "#B8863B" if u.get("role") in _ADMIN_ROLES else "#0A63A6"
    st.markdown(
        f'<div style="border:1px solid #E7E9ED;border-radius:14px;padding:16px 18px;'
        f'display:flex;align-items:center;gap:14px;margin-bottom:6px;">'
        f'<div class="ad-av" style="background:{av};width:44px;height:44px;'
        f'font-size:15px;">{_initials(u.get("name"), u.get("email", "?"))}</div>'
        f'<div style="min-width:0;">'
        f'<div class="ad-uname" style="font-size:15px;">{u.get("name") or U["no_name"]}</div>'
        f'<div class="ad-email">{u.get("email", "—")}</div>'
        f'<div style="margin-top:6px;"><span class="ad-badge" '
        f'style="color:{fg};background:{bg};">{txt}</span>'
        f'&nbsp;<span class="ad-access">🌐 {acc}</span></div>'
        f'</div></div>', unsafe_allow_html=True)
    st.warning(U["del_warning"])
    c1, c2 = st.columns(2)
    if c1.button(U["del_confirm"], type="primary", use_container_width=True,
                 key="_del_yes"):
        try:
            auth.delete_user(u["id"])
            _invalidate_users()
            st.session_state["_del_msg"] = U["del_done"].format(email=u.get("email"))
        except Exception as e:  # noqa: BLE001
            st.session_state["_del_msg_err"] = U["del_failed"].format(err=e)
        st.session_state.pop("_del_user", None)
        st.rerun()
    if c2.button(U["del_cancel"], use_container_width=True, key="_del_no"):
        st.session_state.pop("_del_user", None)
        st.rerun()


def users_section():
    st.markdown(CSS, unsafe_allow_html=True)
    U = _A()["users"]
    me = st.session_state.get("auth_user", {})
    country_opts = _country_options()
    cslugs = list(country_opts)
    cfmt = lambda s: country_opts.get(s, s)          # noqa: E731
    role_badges = _role_badge_map(U)

    users, _ = _load_users()
    pending = [u for u in (users or []) if u.get("beta_requested")]
    unverified = [u for u in (users or []) if not u.get("email_confirmed", True)]

    # ── Status KPIs (like the Overview tiles) ─────────────────────────────────
    kc = st.columns(6)
    _kpi(kc[0], "u_total", _IC_USERS, "#0A63A6", "rgba(10,99,166,.10)",
         len(users) if users is not None else "—", U["kpi_total"])
    _kpi(kc[1], "u_unver", _IC_ALERT, "#B26A00", "rgba(178,106,0,.13)",
         len(unverified), U["kpi_unverified"])
    _kpi(kc[2], "u_betareq", _IC_USERS, "#B26A00", "rgba(178,106,0,.13)",
         len(pending), U["kpi_betareq"])
    st.write("")

    # ── Beta requests card — pending asks from the profile dialog. Accept
    # switches the user to the beta role; either way the request is cleared
    # (the role stays editable any time via the ✏️ popover below). ──
    with st.container(border=True, key="adcard_betareq"):
        st.markdown(
            f'#### {U["br_heading"]} '
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:11px;'
            f'color:#98A0AC;font-weight:400;">&nbsp;&nbsp;{len(pending)}</span>',
            unsafe_allow_html=True)
        st.caption(U["br_caption"])
        if st.session_state.get("_br_msg"):
            st.success(st.session_state.pop("_br_msg"))
        if not pending:
            st.caption(U["br_empty"])
        for u in pending:
            b_user, b_email, b_date, b_ok, b_no = st.columns(
                [2.6, 3, 1.7, 1.2, 1.2], vertical_alignment="center")
            b_user.markdown(
                f'<div class="ad-user"><div class="ad-av" style="background:#0A63A6;">'
                f'{_initials(u.get("name"), u["email"])}</div>'
                f'<span class="ad-uname">{u.get("name") or U["no_name"]}</span></div>',
                unsafe_allow_html=True)
            b_email.markdown(f'<span class="ad-email">{u["email"]}</span>',
                             unsafe_allow_html=True)
            b_date.markdown(f'<span class="ad-access">'
                            f'{U["br_requested"].format(date=u["beta_requested"])}</span>',
                            unsafe_allow_html=True)
            ok = b_ok.button(U["br_accept"], key=f"br_ok_{u['id']}", type="primary",
                             use_container_width=True)
            no = b_no.button(U["br_decline"], key=f"br_no_{u['id']}",
                             use_container_width=True)
            if ok or no:
                try:
                    auth.resolve_beta_request(u["id"], accept=ok)
                    _invalidate_users()
                    st.session_state["_br_msg"] = (
                        U["br_accepted"] if ok else U["br_declined"]
                    ).format(email=u["email"])
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(U["br_failed"].format(err=e))

    st.write("")

    # ── Create user card ──
    with st.container(border=True, key="adcard_create"):
        st.markdown(f"#### {U['create_heading']}")
        a, b = st.columns(2)
        a.markdown(f'<div class="ad-flbl">{U["f_name"]}</div>', unsafe_allow_html=True)
        nn = a.text_input(U["f_name"], key="nu_name", placeholder=U["ph_name"],
                          label_visibility="collapsed")
        b.markdown(f'<div class="ad-flbl">{U["f_email"]}</div>', unsafe_allow_html=True)
        ne = b.text_input(U["f_email"], key="nu_email", placeholder=U["ph_email"],
                          label_visibility="collapsed")
        c, d = st.columns(2)
        c.markdown(f'<div class="ad-flbl">{U["f_password"]}</div>', unsafe_allow_html=True)
        npw = c.text_input(U["f_password"], type="password", key="nu_pw",
                           label_visibility="collapsed")
        d.markdown(f'<div class="ad-flbl">{U["f_role"]}</div>', unsafe_allow_html=True)
        nr = d.selectbox(U["f_role"], auth.ROLES, key="nu_role", label_visibility="collapsed")
        st.markdown(f'<div class="ad-flbl">{U["f_access"]}</div>', unsafe_allow_html=True)
        nc = st.multiselect(U["f_access"], cslugs, default=list(auth.DEFAULT_COUNTRIES),
                            format_func=cfmt, key="nu_countries", label_visibility="collapsed")
        if st.button(U["btn_create"], type="primary", key="nu_create"):
            if not nn.strip() or not ne.strip() or not npw:
                st.error(U["missing"])
            else:
                try:
                    auth.create_user(ne.strip(), npw, nr, countries=nc, name=nn.strip())
                    _invalidate_users()
                    st.success(U["created"].format(email=ne))
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(U["create_failed"].format(err=e))

    st.write("")

    # ── Existing users card ──
    users, err = _load_users()
    with st.container(border=True, key="adcard_users"):
        rc = Counter((u["role"] for u in users)) if users else Counter()
        h1, h2, h3 = st.columns([2.6, 2, 1], vertical_alignment="center")
        h1.markdown(
            f'#### {U["existing_heading"]} '
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:11px;'
            f'color:#98A0AC;font-weight:400;">&nbsp;&nbsp;'
            + U["counts"].format(master=rc.get("master", 0), admin=rc.get("admin", 0),
                                 standard=rc.get("standard", 0), total=sum(rc.values()))
            + '</span>', unsafe_allow_html=True)
        uq = h2.text_input("Search users", key="users_search", placeholder=U["search_ph"],
                           label_visibility="collapsed")
        if h3.button(U["btn_reload"], key="users_reload", use_container_width=True):
            _load_users(force=True)
            st.rerun()
        if err:
            st.error(U["load_error"].format(err=err))
            st.caption(U["retry_hint"])
            return
        if st.session_state.get("_del_msg"):
            st.success(st.session_state.pop("_del_msg"))
        if st.session_state.get("_del_msg_err"):
            st.error(st.session_state.pop("_del_msg_err"))

        shown = [u for u in (users or []) if _match(
            uq, u.get("name"), u["email"], u["role"],
            *(cfmt(s) for s in u.get("countries", [])))]
        if uq.strip() and not shown:
            st.caption(U["no_match"].format(q=uq))

        _W = [2.6, 3, 1.7, 2.2, 1.2]
        head = st.columns(_W)
        for col, cap in zip(head, (U["col_user"], U["col_email"], U["col_role"],
                                   U["col_access"], U["col_actions"])):
            col.markdown(f'<div class="ad-th">{cap}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:1px;background:#EEF0F3;margin:6px 0 2px;"></div>',
                    unsafe_allow_html=True)

        for u in shown:
            c_user, c_email, c_role, c_acc, c_act = st.columns(_W, vertical_alignment="center")
            av = "#B8863B" if u["role"] in _ADMIN_ROLES else "#0A63A6"
            nm = u.get("name") or U["no_name"]
            c_user.markdown(
                f'<div class="ad-user"><div class="ad-av" style="background:{av};">'
                f'{_initials(u.get("name"), u["email"])}</div>'
                f'<span class="ad-uname">{nm}</span></div>', unsafe_allow_html=True)
            c_email.markdown(f'<span class="ad-email">{u["email"]}</span>', unsafe_allow_html=True)
            txt, fg, bg = role_badges.get(u["role"], (u["role"], "#5B6472", "#EEF0F3"))
            you = U["you"] if u["id"] == me.get("id") else ""
            # Amber marker while a beta request is pending (handled in the card above).
            req = ('' if not u.get("beta_requested") else
                   f' <span class="ad-badge" style="color:#B26A00;'
                   f'background:rgba(178,106,0,.14);">{U["badge_requested"]}</span>')
            # Grey marker for accounts that never completed email confirmation.
            unv = ('' if u.get("email_confirmed", True) else
                   f' <span class="ad-badge" style="color:#8A919D;'
                   f'background:#F1F3F6;">{U["badge_unverified"]}</span>')
            c_role.markdown(f'<span class="ad-badge" style="color:{fg};background:{bg};">'
                            f'{txt}</span>{req}{unv}{you}', unsafe_allow_html=True)
            acc = (U["all_countries"] if u["role"] in _ADMIN_ROLES
                   else ", ".join(cfmt(s) for s in u.get("countries", [])) or "—")
            c_acc.markdown(f'<span class="ad-access">🌐 {acc}</span>', unsafe_allow_html=True)

            e_col, d_col = c_act.columns(2)
            with e_col.popover("✏️", help=U["edit_help"]):
                if u["role"] == "master":
                    st.caption(U["master_fixed"])
                elif u["id"] == me.get("id"):
                    st.caption(U["you_fixed"])
                else:
                    nrole = st.selectbox(U["f_role"], auth.ROLES,
                                         index=auth.ROLES.index(u["role"]) if u["role"] in auth.ROLES else 0,
                                         key=f"role_{u['id']}")
                    if nrole != u["role"] and st.button(U["save_role"], key=f"rolebtn_{u['id']}"):
                        try:
                            auth.set_role(u["id"], nrole)
                            _invalidate_users()
                            st.rerun()
                        except Exception as e:  # noqa: BLE001
                            st.error(str(e))
                # Country grants only matter for standard users — admins/master
                # open every country regardless, so hide the picker for them.
                if u["role"] in _ADMIN_ROLES:
                    st.caption(U["admin_access"])
                else:
                    cur = [s for s in u.get("countries", []) if s in cslugs]
                    sel = st.multiselect(U["f_access"], cslugs, default=cur, format_func=cfmt,
                                         key=f"cty_{u['id']}")
                    if st.button(U["save_access"], key=f"ctybtn_{u['id']}"):
                        try:
                            auth.set_countries(u["id"], sel)
                            _invalidate_users()
                            st.success(U["saved"])
                            st.rerun()
                        except Exception as e:  # noqa: BLE001
                            st.error(str(e))
                pwl = U["pw_yours"] if u["id"] == me.get("id") else U["pw_new"]
                newpw = st.text_input(pwl, type="password", key=f"pw_{u['id']}")
                if st.button(U["btn_pw"], key=f"pwbtn_{u['id']}"):
                    try:
                        auth.set_password(u["id"], newpw)
                        st.success(U["pw_updated"])
                    except Exception as e:  # noqa: BLE001
                        st.error(str(e))
            if u["role"] != "master" and u["id"] != me.get("id"):
                if d_col.button("🗑", key=f"del_{u['id']}", help=U["del_help"]):
                    # No one-click deletion: open the confirmation dialog with
                    # the user's profile card (see _delete_dialog).
                    st.session_state["_del_user"] = u
                    st.rerun()

    if st.session_state.get("_del_user"):
        st.dialog(U["del_title"])(_delete_dialog)()


# ── Section: Beta feedback ───────────────────────────────────────────────────
_FB_STATUS_COLORS = {"New": ("#0A63A6", "rgba(10,99,166,.10)"),
                     "Reviewing": ("#B26A00", "rgba(178,106,0,.14)"),
                     "Planned": ("#6B4FA0", "rgba(107,79,160,.12)"),
                     "Resolved": ("#1B8A5A", "rgba(27,138,90,.12)"),
                     "Closed": ("#8A919D", "#F1F3F6")}
_IC_CHAT = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round" width="18" height="18">'
            '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
            '</svg>')
_FB_IMPACT_COLORS = {"Minor": ("#5B6472", "#EEF0F3"),
                     "Significant": ("#B26A00", "rgba(178,106,0,.14)"),
                     "Blocking": ("#C0453A", "rgba(192,69,58,.12)")}


def feedback_section():
    """Beta-feedback management: filterable table (newest first) + per-item
    detail with status + PRIVATE admin notes (never shown to users)."""
    st.markdown(CSS, unsafe_allow_html=True)
    import feedback as fb
    FB = _A()["feedback"]
    rows, err = fb.list_feedback()
    if err:
        st.error(err)
        return
    # ── Status KPIs (like the other admin sections): total + one per status ──
    kc = st.columns(6)
    _kpi(kc[0], "fb_total", _IC_CHAT, "#0A63A6", "rgba(10,99,166,.10)",
         len(rows), FB["kpi_total"])
    for i, s in enumerate(fb.STATUSES, start=1):
        fg, bg = _FB_STATUS_COLORS[s]
        _kpi(kc[i], f"fb_{s.lower()}", _IC_CHAT, fg, bg,
             sum(1 for r in rows if r.get("status") == s), s)
    st.write("")

    open_n = sum(1 for r in rows if r.get("status") in ("New", "Reviewing"))
    st.caption(FB["caption"].format(total=len(rows), open=open_n))

    allv = FB["flt_all"]
    f1, f2, f3 = st.columns(3)
    fstat = f1.selectbox(FB["flt_status"], [allv] + fb.STATUSES, key="fb_f_status")
    ftype = f2.selectbox(FB["flt_type"], [allv] + fb.TYPES, key="fb_f_type")
    ctry_opts = sorted({r.get("country") or fb.GENERAL for r in rows})
    fctry = f3.selectbox(FB["flt_country"], [allv] + ctry_opts, key="fb_f_country")
    shown = [r for r in rows
             if (fstat == allv or r.get("status") == fstat)
             and (ftype == allv or r.get("feedback_type") == ftype)
             and (fctry == allv or (r.get("country") or fb.GENERAL) == fctry)]

    st.write("")
    with st.container(border=True, key="adcard_feedback"):
        st.markdown(f"#### {FB['heading']}")
        if st.session_state.get("_fb_admin_msg"):
            st.success(st.session_state.pop("_fb_admin_msg"))
        if not shown:
            st.caption(FB["empty"])
            return
        _W = [1.5, 1.4, 1.3, 3.2, 1.2, 2.2, 1.2]
        head = st.columns(_W)
        for col, cap in zip(head, (FB["col_date"], FB["col_type"], FB["col_country"],
                                   FB["col_title"], FB["col_impact"],
                                   FB["col_user"], FB["col_status"])):
            col.markdown(f'<div class="ad-th">{cap}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:1px;background:#EEF0F3;margin:6px 0 2px;"></div>',
                    unsafe_allow_html=True)

        for r in shown:                         # already newest-first
            fid = r["id"]
            c1, c2, c3, c4, c5, c6, c7 = st.columns(_W, vertical_alignment="center")
            c1.markdown(f'<span class="ad-access">'
                        f'{str(r.get("created_at", ""))[:16].replace("T", " ")}</span>',
                        unsafe_allow_html=True)
            c2.markdown(f'<span class="ad-access">{r.get("feedback_type", "—")}</span>',
                        unsafe_allow_html=True)
            c3.markdown(f'<span class="ad-access">{r.get("country") or fb.GENERAL}</span>',
                        unsafe_allow_html=True)
            c4.markdown(f'<span class="ad-uname">{r.get("title", "")}</span>',
                        unsafe_allow_html=True)
            ifg, ibg = _FB_IMPACT_COLORS.get(r.get("impact"), ("#5B6472", "#EEF0F3"))
            c5.markdown(f'<span class="ad-badge" style="color:{ifg};background:{ibg};">'
                        f'{r.get("impact", "—")}</span>', unsafe_allow_html=True)
            c6.markdown(f'<span class="ad-email">{r.get("user_email") or "—"}</span>',
                        unsafe_allow_html=True)
            sfg, sbg = _FB_STATUS_COLORS.get(r.get("status"), ("#5B6472", "#EEF0F3"))
            c7.markdown(f'<span class="ad-badge" style="color:{sfg};background:{sbg};">'
                        f'{r.get("status", "—")}</span>', unsafe_allow_html=True)

            with st.expander(FB["open_label"]):
                st.text(r.get("description", ""))
                meta = [f'{FB["m_page"]}: {r.get("page") or "—"}',
                        f'{FB["m_contact"]}: '
                        + (FB["yes"] if r.get("permission_to_contact") else FB["no"])]
                if r.get("app_version"):
                    meta.append(f'{FB["m_version"]}: {r["app_version"]}')
                st.caption(" · ".join(meta))
                e1, e2 = st.columns([1, 2.4])
                nstat = e1.selectbox(
                    FB["f_status"], fb.STATUSES,
                    index=fb.STATUSES.index(r["status"])
                    if r.get("status") in fb.STATUSES else 0,
                    key=f"fbs_{fid}")
                nnotes = e2.text_area(FB["f_notes"], value=r.get("admin_notes") or "",
                                      height=80, key=f"fbn_{fid}",
                                      placeholder=FB["notes_ph"])
                if st.button(FB["btn_save"], key=f"fbsave_{fid}", type="primary"):
                    uerr = fb.update_feedback(fid, status=nstat, admin_notes=nnotes)
                    if uerr:
                        st.error(uerr)
                    else:
                        st.session_state["_fb_admin_msg"] = FB["saved"]
                        st.rerun()


# ── Section: Work-permit rules (Sweden) ──────────────────────────────────────
def _wp_code_list(W, title, caption, state_key, names):
    """Interactive SSYK-code list: row per code (name + 🗑), plus an add box.
    Edits live in session_state; the form's Save rules button persists them."""
    st.markdown(f"**{title}**")
    st.caption(caption)
    codes = st.session_state[state_key]
    if codes:
        for code in sorted(codes):
            r1, r2, r3 = st.columns([2, 6, 1])
            r1.write(code)
            r2.write(names.get(code, "—"))
            if r3.button("🗑", key=f"{state_key}_del_{code}", help=W["remove_help"]):
                st.session_state[state_key] = [c for c in codes if c != code]
                st.rerun()
    else:
        st.caption(W["none"])
    a1, a2 = st.columns([5, 1])
    newc = a1.text_input(title, key=f"{state_key}_add_{len(codes)}",
                         placeholder=W["add_ph"], label_visibility="collapsed")
    if a2.button(W["btn_add"], key=f"{state_key}_addbtn"):
        nc = newc.strip()
        if nc and nc not in codes:
            st.session_state[state_key] = codes + [nc]
        st.rerun()


def wp_section():
    """Work-permit rules editor — migrated from the legacy Sweden page. Reads/
    writes the SAME wp_rules.json via countries/se2's workpermit module, so the
    framework Work-permit tab and this editor always agree."""
    W = _A()["wp"]
    import sweden_codes
    from countries.se2 import workpermit as wp
    rules = wp.load_rules()
    names = sweden_codes.occupation_names("EN")
    for sk, src in (("adm_wp_exempt", "exempt_ssyk"),
                    ("adm_wp_banned_full", "banned_full"),
                    ("adm_wp_banned_partial", "banned_partial")):
        if sk not in st.session_state:
            st.session_state[sk] = list(rules[src])

    with st.container(border=True, key="adcard_wp"):
        st.markdown(f"#### {W['heading']}")
        st.caption(W["caption"])
        with st.form("adm_wp_form"):
            c1, c2, c3 = st.columns(3)
            as_of = c1.text_input(W["f_asof"], rules["as_of"], help=W["h_asof"])
            median = c2.number_input(W["f_median"], value=int(rules["median"]),
                                     step=100, help=W["h_median"])
            bench = c3.number_input(W["f_bench"], value=int(rules["bench_year"]),
                                    step=1, help=W["h_bench"])
            c4, c5, c6 = st.columns(3)
            pg = c4.number_input(W["f_general"], value=float(rules["pct_general"]) * 100,
                                 step=1.0, help=W["h_general"])
            pt = c5.number_input(W["f_transition"],
                                 value=float(rules["pct_transition"]) * 100,
                                 step=1.0, help=W["h_transition"])
            pe = c6.number_input(W["f_exempt"], value=float(rules["pct_exempt"]) * 100,
                                 step=1.0, help=W["h_exempt"])
            c7, c8 = st.columns(2)
            blue = c7.number_input(W["f_blue"], value=int(rules["blue_card_floor"]),
                                   step=100, help=W["h_blue"])
            tend = c8.text_input(W["f_transition_end"], rules["transition_end"],
                                 help=W["h_transition_end"])
            saved = st.form_submit_button(W["btn_save"], type="primary")
        if saved:
            new = dict(rules)
            new.update({
                "as_of": as_of.strip(), "median": int(median), "bench_year": int(bench),
                "pct_general": round(pg / 100, 4), "pct_transition": round(pt / 100, 4),
                "pct_exempt": round(pe / 100, 4), "blue_card_floor": int(blue),
                "transition_end": tend.strip(),
                "exempt_ssyk": sorted(st.session_state["adm_wp_exempt"]),
                "banned_full": sorted(st.session_state["adm_wp_banned_full"]),
                "banned_partial": sorted(st.session_state["adm_wp_banned_partial"]),
            })
            try:
                wp.save_rules(new)
                for sk in ("adm_wp_exempt", "adm_wp_banned_full", "adm_wp_banned_partial"):
                    st.session_state.pop(sk, None)
                st.session_state["_adm_wp_saved"] = True
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(W["save_failed"].format(err=e))
        if st.session_state.pop("_adm_wp_saved", False):
            st.success(W["saved"])

    st.write("")
    with st.container(border=True, key="adcard_wp_lists"):
        st.markdown(f"#### {W['lists_heading']}")
        st.caption(W["lists_caption"])
        _wp_code_list(W, W["l_exempt_t"], W["l_exempt_c"], "adm_wp_exempt", names)
        st.divider()
        _wp_code_list(W, W["l_banned_full_t"], W["l_banned_full_c"],
                      "adm_wp_banned_full", names)
        st.divider()
        _wp_code_list(W, W["l_banned_partial_t"], W["l_banned_partial_c"],
                      "adm_wp_banned_partial", names)


# ── Orchestrator ─────────────────────────────────────────────────────────────
# (The Work-permit editor is not a top-level section — it's Sweden's
# country-specific action, opened from the Sweden data-source card.)
SECTIONS = {"overview": overview_section, "data": data_section,
            "users": users_section, "feedback": feedback_section}


def section_selector() -> str:
    """The Overview / Data sources / Users pill toggle (rendered in the header).
    Options are stable ids; the shown labels come from content/admin.toml."""
    labels = _A()["tabs"]
    sec = st.segmented_control("section", list(SECTIONS), default="overview",
                               key="_admin_section", label_visibility="collapsed",
                               format_func=lambda s: labels.get(s, s))
    return sec or "overview"


def render_body(section: str):
    st.markdown(CSS, unsafe_allow_html=True)
    SECTIONS.get(section, overview_section)()


def render():
    """Standalone entry (tabs + body) — kept for reuse; admin.py renders the header."""
    render_body(section_selector())
