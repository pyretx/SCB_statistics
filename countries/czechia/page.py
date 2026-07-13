"""Thin page loader — lets other pages link to Czechia client-side."""
from countries.czechia.config import CONFIG
from core.page import render_country

render_country(CONFIG)
