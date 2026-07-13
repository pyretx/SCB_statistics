"""Thin page loader — lets other pages link to Lithuania client-side."""
from countries.lithuania.config import CONFIG
from core.page import render_country

render_country(CONFIG)
