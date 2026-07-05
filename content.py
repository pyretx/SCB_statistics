"""Centralised, editable page content.

All user-facing TEXT for a page — headings, labels, button/placeholder text,
help, empty/error messages, source & methodology notes — lives in a TOML file
under ``content/``, NOT in the page code. Edit the .toml and rerun; no code
changes, no redeploy of logic.

    import content
    C = content.load("home")
    st.header(C["hero"]["title"])

The section taxonomy is shared so country pages can follow the same shape:
    brand · header · hero · kpis · countries · filters · charts · tables ·
    messages · source · help · footer
A page simply uses the sections it needs (the home page uses brand/header/hero/
countries/footer; a country data page would add filters/charts/tables/…).
"""
from __future__ import annotations

import os
import tomllib

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")


def load(name: str) -> dict:
    """Read ``content/<name>.toml`` → nested dict.

    Deliberately NOT cached: the files are tiny, so re-reading once per rerun is
    free and means text edits appear immediately (no server restart)."""
    path = os.path.join(_DIR, f"{name}.toml")
    with open(path, "rb") as f:
        return tomllib.load(f)
