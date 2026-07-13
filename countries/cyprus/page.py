"""Thin page loader — lets other pages link to Cyprus client-side."""
from countries.cyprus.config import CONFIG
from core.page import render_country

render_country(CONFIG)
