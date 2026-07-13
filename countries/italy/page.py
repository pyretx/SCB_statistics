"""Thin page loader — lets other pages link to Italy client-side."""
from countries.italy.config import CONFIG
from core.page import render_country

render_country(CONFIG)
