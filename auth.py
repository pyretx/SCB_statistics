"""Supabase-backed authentication + user management for the SCB Salary Explorer.

Roles live in Supabase Auth `app_metadata.role` (master | admin | beta |
standard). `app_metadata` is writable only with the service_role key, so users
cannot change their own role. The service_role key stays server-side
(st.secrets). "beta" behaves like "standard" everywhere except that beta-gated
features (e.g. the import-overlay tab) become visible — see
core.access.is_beta_or_admin.
"""
import os
import tomllib
import streamlit as st
from supabase import create_client, Client

# roles an admin may assign (master is bootstrap-only)
ROLES = ("standard", "beta", "admin")

# Country markets a user may open, stored in app_metadata.countries (slugs like
# "sweden"/"france"/"norway"). Gates access to `registered`/`restricted`
# countries (public countries are open regardless; admin/master see everything).
# New/self-registered users with nothing set fall back to this default.
DEFAULT_COUNTRIES = ("sweden", "france")

_SECRETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             ".streamlit", "secrets.toml")


def _cfg() -> dict:
    """Supabase config from st.secrets, falling back to the secrets.toml next to
    this file (robust regardless of the process working directory)."""
    try:
        return dict(st.secrets["supabase"])
    except Exception:
        pass
    try:
        with open(_SECRETS_PATH, "rb") as f:
            return tomllib.load(f).get("supabase", {})
    except Exception:
        return {}


def _public_key(cfg) -> str | None:
    # New Supabase "publishable" key, or legacy "anon" key.
    return cfg.get("publishable_key") or cfg.get("anon_key")


def _secret_key(cfg) -> str | None:
    # New Supabase "secret" key, or legacy "service_role" key.
    return cfg.get("secret_key") or cfg.get("service_role_key")


def supabase_configured() -> bool:
    cfg = _cfg()
    return bool(cfg.get("url") and _public_key(cfg) and _secret_key(cfg))


def _client(service: bool = False) -> Client:
    cfg = _cfg()
    key = _secret_key(cfg) if service else _public_key(cfg)
    client = create_client(cfg["url"], key)
    if service:
        # Admin calls (list/create/update users) sometimes exceed httpx's 5s
        # default read timeout on a slow Supabase — give them real headroom so
        # one call succeeds instead of several timing out.
        try:
            import httpx
            client.auth._http_client.timeout = httpx.Timeout(30.0)
        except Exception:
            pass
    return client


def country_switcher(current: str):
    """Registry- and access-aware country switcher for the sidebar. Lists every
    country: those the user may open are real client-side page-links (session
    preserved); the rest are shown greyed — '🔒 locked' (needs access) or 'soon'
    (not built). So a visitor/standard user sees e.g. Norway right now, greyed &
    locked, until an admin grants them access."""
    import theme

    # Framework countries in registry order (se2/fr2 = the public Sweden/France;
    # public or landing-tiled countries appear, gated ones greyed 🔒). Signed-out
    # visitors only see the public countries. The legacy builds are deliberately
    # NOT listed — admins reach them from the Admin panel.
    signed_in = st.session_state.get("auth_user") is not None
    items = []
    try:
        from core import registry, access as _acc
        for c in registry.all_countries():
            if c.slug == "demo":
                continue
            if not (getattr(c, "landing", False) or c.access == "public"):
                continue                                 # unreleased, tile-less
            if not signed_in and c.access != "public":
                continue                                 # anonymous: SE + FR only
            items.append({"slug": c.slug, "name": c.name, "iso": c.iso,
                          "page": f"countries/{c.slug}/page.py",
                          "state": "open" if _acc.can_open(c) else "locked"})
    except Exception:
        pass

    label = next((it["name"] for it in items if it["slug"] == current), "Country")

    def _flag(iso, dim=False):
        st.markdown(f'<img class="cc-flag" src="{theme.flag_uri(iso)}" alt=""'
                    f'{" style=opacity:.45" if dim else ""}>', unsafe_allow_html=True)

    # Region per country (from the landing catalogue) → group the list with a
    # heading per region, sorted A→Z within each. Keeps a 40-country list scannable.
    regions = {}
    try:
        import content
        for e in content.load("home").get("countries", {}).get("catalog", []):
            regions[e.get("iso")] = e.get("region", "other")
    except Exception:
        pass
    for it in items:
        it["region"] = regions.get(it["iso"], "other")
    _REGION_ORDER = [("europe", "Europe"), ("americas", "Americas"),
                     ("apac", "Asia-Pacific"), ("other", "Other")]

    def _row(it):
        fc, lc = st.columns([1, 5], vertical_alignment="center")
        with fc:
            _flag(it["iso"], dim=(it["state"] != "open"))
        if it["state"] == "open":
            lc.page_link(it["page"], label=it["name"])
        elif it["state"] == "locked":
            lc.markdown(f'<div class="cc-soon">{it["name"]} · 🔒 locked</div>',
                        unsafe_allow_html=True)
        else:  # soon
            lc.markdown(f'<div class="cc-soon">{it["name"]} · soon</div>',
                        unsafe_allow_html=True)

    with st.popover(label, use_container_width=True):
        for rkey, rlabel in _REGION_ORDER:
            grp = sorted((it for it in items if it["region"] == rkey),
                         key=lambda it: it["name"])
            if not grp:
                continue
            st.markdown(
                f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
                f'font-weight:600;letter-spacing:.12em;color:#8A9199;'
                f'margin:12px 0 4px;">{rlabel.upper()}</div>', unsafe_allow_html=True)
            for it in grp:
                _row(it)


