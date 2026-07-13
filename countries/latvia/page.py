"""Thin page loader — lets other pages link to Latvia client-side."""
from countries.latvia.config import CONFIG
from core.page import render_country

render_country(CONFIG)
