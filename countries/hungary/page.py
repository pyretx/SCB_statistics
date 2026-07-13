"""Thin page loader — lets other pages link to Hungary client-side."""
from countries.hungary.config import CONFIG
from core.page import render_country

render_country(CONFIG)
