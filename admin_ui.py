"""Shared, full-page Admin panel UI (rendered by admin.py).

Plain module — NO top-level Streamlit calls — so its section functions can be
reused elsewhere (e.g. Sweden's 'Manage users' dialog calls users_section()).
Access is gated to admin/master by admin.py before any of this renders.

Sections: Overview · Data sources · Users. The visual design (card tiles, status
pills, mono stat grids, compact button rows) follows the approved Admin-panel
mockup; the data/logic underneath is unchanged.
"""
from __future__ import annotations

import gzip
import json
import os
from collections import Counter

import streamlit as st

import auth
import theme

_ADMIN_ROLES = ("admin", "master")
_ROOT = os.path.dirname(os.path.abspath(__file__))   # repo root (admin_ui.py lives here)


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


def _norway_latest_year():
    try:
        from core import registry
        yr = getattr(registry.get("norway").capabilities, "year_range", None)
        return yr[1] if yr else None
    except Exception:
        return None


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
        with st.spinner("Loading users…"):
            try:
                st.session_state["_admin_users"] = (auth.list_users(), None)
            except Exception as e:  # noqa: BLE001
                st.session_state["_admin_users"] = (None, str(e))
    return st.session_state["_admin_users"]


def _invalidate_users():
    st.session_state.pop("_admin_users", None)


def _match(query: str, *texts) -> bool:
    q = (query or "").strip().lower()
    return (not q) or any(q in (t or "").lower() for t in texts)


def _pill(kind: str, text: str) -> str:
    return f'<span class="ad-pill ad-{kind}">{text}</span>'


def _stats(pairs) -> str:
    items = "".join(f'<div><div class="ad-lbl">{l}</div><div class="ad-val">{v}</div></div>'
                    for l, v in pairs)
    return f'<div class="ad-stats">{items}</div>'


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
def _kpi(col, icon, color, tint, num, label):
    with col, st.container(border=True, key=f"adkpi_{label.lower().replace(' ', '_')}"):
        st.markdown(
            f'<div class="ad-kico" style="background:{tint};color:{color};">{icon}</div>'
            f'<div class="ad-knum">{num}</div><div class="ad-klbl">{label}</div>',
            unsafe_allow_html=True)


def _country_links() -> list[tuple[str, str, str, str]]:
    """[(slug, name, iso, page)] — released markets first, then framework countries."""
    links = [("sweden", "Sweden", "se", "scb_salaries.py"),
             ("france", "France", "fr", "france.py")]
    try:
        from core import registry
        for c in registry.all_countries():
            if c.slug != "demo":
                links.append((c.slug, c.name, c.iso, f"countries/{c.slug}/page.py"))
    except Exception:
        pass
    return links


def overview_section():
    users, uerr = _load_users()
    n_users = len(users) if users is not None else "—"
    links = _country_links()
    updates = sum(1 for k in ("_us_upd", "_fr_upd") if st.session_state.get(k))

    c1, c2, c3, c4 = st.columns(4)
    _kpi(c1, _IC_USERS, "#0A63A6", "rgba(10,99,166,.10)", n_users, "Registered users")
    _kpi(c2, _IC_GLOBE, "#1B8A5A", "rgba(27,138,90,.12)", len(links), "Countries")
    _kpi(c3, _IC_ZAP, "#B26A00", "rgba(178,106,0,.13)", 3, "Live sources")
    _kpi(c4, _IC_ALERT, "#C0453A", "rgba(192,69,58,.12)", updates, "Updates available")
    if uerr:
        st.caption(f"⚠ Could not load users: {uerr}")

    st.write("")
    with st.container(border=True, key="adcard_open"):
        st.markdown("#### Open a country")
        st.caption("Jump straight into any country page, including admin-only previews.")
        cols = st.columns(4)
        flag_css = ""
        for i, (slug, name, iso, page) in enumerate(links):
            with cols[i % 4], st.container(key=f"adtile_{slug}"):
                st.page_link(page, label=name)
            flag_css += (f".st-key-adtile_{slug} [data-testid='stPageLink'] a"
                         f"{{background-image:url('{theme.flag_uri(iso)}');}}\n")
        st.markdown(f"<style>{flag_css}</style>", unsafe_allow_html=True)


# ── Section: Data sources ────────────────────────────────────────────────────
def _run_us_refresh(usbuild, target):
    with st.status("Refreshing US OEWS…", expanded=True) as status:
        def log(msg):
            status.write(msg)
        try:
            res = usbuild.build(year=target, log=log)
            try:
                from countries.us import provider as usprov
                usprov._load.clear()
            except Exception:
                pass
            st.session_state["_us_refresh_result"] = res
            st.session_state.pop("_us_latest", None)
            st.session_state.pop("_us_upd", None)
            status.update(label=f"Done — May {res['year']}", state="complete")
        except Exception as e:  # noqa: BLE001
            status.update(label="Refresh failed", state="error")
            st.session_state["_us_refresh_error"] = str(e)
    st.rerun()