def sidebar_identity():
    """Render the signed-in user's identity (avatar initials + name + role) and a
    Log out button in the sidebar. No-op when signed out. Shared by the country
    pages so the logged-in state is always visible in the left menu."""
    u = st.session_state.get("auth_user")
    if not u:
        return
    email = u.get("email", "")
    name = email.split("@")[0] if email else "Account"
    ini = ("".join(w[0] for w in name.replace(".", " ").replace("_", " ").split()[:2])
           or name[:1]).upper()
    role = u.get("role", "standard")
    rc = "#B8863B" if role in ("admin", "master") else "#0A63A6"  # gold accent for admins
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:9px 11px;margin-top:8px;
                border:1px solid #E7E9ED;border-radius:11px;background:#fff;">
      <div style="width:32px;height:32px;border-radius:50%;background:{rc};color:#fff;flex:none;
           display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;">{ini}</div>
      <div style="min-width:0;line-height:1.18;">
        <div style="font-weight:600;font-size:13px;color:#0C1119;overflow:hidden;
             text-overflow:ellipsis;white-space:nowrap;">{name}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.08em;
             text-transform:uppercase;color:{rc};font-weight:600;">{role}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Log out", use_container_width=True, key="sb_logout"):
        import auth_cookie  # local import — auth_cookie imports auth (no cycle)
        revoke_refresh(st.context.cookies.get(auth_cookie.COOKIE_NAME))
        auth_cookie.queue_clear()
        st.session_state.pop("auth_user", None)
        st.rerun()


def _countries_of(meta: dict) -> list:
    """Effective country grants: explicit app_metadata.countries if set (even
    []), else the default. (Self-registered users have nothing set → default.)"""
    return list(meta["countries"]) if "countries" in (meta or {}) else list(DEFAULT_COUNTRIES)


def _profile(u) -> dict:
    """Normalize a gotrue User into the auth_user dict the app keeps in
    session_state: {id, email, name, role, countries, beta_requested}."""
    meta = u.app_metadata or {}
    umeta = u.user_metadata or {}
    return {"id": u.id, "email": u.email,
            "name": umeta.get("full_name") or umeta.get("name") or "",
            "role": meta.get("role", "standard"),
            "countries": _countries_of(meta),
            "beta_requested": meta.get("beta_requested")}


def sign_in(email: str, password: str):
    """Return (user_dict, error). user_dict = {id, email, name, role, countries,
    beta_requested} — beta_requested is the ISO date the user asked to join the
    beta program (from their profile dialog), or None."""
    user, _rt, err = sign_in_with_session(email, password)
    return user, err


