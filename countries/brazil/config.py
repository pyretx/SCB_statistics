"""Brazil config — IBGE PNAD Contínua (table 9457).

Estimated gross MONTHLY earnings (avg hourly × full-time month) by the 10 ISCO
major occupational groups, with a 2012→ trend. Average only; no median, sex,
percentiles or region in this series. EN + Português. access='restricted' → BETA.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import BrazilProvider, _load

_prov = BrazilProvider()
_YR = latest_year()
_YEARS = _load().get("years") or [2012, _YR]
_CAPTION = ("IBGE · PNAD Contínua · estimated gross monthly earnings by occupation "
            "group (ISCO)")

_GUIDE_EN = {
    "title": "How to use the Brazilian Salary Explorer",
    "source": f"IBGE – PNAD Contínua · table 9457 · {_YR}",
    "intro": "Look up Brazilian earnings by occupation — official data from IBGE's "
             "continuous household survey (PNAD Contínua).",
    "steps_title": "Getting started",
    "steps": [
        ("Search", "Pick one or more occupation groups in the left sidebar, then "
                   "press the blue Search button."),
        ("Read the results", "Explore the tabs — including the trend since 2012."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box."),
        ("Occupations", "The data covers the 10 ISCO major occupation groups."),
    ],
    "charts_title": "Reading the figures",
    "charts_intro": "IBGE publishes the average earnings per occupation group:",
    "pcts": [("MEAN", 52, "average earnings")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are an ESTIMATED gross MONTHLY amount — IBGE's average HOURLY "
        "earnings × a standard full-time month (44 h/week, ≈190.7 h). It is an "
        "estimate; IBGE publishes the hourly figure.",
        "Occupations are the 10 ISCO major groups — this IBGE series has no finer "
        "occupation, median, percentile, sex or regional breakdown.",
        "The trend covers 2012 onward, with an optional forward projection.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The average at a glance for each occupation group."),
        ("Salary distribution", "The average + the 2012→ trend and a projection."),
        ("Basic statistics", "A per-occupation summary table with CSV export."),
        ("Leaderboard", "Ranks the occupation groups by pay."),
    ],
    "footer": "All figures are from IBGE PNAD Contínua (SIDRA table 9457).",
}

CONFIG = CountryConfig(
    slug="brazil",
    name="Brazil",
    native="Brasil",
    iso="br",
    eyebrow="OFFICIAL STATISTICS · BRAZIL",
    source_name="IBGE",
    source_url="https://sidra.ibge.gov.br/tabela/9457",
    caption=_CAPTION,
    currency="BRL", currency_suffix="R$", money_prefix=True, period="monthly",
    capabilities=Capabilities(
        has_occupation_hierarchy=False,          # 10 flat ISCO major groups
        has_mean=True, has_median=False, has_sex=False,
        has_trend=True,                          # 2012→
        has_leaderboard=True, leaderboard_scope=1,
        sectors=(),
        year_range=(min(_YEARS), max(_YEARS)),
    ),
    tabs=("overview", "distribution", "stats", "leaderboard"),
    access="restricted",                         # BETA
    fetch_mode="search",
    landing=True,
    classification="ISCO-08 major groups",
    bullets=(
        "Average earnings · 10 occupation groups (ISCO)",
        "Trend since 2012 · forward projection",
        f"Est. gross monthly earnings · IBGE · {_YR}",
    ),
    labels={"badge": "Beta", "source_short": "IBGE · official"},
    languages=(("EN", "English"), ("PT", "Português")),
    i18n={
        "EN": {"title": "Brazilian Salary Explorer", "caption": _CAPTION},
        "PT": {"title": "Explorador de Salários do Brasil",
               "caption": "IBGE · PNAD Contínua · rendimento mensal estimado por "
                          "grupamento ocupacional (ISCO)"},
    },
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