def _us_card(query):
    from countries.us import build as usbuild
    if not _match(query, "united states", "us", "bls", "oews", "bundled", "soc"):
        return
    info = usbuild.bundled_info()
    c = info.get("counts", {})
    latest = st.session_state.get("_us_latest")
    newer = bool(latest and info.get("year") and latest > info["year"])
    st.session_state["_us_upd"] = newer
    pill = _pill("amber", "Update available") if newer else _pill("green", "Up to date")
    with st.container(border=True, key="adcard_us"):
        html = _hdr("us", "United States", "BLS OEWS", "bundled file", pill)
        html += _stats([("Latest data year", f"May {info.get('year', '—')}"),
                        ("Occupations", _n(c.get("occupations", "—"))),
                        ("Scopes", _n(c.get("scopes", "—"))),
                        ("File size", _fmt_bytes(info.get("size")))])
        html += (f'<div class="ad-cap">Bundled file built {info.get("built_at", "—")} · '
                 "re-downloadable from BLS special-requests files (national + state + "
                 "national-industry).</div>")
        if newer:
            html += (f'<div class="ad-alert">↻ May {latest} available — newer than the '
                     f'bundled May {info["year"]}.</div>')
        st.markdown(html, unsafe_allow_html=True)

        target = latest if newer else None
        with _btnrow():
            go = st.button(f"↻ Refresh to May {target}" if target else "↻ Rebuild from BLS",
                           type="primary", key="us_refresh_btn")
            chk = st.button("🔍 Check for newer release", key="us_scan")
        if go:
            st.session_state["_us_confirm"] = True
        if chk:
            with st.spinner("Scanning BLS…"):
                st.session_state["_us_latest"] = usbuild.latest_available_year()
            st.rerun()

        if st.session_state.get("_us_confirm"):
            st.warning("This re-downloads ~65 MB from BLS and rebuilds the dataset (≈1–2 min). "
                       "The running app updates immediately; to persist across redeploys, "
                       "commit the regenerated `us_oews.json.gz`.")
            with _btnrow():
                yes = st.button("✅ Confirm refresh", type="primary", key="us_confirm_yes")
                no = st.button("Cancel", key="us_confirm_no")
            if yes:
                st.session_state.pop("_us_confirm", None)
                _run_us_refresh(usbuild, target)
            if no:
                st.session_state.pop("_us_confirm", None)
                st.rerun()
        if st.session_state.get("_us_refresh_error"):
            st.error(f"Last refresh failed: {st.session_state.pop('_us_refresh_error')}")
        res = st.session_state.get("_us_refresh_result")
        if res:
            st.success(f"✅ Refreshed to May {res['year']} · {_n(res['occupations'])} occupations "
                       f"· {_n(res['scopes'])} scopes · {_n(res['rows'])} rows · "
                       f"{_fmt_bytes(res['size'])}")


def _norway_card(query):
    if not _match(query, "norway", "ssb", "styrk", "live"):
        return
    styrk = (_file_meta("styrk_labels.json").get("data") or {})
    with st.container(border=True, key="adcard_no"):
        st.markdown(
            _hdr("no", "Norway", "SSB", "live API + STYRK labels", _pill("green", "Up to date"))
            + _stats([("Latest data year", _norway_latest_year() or "—"),
                      ("STYRK labels built", styrk.get("built_at", "—"))])
            + ('<div class="ad-cap">Salaries fetched live from SSB table 11418 and disk-cached; '
               "the bundled bilingual STYRK labels give instant dropdowns. Rebuilding re-fetches "
               "the labels from SSB (EN + NO).</div>"),
            unsafe_allow_html=True)
        with _btnrow():
            go = st.button("↻ Rebuild labels", key="no_rebuild")
        if go:
            with st.status("Rebuilding STYRK labels…", expanded=True) as status:
                try:
                    from countries.norway import build as nobuild
                    res = nobuild.build(log=status.write)
                    try:
                        from countries.norway import provider as noprov
                        noprov._codes.clear()          # serve the new labels immediately
                    except Exception:
                        pass
                    st.session_state["_no_labels_result"] = res
                    status.update(label=f"Done — {res['built_at']}", state="complete")
                except Exception as e:  # noqa: BLE001
                    status.update(label="Rebuild failed", state="error")
                    st.error(str(e))
            st.rerun()
        res = st.session_state.get("_no_labels_result")
        if res:
            st.success(f"✅ Labels rebuilt {res['built_at']} · {_n(res['codes'])} codes "
                       f"({_n(res['leaves'])} occupations).")


