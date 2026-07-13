"""Thin page loader — lets other pages link to Spain client-side."""
from countries.spain.config import CONFIG
from core.page import render_country

render_country(CONFIG)
