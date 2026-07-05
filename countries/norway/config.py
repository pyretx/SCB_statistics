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
    access="internal",
    fetch_mode="search",                    # commit-on-Search, like Sweden
    labels={
        "title": "Norwegian Salary Explorer",
        "sector_all": "All sectors",
        "sector_private": "Private + public enterprises",
        "sector_local": "Local government",
        "sector_central": "Central government",
    },
    provider=NorwayProvider(),
)
