"""Country registry — the single list `app.py` builds its nav from.

Adding a country = add its CountryConfig here (plus its config/provider module).
Imports are lazy so a broken country module can't take down the whole app at
import time, and to avoid import-order coupling.
"""
from __future__ import annotations

from .access import can_open


def all_countries() -> list:
    """Every framework-driven country. (Legacy Sweden/France pages are still
    registered directly in app.py and are NOT in here yet — Phase 3/5.)"""
    out = []
    try:
        from countries.demo.config import CONFIG as DEMO
        out.append(DEMO)
    except Exception:
        pass
    return out


def get(slug: str):
    for c in all_countries():
        if c.slug == slug:
            return c
    return None


def visible_for_current_user() -> list:
    """Countries the signed-in user is allowed to open (for switcher/landing)."""
    return [c for c in all_countries() if can_open(c)]
