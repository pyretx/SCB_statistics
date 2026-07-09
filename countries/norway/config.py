"""Norway config — the entire country-specific surface (this + provider.py).
access='restricted' → admin/master or a user granted "norway" (beta tester) can
open /norway while it's WIP; everyone else sees the landing tile as Locked."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .provider import NorwayProvider

_GUIDE_EN = """
# 👋 Welcome to the Norwegian Salary Explorer

Look up **Norwegian salaries** by occupation — official data from Statistics
Norway (SSB), table 11418. No technical knowledge needed.

## 🚀 Getting started — 3 steps
1. **Choose your filters** in the left sidebar: sector (all, private + public
   enterprises, or local / central government), sex and a year range (2015→).
2. Click **🔍 Search**.
3. **Read the results** in the tabs. Change a filter and search again to update.

## 🔎 Finding the right occupation
- Type in the **"Search occupations…"** box — it matches job titles and codes.
- Or drill down with **Occupational field → Area → Group** (STYRK 1 → 2 → 3
  digit).
- Open the **Code browser** to explore the whole STYRK-08 classification.
- Picked several occupations? Toggle **Aggregate selection** above the tabs to
  merge them into one headcount-weighted series.

## 📈 Reading the salary charts
SSB publishes **quartiles**, not the full percentile range:
- **P25** — a quarter earn less than this.
- **Median (P50)** — the middle salary; half earn more, half less.
- **P75** — a quarter earn more.
- **Average** — shown as a separate ♦ marker.

## 🗂 The tabs
- **Overview** — the key figures at a glance, with a year selector.
- **Salary distribution** — the quartile chart, plus raw data + CSV export.
- **Trend** — development over time: nominal, growth vs inflation (CPI), or
  real (constant prices).
- **Where do I stand?** — enter a salary and see roughly where it falls.
- **Leaderboard** — ranks all occupations by pay, gender gap or growth.
- **By gender** — women vs men, with a women-as-%-of-men view.

## ❓ Good to know
- Figures are **gross monthly earnings** (NOK), converted to full-time
  equivalents.
- Some occupation × sector combinations aren't published (e.g. ambulance
  workers in the private sector) — try **All sectors**.
- Interface in **English / Norsk** — switch at the top of the sidebar.
"""

_GUIDE_NO = """
# 👋 Velkommen til den norske lønnsutforskeren

Slå opp **norske lønninger** per yrke — offisielle data fra Statistisk
sentralbyrå (SSB), tabell 11418. Ingen tekniske forkunnskaper kreves.

## 🚀 Kom i gang — 3 steg
1. **Velg filtrene dine** i menyen til venstre: sektor (alle, privat +
   offentlig eide foretak, eller kommune / stat), kjønn og et årsintervall
   (2015→).
2. Klikk **🔍 Søk**.
3. **Les resultatene** i fanene. Endre et filter og søk igjen for å oppdatere.

## 🔎 Finn riktig yrke
- Skriv i **«Søk yrker…»**-feltet — det matcher yrkestitler og koder.
- Eller bor deg ned via **Yrkesfelt → Yrkesområde → Yrkesgruppe** (STYRK
  1 → 2 → 3 siffer).
- Åpne **Kodeoversikt** for å utforske hele STYRK-08-klassifiseringen.
- Valgt flere yrker? Slå på **Aggreger utvalget** over fanene for å slå dem
  sammen til én serie vektet etter antall ansatte.

## 📈 Lese lønnsdiagrammene
SSB publiserer **kvartiler**, ikke hele persentilspennet:
- **P25** — en fjerdedel tjener mindre enn dette.
- **Median (P50)** — midtlønnen; halvparten tjener mer, halvparten mindre.
- **P75** — en fjerdedel tjener mer.
- **Gjennomsnitt** — vises som egen ♦-markør.

## 🗂 Fanene
- **Oversikt** — nøkkeltallene samlet, med årsvelger.
- **Lønnsfordeling** — kvartildiagrammet, pluss rådata + CSV-eksport.
- **Trend** — utvikling over tid: nominelt, vekst mot inflasjon (KPI) eller
  realverdi (faste priser).
- **Hvor står jeg?** — oppgi en lønn og se omtrent hvor den ligger.
- **Toppliste** — rangerer alle yrker etter lønn, kjønnsgap eller vekst.
- **Etter kjønn** — kvinner mot menn, med kvinner-i-%-av-menn-visning.

## ❓ Verdt å vite
- Tallene er **brutto månedslønn** (NOK), omregnet til heltidsekvivalenter.
- Enkelte kombinasjoner av yrke × sektor er ikke publisert (f.eks.
  ambulansepersonell i privat sektor) — prøv **Alle sektorer**.
- Grensesnitt på **English / Norsk** — bytt øverst i menyen.
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
        has_leaderboard=True,
        sectors=("all", "private", "local", "central"),
        year_range=(2015, 2024),
    ),
    # standard order (docs/architecture.md); Basic statistics is merged into Overview
    tabs=("overview", "distribution", "trend", "where", "leaderboard", "sex",
          "import_overlay"),
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
