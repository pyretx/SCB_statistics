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
