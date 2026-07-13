"""Country registry — the single list `app.py` builds its nav from.

Adding a country = add its CountryConfig here (plus its config/provider module).
Imports are lazy so a broken country module can't take down the whole app at
import time, and to avoid import-order coupling.
"""
from __future__ import annotations

import importlib

from .access import can_open

# Framework-driven countries, in nav order. Add a country by dropping its module
# under countries/<name>/ (config.py exposing CONFIG) and listing it here.
# se2/fr2 ARE the public Sweden/France pages (serving /sweden + /france); the
# legacy builds stay registered admin-only in app.py (/sweden-old, /france-old).
# NOTE: module dir MUST equal the config's slug (app.py builds page paths from it).
_COUNTRY_MODULES = ["demo", "se2", "fr2", "norway", "us", "denmark",
                    "iceland", "finland", "estonia", "netherlands", "uk", "germany",
                    "canada", "newzealand"]


def all_countries() -> list:
    out = []
    for name in _COUNTRY_MODULES:
        try:
            out.append(importlib.import_module(f"countries.{name}.config").CONFIG)
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
