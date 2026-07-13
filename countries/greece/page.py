"""Thin page loader — lets other pages link to Greece client-side."""
from countries.greece.config import CONFIG
from core.page import render_country

render_country(CONFIG)
