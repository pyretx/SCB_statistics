"""Thin page loader — lets other pages link to Australia client-side."""
from countries.australia.config import CONFIG
from core.page import render_country

render_country(CONFIG)
