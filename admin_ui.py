"""Shared, full-page Admin panel UI (rendered by admin.py).

Plain module — NO top-level Streamlit calls — so its section functions can be
reused elsewhere (e.g. Sweden's 'Manage users' dialog calls users_section()).
Access is gated to admin/master by admin.py before any of this renders.

Sections: Overview · Data sources · Users.
"""
from __future__ import annotations

import gzip
import json
import os

import streamlit as st

import auth

_ADMIN_ROLES = ("admin", "master")
_ROOT = os.path.dirname(os.path.abspath(__file__))   # repo root (admin_ui.py lives here)


def _file_meta(name: str) -> dict:
    """Read a repo-root data file (plain or .gz JSON) → {exists, size, data}.
    Lets the admin panel report a data source's freshness without importing the
    legacy page modules (which would execute their whole page script)."""
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


# ── small helpers ────────────────────────────────────────────────────────────
def _country_options() -> dict:
    """{slug: display name} of the markets a user may be granted access to."""
    opts = {"sweden": "Sweden", "france": "France"}
    try:
        from core import registry
        for c in registry.all_countries():
            if c.slug != "demo":
                opts[c.slug] = c.name
    except Exception:
        pass
    return opts


def _fmt_bytes(n) -> str:
    return f"{n / 1e6:.2f} MB" if n else "—"


def _load_users(force: bool = False):
    """(users_list, error) cached in session so Overview + Users don't each hit
    Supabase on every rerun. Mutations pop the cache to force a reload."""
    if force or "_admin_users" not in st.session_state:
        try:
            st.session_state["_admin_users"] = (auth.list_users(), None)
        except Exception as e:  # noqa: BLE001
            st.session_state["_admin_users"] = (None, str(e))
    return st.session_state["_admin_users"]


def _invalidate_users():
    st.session_state.pop("_admin_users", None)


# ── Section: Overview ────────────────────────────────────────────────────────
def overview_section():
    st.subheader("Overview")
    users, uerr = _load_users()
    n_users = len(users) if users is not None else None
    n_admins = sum(1 for u in users if u["role"] in _ADMIN_ROLES) if users else None

    # Released markets (Sweden, France) + framework countries (excluding the demo).
    links = [("Sweden", "scb_salaries.py"), ("France", "france.py")]
    try:
        from core import registry
        for c in registry.all_countries():
            if c.slug != "demo":
                links.append((c.name, f"countries/{c.slug}/page.py"))
    except Exception:
        pass

    m1, m2 = st.columns(2)
    m1.metric("Registered users", n_users if n_users is not None else "—",
              help=(f"{n_admins} admin / master" if n_admins is not None else uerr))
    m2.metric("Countries", len(links), help="Released markets + framework countries")

    st.markdown("#### Open a country")
    st.caption("Jump straight into any country page (including admin-only previews).")
    cols = st.columns(4)
    for i, (name, page) in enumerate(links):
        cols[i % 4].page_link(page, label=name, icon=":material/open_in_new:")


# ── Section: Data sources ────────────────────────────────────────────────────
def _run_us_refresh(usbuild, target):
    """Blocking rebuild with live log, then hot-swap the provider cache."""
    with st.status("Refreshing US OEWS…", expanded=True) as status:
        def log(msg):
            status.write(msg)
        try:
            res = usbuild.build(year=target, log=log)
            try:
                from countries.us import provider as usprov
                usprov._load.clear()                       # serve the new file immediately
            except Exception:
                pass
            st.session_state["_us_refresh_result"] = res
            st.session_state.pop("_us_latest", None)       # re-scan next time
            status.update(label=f"Done — May {res['year']}", state="complete")
        except Exception as e:  # noqa: BLE001
            status.update(label="Refresh failed", state="error")
            st.session_state["_us_refresh_error"] = str(e)
    st.rerun()


def _src_head(title, subtitle):
    st.markdown(f"#### {title}  <span style='color:#8A919D;font-weight:400;'>· {subtitle}</span>",
                unsafe_allow_html=True)


