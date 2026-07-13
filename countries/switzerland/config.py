"""Switzerland config — FSO/BFS Earnings Structure Survey (LSE), cube _205.

Full P10·P25·median·P75·P90 by ISCO-08 occupation (1- and 2-digit) × sex ×
biennial year (2012→), standardised monthly gross wage in CHF — the richest set
alongside the UK / Slovenia. No mean in this cube. access='restricted' → BETA.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import SwitzerlandProvider, _load

_prov = SwitzerlandProvider()
_YR = latest_year()
_YEARS = _load().get("years") or [2012, _YR]
_CAPTION = "FSO · Earnings by occupation (ISCO-08) · gross monthly, CHF"

_GUIDE_EN = {
    "title": "How to use the Swiss Salary Explorer",
    "source": f"Swiss Federal Statistical Office (FSO) · LSE · {_YR}",
    "intro": "Look up Swiss salaries by occupation — official data from the FSO "
             "Earnings Structure Survey (LSE). This guide covers finding "
             "occupations and reading the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Search", "Pick one or more occupations in the left sidebar, then press "
                   "the blue Search button."),
        ("Drill down", "Narrow through the ISCO-08 hierarchy (1-digit major → "
                       "2-digit sub-major group)."),
        ("Read the results", "Explore the tabs — the P10–P90 distribution, the "
                             "2012→ trend, By gender and the leaderboard."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches names "
                       "and ISCO codes."),
        ("Code browser", "Open the Code browser to explore the whole ISCO-08 tree."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection to "
                      "merge them into one series."),
    ],
    "charts_title": "Reading the wage charts",
    "charts_intro": "The FSO publishes the full spread — a wide P10–P90 gap means "
                    "pay varies a lot in that job:",
    "pcts": [("P10", 22, "10% earn less"), ("P25", 36, "a quarter earn less"),
             ("MED", 52, "half earn less"), ("P75", 68, "a quarter earn more"),
             ("P90", 84, "only 10% earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are the STANDARDISED monthly gross wage (CHF, based on 4⅓ weeks / "
        "40 hours) — the LSE's comparable full-time-equivalent measure.",
        "The By-gender tab splits women vs men; the trend is biennial (2012–2024), "
        "with a forward projection.",
        "The survey has no mean in this cube — the median (central value) is the "
        "headline figure.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance."),
        ("Salary distribution", "The P10–P90 chart + the 2012→ trend, raw data + CSV."),
        ("Where do I stand?", "Enter a monthly salary and see its percentile."),
        ("Leaderboard", "Ranks occupations by pay or the gender gap."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "All figures are from the FSO STAT-TAB cube px-x-0304010000_205 (LSE).",
}

CONFIG = CountryConfig(
    slug="switzerland",
    name="Switzerland",
    native="Schweiz",
    iso="ch",
    eyebrow="OFFICIAL STATISTICS · SWITZERLAND",
    source_name="Swiss Federal Statistical Office (FSO)",
    source_url="https://www.pxweb.bfs.admin.ch/pxweb/de/px-x-0304010000_205",
    caption=_CAPTION,
    currency="CHF", currency_suffix="CHF", money_prefix=True, period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True,        # P10 · P25 · median · P75 · P90
        has_occupation_hierarchy=True,          # ISCO-08 1- and 2-digit
        has_mean=False, has_median=True, has_sex=True,
        has_trend=True,                         # biennial 2012–2024
        has_leaderboard=True, leaderboard_scope=1,
        sectors=(),
        year_range=(min(_YEARS), max(_YEARS)),
    ),
    tabs=("overview", "distribution", "where", "leaderboard", "sex", "import_overlay"),
    access="restricted",                        # BETA — admins + beta users only
    fetch_mode="search",
    landing=True,
    classification="ISCO-08",
    bullets=(
        "P10–P90 distribution · ISCO-08 occupations (1- & 2-digit)",
        "Gender breakdown & 2012–2024 biennial trend",
        f"Standardised gross monthly wage · FSO LSE · {_YR}",
    ),
    labels={"badge": "Beta", "source_short": "FSO LSE · official"},
    languages=(("EN", "English"), ("DE", "Deutsch")),
    i18n={
        "EN": {
            "title": "Swiss Salary Explorer",
            "caption": _CAPTION,
            "grp_1": "Major group", "grp_2": "Sub-major group",
            "all_grp_1": "— All major groups —", "all_grp_2": "— All sub-major groups —",
            "brlvl_1": "Major group", "brlvl_2": "Sub-major group",
        },
        "DE": {
            "title": "Schweizer Lohnrechner",
            "caption": "BFS · Lohn nach Beruf (ISCO-08) · Bruttomonatslohn, CHF",
            "grp_1": "Berufshauptgruppe", "grp_2": "Berufsgruppe",
            "all_grp_1": "— Alle Hauptgruppen —", "all_grp_2": "— Alle Berufsgruppen —",
            "brlvl_1": "Berufshauptgruppe", "brlvl_2": "Berufsgruppe",
        },
    },
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
