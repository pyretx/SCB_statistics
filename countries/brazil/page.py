"""Thin page loader — lets other pages link to Brazil client-side."""
from countries.brazil.config import CONFIG
from core.page import render_country

render_country(CONFIG)
