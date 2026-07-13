"""Thin page loader — lets other pages link to Austria client-side."""
from countries.austria.config import CONFIG
from core.page import render_country

render_country(CONFIG)