def _us_card():
    from countries.us import build as usbuild
    info = usbuild.bundled_info()
    counts = info.get("counts", {})
    with st.container(border=True):
        _src_head("🇺🇸 United States · BLS OEWS", "bundled file")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Latest data year", f"May {info.get('year', '—')}")
        m2.metric("Occupations", f"{counts.get('occupations', '—')}")
        m3.metric("Scopes", f"{counts.get('scopes', '—')}",
                  help="US national + states + NAICS industries")
        m4.metric("File size", _fmt_bytes(info.get("size")))
        st.caption(f"Bundled file built {info.get('built_at', '—')} · re-downloadable from BLS "
                   "special-requests files (national + state + national-industry).")

        sc1, sc2 = st.columns([1, 2.4], vertical_alignment="center")
        if sc1.button("🔎 Check for newer release", key="us_scan", use_container_width=True):
            with st.spinner("Scanning BLS…"):
                st.session_state["_us_latest"] = usbuild.latest_available_year()
        latest = st.session_state.get("_us_latest")
        if latest is not None:
            if info.get("year") and latest > info["year"]:
                sc2.warning(f"🆕 **May {latest}** available — newer than the bundled "
                            f"May {info['year']}.")
            else:
                sc2.success(f"✅ Up to date (latest published: May {latest}).")

        st.divider()
        target = latest if (latest and info.get("year") and latest > info["year"]) else None
        label = f"↻ Refresh to May {target}" if target else "↻ Rebuild from BLS"
        if st.button(label, type="primary", key="us_refresh_btn"):
            st.session_state["_us_confirm"] = True
        if st.session_state.get("_us_confirm"):
            st.warning("This re-downloads ~65 MB from BLS and rebuilds the dataset "
                       "(≈1–2 min). The running app updates immediately; to persist "
                       "across redeploys, commit the regenerated `us_oews.json.gz`.")
            cc1, cc2 = st.columns(2)
            if cc1.button("✅ Confirm refresh", type="primary", key="us_confirm_yes",
                          use_container_width=True):
                st.session_state.pop("_us_confirm", None)
                _run_us_refresh(usbuild, target)
            if cc2.button("Cancel", key="us_confirm_no", use_container_width=True):
                st.session_state.pop("_us_confirm", None)
                st.rerun()
        if st.session_state.get("_us_refresh_error"):
            st.error(f"Last refresh failed: {st.session_state.pop('_us_refresh_error')}")
        res = st.session_state.get("_us_refresh_result")
        if res:
            st.success(
                f"✅ Refreshed to **May {res['year']}** · {res['occupations']} occupations · "
                f"{res['scopes']} scopes · {res['rows']:,} rows · {_fmt_bytes(res['size'])} "
                f"· built {res['built_at']}")


def _norway_card():
    styrk = (_file_meta("styrk_labels.json").get("data") or {})
    with st.container(border=True):
        _src_head("🇳🇴 Norway · SSB", "live API + STYRK labels")
        m1, m2 = st.columns(2)
        m1.metric("Latest data year", _norway_latest_year() or "—")
        m2.metric("STYRK labels built", styrk.get("built_at", "—"))
        st.caption("Salaries fetched live from SSB table 11418 and disk-cached; the bundled "
                   "bilingual STYRK labels give instant dropdowns. No file to refresh — "
                   "rebuild labels offline via build_styrk_labels.py.")


def _sweden_card():
    occ = (_file_meta("occupations_cache.json").get("data") or {})
    ssyk = (_file_meta("ssyk_descriptions.json").get("data") or {})
    appset = (_file_meta("app_settings.json").get("data") or {})
    with st.container(border=True):
        _src_head("🇸🇪 Sweden · SCB", "live API + stored codes & labels")
        m1, m2, m3 = st.columns(3)
        m1.metric("Latest data year", appset.get("latest_data_year", 2025))
        m2.metric("SCB codes cached", (occ.get("cached_at") or "—")[:10])
        m3.metric("SSYK labels built", (ssyk.get("built_at") or "—")[:10])
        st.caption("Salaries fetched live from SCB; occupation codes + SSYK labels/translations "
                   "are cached for fast, translated dropdowns. Code re-fetch and the data-year "
                   "check currently run from the Sweden page's own admin — migrating those "
                   "actions here is the next step.")


