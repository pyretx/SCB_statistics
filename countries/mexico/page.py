"""Thin page loader — lets other pages link to Mexico client-side."""
from countries.mexico.config import CONFIG
from core.page import render_country

render_country(CONFIG)
