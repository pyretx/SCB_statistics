"""Thin page loader — lets other pages link to Romania client-side."""
from countries.romania.config import CONFIG
from core.page import render_country

render_country(CONFIG)
