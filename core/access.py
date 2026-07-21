"""Access-tier gate for country pages (see docs/architecture.md).

Tiers: public (anyone — Sweden/France) · registered (any signed-in user, still
free — the "Live" countries) · internal (admin/master only) · restricted (the
BETA tier: admins, the global "beta" role, or a per-country
app_metadata.countries grant). Releasing or gating a country is a config change
(cfg.access), never code. Signed-out visitors only ever SEE the public
countries — landing tiles and the sidebar switcher hide the rest.
"""
from __future__ import annotations

import streamlit as st

_ADMIN_ROLES = ("admin", "master")


def _user():
    return st.session_state.get("auth_user")


def is_beta_or_admin(cfg) -> bool:
    """Whether the current user may see beta-gated features (e.g. the
    import-overlay tab): admin/master, the global "beta" role, or a per-country
    beta tester — a user whose app_metadata.countries grant includes this
    country (the same definition the 'restricted' access tier uses)."""
    u = _user()
    if u is None:
        return False
    role = u.get("role", "")
    if role in _ADMIN_ROLES or role == "beta":
        return True
    return cfg.slug in (u.get("countries") or [])


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
        # The BETA tier — admins, the global "beta" role, per-country testers.
        return is_beta_or_admin(cfg)
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
    # Highest-intent moment for the access-level page: the user just hit the
    # boundary it explains. Guarded — the gate must never break on a nav issue.
    try:
        st.page_link("plans.py", label="See what each access level includes →")
    except Exception:
        pass
    st.stop()
    return False
