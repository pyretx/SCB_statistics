"""Access-tier gate for country pages (see docs/architecture.md).

Tiers: public (anyone) · registered (any signed-in user, still free) · internal
(admin/master only) · restricted (explicit app_metadata.countries allow-list).
Releasing or gating a country is a config change (cfg.access), never code.
"""
from __future__ import annotations

import streamlit as st

_ADMIN_ROLES = ("admin", "master")


def _user():
    return st.session_state.get("auth_user")


def can_open(cfg) -> bool:
    """Whether the current user may open this country page."""
    u = _user()
    role = (u or {}).get("role", "")
    access = getattr(cfg, "access", "internal")
    if access == "public":
        return True
    if access == "registered":
        return u is not None
    if access == "internal":
        return role in _ADMIN_ROLES
    if access == "restricted":
        allowed = (u or {}).get("countries", [])
        return role in _ADMIN_ROLES or cfg.slug in allowed
    return False


def require_access(cfg) -> bool:
    """Render a friendly gate + st.stop() when the user may not open ``cfg``.
    Returns True when access is granted (so callers can early-continue)."""
    if can_open(cfg):
        return True
    u = _user()
    if u is None:
        st.info(f"🔒 **{cfg.name}** requires you to sign in. "
                "Head to the home page to sign in or create a free account.")
    else:
        st.info(f"🔒 **{cfg.name}** isn't available on your account yet — "
                "it's still in development.")
    st.stop()
    return False
