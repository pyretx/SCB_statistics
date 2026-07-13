"""Thin page loader — lets other pages link to Luxembourg client-side."""
from countries.luxembourg.config import CONFIG
from core.page import render_country

render_country(CONFIG)
