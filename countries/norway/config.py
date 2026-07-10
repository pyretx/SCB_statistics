"""Norway config — the entire country-specific surface (this + provider.py).
access='registered' → LIVE for every signed-in user (free account); signed-out
visitors don't see Norway at all (landing tile + switcher hide it)."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .provider import NorwayProvider

# Structured guides (the approved User-Guide design; rendered by core/panels.py)
_GUIDE_EN = {
    "title": "How to use the Norwegian Salary Explorer",
    "source": "Statistics Norway (SSB) · Monthly earnings by occupation (STYRK-08) · table 11418",
    "intro": "Look up Norwegian salaries by occupation — official data from Statistics "
             "Norway, no technical knowledge needed. This guide covers the three-step "
             "flow, finding occupations, and how to read the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your filters",
         "In the left sidebar: sector (all, private + public enterprises, or local / "
         "central government), gender, and a year range (2015 onward)."),
        ("Search",
         "Pick one or more occupations, then press the blue Search button at the "
         "bottom of the sidebar."),
        ("Read the results",
         "Explore the tabs on the right. Change any filter and search again to "
         "update the charts."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches both job "
                       "titles and STYRK codes."),
        ("Drill down", "Or narrow step by step with Occupational field → Area → Group "
                       "(STYRK 1 → 2 → 3 digit)."),
        ("Code browser", "Open the Code browser to explore the entire STYRK-08 "
                         "classification tree."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection above "
                      "the tabs to merge them into one headcount-weighted series."),
    ],
    "charts_title": "Reading the salary charts",
    "charts_intro": "SSB publishes quartiles, not the full percentile range. "
                    "Every chart shows three points (the average is a separate ♦ marker):",
    "pcts": [("P25", 32, "a quarter earn less"),
             ("MED", 52, "half earn less"),
             ("P75", 72, "a quarter earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are gross monthly earnings (NOK), converted to full-time equivalents.",
        "Some occupation × sector combinations aren’t published (e.g. ambulance "
        "workers in the private sector) — try All sectors.",
        "Small groups can be suppressed by SSB for privacy — a missing year is not an error.",
        "The mean can sit above the median when a few high salaries pull the average up.",
        "Interface in English / Norsk — switch at the top of the sidebar.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance, with a year selector."),
        ("Salary distribution", "The quartile chart, plus raw data + CSV export."),
        ("Trend", "Development over time: nominal, growth vs inflation (CPI), or "
                  "real (constant prices)."),
        ("Where do I stand?", "Enter a salary and see roughly where it falls."),
        ("Leaderboard", "Ranks all occupations by pay, gender gap or growth."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "All figures are gross monthly earnings from SSB table 11418, updated annually.",
}

_GUIDE_NO = {
    "title": "Slik bruker du den norske lønnsutforskeren",
    "source": "Statistisk sentralbyrå (SSB) · Månedslønn etter yrke (STYRK-08) · tabell 11418",
    "intro": "Slå opp norske lønninger per yrke — offisielle data fra Statistisk "
             "sentralbyrå, ingen tekniske forkunnskaper kreves. Denne veiledningen "
             "dekker tre-stegs-flyten, hvordan du finner yrker, og hvordan du leser "
             "diagrammene.",
    "steps_title": "Kom i gang — tre steg",
    "steps": [
        ("Velg filtrene dine",
         "I menyen til venstre: sektor (alle, privat + offentlig eide foretak, eller "
         "kommune / stat), kjønn og et årsintervall (fra 2015)."),
        ("Søk",
         "Velg ett eller flere yrker, og trykk på den blå Søk-knappen nederst i menyen."),
        ("Les resultatene",
         "Utforsk fanene til høyre. Endre et filter og søk igjen for å oppdatere "
         "diagrammene."),
    ],
    "find_title": "Finn riktig yrke",
    "find": [
        ("Søkefelt", "Skriv i «Søk yrker…»-feltet — det matcher både yrkestitler og "
                     "STYRK-koder."),
        ("Bor deg ned", "Eller avgrens steg for steg med Yrkesfelt → Yrkesområde → "
                        "Yrkesgruppe (STYRK 1 → 2 → 3 siffer)."),
        ("Kodeoversikt", "Åpne Kodeoversikt for å utforske hele STYRK-08-treet."),
        ("Aggreger", "Valgt flere yrker? Slå på Aggreger utvalget over fanene for å "
                     "slå dem sammen til én serie vektet etter antall ansatte."),
    ],
    "charts_title": "Lese lønnsdiagrammene",
    "charts_intro": "SSB publiserer kvartiler, ikke hele persentilspennet. Hvert "
                    "diagram viser tre punkter (gjennomsnittet er en egen ♦-markør):",
    "pcts": [("P25", 32, "en fjerdedel tjener mindre"),
             ("MED", 52, "halvparten tjener mindre"),
             ("P75", 72, "en fjerdedel tjener mer")],
    "notes_title": "Verdt å vite",
    "notes": [
        "Tallene er brutto månedslønn (NOK), omregnet til heltidsekvivalenter.",
        "Enkelte kombinasjoner av yrke × sektor er ikke publisert (f.eks. "
        "ambulansepersonell i privat sektor) — prøv Alle sektorer.",
        "Små grupper kan være skjult av SSB av personvernhensyn — et manglende år "
        "er ikke en feil.",
        "Gjennomsnittet kan ligge over medianen når noen få høye lønninger drar "
        "snittet opp.",
        "Grensesnitt på English / Norsk — bytt øverst i menyen.",
    ],
    "tabs_title": "Fanene",
    "tabs": [
        ("Oversikt", "Nøkkeltallene samlet, med årsvelger."),
        ("Lønnsfordeling", "Kvartildiagrammet, pluss rådata + CSV-eksport."),
        ("Trend", "Utvikling over tid: nominelt, vekst mot inflasjon (KPI) eller "
                  "realverdi (faste priser)."),
        ("Hvor står jeg?", "Oppgi en lønn og se omtrent hvor den ligger."),
        ("Toppliste", "Rangerer alle yrker etter lønn, kjønnsgap eller vekst."),
        ("Etter kjønn", "Kvinner mot menn, med kvinner-i-%-av-menn-visning."),
    ],
    "footer": "Alle tall er brutto månedslønn fra SSB tabell 11418, oppdatert årlig.",
}

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
    access="registered",                    # LIVE — any signed-in user
    fetch_mode="search",                    # commit-on-Search, like Sweden
    landing=True,                           # show a gated tile on the landing page
    classification="STYRK-08",
    bullets=(
        "Mean &amp; median salary · ~400 occupations (STYRK-08)",
        "Sector &amp; gender breakdowns · quartiles",
        "Monthly earnings · 2015–2024",
    ),
    # flat, language-independent strings the landing tile reads
    labels={
        "badge": "Live",
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
