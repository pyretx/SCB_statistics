"""Norway config — the entire country-specific surface (this + provider.py).
access='internal' → only admin/master accounts can open /norway while it's WIP."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .provider import NorwayProvider

CONFIG = CountryConfig(
    slug="norway",
    name="Norway",
    native="Norge",
    iso="no",
    eyebrow="OFFICIAL STATISTICS · NORWAY",
    source_name="Statistics Norway (SSB)",
    source_url="https://data.ssb.no/api/v0/en/table/11418",
    caption="Statistics Norway (SSB) · Monthly earnings by occupation (STYRK-08)",
    currency="NOK", currency_suffix="kr", period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=False,   # SSB 11418 has quartiles, not P10/P90
        has_mean=True, has_median=True, has_sex=True,
        sectors=("all", "private", "local", "central"),
        year_range=(2015, 2024),
    ),
    tabs=("overview",),
    # restricted = admin/master OR a user explicitly granted this country
    # (app_metadata.countries includes "norway" — a beta tester). Everyone else
    # sees the landing tile as Locked.
    access="restricted",
    fetch_mode="search",                    # commit-on-Search, like Sweden
    landing=True,                           # show a gated tile on the landing page
    bullets=(
        "Mean &amp; median salary · ~400 occupations (STYRK-08)",
        "Sector &amp; sex breakdowns · quartiles",
        "Monthly earnings · 2015–2024",
    ),
    labels={
        "title": "Norwegian Salary Explorer",
        "badge": "Beta",
        "source_short": "SSB · official",
        "sector_all": "All sectors",
        "sector_private": "Private + public enterprises",
        "sector_local": "Local government",
        "sector_central": "Central government",
    },
    provider=NorwayProvider(),
)
