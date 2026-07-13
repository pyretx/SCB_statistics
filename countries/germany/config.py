"""Germany config — Destatis GENESIS-Online, earnings by KldB 2010 occupation.

Mean + median gross MONTHLY earnings (EUR, full-time) by occupation × SEX across
the full KldB 2010 hierarchy (37 Berufshauptgruppen / 144 Berufsgruppen / 1300
Berufsgattungen), with official EN + DE occupation names (GENESIS table
62361-0030). A single annual snapshot — no percentiles, region or trend in this
table — so the page runs Overview / Basic statistics / Leaderboard / By-gender.
access='restricted' → BETA.

Data source: Statistisches Bundesamt (Destatis), GENESIS-Online; used under
Datenlizenz Deutschland – Namensnennung – Version 2.0.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from . import skill_levels
from .build import latest_year
from .provider import GermanyProvider, _load

_prov = GermanyProvider()
_YR = latest_year()
_RETRIEVED = _load().get("retrieved", "")
# Required Data licence Germany (dl-de/by-2-0) attribution.
ATTRIBUTION = (f"Data source: Statistisches Bundesamt (Destatis), GENESIS-Online, "
               f"retrieved {_RETRIEVED}; Data licence Germany – attribution – "
               f"Version 2.0.")
_CAPTION = ("Statistisches Bundesamt (Destatis) · GENESIS-Online · gross monthly "
            "earnings by occupation (KldB 2010)")

_GUIDE_EN = {
    "title": "How to use the German Salary Explorer",
    "source": f"Statistisches Bundesamt (Destatis) · GENESIS-Online 62361-0030 · {_YR}",
    "intro": "Look up German salaries by occupation — official data from Destatis' "
             "earnings survey via GENESIS-Online. This guide covers finding "
             "occupations and reading the figures.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Search", "Pick one or more occupations in the left sidebar, then press "
                   "the blue Search button."),
        ("Drill down", "Narrow step by step through the KldB hierarchy "
                       "(Berufshauptgruppe → Berufsgruppe → Berufsgattung)."),
        ("Read the results", "Explore the tabs on the right — the average and "
                             "median for each occupation."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches the "
                       "German KldB occupation names and codes."),
        ("Code browser", "Open the Code browser to explore the whole KldB-2010 "
                         "classification."),
        ("Skill level", "The 5-digit occupations end in a requirement level — "
                        "Helfer, Fachkraft, Spezialist or Experte."),
    ],
    "charts_title": "Reading the figures",
    "charts_intro": "Destatis publishes two averages per occupation — the "
                    "arithmetic mean and the median (the middle earner):",
    "pcts": [("MEAN", 52, "arithmetic average"),
             ("MED", 52, "the middle earner")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are gross MONTHLY earnings (EUR) of full-time employees, "
        "excluding special payments (bonuses), reference month April.",
        "The By-gender tab splits women vs men. This table has no percentile, "
        "regional or time-trend breakdown by occupation — only mean and median — "
        "so those tabs don't appear.",
        "Occupation names are the official Destatis KldB 2010 titles; switch to "
        "Deutsch for the German names.",
        "Small occupation cells can be suppressed by Destatis — a missing figure "
        "is not an error.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The mean and median at a glance for each occupation."),
        ("Basic statistics", "A per-occupation summary table with CSV export."),
        ("Leaderboard", "Ranks occupations by mean or median pay within a KldB "
                        "group."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
        ("Skill levels", "Pay across an occupation's requirement levels "
                         "(Helfer → Fachkraft → Spezialist → Experte)."),
    ],
    "footer": ATTRIBUTION,
}

_GUIDE_DE = {
    "title": "So nutzt du den deutschen Gehaltsexplorer",
    "source": f"Statistisches Bundesamt (Destatis) · GENESIS-Online 62361-0030 · {_YR}",
    "intro": "Gehälter nach Beruf nachschlagen — amtliche Daten aus der "
             "Verdiensterhebung des Statistischen Bundesamtes über GENESIS-Online.",
    "steps_title": "Erste Schritte — drei Schritte",
    "steps": [
        ("Suchen", "Wähle links einen oder mehrere Berufe und klicke auf den "
                   "blauen Such-Button."),
        ("Eingrenzen", "Grenze Schritt für Schritt über die KldB-Hierarchie ein "
                       "(Berufshauptgruppe → Berufsgruppe → Berufsgattung)."),
        ("Ergebnisse lesen", "Erkunde die Reiter rechts — Durchschnitt und Median "
                             "je Beruf."),
    ],
    "find_title": "Den richtigen Beruf finden",
    "find": [
        ("Suchfeld", "Tippe in das Feld „Berufe suchen…“ — es findet KldB-Namen "
                     "und -Kennziffern."),
        ("Code-Browser", "Öffne den Code-Browser für die ganze KldB-2010-"
                         "Klassifikation."),
        ("Anforderungsniveau", "Die 5-stelligen Berufe enden auf einem "
                               "Anforderungsniveau — Helfer, Fachkraft, Spezialist "
                               "oder Experte."),
    ],
    "charts_title": "Die Zahlen lesen",
    "charts_intro": "Destatis veröffentlicht zwei Mittelwerte je Beruf — das "
                    "arithmetische Mittel und den Median:",
    "pcts": [("MITTEL", 52, "arithmetisches Mittel"),
             ("MED", 52, "der mittlere Verdienst")],
    "notes_title": "Gut zu wissen",
    "notes": [
        "Werte sind Brutto-MONATSverdienste (EUR) von Vollzeitbeschäftigten, ohne "
        "Sonderzahlungen, Berichtsmonat April.",
        "Der Reiter „Nach Geschlecht“ trennt Frauen und Männer. Diese Tabelle hat "
        "keine Perzentile, Region oder Zeitreihe je Beruf — nur Mittel und Median.",
        "Die Berufsnamen sind die amtlichen KldB-2010-Bezeichnungen; auf Englisch "
        "umschalten für die englischen Namen.",
        "Kleine Berufszellen können von Destatis gesperrt sein — ein fehlender "
        "Wert ist kein Fehler.",
    ],
    "tabs_title": "Die Reiter",
    "tabs": [
        ("Überblick", "Mittel und Median je Beruf auf einen Blick."),
        ("Basisstatistik", "Übersichtstabelle je Beruf mit CSV-Export."),
        ("Rangliste", "Ordnet Berufe nach Mittel oder Median innerhalb einer "
                      "KldB-Gruppe."),
        ("Nach Geschlecht", "Frauen vs. Männer, mit Frauen-in-%-der-Männer-Ansicht."),
        ("Anforderungsniveaus", "Verdienst über die Anforderungsniveaus eines "
                                "Berufs (Helfer → Fachkraft → Spezialist → Experte)."),
    ],
    "footer": ATTRIBUTION,
}

CONFIG = CountryConfig(
    slug="germany",
    name="Germany",
    native="Deutschland",
    iso="de",
    eyebrow="OFFICIAL STATISTICS · GERMANY",
    source_name="Statistisches Bundesamt (Destatis)",
    source_url="https://www.destatis.de/DE/Themen/Arbeit/Verdienste/Verdienste-Branche-Berufe/",
    caption=_CAPTION,
    currency="EUR", currency_suffix="€", money_prefix=False, period="monthly",
    capabilities=Capabilities(
        has_occupation_hierarchy=True,           # KldB 2010: 2 → 3 → 5 digit
        has_mean=True, has_median=True,
        has_sex=True, has_trend=False,           # mean+median × sex (GENESIS 62361-0030)
        has_leaderboard=True, leaderboard_scope=2,   # Berufshauptgruppe (2-digit)
        sectors=(),
        year_range=(_YR, _YR),                   # single annual snapshot
    ),
    tabs=("overview", "stats", "leaderboard", "sex"),
    extra_tabs={"skill_levels": skill_levels.render},   # Germany-specific (KldB 5th digit)
    access="restricted",                         # BETA — admins + beta users only
    fetch_mode="search",
    landing=True,
    classification="KldB 2010",
    bullets=(
        "Mean, median &amp; gender split · ~1300 occupations (KldB 2010)",
        "Full occupation hierarchy &amp; leaderboard",
        f"Gross monthly earnings · Destatis GENESIS · {_YR}",
    ),
    labels={"badge": "Beta", "source_short": "Destatis · official"},
    languages=(("EN", "English"), ("DE", "Deutsch")),
    i18n={
        "EN": {
            "title": "German Salary Explorer",
            "caption": _CAPTION,
            "tab_skill_levels": "Skill levels",
            "grp_1": "Major group", "grp_2": "Occupation group",
            "grp_3": "Occupation",
            "all_grp_1": "— All major groups —", "all_grp_2": "— All occupation groups —",
            "all_grp_3": "— All occupations —",
            "brlvl_2": "Major group (2-digit)", "brlvl_3": "Occupation group (3-digit)",
            "brlvl_4": "Occupation (4-digit)", "brlvl_5": "Skill level (5-digit)",
        },
        "DE": {
            "title": "Deutscher Gehaltsexplorer",
            "caption": "Statistisches Bundesamt (Destatis) · GENESIS-Online · "
                       "Bruttomonatsverdienste nach Beruf (KldB 2010)",
            "tab_skill_levels": "Anforderungsniveaus",
            "grp_1": "Berufshauptgruppe", "grp_2": "Berufsgruppe", "grp_3": "Beruf",
            "all_grp_1": "— Alle Berufshauptgruppen —", "all_grp_2": "— Alle Berufsgruppen —",
            "all_grp_3": "— Alle Berufe —",
            "brlvl_2": "Berufshauptgruppe (2-stellig)", "brlvl_3": "Berufsgruppe (3-stellig)",
            "brlvl_4": "Berufsuntergruppe (4-stellig)", "brlvl_5": "Anforderungsniveau (5-stellig)",
        },
    },
    guide={"EN": _GUIDE_EN, "DE": _GUIDE_DE},
    provider=_prov,
)
