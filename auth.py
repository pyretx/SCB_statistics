"""Supabase-backed authentication + user management for the SCB Salary Explorer.

Roles live in Supabase Auth `app_metadata.role` (master | admin | standard).
`app_metadata` is writable only with the service_role key, so users cannot
change their own role. The service_role key stays server-side (st.secrets).
"""
import os
import tomllib
import streamlit as st
from supabase import create_client, Client

ROLES = ("standard", "admin")  # roles an admin may assign (master is bootstrap-only)

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
    return create_client(cfg["url"], key)


def country_switcher(current: str):
    """Compact country switcher for the sidebar, next to the logo. ``current`` is
    'sweden' or 'france'. Sweden/France are real page-links (client-side nav, so
    the session/login is preserved); the US is shown greyed ('soon'). Access
    gating (who may open which country) will hook in here later."""
    label = {"sweden": "Sweden", "france": "France"}.get(current, "Country")
    with st.popover(label, use_container_width=True):
        st.page_link("scb_salaries.py", label="Sweden", icon="🇸🇪")
        st.page_link("france.py",       label="France", icon="🇫🇷")
        st.markdown('<div class="cc-soon">🇺🇸&nbsp; United States · soon</div>',
                    unsafe_allow_html=True)


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
        st.session_state.pop("auth_user", None)
        st.rerun()


def sign_in(email: str, password: str):
    """Return (user_dict, error). user_dict = {id, email, role}."""
    try:
        res = _client(service=False).auth.sign_in_with_password(
            {"email": email, "password": password})
        u = res.user
        role = (u.app_metadata or {}).get("role", "standard")
        return {"id": u.id, "email": u.email, "role": role}, None
    except Exception as e:
        return None, str(e)


def sign_up(email: str, password: str, full_name: str = ""):
    """Public self-service registration (uses the anon/public client, not the
    admin API). New accounts default to role 'standard' (no app_metadata is
    set here — only the service-role client may set it). Depends on the
    Supabase project having "Enable sign ups" turned on, and on whether email
    confirmation is required there (both are dashboard settings, not code).
    Returns (user_dict_or_None, error_str_or_None)."""
    try:
        res = _client(service=False).auth.sign_up({
            "email": email, "password": password,
            "options": {"data": {"full_name": full_name}} if full_name else {},
        })
        u = res.user
        if u is None:
            return None, "Sign-up did not return a user."
        role = (u.app_metadata or {}).get("role", "standard")
        return {"id": u.id, "email": u.email, "role": role}, None
    except Exception as e:
        return None, str(e)


def list_users() -> list[dict]:
    resp = _client(service=True).auth.admin.list_users()
    users = resp if isinstance(resp, list) else getattr(resp, "users", resp)
    out = []
    for u in users:
        out.append({
            "id":    u.id,
            "email": u.email,
            "role":  (u.app_metadata or {}).get("role", "standard"),
        })
    out.sort(key=lambda r: ({"master": 0, "admin": 1, "standard": 2}.get(r["role"], 3), r["email"]))
    return out


def create_user(email: str, password: str, role: str):
    """Create an auto-confirmed user with the given role. Raises on failure."""
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    _client(service=True).auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "app_metadata": {"role": role},
    })


def set_role(user_id: str, role: str):
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    _client(service=True).auth.admin.update_user_by_id(
        user_id, {"app_metadata": {"role": role}})


def set_password(user_id: str, new_password: str):
    """Set a user's password (admin action; also used to change your own)."""
    _client(service=True).auth.admin.update_user_by_id(
        user_id, {"password": new_password})


def delete_user(user_id: str):
    _client(service=True).auth.admin.delete_user(user_id)
