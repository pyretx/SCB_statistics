"""Netherlands config — CBS table 85517NED. Gross HOURLY wages (EUR) by BRC-2014
occupation (2–4 digit hierarchy) × year, 2013→. P25·median·P75 (quartiles) +
employee count, with a full annual trend. No mean and no sex breakdown (this CBS
table has neither). access='restricted' → BETA (admins + beta users)."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import NetherlandsProvider

_YR = latest_year()

_GUIDE_EN = {
    "title": "How to use the Dutch Salary Explorer",
    "source": f"Statistics Netherlands (CBS) · Hourly wage by occupation (BRC 2014) · table 85517NED · 2013–{_YR}",
    "intro": "Look up Dutch hourly wages by occupation — official data from "
             "Statistics Netherlands (CBS). This guide covers the three-step flow, "
             "finding occupations, and how to read the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your year", "In the left sidebar, pick a year (2013–%s)." % _YR),
        ("Search", "Pick one or more occupations, then press the blue Search "
                   "button at the bottom of the sidebar."),
        ("Read the results", "Explore the tabs on the right, including the "
                             "salary trend since 2013."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches the "
                       "Dutch occupation names and BRC codes."),
        ("Drill down", "Or narrow step by step through the BRC hierarchy "
                       "(segment → group → detailed occupation)."),
        ("Code browser", "Open the Code browser to explore the whole BRC-2014 "
                         "classification."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection to "
                      "merge them into one series."),
    ],
    "charts_title": "Reading the wage charts",
    "charts_intro": "CBS publishes the 25th percentile, median and 75th percentile "
                    "— the middle of the pay range for each occupation:",
    "pcts": [("P25", 34, "a quarter earn less"),
             ("MED", 52, "half earn less"),
             ("P75", 70, "a quarter earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are gross HOURLY wages (EUR) for employees.",
        "This CBS table has no mean and no gender breakdown — only the median "
        "and quartiles, so the By-gender view doesn't appear.",
        "Occupation names are in Dutch — CBS publishes no English names for this "
        "table.",
        "Small occupation × year cells can be suppressed by CBS — a missing figure "
        "is not an error.",
        "Interface in English / Nederlands — switch at the top of the sidebar.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance, plus employment."),
        ("Salary distribution", "The P25–median–P75 chart + the trend since 2013, "
                                "plus raw data + CSV export."),
        ("Where do I stand?", "Enter an hourly wage and see roughly where it falls."),
        ("Leaderboard", "Ranks all occupations by pay."),
    ],
    "footer": f"All figures are gross hourly wages from CBS table 85517NED (2013–{_YR}).",
}

_GUIDE_NL = {
    "title": "Zo gebruik je de Nederlandse salarisverkenner",
    "source": f"CBS · Uurloon naar beroep (BRC 2014) · tabel 85517NED · 2013–{_YR}",
    "intro": "Zoek Nederlandse uurlonen op naar beroep — officiële gegevens van "
             "het CBS. Deze gids behandelt de drie stappen, het vinden van "
             "beroepen en het lezen van de grafieken.",
    "steps_title": "Aan de slag — drie stappen",
    "steps": [
        ("Kies een jaar", "Kies links een jaar (2013–%s)." % _YR),
        ("Zoek", "Kies een of meer beroepen en druk op de blauwe Zoek-knop "
                 "onderaan het menu."),
        ("Lees de resultaten", "Bekijk de tabbladen rechts, inclusief de "
                               "loontrend sinds 2013."),
    ],
    "find_title": "Het juiste beroep vinden",
    "find": [
        ("Zoekvak", "Typ in het „Zoek beroepen…“-vak — het matcht de beroepsnamen "
                    "en BRC-codes."),
        ("Verdiep", "Of verfijn stap voor stap via de BRC-indeling "
                    "(segment → groep → beroep)."),
        ("Code-browser", "Open de Code-browser om de hele BRC-2014-indeling te "
                         "verkennen."),
        ("Samenvoegen", "Meerdere beroepen gekozen? Zet Samenvoegen aan om ze tot "
                        "één reeks te combineren."),
    ],
    "charts_title": "De loongrafieken lezen",
    "charts_intro": "CBS publiceert het 25e percentiel, de mediaan en het 75e "
                    "percentiel — het midden van de loonrange per beroep:",
    "pcts": [("P25", 34, "een kwart verdient minder"),
             ("MED", 52, "de helft verdient minder"),
             ("P75", 70, "een kwart verdient meer")],
    "notes_title": "Goed om te weten",
    "notes": [
        "De bedragen zijn bruto UURLONEN (euro) voor werknemers.",
        "Deze CBS-tabel heeft geen gemiddelde en geen uitsplitsing naar geslacht "
        "— alleen mediaan en kwartielen, dus het tabblad Naar geslacht ontbreekt.",
        "Kleine beroep × jaar cellen kunnen door het CBS zijn onderdrukt — een "
        "ontbrekend cijfer is geen fout.",
        "Interface in English / Nederlands — wissel bovenaan het menu.",
    ],
    "tabs_title": "De tabbladen",
    "tabs": [
        ("Overzicht", "De kerncijfers in één oogopslag, plus werkgelegenheid."),
        ("Loonverdeling", "De P25–mediaan–P75-grafiek + de trend sinds 2013, plus "
                          "ruwe data + CSV-export."),
        ("Waar sta ik?", "Vul een uurloon in en zie ongeveer waar het valt."),
        ("Ranglijst", "Rangschikt alle beroepen op loon."),
    ],
    "footer": f"Alle cijfers zijn bruto uurlonen uit CBS-tabel 85517NED (2013–{_YR}).",
}

CONFIG = CountryConfig(
    slug="netherlands",
    name="Netherlands",
    native="Nederland",
    iso="nl",
    eyebrow="OFFICIAL STATISTICS · NETHERLANDS",
    source_name="Statistics Netherlands (CBS)",
    source_url="https://opendata.cbs.nl/statline/#/CBS/nl/dataset/85517NED",
    caption=f"Statistics Netherlands (CBS) · Hourly wage by occupation (BRC 2014) · 2013–{_YR}",
    currency="EUR", currency_suffix="€", money_prefix=False, period="hourly",
    capabilities=Capabilities(
        has_occupation_percentiles=False,
        has_occupation_hierarchy=True,       # BRC nests 2 → 3 → 4 digit
        has_quartiles=True,                  # P25 · median · P75
        has_mean=False, has_median=True, has_sex=False,
        has_trend=True,                      # annual 2013→
        has_leaderboard=True, leaderboard_scope=2,
        sectors=(),
        year_range=(2013, _YR),
    ),
    tabs=("overview", "distribution", "trend", "where", "leaderboard",
          "import_overlay"),
    access="restricted",                     # BETA — admins + beta users only
    fetch_mode="search",
    landing=True,
    classification="BRC 2014",
    bullets=(
        "Median &amp; quartiles · ~110 occupations (BRC)",
        "Hierarchy drill-down · P25–P75 · trend",
        f"Gross hourly wages · 2013–{_YR}",
    ),
    labels={"badge": "Beta", "source_short": "CBS · official"},
    languages=(("EN", "English"), ("NL", "Nederlands")),
    i18n={
        "EN": {"title": "Dutch Salary Explorer",
               "caption": f"Statistics Netherlands (CBS) · Hourly wage by occupation (BRC 2014) · 2013–{_YR}",
               "brlvl_2": "Occupational segment", "brlvl_3": "Occupational group",
               "brlvl_4": "Detailed occupation"},
        "NL": {"title": "Nederlandse salarisverkenner",
               "caption": f"CBS · Uurloon naar beroep (BRC 2014) · 2013–{_YR}",
               "brlvl_2": "Beroepssegment", "brlvl_3": "Beroepsgroep",
               "brlvl_4": "Beroep"},
    },
    guide={"EN": _GUIDE_EN, "NL": _GUIDE_NL},
    provider=NetherlandsProvider(),
)
