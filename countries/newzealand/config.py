"""New Zealand config — Stats NZ ADE dataflow INC_INC_004.

Median + average gross MONTHLY earnings by ANZSCO major-group occupation × sex,
with a 2009→ trend (median/mean weekly × 52/12). Wage & salary earners, all ages.
Occupations are the 9 ANZSCO major groups (flat, no percentiles/region).
access='restricted' → BETA.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import NewZealandProvider, _load

_prov = NewZealandProvider()
_YR = latest_year()
_YEARS = _load().get("years") or [_YR]
_CAPTION = ("Stats NZ · Earnings by occupation (ANZSCO) · gross monthly, wage & "
            "salary earners")

_GUIDE_EN = {
    "title": "How to use the New Zealand Salary Explorer",
    "source": f"Stats NZ – Tatauranga Aotearoa · Income (INC_INC_004) · {_YR}",
    "intro": "Look up New Zealand earnings by occupation — official data from Stats "
             "NZ's income statistics (Aotearoa Data Explorer).",
    "steps_title": "Getting started",
    "steps": [
        ("Search", "Pick one or more occupations in the left sidebar, then press "
                   "the blue Search button."),
        ("Read the results", "Explore the tabs on the right, including the trend "
                             "since 2009 and By gender."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box."),
        ("Occupations", "The data covers the 9 ANZSCO major occupation groups."),
    ],
    "charts_title": "Reading the figures",
    "charts_intro": "Stats NZ publishes the median and the average earnings per "
                    "occupation:",
    "pcts": [("MEAN", 52, "average earnings"), ("MED", 52, "the middle earner")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are gross MONTHLY — the median/average WEEKLY earnings from the "
        "main wage & salary job × 52 / 12, all ages.",
        "Occupations are the 9 ANZSCO major groups — this Stats NZ series has no "
        "finer occupation, percentile or regional breakdown.",
        "The By-gender tab splits women vs men; the trend covers 2009 onward.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The median and average at a glance."),
        ("Salary distribution", "Median & mean + the 2009→ trend and a forward "
                                "projection."),
        ("Basic statistics", "A per-occupation summary table with CSV export."),
        ("Leaderboard", "Ranks the occupation groups by pay."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "All figures are from Stats NZ (Aotearoa Data Explorer, INC_INC_004).",
}

CONFIG = CountryConfig(
    slug="newzealand",
    name="New Zealand",
    native="Aotearoa",
    iso="nz",
    eyebrow="OFFICIAL STATISTICS · NEW ZEALAND",
    source_name="Stats NZ – Tatauranga Aotearoa",
    source_url="https://explore.data.stats.govt.nz/",
    caption=_CAPTION,
    currency="NZD", currency_suffix="$", money_prefix=True, period="monthly",
    capabilities=Capabilities(
        has_occupation_hierarchy=False,          # 9 flat ANZSCO major groups
        has_mean=True, has_median=True, has_sex=True,
        has_trend=True,                          # 2009→
        has_leaderboard=True, leaderboard_scope=1,
        sectors=(),
        year_range=(min(_YEARS), max(_YEARS)),
    ),
    tabs=("overview", "distribution", "stats", "leaderboard", "sex"),
    access="restricted",                         # BETA
    fetch_mode="search",
    landing=True,
    classification="ANZSCO",
    bullets=(
        "Median, mean & gender split · 9 occupation groups (ANZSCO)",
        "Trend since 2009 · forward projection",
        f"Gross monthly earnings · Stats NZ · {_YR}",
    ),
    labels={"badge": "Beta", "source_short": "Stats NZ · official"},
    languages=(("EN", "English"),),
    i18n={"EN": {"title": "New Zealand Salary Explorer", "caption": _CAPTION}},
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
