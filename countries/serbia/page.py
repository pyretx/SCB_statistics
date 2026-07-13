"""Thin page loader — lets other pages link to Serbia client-side."""
from countries.serbia.config import CONFIG
from core.page import render_country

render_country(CONFIG)
