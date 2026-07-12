"""Thin page loader (see countries/demo/page.py) — lets other pages link to the
Netherlands client-side, preserving the session."""
from countries.netherlands.config import CONFIG
from core.page import render_country

render_country(CONFIG)
