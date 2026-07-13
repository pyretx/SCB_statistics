"""Thin page loader — lets other pages link to Switzerland client-side."""
from countries.switzerland.config import CONFIG
from core.page import render_country

render_country(CONFIG)
