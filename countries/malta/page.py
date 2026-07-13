"""Thin page loader — lets other pages link to Malta client-side."""
from countries.malta.config import CONFIG
from core.page import render_country

render_country(CONFIG)
