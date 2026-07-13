"""Mexico config — INEGI ENOE microdata (computed offline).

Survey-weighted mean & median monthly occupational income by 10 ENOE occupation
groups × sex (from the ENOE microdata; no percentiles/trend/region in this cut).
EN + Español. access='restricted' → BETA.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import MexicoProvider, _load

_prov = MexicoProvider()
_YR = latest_year()
_PERIOD = _load().get("period_label", str(_YR))
_CAPTION = ("INEGI · ENOE · monthly occupational income by occupation group "
            "(SINCO-based)")

_GUIDE_EN = {
    "title": "How to use the Mexican Salary Explorer",
    "source": f"INEGI – ENOE microdata · {_PERIOD}",
    "intro": "Look up Mexican earnings by occupation — computed from INEGI's ENOE "
             "labour-force survey microdata (survey-weighted).",
    "steps_title": "Getting started",
    "steps": [
        ("Search", "Pick one or more occupation groups in the left sidebar, then "
                   "press the blue Search button."),
        ("Read the results", "Explore the tabs — including By gender."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box."),
        ("Occupations", "The data covers the 10 ENOE occupation groups (SINCO)."),
    ],
    "charts_title": "Reading the figures",
    "charts_intro": "The figures are the mean and the median monthly income per "
                    "occupation group:",
    "pcts": [("MEAN", 52, "average income"), ("MED", 52, "the middle earner")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are the survey-WEIGHTED mean and median MONTHLY occupational "
        "income (MXN) of employed people, computed from the ENOE microdata.",
        "Occupations are the 10 ENOE groups (coded from SINCO) — the survey has no "
        "finer public occupation, percentile or time-series cut here.",
        "The By-gender tab splits women vs men.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The mean and median at a glance for each occupation group."),
        ("Basic statistics", "A per-occupation summary table with CSV export."),
        ("Leaderboard", "Ranks the occupation groups by pay."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "Computed from INEGI ENOE microdata (SDEMT).",
}

CONFIG = CountryConfig(
    slug="mexico",
    name="Mexico",
    native="México",
    iso="mx",
    eyebrow="OFFICIAL STATISTICS · MEXICO",
    source_name="INEGI (ENOE)",
    source_url="https://www.inegi.org.mx/programas/enoe/15ymas/",
    caption=_CAPTION,
    currency="MXN", currency_suffix="$", money_prefix=True, period="monthly",
    capabilities=Capabilities(
        has_occupation_hierarchy=False,          # 10 flat ENOE occupation groups
        has_mean=True, has_median=True, has_sex=True,
        has_trend=False,
        has_leaderboard=True, leaderboard_scope=1,
        sectors=(),
        year_range=(_YR, _YR),
    ),
    tabs=("overview", "stats", "leaderboard", "sex"),
    access="restricted",                         # BETA
    fetch_mode="search",
    landing=True,
    classification="ENOE / SINCO groups",
    bullets=(
        "Mean, median & gender split · 10 occupation groups (SINCO)",
        "Computed from ENOE microdata (survey-weighted)",
        f"Monthly occupational income · INEGI · {_PERIOD}",
    ),
    labels={"badge": "Beta", "source_short": "INEGI ENOE · official"},
    languages=(("EN", "English"), ("ES", "Español")),
    i18n={
        "EN": {"title": "Mexican Salary Explorer", "caption": _CAPTION},
        "ES": {"title": "Explorador de Salarios de México",
               "caption": "INEGI · ENOE · ingreso mensual por grupo de ocupación "
                          "(basado en SINCO)"},
    },
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
