"""Australia config — ABS Employee Earnings and Hours (cube 11).

Average gross MONTHLY earnings by detailed ANZSCO occupation × sex (mean only —
no median/percentiles/trend/region in the occupation cube). access='restricted'
→ BETA.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import AustraliaProvider

_prov = AustraliaProvider()
_YR = latest_year()
_CAPTION = ("Australian Bureau of Statistics · Employee Earnings and Hours · "
            "average monthly earnings by occupation (ANZSCO)")

_GUIDE_EN = {
    "title": "How to use the Australian Salary Explorer",
    "source": f"Australian Bureau of Statistics · EEH (cat 6306.0) · May {_YR}",
    "intro": "Look up Australian earnings by occupation — official data from the ABS "
             "Employee Earnings and Hours survey.",
    "steps_title": "Getting started",
    "steps": [
        ("Search", "Pick one or more occupations in the left sidebar, then press "
                   "the blue Search button."),
        ("Read the results", "Explore the tabs on the right, including By gender."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches ANZSCO "
                       "occupation names and codes."),
        ("Occupations", "~360 detailed ANZSCO (4-digit) occupations."),
    ],
    "charts_title": "Reading the figures",
    "charts_intro": "The ABS occupation cube publishes the average weekly earnings "
                    "per occupation:",
    "pcts": [("MEAN", 52, "average weekly earnings")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are gross MONTHLY — average WEEKLY total cash earnings × 52 / 12, "
        "all employees, May reference period.",
        "The occupation cube has the average only — no median, percentiles, trend "
        "or region — so those views don't appear.",
        "The By-gender tab splits women (females) vs men (males).",
        "Small cells are suppressed by the ABS — a missing figure is not an error.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The average at a glance for each occupation."),
        ("Basic statistics", "A per-occupation summary table with CSV export."),
        ("Leaderboard", "Ranks occupations by average pay."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "All figures are from the ABS Employee Earnings and Hours survey "
              "(cat 6306.0), data cube 11.",
}

CONFIG = CountryConfig(
    slug="australia",
    name="Australia",
    native="Australia",
    iso="au",
    eyebrow="OFFICIAL STATISTICS · AUSTRALIA",
    source_name="Australian Bureau of Statistics",
    source_url="https://www.abs.gov.au/statistics/labour/earnings-and-working-conditions/employee-earnings-and-hours-australia/latest-release",
    caption=_CAPTION,
    currency="AUD", currency_suffix="$", money_prefix=True, period="monthly",
    capabilities=Capabilities(
        has_occupation_hierarchy=False,          # ~360 flat ANZSCO 4-digit
        has_mean=True, has_median=False, has_sex=True,
        has_trend=False,
        has_leaderboard=True, leaderboard_scope=1,
        sectors=(),
        year_range=(_YR, _YR),
    ),
    tabs=("overview", "stats", "leaderboard", "sex"),
    access="registered",                         # LIVE — any signed-in user
    fetch_mode="search",
    landing=True,
    classification="ANZSCO",
    bullets=(
        "Average earnings & gender split · ~360 occupations (ANZSCO)",
        "Detailed 4-digit occupations",
        f"Gross monthly earnings · ABS EEH · May {_YR}",
    ),
    labels={"badge": "Live", "source_short": "ABS EEH · official"},
    languages=(("EN", "English"),),
    i18n={"EN": {"title": "Australian Salary Explorer", "caption": _CAPTION}},
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