def sign_in_with_session(email: str, password: str):
    """Like sign_in, but also returns the session's refresh token so the caller
    can persist the login in a browser cookie (auth_cookie.queue_save).
    Returns (user_dict, refresh_token, error)."""
    try:
        res = _client(service=False).auth.sign_in_with_password(
            {"email": email, "password": password})
        rt = res.session.refresh_token if res.session else None
        return _profile(res.user), rt, None
    except Exception as e:
        return None, None, str(e)


def restore_from_refresh(refresh_token: str):
    """Rebuild a login from the sb_refresh cookie (auth_cookie.restore).
    Returns (user_dict, new_refresh_token) — Supabase ROTATES refresh tokens,
    so the caller must store the returned one. (None, None) on any failure
    (expired/revoked/garbage token). Never log the token value."""
    try:
        res = _client(service=False).auth.refresh_session(refresh_token)
        if res.user is None or res.session is None:
            return None, None
        return _profile(res.user), res.session.refresh_token
    except Exception:
        return None, None


def revoke_refresh(refresh_token) -> None:
    """Best-effort server-side revoke at logout: rehydrate a throwaway client
    from the refresh token, then sign_out() to kill that session chain. We
    hold no access token, so this is the only revoke path available. Failures
    are swallowed — logout must always succeed locally, even offline."""
    if not refresh_token:
        return
    try:
        c = _client(service=False)
        c.auth.refresh_session(refresh_token)
        c.auth.sign_out()
    except Exception:
        pass


def confirm_email_token(token_hash: str):
    """Verify a signup-confirmation token_hash (the root-cause fix for mail
    scanners eating one-time links: the email links to OUR page with the hash,
    and verification only runs when the user presses the Confirm button —
    prefetchers never press buttons). On success the user is signed in.
    Returns (user_dict, error)."""
    user, _rt, err = confirm_email_token_with_session(token_hash)
    return user, err


def confirm_email_token_with_session(token_hash: str):
    """Like confirm_email_token, but also returns the session's refresh token
    for the login cookie. Returns (user_dict, refresh_token, error)."""
    last_err = None
    for otp_type in ("email", "signup"):     # gotrue naming varies by version
        try:
            res = _client(service=False).auth.verify_otp(
                {"token_hash": token_hash, "type": otp_type})
            u = res.user
            if u is None:
                last_err = "verification returned no user"
                continue
            rt = res.session.refresh_token if res.session else None
            return _profile(u), rt, None
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
    return None, None, last_err


def resend_confirmation(email: str, redirect_to: str | None = None):
    """Re-send the signup confirmation email (public client). Returns an error
    string or None. Covers the common real-world failure where the first
    email's one-time link gets consumed by a mail-app preview/scanner before
    the user clicks it — the user then sees 'Email not confirmed' on sign-in
    and can self-serve a fresh link instead of needing an admin."""
    try:
        payload: dict = {"type": "signup", "email": email}
        if redirect_to:
            payload["options"] = {"email_redirect_to": redirect_to}
        _client(service=False).auth.resend(payload)
        return None
    except Exception as e:  # noqa: BLE001
        return str(e)


