"""Thin page loader — lets other pages link to Belgium client-side."""
from countries.belgium.config import CONFIG
from core.page import render_country

render_country(CONFIG)
