"""UK config — ONS ASHE Table 14 (occupation, 4-digit SOC 2020).

Full P10·P25·median·P75·P90 + mean + jobs, by SOC occupation × sex × year — the
richest capability set in the app: distribution, By-gender, a 2021-2024 trend
(with a CPIH real-terms overlay), leaderboard and the salary calculator. Figures
are gross MONTHLY pay (official gross annual ÷ 12). access='restricted' → BETA
(admins + beta users only).
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import UkProvider, _load

_prov = UkProvider()
_YR = latest_year()
_YEARS = _load().get("years") or [2021, _YR]
_CAPTION = ("Office for National Statistics · ASHE by occupation (SOC 2020) · "
            "gross monthly pay")

_GUIDE_EN = {
    "title": "How to use the UK Salary Explorer",
    "source": f"Office for National Statistics · ASHE Table 14 (SOC 2020) · {_YR}",
    "intro": "Look up UK salaries by occupation — official data from the ONS "
             "Annual Survey of Hours and Earnings (ASHE). This guide covers the "
             "three-step flow, finding occupations, and how to read the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your filters", "In the left sidebar: gender (all, women, men) and "
                                "the year range for the trend."),
        ("Search", "Pick one or more occupations, then press the blue Search "
                   "button at the bottom of the sidebar."),
        ("Read the results", "Explore the tabs on the right. Change any filter and "
                             "search again to update the charts."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches both "
                       "job titles and SOC codes."),
        ("Drill down", "Or narrow step by step with Major → Sub-major → Minor "
                       "group (the SOC 2020 hierarchy)."),
        ("Code browser", "Open the Code browser to explore the whole SOC-2020 "
                         "classification tree."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection to "
                      "merge them into one jobs-weighted series."),
    ],
    "charts_title": "Reading the wage charts",
    "charts_intro": "Wages are shown as percentiles — a wide gap between P10 and "
                    "P90 means pay varies a lot in that job (the average is a "
                    "separate ♦ marker):",
    "pcts": [("P10", 22, "10% earn less"),
             ("P25", 36, "a quarter earn less"),
             ("MED", 52, "half earn less"),
             ("P75", 68, "a quarter earn more"),
             ("P90", 84, "only 10% earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are GROSS MONTHLY pay — ONS's official gross ANNUAL pay divided "
        "by 12, so the UK is comparable with the app's other monthly countries.",
        "The By-gender tab splits women vs men; the trend covers 2021–2024 (the "
        "years on the current SOC 2020 basis), with a CPIH real-terms view.",
        "Small or volatile occupation cells are suppressed by ONS for quality — a "
        "missing figure or percentile is not an error.",
        "ASHE annual pay is based on employees on adult rates whose pay was not "
        "affected by absence.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance, plus employment (jobs)."),
        ("Salary distribution", "The P10–P90 percentile chart + the 2021–2024 "
                                "trend, plus raw data + CSV export."),
        ("Where do I stand?", "Enter a monthly salary and see which percentile it "
                              "falls in."),
        ("Leaderboard", "Ranks occupations by pay or the gender gap within a SOC "
                        "group."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "All figures are from the ONS ASHE Table 14 (occupation by 4-digit "
              "SOC 2020), updated annually.",
}

CONFIG = CountryConfig(
    slug="uk",
    name="United Kingdom",
    native="United Kingdom",
    iso="gb",
    eyebrow="OFFICIAL STATISTICS · UNITED KINGDOM",
    source_name="Office for National Statistics (ASHE)",
    source_url="https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours",
    caption=_CAPTION,
    currency="GBP", currency_suffix="£", money_prefix=True, period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True,     # P10 · P25 · median · P75 · P90
        has_occupation_hierarchy=True,       # SOC 2020 major→sub-major→minor→unit
        has_mean=True, has_median=True, has_sex=True,
        has_trend=True,                      # 2021–2024 (SOC 2020 basis) + CPIH
        has_leaderboard=True, leaderboard_scope=2,   # SOC sub-major group
        sectors=(),
        year_range=(min(_YEARS), max(_YEARS)),
    ),
    tabs=("overview", "distribution", "where", "leaderboard", "sex", "import_overlay"),
    access="registered",                     # LIVE — any signed-in user
    fetch_mode="search",
    landing=True,
    classification="SOC 2020",
    bullets=(
        "P10–P90 + mean · 412 occupations (SOC 2020)",
        "Gender breakdown &amp; 2021–2024 trend (real terms)",
        f"Gross monthly pay · ONS ASHE · {_YR}",
    ),
    labels={"badge": "Live", "source_short": "ONS ASHE · official"},
    languages=(("EN", "English"),),
    i18n={"EN": {
        "title": "UK Salary Explorer",
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