def _france_card():
    lbl = (_file_meta("pcs_labels.json").get("data") or {})
    micro_meta = _file_meta("pcs_microdata_percentiles.json")
    micro = micro_meta.get("data") or {}
    micro_year = micro.get("year", "—")
    with st.container(border=True):
        _src_head("🇫🇷 France · INSEE", "live API + microdata file + PCS labels")
        m1, m2, m3 = st.columns(3)
        m1.metric("Microdata year", micro_year)
        m2.metric("PCS labels built", lbl.get("built_at", "—"))
        m3.metric("Microdata size", _fmt_bytes(micro_meta.get("size")))
        st.caption("Mean-salary series fetched live from INSEE Melodi; per-occupation "
                   "percentiles come from a bundled **microdata** file (FD_SALAAN), and PCS "
                   "labels/translations from a bundled file. Both rebuild offline — INSEE "
                   "microdata is a manual download, not a live URL.")

        sc1, sc2 = st.columns([1, 2.4], vertical_alignment="center")
        if sc1.button("🔎 Check INSEE for a newer year", key="fr_scan",
                      use_container_width=True):
            with st.spinner("Querying INSEE Melodi…"):
                try:
                    import france_data as fd
                    st.session_state["_fr_latest"] = fd.fetch_available_year("private")
                except Exception as e:  # noqa: BLE001
                    st.session_state["_fr_latest"], st.session_state["_fr_err"] = None, str(e)
        frl = st.session_state.get("_fr_latest")
        if frl:
            try:
                my = int(str(micro_year)[:4])
            except (TypeError, ValueError):
                my = 0
            if frl > my:
                sc2.warning(f"🆕 INSEE publishes annual data through **{frl}** — the bundled "
                            f"microdata is {micro_year}. Rebuild via "
                            "build_pcs_microdata_percentiles.py to update.")
            else:
                sc2.success(f"✅ Microdata year {micro_year} matches INSEE's latest ({frl}).")
        elif st.session_state.get("_fr_err"):
            sc2.error(f"INSEE check failed: {st.session_state.pop('_fr_err')}")


def data_section():
    st.subheader("Data sources")
    st.caption("Each source shows its latest data year and how it refreshes.")
    _us_card()
    _norway_card()
    _sweden_card()
    _france_card()
    with st.container(border=True):
        _src_head("Caches", "Sweden · Norway · France live fetches")
        st.caption("The live-API sources cache fetched figures to disk. Clear to force a "
                   "re-fetch of the latest published data on next view.")
        if st.button("🗑 Clear data caches", key="clear_caches"):
            st.cache_data.clear()
            st.success("Cleared — fresh figures will be fetched on next view.")


