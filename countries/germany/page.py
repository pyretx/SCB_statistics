"""Thin page loader (see countries/demo/page.py) — lets other pages link to
Germany client-side, preserving the session."""
from countries.germany.config import CONFIG
from core.page import render_country

render_country(CONFIG)
