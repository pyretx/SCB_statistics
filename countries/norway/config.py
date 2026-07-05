"""Norway config — the entire country-specific surface (this + provider.py).
access='restricted' → admin/master or a user granted "norway" (beta tester) can
open /norway while it's WIP; everyone else sees the landing tile as Locked."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .provider import NorwayProvider

_GUIDE_EN = """
**What this shows.** Monthly gross earnings for ~400 occupations (STYRK-08),
from Statistics Norway (SSB), table 11418.

**How to use it**
1. Pick a **sector** — all, private + public enterprises, or local / central government.
2. Choose **sex** and a **year range** (2015–2024).
3. Narrow by **occupation field**, then select one or more **occupations**.
4. Press **Search**.

**Good to know**
- Figures are **mean** and **median** monthly earnings, plus lower/upper **quartiles** (no P10/P90).
- Some occupation × sector combinations aren't published (e.g. ambulance workers in
  the private sector) — try **All sectors**.
- Use the **Code browser** to explore the STYRK-08 classification.
"""

_GUIDE_NO = """
**Hva dette viser.** Månedslønn (brutto) for ca. 400 yrker (STYRK-08),
fra Statistisk sentralbyrå (SSB), tabell 11418.

**Slik bruker du den**
1. Velg **sektor** — alle, privat + offentlig eide foretak, eller kommune / stat.
2. Velg **kjønn** og et **årsintervall** (2015–2024).
3. Avgrens etter **yrkesfelt**, og velg deretter ett eller flere **yrker**.
4. Trykk **Søk**.

**Verdt å vite**
- Tallene er **gjennomsnitt** og **median** månedslønn, samt nedre/øvre **kvartiler** (ikke P10/P90).
- Enkelte kombinasjoner av yrke × sektor er ikke publisert (f.eks. ambulansepersonell
  i privat sektor) — prøv **Alle sektorer**.
- Bruk **Kodeoversikt** for å utforske STYRK-08-klassifiseringen.
"""

CONFIG = CountryConfig(
    slug="norway",
    name="Norway",
    native="Norge",
    iso="no",
    eyebrow="OFFICIAL STATISTICS · NORWAY",
    source_name="Statistics Norway (SSB)",
    source_url="https://data.ssb.no/api/v0/en/table/11418",
    caption="Statistics Norway (SSB) · Monthly earnings by occupation (STYRK-08)",
    currency="NOK", currency_suffix="kr", period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=False,   # SSB 11418 has quartiles, not P10/P90
        has_occupation_hierarchy=True,       # STYRK-08 nests (ISCO-08 aligned)
        has_quartiles=True,                  # P25 · median · P75 spread
        has_mean=True, has_median=True, has_sex=True, has_trend=True,
        sectors=("all", "private", "local", "central"),
        year_range=(2015, 2024),
    ),
    tabs=("distribution", "overview", "sex"),  # trend is embedded in Distribution, like Sweden
    access="restricted",
    fetch_mode="search",                    # commit-on-Search, like Sweden
    landing=True,                           # show a gated tile on the landing page
    classification="STYRK-08",
    bullets=(
        "Mean &amp; median salary · ~400 occupations (STYRK-08)",
        "Sector &amp; sex breakdowns · quartiles",
        "Monthly earnings · 2015–2024",
    ),
    # flat, language-independent strings the landing tile reads
    labels={
        "badge": "Beta",
        "source_short": "SSB · official",
    },
    # in-app strings that follow the language toggle (generic UI comes from
    # core.i18n; only Norway-specific strings live here)
    languages=(("EN", "English"), ("NO", "Norsk")),
    i18n={
        "EN": {
            "title": "Norwegian Salary Explorer",
            "caption": "Statistics Norway (SSB) · Monthly earnings by occupation (STYRK-08)",
            "sector_all": "All sectors",
            "sector_private": "Private + public enterprises",
            "sector_local": "Local government",
            "sector_central": "Central government",
        },
        "NO": {
            "title": "Norsk lønnsutforsker",
            "caption": "Statistisk sentralbyrå (SSB) · Månedslønn etter yrke (STYRK-08)",
            "sector_all": "Alle sektorer",
            "sector_private": "Privat + offentlig eide foretak",
            "sector_local": "Kommuneforvaltningen",
            "sector_central": "Statsforvaltningen",
        },
    },
    guide={"EN": _GUIDE_EN, "NO": _GUIDE_NO},
    provider=NorwayProvider(),
)