def _sweden_card(query):
    if not _match(query, "sweden", "scb", "ssyk", "live"):
        return
    occ = (_file_meta("occupations_cache.json").get("data") or {})
    ssyk = (_file_meta("ssyk_descriptions.json").get("data") or {})
    appset = (_file_meta("app_settings.json").get("data") or {})
    with st.container(border=True, key="adcard_se"):
        st.markdown(
            _hdr("se", "Sweden", "SCB", "live API + stored codes & labels",
                 _pill("green", "Up to date"))
            + _stats([("Latest data year", appset.get("latest_data_year", 2025)),
                      ("SCB codes cached", (occ.get("cached_at") or "—")[:10]),
                      ("SSYK labels built", (ssyk.get("built_at") or "—")[:10])])
            + ('<div class="ad-cap">Salaries fetched live from SCB; occupation codes + SSYK '
               "labels/translations are cached for fast, translated dropdowns. Re-fetching "
               "updates the occupation codes from the SCB API (EN + SV).</div>"),
            unsafe_allow_html=True)
        with _btnrow():
            go = st.button("↻ Re-fetch codes", key="se_refetch")
        if go:
            with st.spinner("Fetching occupation codes from SCB…"):
                try:
                    import sweden_codes
                    ts = sweden_codes.refresh()
                    # Sweden's page reads session-state first — drop its copies
                    # so it reloads the fresh disk cache.
                    for k in ("occupations_EN", "occupations_SV", "cache_ts"):
                        st.session_state.pop(k, None)
                    st.session_state["_se_codes_result"] = ts
                except Exception as e:  # noqa: BLE001
                    st.error(f"Re-fetch failed: {e}")
            st.rerun()
        res = st.session_state.get("_se_codes_result")
        if res:
            st.success(f"✅ SCB codes re-fetched {res}.")


def _france_card(query):
    if not _match(query, "france", "insee", "melodi", "microdata", "pcs", "live"):
        return
    lbl = (_file_meta("pcs_labels.json").get("data") or {})
    micro_meta = _file_meta("pcs_microdata_percentiles.json")
    micro = micro_meta.get("data") or {}
    micro_year = micro.get("year", "—")
    frl = st.session_state.get("_fr_latest")
    try:
        my = int(str(micro_year)[:4])
    except (TypeError, ValueError):
        my = 0
    newer = bool(frl and frl > my)
    st.session_state["_fr_upd"] = newer
    pill = _pill("amber", "Update available") if newer else _pill("green", "Up to date")
    with st.container(border=True, key="adcard_fr"):
        html = _hdr("fr", "France", "INSEE", "live API + microdata + PCS labels", pill)
        html += _stats([("Microdata year", micro_year),
                        ("PCS labels built", lbl.get("built_at", "—")),
                        ("Microdata size", _fmt_bytes(micro_meta.get("size")))])
        html += ('<div class="ad-cap">Mean-salary series fetched live from INSEE Melodi; '
                 "per-occupation percentiles come from a bundled microdata file (FD_SALAAN), PCS "
                 "labels from a bundled file. Both rebuild offline — INSEE microdata is a manual "
                 "download, not a live URL.</div>")
        if newer:
            html += (f'<div class="ad-alert">↻ INSEE publishes annual data through {frl} — '
                     f'the bundled microdata is {micro_year}.</div>')
        st.markdown(html, unsafe_allow_html=True)
        with _btnrow():
            chk = st.button("🔍 Check INSEE for a newer year", key="fr_scan")
        if chk:
            with st.spinner("Querying INSEE Melodi…"):
                try:
                    import france_data as fd
                    st.session_state["_fr_latest"] = fd.fetch_available_year("private")
                except Exception as e:  # noqa: BLE001
                    st.session_state["_fr_err"] = str(e)
            st.rerun()
        if st.session_state.get("_fr_err"):
            st.error(f"INSEE check failed: {st.session_state.pop('_fr_err')}")


def _caches_card(query):
    if not _match(query, "cache", "clear", "sweden", "norway", "france"):
        return
    with st.container(border=True, key="adcard_caches"):
        lc, rc = st.columns([3, 1.2], vertical_alignment="center")
        lc.markdown(
            '<div class="ad-hdL"><span><span class="ad-name">Caches</span>'
            '<span class="ad-type">· Sweden · Norway · France live fetches</span></span></div>'
            '<div class="ad-cap" style="margin-top:8px;">Live-API sources cache fetched figures '
            "to disk. Clear to force a re-fetch of the latest published data on next view.</div>",
            unsafe_allow_html=True)
        if rc.button("🗑 Clear data caches", key="clear_caches"):
            st.cache_data.clear()
            st.success("Cleared — fresh figures on next view.")