def sign_up(email: str, password: str, full_name: str = "", redirect_to: str | None = None,
            terms_version: str | None = None):
    """Public self-service registration (uses the anon/public client, not the
    admin API). New accounts default to role 'standard' (no app_metadata is
    set here — only the service-role client may set it). Depends on the
    Supabase project having "Enable sign ups" turned on, and on whether email
    confirmation is required there (both are dashboard settings, not code).

    ``redirect_to`` sets where the confirmation email link lands after Supabase
    verifies the token (must be in the project's Redirect URLs allow-list) — pass
    the app URL with a marker like ``…/?confirmed=1`` so the app can greet the
    user. Returns (user_dict_or_None, error_str_or_None).

    The name is REQUIRED and stored in Supabase user_metadata.full_name.
    ``terms_version`` (content/terms.toml [meta] terms_version, passed by the
    create-account dialog after its required checkbox) is recorded in
    user_metadata so acceptance is provable and re-promptable on change."""
    if not (full_name or "").strip():
        return None, "Name is required."
    try:
        data: dict = {"full_name": full_name.strip()}
        if terms_version:
            from datetime import datetime, timezone
            data["accepted_terms_version"] = terms_version
            data["accepted_terms_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        options: dict = {"data": data}
        if redirect_to:
            options["email_redirect_to"] = redirect_to
        res = _client(service=False).auth.sign_up({
            "email": email, "password": password, "options": options,
        })
        u = res.user
        if u is None:
            return None, "Sign-up did not return a user."
        role = (u.app_metadata or {}).get("role", "standard")
        return {"id": u.id, "email": u.email, "role": role}, None
    except Exception as e:
        return None, str(e)


# ── Dev-only test login ──────────────────────────────────────────────────────
# Impersonation of the three seeded, PASSWORDLESS test users (one per role,
# deploy/seed_test_users.py) so the bug-hunter agent and manual role testing
# can enter the app without any credential entry. Rendered/reachable ONLY
# where secrets contain [test_login] enabled = true — set locally and in the
# DEV server secrets, never in test/prod: where the flag is absent the code
# path is dead, so the accounts cannot be entered on prod even though the
# shared Supabase knows them.
TEST_LOGIN_ROLES = ("admin", "beta", "standard")
TEST_LOGIN_DOMAIN = "salary-explorer.invalid"   # RFC-reserved TLD: undeliverable


def test_login_email(role: str) -> str:
    return f"test-{role}@{TEST_LOGIN_DOMAIN}"


def test_login_enabled() -> bool:
    """True only where [test_login] enabled = true exists in secrets."""
    try:
        return bool(st.secrets["test_login"]["enabled"])
    except Exception:
        pass
    try:
        with open(_SECRETS_PATH, "rb") as f:
            return bool(tomllib.load(f).get("test_login", {}).get("enabled"))
    except Exception:
        return False


def test_sign_in(role: str):
    """Sign the session in as the seeded test user for ``role`` — no password,
    no Supabase session, no cookie: the user is looked up server-side with the
    service key and its profile dict (same shape _profile() builds) goes into
    session_state. The login therefore lasts one browser session and cannot be
    replayed anywhere the flag is off. Returns (user_dict, error)."""
    if not test_login_enabled():
        return None, "Test login is disabled."
    if role not in TEST_LOGIN_ROLES:
        return None, f"role must be one of {TEST_LOGIN_ROLES}"
    email = test_login_email(role)
    try:
        for u in list_users():
            if u["email"] == email:
                return {"id": u["id"], "email": u["email"], "name": u["name"],
                        "role": u["role"], "countries": u["countries"],
                        "beta_requested": u.get("beta_requested")}, None
        return None, f"{email} not found — run deploy/seed_test_users.py first."
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def list_users(retries: int = 1) -> list[dict]:
    # The service client now runs with a 30s timeout (see _client); one retry
    # covers transient drops without stacking long waits.
    resp, last_err = None, None
    for _ in range(retries + 1):
        try:
            resp = _client(service=True).auth.admin.list_users()
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
    if resp is None:
        raise last_err
    users = resp if isinstance(resp, list) else getattr(resp, "users", resp)
    out = []
    for u in users:
        meta = u.app_metadata or {}
        umeta = getattr(u, "user_metadata", None) or {}
        name = (umeta.get("full_name") or umeta.get("name")
                or umeta.get("display_name") or "")
        out.append({
            "id":    u.id,
            "email": u.email,
            "name":  name,
            "role":  meta.get("role", "standard"),
            "countries": _countries_of(meta),
            "beta_requested": meta.get("beta_requested"),
            # False = registered but never completed the email confirmation
            # (the admin panel surfaces these as "waiting for verification")
            "email_confirmed": bool(getattr(u, "email_confirmed_at", None)),
        })
    out.sort(key=lambda r: ({"master": 0, "admin": 1, "standard": 2}.get(r["role"], 3), r["email"]))
    return out


def _set_app_metadata(user_id: str, **changes):
    """Merge changes into a user's app_metadata (fetch → merge → update), so
    setting the role never wipes country grants and vice-versa."""
    client = _client(service=True)
    cur = client.auth.admin.get_user_by_id(user_id)
    meta = dict(getattr(cur.user, "app_metadata", None) or {})
    meta.update(changes)
    client.auth.admin.update_user_by_id(user_id, {"app_metadata": meta})


def create_user(email: str, password: str, role: str, countries=None, name: str = ""):
    """Create an auto-confirmed user with the given role + country access. The
    display name is REQUIRED and stored in Supabase user_metadata.full_name.
    Defaults to the DEFAULT_COUNTRIES set. Raises on failure."""
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    if not (name or "").strip():
        raise ValueError("Name is required.")
    _client(service=True).auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"full_name": name.strip()},
        "app_metadata": {"role": role,
                         "countries": list(countries) if countries is not None
                         else list(DEFAULT_COUNTRIES)},
    })


