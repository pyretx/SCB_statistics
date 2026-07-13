"""Thin page loader — lets other pages link to Portugal client-side."""
from countries.portugal.config import CONFIG
from core.page import render_country

render_country(CONFIG)
