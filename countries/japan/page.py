"""Thin page loader — lets other pages link to Japan client-side."""
from countries.japan.config import CONFIG
from core.page import render_country

render_country(CONFIG)