# ── Section: Users ───────────────────────────────────────────────────────────
def users_section():
    """Create / list / manage users. Reused by Sweden's 'Manage users' dialog."""
    me = st.session_state.get("auth_user", {})
    country_opts = _country_options()
    cslugs = list(country_opts)
    cfmt = lambda s: country_opts.get(s, s)          # noqa: E731

    st.markdown("**Create user**")
    n1, n2 = st.columns(2)
    nn = n1.text_input("Name", key="nu_name", placeholder="Full name (optional)")
    ne = n2.text_input("Email", key="nu_email")
    p1, p2 = st.columns(2)
    npw = p1.text_input("Password", type="password", key="nu_pw")
    nr = p2.selectbox("Role", auth.ROLES, key="nu_role")
    nc = st.multiselect("Country access", cslugs, default=list(auth.DEFAULT_COUNTRIES),
                        format_func=cfmt, key="nu_countries")
    if st.button("Create user", type="primary"):
        try:
            auth.create_user(ne.strip(), npw, nr, countries=nc, name=nn.strip())
            _invalidate_users()
            st.success(f"Created {ne}")
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not create user: {e}")

    st.divider()
    hc1, hc2 = st.columns([4, 1], vertical_alignment="center")
    hc1.markdown("**Existing users**")
    if hc2.button("↻ Reload", key="users_reload", use_container_width=True):
        _load_users(force=True)
        st.rerun()

    users, err = _load_users()
    if err:
        st.error(f"Could not list users: {err}")
        return
    users = users or []

    # Per-role counter
    from collections import Counter
    rc = Counter(u["role"] for u in users)
    st.caption(f"👑 {rc.get('master', 0)} master · {rc.get('admin', 0)} admin · "
               f"{rc.get('standard', 0)} standard · {len(users)} total")

    # Column captions (same ratios as the rows so they line up)
    _W = [2.2, 3, 2, 2.8]

    def _cap(col, text):
        col.markdown(f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:10.5px;"
                     "letter-spacing:.08em;text-transform:uppercase;color:#8A919D;'>"
                     f"{text}</div>", unsafe_allow_html=True)

    _h = st.columns(_W)
    for _c, _t in zip(_h, ("Name", "Email", "Role", "Function")):
        _cap(_c, _t)

    for u in users:
        c_name, c_email, c_role, c_fn = st.columns(_W, vertical_alignment="center")
        c_name.write(u.get("name") or "—")
        c_email.write(u["email"])
        if u["role"] == "master":
            c_role.write("👑 master")
        elif u["id"] == me.get("id"):
            c_role.write(f"{u['role']} (you)")
        else:
            nrole = c_role.selectbox(
                "role", auth.ROLES,
                index=auth.ROLES.index(u["role"]) if u["role"] in auth.ROLES else 0,
                key=f"role_{u['id']}", label_visibility="collapsed")
            if nrole != u["role"]:
                try:
                    auth.set_role(u["id"], nrole)
                    _invalidate_users()
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(str(e))
        # Function column: country access · password · delete
        f1, f2, f3 = c_fn.columns(3)
        with f1.popover("🌐", help="Country access"):
            cur = [s for s in u.get("countries", []) if s in cslugs]
            sel = st.multiselect(f"Countries for {u['email']}", cslugs, default=cur,
                                 format_func=cfmt, key=f"cty_{u['id']}")
            st.caption("Admins & master can open every country regardless.")
            if st.button("Save access", key=f"ctybtn_{u['id']}"):
                try:
                    auth.set_countries(u["id"], sel)
                    _invalidate_users()
                    st.success("Saved.")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(str(e))
        with f2.popover("🔑", help="Set password"):
            pw_label = "Your new password" if u["id"] == me.get("id") \
                else f"New password for {u['email']}"
            newpw = st.text_input(pw_label, type="password", key=f"pw_{u['id']}")
            if st.button("Update password", key=f"pwbtn_{u['id']}"):
                try:
                    auth.set_password(u["id"], newpw)
                    st.success("Password updated.")
                except Exception as e:  # noqa: BLE001
                    st.error(str(e))
        if u["role"] != "master" and u["id"] != me.get("id"):
            if f3.button("🗑", key=f"del_{u['id']}", help="Delete user"):
                try:
                    auth.delete_user(u["id"])
                    _invalidate_users()
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(str(e))


# ── Orchestrator ─────────────────────────────────────────────────────────────
SECTIONS = {"Overview": overview_section, "Data sources": data_section, "Users": users_section}


def render():
    """Section nav (renders only the active section) + the section body."""
    sec = st.segmented_control(
        "section", list(SECTIONS), default="Overview",
        key="_admin_section", label_visibility="collapsed")
    SECTIONS.get(sec or "Overview", overview_section)()
