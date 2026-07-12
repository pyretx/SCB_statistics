"""Thin page loader (see countries/demo/page.py) — lets other pages link to
Denmark client-side, preserving the session."""
from countries.denmark.config import CONFIG
from core.page import render_country

render_country(CONFIG)
