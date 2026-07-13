"""Thin page loader — lets other pages link to New Zealand client-side."""
from countries.newzealand.config import CONFIG
from core.page import render_country

render_country(CONFIG)
