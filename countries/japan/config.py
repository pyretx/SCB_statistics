"""Japan config — e-Stat Basic Survey on Wage Structure (table 0003426334).

Mean scheduled monthly cash earnings (JPY) by 11 JSCO-2020 major occupation
groups × sex × 2020–2023 (trend). Flat, mean-only + sex + trend. EN + JA.
access='restricted' → BETA.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import JapanProvider, _load

_prov = JapanProvider()
_YEARS = _load().get("years") or [latest_year()]
_YR = max(_YEARS)
_CAPTION = "e-Stat · Mean earnings by occupation (JSCO major groups) · monthly, JPY"

_GUIDE_EN = {
    "title": "How to use the Japanese Salary Explorer",
    "source": f"e-Stat · Basic Survey on Wage Structure · {_YR}",
    "intro": "Look up Japanese earnings by occupation group — official data from "
             "the MHLW Basic Survey on Wage Structure (賃金構造基本統計調査).",
    "steps_title": "Getting started",
    "steps": [("Search", "Pick one or more occupation groups in the sidebar, then "
                        "press the blue Search button."),
              ("Read the results", "Explore the tabs — the 2020→ trend and By gender.")],
    "find_title": "Finding the right occupation",
    "find": [("Occupations", "The data covers the 11 JSCO-2020 major occupation groups.")],
    "charts_title": "Reading the figures",
    "charts_intro": "Figures are the MEAN scheduled monthly cash earnings per group:",
    "pcts": [("MEAN", 52, "average monthly earnings")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are MEAN 所定内給与額 (scheduled monthly cash earnings, JPY) — "
        "regular monthly pay excluding overtime and bonuses — for enterprises with "
        "10+ employees, national.",
        "The trend covers 2020–2023; the By-gender tab splits women vs men.",
    ],
    "tabs_title": "The tabs",
    "tabs": [("Overview", "Mean earnings at a glance."),
             ("Salary distribution", "The 2020→ trend + a forward projection."),
             ("Leaderboard", "Ranks the occupation groups by pay."),
             ("By gender", "Women vs men.")],
    "footer": "Data from e-Stat table 0003426334 (賃金構造基本統計調査).",
}

CONFIG = CountryConfig(
    slug="japan",
    name="Japan",
    native="日本",
    iso="jp",
    eyebrow="OFFICIAL STATISTICS · JAPAN",
    source_name="e-Stat — Basic Survey on Wage Structure (MHLW)",
    source_url="https://www.e-stat.go.jp/dbview?sid=0003426334",
    caption=_CAPTION,
    currency="JPY", currency_suffix="¥", money_prefix=True, period="monthly",
    capabilities=Capabilities(
        has_occupation_hierarchy=False,
        has_mean=True, has_median=False, has_sex=True,
        has_trend=True,
        has_leaderboard=True, leaderboard_scope=1,
        sectors=(),
        year_range=(min(_YEARS), max(_YEARS)),
    ),
    tabs=("overview", "distribution", "leaderboard", "sex"),
    access="restricted",
    fetch_mode="search",
    landing=True,
    classification="JSCO 2020 (major groups)",
    bullets=(
        "Mean earnings & gender split · 11 JSCO major groups",
        "Basic Survey on Wage Structure · 2020–2023 trend",
        f"Scheduled monthly cash earnings · e-Stat · {_YR}",
    ),
    labels={"badge": "Beta", "source_short": "e-Stat · official"},
    languages=(("EN", "English"), ("JA", "日本語")),
    i18n={
        "EN": {"title": "Japanese Salary Explorer", "caption": _CAPTION},
        "JA": {"title": "日本の給与エクスプローラー",
               "caption": "e-Stat · 職種別 所定内給与額 · 月額, 円"},
    },
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
