"""Thin page loader (see countries/norway/page.py) — lets other pages link to
the US client-side, preserving the session."""
from countries.us.config import CONFIG
from core.page import render_country

render_country(CONFIG)
