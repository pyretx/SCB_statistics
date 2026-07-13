"""Thin page loader — lets other pages link to Bulgaria client-side."""
from countries.bulgaria.config import CONFIG
from core.page import render_country

render_country(CONFIG)
