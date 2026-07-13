"""Thin page loader — lets other pages link to Poland client-side."""
from countries.poland.config import CONFIG
from core.page import render_country

render_country(CONFIG)
