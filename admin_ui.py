"""Shared, full-page Admin panel UI (rendered by admin.py).

Plain module — NO top-level Streamlit calls — so its section functions can be
reused elsewhere (e.g. Sweden's 'Manage users' dialog calls users_section()).
Access is gated to admin/master by admin.py before any of this renders.

Sections: Overview · Data sources · Users.
"""
from __future__ import annotations

import streamlit as st

import auth

_ADMIN_ROLES = ("admin", "master")


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
    from countries.us import build as usbuild

    st.subheader("Overview")
    users, uerr = _load_users()
    n_users = len(users) if users is not None else None
    n_admins = sum(1 for u in users if u["role"] in _ADMIN_ROLES) if users else None

    info = usbuild.bundled_info()
    try:
        from core import registry
        n_countries = len([c for c in registry.all_countries() if c.slug != "demo"]) + 2  # + SE/FR
    except Exception:
        n_countries = "—"

    m1, m2, m3 = st.columns(3)
    m1.metric("Registered users", n_users if n_users is not None else "—",
              help=(f"{n_admins} admin / master" if n_admins is not None else uerr))
    m2.metric("Countries", n_countries, help="Framework + legacy Sweden/France")
    m3.metric("US OEWS data", f"May {info.get('year', '—')}",
              help=f"built {info.get('built_at', '—')}")

    # Data-freshness heads-up (uses the last auto-scan result if present)
    latest = st.session_state.get("_us_latest")
    if latest and info.get("year") and latest > info["year"]:
        st.warning(f"🆕 A newer US release (**May {latest}**) is available. "
                   "Refresh it under **Data sources**.")

    st.markdown("#### Open a country")
    st.caption("Jump straight into any country page (including admin-only previews).")
    try:
        from core import registry
        vis = registry.visible_for_current_user()
        if vis:
            cols = st.columns(min(4, len(vis)))
            for i, c in enumerate(vis):
                cols[i % len(cols)].page_link(f"countries/{c.slug}/page.py",
                                              label=c.name, icon=":material/open_in_new:")
    except Exception:
        pass
    lc1, lc2 = st.columns(2)
    lc1.page_link("scb_salaries.py", label="Sweden", icon=":material/open_in_new:")
    lc2.page_link("france.py", label="France", icon=":material/open_in_new:")


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


def data_section():
    from countries.us import build as usbuild

    st.subheader("Data sources")
    st.caption("Watch for newer official releases and refresh the bundled datasets.")

    info = usbuild.bundled_info()
    counts = info.get("counts", {})
    with st.container(border=True):
        st.markdown("#### 🇺🇸 United States · BLS OEWS  <span style='color:#8A919D;font-weight:400;'>"
                    "· bundled snapshot</span>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Reference year", f"May {info.get('year', '—')}")
        m2.metric("Occupations", f"{counts.get('occupations', '—')}")
        m3.metric("Scopes", f"{counts.get('scopes', '—')}",
                  help="US national + states + NAICS industries")
        m4.metric("File size", _fmt_bytes(info.get("size")))
        st.caption(f"Built {info.get('built_at', '—')} · source: BLS special-requests files "
                   "(national + state + national-industry).")

        # Auto-scan — cached in session so we don't hit BLS on every rerun.
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

    with st.container(border=True):
        st.markdown("#### Live-API sources  <span style='color:#8A919D;font-weight:400;'>"
                    "· Sweden · Norway · France</span>", unsafe_allow_html=True)
        st.caption("These fetch on demand and cache to disk — there is no bundled file to "
                   "rebuild. Clear the cache to force a re-fetch of the latest figures.")
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
    c1, c2, c3 = st.columns([3, 2, 2])
    ne = c1.text_input("Email", key="nu_email")
    npw = c2.text_input("Password", type="password", key="nu_pw")
    nr = c3.selectbox("Role", auth.ROLES, key="nu_role")
    nc = st.multiselect("Country access", cslugs, default=list(auth.DEFAULT_COUNTRIES),
                        format_func=cfmt, key="nu_countries")
    if st.button("Create user", type="primary"):
        try:
            auth.create_user(ne.strip(), npw, nr, countries=nc)
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
    for u in users or []:
        c1, c2, cc, c3, c4 = st.columns([3.4, 2, 1, 1, 1])
        c1.write(u["email"])
        if u["role"] == "master":
            c2.write("👑 master")
        elif u["id"] == me.get("id"):
            c2.write(f"{u['role']} (you)")
        else:
            nrole = c2.selectbox(
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
        with cc.popover("🌐", help="Country access"):
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
        with c3.popover("🔑", help="Set password"):
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
            if c4.button("🗑", key=f"del_{u['id']}", help="Delete user"):
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
