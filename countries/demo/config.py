"""Demo country config — the whole 'add a country' surface is this file + the
provider. Access is 'internal' so only admin/master accounts can open it."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .provider import DemoProvider

CONFIG = CountryConfig(
    slug="demo",
    name="Demo Country",
    native="Demo",
    iso="se",                                   # reuse the SE flag asset for the demo
    eyebrow="FRAMEWORK DEMO · INTERNAL",
    source_name="Demo",
    source_url="",
    caption="Framework skeleton demo — sample data, admin-only.",
    currency="SEK", currency_suffix="kr", period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True, has_mean=True, has_median=True,
        has_sex=True, sectors=("all",), year_range=(2020, 2025),
    ),
    tabs=("overview",),
    access="internal",
    fetch_mode="reactive",
    i18n={"EN": {"title": "Framework Demo Explorer", "sector_all": "All sectors"}},
    provider=DemoProvider(),
)
