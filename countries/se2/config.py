"""Sweden v2 config — the legacy scb_salaries.py rebuilt on the framework.

access='internal' → admin/master ONLY (the SE2 beta the legacy page is compared
against; see docs/se2-fr2-parity.md). landing=False keeps it off the home grid;
admins reach it from the admin panel's Open-a-country or /se2.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities

from .labels import SECTORS
from .provider import Sweden2Provider, latest_year

_SECTOR_CODES = ("0", "1-3", "1", "2", "3", "4-5", "4", "5")

_GUIDE_EN = """
**What this shows.** Monthly salaries for ~430 occupations (SSYK 2012) from
Statistics Sweden (SCB): mean and the P10 / P25 / median / P75 / P90
percentiles, by sector, sex and year (2014→), plus age / education / region
breakdowns, a trend view with inflation, a leaderboard and a salary calculator.

**How to use it**
1. Pick a **sector**, **sex** and **year range**.
2. Narrow by occupation group (SSYK 1 → 2 → 3 digit), pick occupation(s),
   press **Search**.

**Good to know**
- This is **Sweden v2** — the framework rebuild of the original Sweden page.
  The work-permit checker and SSYK guide still live on the original page.
- Figures are gross monthly salaries converted to full-time equivalents.
"""

_GUIDE_SV = """
**Vad detta visar.** Månadslöner för ~430 yrken (SSYK 2012) från SCB: medelvärde
och percentilerna P10 / P25 / median / P75 / P90, per sektor, kön och år
(2014→), plus uppdelning efter ålder / utbildning / region, löneutveckling med
inflation, topplista och en lönekalkylator.

**Så använder du den**
1. Välj **sektor**, **kön** och **årsintervall**.
2. Avgränsa efter yrkesgrupp (SSYK 1 → 2 → 3 siffror), välj yrke(n),
   tryck **Sök**.

**Bra att veta**
- Detta är **Sweden v2** — ramverksversionen av den ursprungliga Sverige-sidan.
  Arbetstillståndskollen och SSYK-guiden finns kvar på originalsidan.
- Siffrorna är heltidsekvivalenta grundlöner per månad.
"""

CONFIG = CountryConfig(
    slug="se2",
    name="Sweden v2",
    native="Sverige",
    iso="se",
    eyebrow="OFFICIAL STATISTICS · SWEDEN",
    source_name="Statistics Sweden (SCB)",
    source_url="https://www.scb.se/en/finding-statistics/statistics-by-subject-area/labour-market/",
    caption="SCB salary structure statistics · monthly SEK · 2014–{yr}".format(yr=latest_year()),
    currency="SEK", currency_suffix="kr", period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True,      # full P10..P90 + mean + median
        has_mean=True, has_median=True,
        has_sex=True, has_age=True, has_education=True, has_region=True,
        has_trend=True,
        has_leaderboard=True, leaderboard_scope=2,   # SSYK sub-major group
        sectors=_SECTOR_CODES,
        year_range=(2014, latest_year()),
    ),
    tabs=("overview", "distribution", "trend", "where", "leaderboard",
          "sex", "age", "education", "region"),
    access="internal",                        # admin/master only (SE2 beta)
    fetch_mode="search",
    landing=False,                            # no home tile — admin preview only
    classification="SSYK 2012",
    labels={"badge": "Beta", "source_short": "SCB · official"},
    languages=(("EN", "English"), ("SV", "Svenska")),
    i18n={
        "EN": {
            "title": "Swedish Salary Explorer (v2)",
            "caption": f"SCB salary structure statistics · monthly SEK · 2014–{latest_year()}",
            **{f"sector_{c}": n for c, n in SECTORS["EN"].items()},
        },
        "SV": {
            "title": "Svensk löneutforskare (v2)",
            "caption": f"SCB:s lönestrukturstatistik · månadslön SEK · 2014–{latest_year()}",
            **{f"sector_{c}": n for c, n in SECTORS["SV"].items()},
        },
    },
    guide={"EN": _GUIDE_EN, "SV": _GUIDE_SV},
    provider=Sweden2Provider(),
)
