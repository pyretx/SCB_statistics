"""Thin page loader so st.navigation and st.page_link can target this country by
file path — which lets other pages link to it *client-side* (no reload, session
preserved). The whole page is still driven by config + provider."""
from countries.demo.config import CONFIG
from core.page import render_country

render_country(CONFIG)
