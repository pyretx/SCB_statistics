"""Thin page loader (see countries/demo/page.py) — lets other pages link to
Norway client-side, preserving the session."""
from countries.norway.config import CONFIG
from core.page import render_country

render_country(CONFIG)
