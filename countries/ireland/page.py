"""Thin page loader — lets other pages link to Ireland client-side."""
from countries.ireland.config import CONFIG
from core.page import render_country

render_country(CONFIG)
