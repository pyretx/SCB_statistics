"""Thin page loader — lets other pages link to Canada client-side."""
from countries.canada.config import CONFIG
from core.page import render_country

render_country(CONFIG)