def data_section():
    st.markdown(CSS, unsafe_allow_html=True)
    tl, tr = st.columns([2.4, 1], vertical_alignment="center")
    tl.caption("Each source shows its latest data year and how it refreshes.")
    tr.markdown('<div style="text-align:right;font-size:12px;color:#7A828F;">'
                '<span class="ad-pill ad-green" style="padding:2px 8px;">Up to date</span>&nbsp;'
                '<span class="ad-pill ad-amber" style="padding:2px 8px;">Update available</span></div>',
                unsafe_allow_html=True)
    query = st.text_input("Search data sources", key="ds_search",
                          placeholder="🔍  Search sources — country, agency, classification…",
                          label_visibility="collapsed")
    _us_card(query)
    _norway_card(query)
    _sweden_card(query)
    _france_card(query)
    _caches_card(query)
    if query.strip() and not any(_match(query, *t) for t in (
            ("united states", "us", "bls", "oews", "bundled", "soc"),
            ("norway", "ssb", "styrk"), ("sweden", "scb", "ssyk"),
            ("france", "insee", "melodi", "microdata", "pcs"), ("cache", "clear"))):
        st.caption(f"No data source matches “{query}”.")


# ── Section: Users ───────────────────────────────────────────────────────────
_ROLE_BADGE = {
    "master": ('👑 Master', '#8A6A2A', 'rgba(184,134,59,.16)'),
    "admin": ('Admin', '#0A63A6', 'rgba(10,99,166,.10)'),
    "standard": ('Standard', '#5B6472', '#EEF0F3'),
}


def _initials(name, email):
    base = (name or (email.split("@")[0] if email else "?")).strip()
    parts = base.replace(".", " ").replace("_", " ").split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    b = parts[0] if parts else "?"
    if len(b) > 1 and b[-1].isdigit():          # "kristoffer2" → "K2"
        return (b[0] + b[-1]).upper()
    return b[:2].upper()


