"""Slovenia config — SURS PxWeb table 0711335S.

Full P10·P25·median·P75·P90 + mean by SKP-08 (ISCO-08) occupation × sex × year
(2011–2022), gross monthly EUR — the richest set after the UK. access='restricted'
→ BETA.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import SloveniaProvider, _load

_prov = SloveniaProvider()
_YR = latest_year()
_YEARS = _load().get("years") or [2011, _YR]
_CAPTION = "SURS · Earnings by occupation (SKP-08 / ISCO) · gross monthly, EUR"

_GUIDE_EN = {
    "title": "How to use the Slovenian Salary Explorer",
    "source": f"Statistical Office of Slovenia (SURS) · 0711335S · {_YR}",
    "intro": "Look up Slovenian salaries by occupation — official data from SURS "
             "(Structure of Earnings). This guide covers finding occupations and "
             "reading the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Search", "Pick one or more occupations in the left sidebar, then press "
                   "the blue Search button."),
        ("Drill down", "Narrow step by step through the SKP-08 (ISCO) hierarchy "
                       "(1 → 2 → 3 → 4 digit)."),
        ("Read the results", "Explore the tabs — the P10–P90 distribution, the "
                             "2011→ trend, By gender and the leaderboard."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches names "
                       "and SKP codes."),
        ("Code browser", "Open the Code browser to explore the whole SKP-08 tree."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection to "
                      "merge them into one series."),
    ],
    "charts_title": "Reading the wage charts",
    "charts_intro": "SURS publishes the full spread — a wide P10–P90 gap means pay "
                    "varies a lot in that job (the average is a separate ♦ marker):",
    "pcts": [("P10", 22, "10% earn less"), ("P25", 36, "a quarter earn less"),
             ("MED", 52, "half earn less"), ("P75", 68, "a quarter earn more"),
             ("P90", 84, "only 10% earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are GROSS MONTHLY earnings (EUR).",
        "The By-gender tab splits women vs men; the trend covers 2011–2022, with a "
        "forward projection.",
        "Small occupation cells are suppressed by SURS — a missing figure is not an "
        "error.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance."),
        ("Salary distribution", "The P10–P90 chart + the 2011→ trend, raw data + CSV."),
        ("Where do I stand?", "Enter a monthly salary and see its percentile."),
        ("Leaderboard", "Ranks occupations by pay or the gender gap."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "All figures are from the SURS SiStat table 0711335S.",
}

CONFIG = CountryConfig(
    slug="slovenia",
    name="Slovenia",
    native="Slovenija",
    iso="si",
    eyebrow="OFFICIAL STATISTICS · SLOVENIA",
    source_name="Statistical Office of Slovenia (SURS)",
    source_url="https://pxweb.stat.si/SiStatData/pxweb/en/Data/-/0711335S.px",
    caption=_CAPTION,
    currency="EUR", currency_suffix="€", money_prefix=False, period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True,        # P10 · P25 · median · P75 · P90
        has_occupation_hierarchy=True,          # SKP-08 / ISCO 1→4 digit
        has_mean=True, has_median=True, has_sex=True,
        has_trend=True,                         # 2011–2022
        has_leaderboard=True, leaderboard_scope=2,
        sectors=(),
        year_range=(min(_YEARS), max(_YEARS)),
    ),
    tabs=("overview", "distribution", "where", "leaderboard", "sex", "import_overlay"),
    access="registered",                        # LIVE — any signed-in user
    fetch_mode="search",
    landing=True,
    classification="SKP-08",
    bullets=(
        "P10–P90 + mean · ~600 occupations (SKP-08/ISCO)",
        "Gender breakdown & 2011–2022 trend",
        f"Gross monthly earnings · SURS · {_YR}",
    ),
    labels={"badge": "Live", "source_short": "SURS · official"},
    languages=(("EN", "English"),),
    i18n={"EN": {
        "title": "Slovenian Salary Explorer",
        "caption": _CAPTION,
        "grp_1": "Major group", "grp_2": "Sub-major group", "grp_3": "Minor group",
        "all_grp_1": "— All major groups —", "all_grp_2": "— All sub-major groups —",
        "all_grp_3": "— All minor groups —",
        "brlvl_1": "Major group", "brlvl_2": "Sub-major group",
        "brlvl_3": "Minor group", "brlvl_4": "Unit group",
    }},
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
