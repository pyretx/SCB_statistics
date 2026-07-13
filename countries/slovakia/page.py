"""Thin page loader — lets other pages link to Slovakia client-side."""
from countries.slovakia.config import CONFIG
from core.page import render_country

render_country(CONFIG)