def users_section():
    st.markdown(CSS, unsafe_allow_html=True)
    me = st.session_state.get("auth_user", {})
    country_opts = _country_options()
    cslugs = list(country_opts)
    cfmt = lambda s: country_opts.get(s, s)          # noqa: E731

    # ── Create user card ──
    with st.container(border=True, key="adcard_create"):
        st.markdown("#### Create user")
        a, b = st.columns(2)
        a.markdown('<div class="ad-flbl">Name</div>', unsafe_allow_html=True)
        nn = a.text_input("Name", key="nu_name", placeholder="Full name",
                          label_visibility="collapsed")
        b.markdown('<div class="ad-flbl">Email</div>', unsafe_allow_html=True)
        ne = b.text_input("Email", key="nu_email", placeholder="name@company.com",
                          label_visibility="collapsed")
        c, d = st.columns(2)
        c.markdown('<div class="ad-flbl">Password</div>', unsafe_allow_html=True)
        npw = c.text_input("Password", type="password", key="nu_pw", label_visibility="collapsed")
        d.markdown('<div class="ad-flbl">Role</div>', unsafe_allow_html=True)
        nr = d.selectbox("Role", auth.ROLES, key="nu_role", label_visibility="collapsed")
        st.markdown('<div class="ad-flbl">Country access</div>', unsafe_allow_html=True)
        nc = st.multiselect("Country access", cslugs, default=list(auth.DEFAULT_COUNTRIES),
                            format_func=cfmt, key="nu_countries", label_visibility="collapsed")
        if st.button("Create user", type="primary", key="nu_create"):
            if not nn.strip() or not ne.strip() or not npw:
                st.error("Name, email and password are required.")
            else:
                try:
                    auth.create_user(ne.strip(), npw, nr, countries=nc, name=nn.strip())
                    _invalidate_users()
                    st.success(f"Created {ne}")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"Could not create user: {e}")

    st.write("")

    # ── Existing users card ──
    users, err = _load_users()
    with st.container(border=True, key="adcard_users"):
        rc = Counter((u["role"] for u in users)) if users else Counter()
        h1, h2 = st.columns([4, 1], vertical_alignment="center")
        h1.markdown(
            '#### Existing users '
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:11px;'
            f'color:#98A0AC;font-weight:400;">&nbsp;&nbsp;{rc.get("master",0)} master · '
            f'{rc.get("admin",0)} admin · {rc.get("standard",0)} standard · '
            f'{sum(rc.values())} total</span>', unsafe_allow_html=True)
        if h2.button("↻ Reload", key="users_reload", use_container_width=True):
            _load_users(force=True)
            st.rerun()
        if err:
            st.error(f"Could not list users: {err}")
            st.caption("Supabase can be slow to respond — try ↻ Reload.")
            return

        _W = [2.6, 3, 1.7, 2.2, 1.2]
        head = st.columns(_W)
        for col, cap in zip(head, ("User", "Email", "Role", "Access", "Actions")):
            col.markdown(f'<div class="ad-th">{cap}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:1px;background:#EEF0F3;margin:6px 0 2px;"></div>',
                    unsafe_allow_html=True)

        for u in users or []:
            c_user, c_email, c_role, c_acc, c_act = st.columns(_W, vertical_alignment="center")
            av = "#B8863B" if u["role"] in _ADMIN_ROLES else "#0A63A6"
            nm = u.get("name") or "— (no name)"
            c_user.markdown(
                f'<div class="ad-user"><div class="ad-av" style="background:{av};">'
                f'{_initials(u.get("name"), u["email"])}</div>'
                f'<span class="ad-uname">{nm}</span></div>', unsafe_allow_html=True)
            c_email.markdown(f'<span class="ad-email">{u["email"]}</span>', unsafe_allow_html=True)
            txt, fg, bg = _ROLE_BADGE.get(u["role"], (u["role"], "#5B6472", "#EEF0F3"))
            you = " (you)" if u["id"] == me.get("id") else ""
            c_role.markdown(f'<span class="ad-badge" style="color:{fg};background:{bg};">'
                            f'{txt}</span>{you}', unsafe_allow_html=True)
            acc = ("All countries" if u["role"] in _ADMIN_ROLES
                   else ", ".join(cfmt(s) for s in u.get("countries", [])) or "—")
            c_acc.markdown(f'<span class="ad-access">🌐 {acc}</span>', unsafe_allow_html=True)

            e_col, d_col = c_act.columns(2)
            with e_col.popover("✏️", help="Edit user"):
                if u["role"] == "master":
                    st.caption("👑 Master — role fixed.")
                elif u["id"] == me.get("id"):
                    st.caption("This is you — role fixed.")
                else:
                    nrole = st.selectbox("Role", auth.ROLES,
                                         index=auth.ROLES.index(u["role"]) if u["role"] in auth.ROLES else 0,
                                         key=f"role_{u['id']}")
                    if nrole != u["role"] and st.button("Save role", key=f"rolebtn_{u['id']}"):
                        try:
                            auth.set_role(u["id"], nrole)
                            _invalidate_users()
                            st.rerun()
                        except Exception as e:  # noqa: BLE001
                            st.error(str(e))
                cur = [s for s in u.get("countries", []) if s in cslugs]
                sel = st.multiselect("Country access", cslugs, default=cur, format_func=cfmt,
                                     key=f"cty_{u['id']}")
                if st.button("Save access", key=f"ctybtn_{u['id']}"):
                    try:
                        auth.set_countries(u["id"], sel)
                        _invalidate_users()
                        st.success("Saved.")
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.error(str(e))
                pwl = "Your new password" if u["id"] == me.get("id") else "New password"
                newpw = st.text_input(pwl, type="password", key=f"pw_{u['id']}")
                if st.button("Update password", key=f"pwbtn_{u['id']}"):
                    try:
                        auth.set_password(u["id"], newpw)
                        st.success("Password updated.")
                    except Exception as e:  # noqa: BLE001
                        st.error(str(e))
            if u["role"] != "master" and u["id"] != me.get("id"):
                if d_col.button("🗑", key=f"del_{u['id']}", help="Delete user"):
                    try:
                        auth.delete_user(u["id"])
                        _invalidate_users()
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.error(str(e))


# ── Orchestrator ─────────────────────────────────────────────────────────────
SECTIONS = {"Overview": overview_section, "Data sources": data_section, "Users": users_section}


def section_selector() -> str:
    """The Overview / Data sources / Users pill toggle (rendered in the header)."""
    sec = st.segmented_control("section", list(SECTIONS), default="Overview",
                               key="_admin_section", label_visibility="collapsed")
    return sec or "Overview"


def render_body(section: str):
    st.markdown(CSS, unsafe_allow_html=True)
    SECTIONS.get(section, overview_section)()


def render():
    """Standalone entry (tabs + body) — kept for reuse; admin.py renders the header."""
    render_body(section_selector())
