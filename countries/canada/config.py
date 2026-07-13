"""Canada config — Statistics Canada 14-10-0417 (employee wages by occupation).

Average + median gross MONTHLY wages by NOC occupation × gender, with the 10
provinces as REAL region data (By-region tab, like the US states). Full-time
employees, age 15+, latest year. No percentiles/trend in this cut.
access='restricted' → BETA.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import CanadaProvider

_prov = CanadaProvider()
_YR = latest_year()
_CAPTION = ("Statistics Canada · Employee wages by occupation (NOC) · gross "
            "monthly, full-time")

_GUIDE_EN = {
    "title": "How to use the Canadian Salary Explorer",
    "source": f"Statistics Canada · Table 14-10-0417 (NOC) · {_YR}",
    "intro": "Look up Canadian wages by occupation — official data from Statistics "
             "Canada's employee-wage estimates. This guide covers finding "
             "occupations and reading the figures.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Search", "Pick one or more occupations in the left sidebar, then press "
                   "the blue Search button."),
        ("Drill down", "Narrow step by step through the NOC hierarchy (broad "
                       "category → group → detailed)."),
        ("Read the results", "Explore the tabs on the right, including By region "
                             "(all 10 provinces) and By gender."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches "
                       "occupation names."),
        ("Code browser", "Open the Code browser to explore the whole NOC tree."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection to "
                      "merge them into one series."),
    ],
    "charts_title": "Reading the figures",
    "charts_intro": "Statistics Canada publishes the average and the median wage "
                    "per occupation:",
    "pcts": [("MEAN", 52, "arithmetic average"),
             ("MED", 52, "the middle earner")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are gross MONTHLY wages — the official WEEKLY wage × 52 / 12 — for "
        "full-time employees aged 15+.",
        "The By-region tab shows each province's actual wage for the occupation "
        "(real data, not an estimate); By gender splits women vs men.",
        "This table has the average and median only — no percentiles or trend by "
        "occupation — so those views don't appear.",
        "Small cells are suppressed by Statistics Canada — a missing figure is not "
        "an error.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The average and median at a glance for each occupation."),
        ("Basic statistics", "A per-occupation summary table with CSV export."),
        ("Leaderboard", "Ranks occupations by average or median pay."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
        ("By region", "Compare a province's actual wage against the national "
                      "figure — real data."),
    ],
    "footer": "All figures are from Statistics Canada table 14-10-0417, updated "
              "annually.",
}

CONFIG = CountryConfig(
    slug="canada",
    name="Canada",
    native="Canada",
    iso="ca",
    eyebrow="OFFICIAL STATISTICS · CANADA",
    source_name="Statistics Canada",
    source_url="https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410041701",
    caption=_CAPTION,
    currency="CAD", currency_suffix="$", money_prefix=True, period="monthly",
    capabilities=Capabilities(
        has_occupation_hierarchy=True,          # NOC (synthetic prefix tree 2/4/6)
        has_mean=True, has_median=True, has_sex=True,
        has_trend=False,
        has_leaderboard=True, leaderboard_scope=2,   # NOC broad category
        has_region_data=True,                   # real per-province → By-region tab
        sectors=(),                             # national default; provinces in By-region
        year_range=(_YR, _YR),
    ),
    tabs=("overview", "stats", "leaderboard", "sex", "region_sim"),
    access="registered",                        # LIVE — any signed-in user
    fetch_mode="search",
    landing=True,
    classification="NOC 2021",
    bullets=(
        "Mean, median & gender split · ~430 occupations (NOC)",
        "Real per-province data (all 10 provinces)",
        f"Gross monthly wages · Statistics Canada · {_YR}",
    ),
    labels={"badge": "Live", "source_short": "StatCan · official"},
    languages=(("EN", "English"),),
    i18n={"EN": {
        "title": "Canadian Salary Explorer",
        "caption": _CAPTION,
        "grp_1": "Broad category", "grp_2": "Occupation group",
        "all_grp_1": "— All broad categories —", "all_grp_2": "— All groups —",
        "brlvl_2": "Broad category", "brlvl_4": "Occupation group",
        "brlvl_6": "Detailed occupation",
    }},
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
