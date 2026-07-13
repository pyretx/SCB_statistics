"""Spain config — INE Encuesta de Estructura Salarial (table 70672).

Full P10·P25·median·P75·P90 + mean by CNO-11 (ISCO-08) occupation (major +
sub-major) × sex, gross monthly EUR (= official annual / 12), 2018. Single-year
snapshot (no trend). access='restricted' → BETA.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import SpainProvider, _load

_prov = SpainProvider()
_YR = latest_year()
_YEARS = _load().get("years") or [_YR]
_CAPTION = "INE · Earnings by occupation (CNO-11 / ISCO) · gross monthly, EUR"

_GUIDE_EN = {
    "title": "How to use the Spanish Salary Explorer",
    "source": f"Instituto Nacional de Estadística (INE) · SES · {_YR}",
    "intro": "Look up Spanish salaries by occupation — official data from INE's "
             "Structure of Earnings Survey (Encuesta de Estructura Salarial).",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Search", "Pick one or more occupations in the left sidebar, then press "
                   "the blue Search button."),
        ("Drill down", "Narrow through the CNO-11 hierarchy (1-digit major → "
                       "2-digit sub-major group)."),
        ("Read the results", "Explore the tabs — the P10–P90 distribution, By "
                             "gender and the leaderboard."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches names "
                       "and CNO codes."),
        ("Code browser", "Open the Code browser to explore the whole CNO-11 tree."),
        ("Aggregate", "Picked several? Toggle Aggregate selection to merge them."),
    ],
    "charts_title": "Reading the wage charts",
    "charts_intro": "INE publishes the full spread — a wide P10–P90 gap means pay "
                    "varies a lot in that job (the average is a separate ♦ marker):",
    "pcts": [("P10", 22, "10% earn less"), ("P25", 36, "a quarter earn less"),
             ("MED", 52, "half earn less"), ("P75", 68, "a quarter earn more"),
             ("P90", 84, "only 10% earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are gross MONTHLY earnings (EUR) = the official gross ANNUAL "
        "earnings ÷ 12.",
        "The By-gender tab splits women vs men.",
        "This is the quadrennial Structure of Earnings Survey — a 2018 snapshot, "
        "so there is no year-on-year trend here.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance."),
        ("Salary distribution", "The P10–P90 chart, raw data + CSV."),
        ("Where do I stand?", "Enter a monthly salary and see its percentile."),
        ("Leaderboard", "Ranks occupations by pay or the gender gap."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "All figures are from INE table 70672 (Encuesta de Estructura Salarial).",
}

CONFIG = CountryConfig(
    slug="spain",
    name="Spain",
    native="España",
    iso="es",
    eyebrow="OFFICIAL STATISTICS · SPAIN",
    source_name="Instituto Nacional de Estadística (INE)",
    source_url="https://www.ine.es/jaxiT3/Tabla.htm?t=70672",
    caption=_CAPTION,
    currency="EUR", currency_suffix="€", money_prefix=False, period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True,        # P10 · P25 · median · P75 · P90
        has_occupation_hierarchy=True,          # CNO-11 1- and 2-digit
        has_mean=True, has_median=True, has_sex=True,
        has_trend=False,                        # single-year (2018) snapshot
        has_leaderboard=True, leaderboard_scope=1,
        sectors=(),
        year_range=(min(_YEARS), max(_YEARS)),
    ),
    tabs=("overview", "distribution", "where", "leaderboard", "sex"),
    access="restricted",                        # BETA — admins + beta users only
    fetch_mode="search",
    landing=True,
    classification="CNO-11",
    bullets=(
        "P10–P90 + mean · CNO-11 occupations (major & sub-major)",
        "Gender breakdown · quadrennial Structure of Earnings Survey",
        f"Gross monthly earnings · INE · {_YR}",
    ),
    labels={"badge": "Beta", "source_short": "INE · official"},
    languages=(("EN", "English"), ("ES", "Español")),
    i18n={
        "EN": {
            "title": "Spanish Salary Explorer", "caption": _CAPTION,
            "grp_1": "Major group", "grp_2": "Sub-major group",
            "all_grp_1": "— All major groups —", "all_grp_2": "— All sub-major groups —",
            "brlvl_1": "Major group", "brlvl_2": "Sub-major group",
        },
        "ES": {
            "title": "Explorador de Salarios de España",
            "caption": "INE · Salario por ocupación (CNO-11) · bruto mensual, EUR",
            "grp_1": "Gran grupo", "grp_2": "Subgrupo principal",
            "all_grp_1": "— Todos los grandes grupos —", "all_grp_2": "— Todos los subgrupos —",
            "brlvl_1": "Gran grupo", "brlvl_2": "Subgrupo principal",
        },
    },
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