def set_role(user_id: str, role: str):
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    _set_app_metadata(user_id, role=role)


def set_countries(user_id: str, countries):
    """Set which country markets a user may open (app_metadata.countries)."""
    _set_app_metadata(user_id, countries=list(countries))


def request_beta(user_id: str) -> str:
    """A signed-in user asks to join the beta program (profile dialog). Stored
    as app_metadata.beta_requested = ISO date — written server-side with the
    service key, so users still can't touch their own role. Returns the stamp."""
    import datetime as _dt
    stamp = _dt.date.today().isoformat()
    _set_app_metadata(user_id, beta_requested=stamp)
    return stamp


def resolve_beta_request(user_id: str, accept: bool):
    """Admin decision on a pending beta request: accept switches the user's
    role to 'beta'; either way the pending flag is cleared (a declined user may
    ask again from their profile). Admins can always change the role later via
    set_role — this is just the request workflow."""
    changes: dict = {"beta_requested": None}
    if accept:
        changes["role"] = "beta"
    _set_app_metadata(user_id, **changes)


def set_password(user_id: str, new_password: str):
    """Set a user's password (admin action; also used to change your own)."""
    _client(service=True).auth.admin.update_user_by_id(
        user_id, {"password": new_password})


def delete_user(user_id: str):
    _client(service=True).auth.admin.delete_user(user_id)


# Sentinel written into beta_feedback.user_id (NOT NULL) when the author
# deletes their account: keeps the report text for product history while
# unlinking it from any real user — exactly what the privacy policy promises.
ANON_USER_ID = "00000000-0000-0000-0000-000000000000"


def delete_own_account(user_id: str) -> str | None:
    """Self-service account deletion (profile dialog on the landing page).

    Order matters: first anonymise the user's beta_feedback rows (user_id →
    ANON_USER_ID, email + contact permission cleared), then delete the auth
    user. Refuses the bootstrap 'master' account and the seeded passwordless
    test users (the bug-hunter agent signs in as those — a self-service
    delete must never be able to remove shared fixtures). The UI hides the
    control in the same cases; this is the server-side backstop.
    Returns an error string, or None on success."""
    try:
        cur = _client(service=True).auth.admin.get_user_by_id(user_id)
        u = getattr(cur, "user", None)
        if u is None:
            return "Account not found."
        if (u.email or "").endswith("@" + TEST_LOGIN_DOMAIN):
            return "Shared test accounts cannot be deleted."
        if (u.app_metadata or {}).get("role") == "master":
            return "The master account cannot be deleted from the profile."
        _client(service=True).table("beta_feedback").update(
            {"user_id": ANON_USER_ID, "user_email": None,
             "permission_to_contact": False}
        ).eq("user_id", user_id).execute()
        _client(service=True).auth.admin.delete_user(user_id)
        return None
    except Exception as e:  # noqa: BLE001
        return str(e)
