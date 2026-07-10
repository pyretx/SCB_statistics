"""France v2 config — the legacy france.py rebuilt on the framework.

access='internal' → admin/master ONLY (the FR2 beta the legacy page is compared
against; see docs/se2-fr2-parity.md). landing=False keeps it off the home grid.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities

from .provider import France2Provider, micro_year

_YR = micro_year()

# Structured guides (the approved User-Guide design; rendered by core/panels.py)
_GUIDE_EN = {
    "title": "How to use the French Salary Explorer",
    "source": f"INSEE · Net FTE monthly salaries (PCS-ESE 2017) · Melodi API + FD_SALAAN microdata {_YR}",
    "intro": "Look up French salaries by detailed occupation — official data from "
             "INSEE, no technical knowledge needed. This guide covers the three-step "
             "flow, finding occupations, and how to read the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your filters",
         "In the left sidebar: sector (private / public) and optionally a gender."),
        ("Search",
         "Pick one or more occupations, then press the blue Search button at the "
         "bottom of the sidebar."),
        ("Read the results",
         "Explore the tabs on the right. Change any filter and search again to "
         "update the charts."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches both "
                       "titles and PCS codes."),
        ("Drill down", "Or narrow step by step with Group → Category "
                       "(PCS 1 → 2 characters)."),
        ("Code browser", "Open the Code browser to explore the whole PCS-ESE 2017 "
                         "nomenclature."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection above "
                      "the tabs to merge them into one headcount-weighted series."),
    ],
    "charts_title": "Reading the salary charts",
    "charts_intro": "The mean comes live from INSEE's Melodi API; the percentiles are "
                    f"estimates from the anonymised FD_SALAAN microdata ({_YR}, both "
                    "genders together). The grey dashed line is the all-employee "
                    "distribution — how the occupation compares with everyone:",
    "pcts": [("P10", 22, "10% earn less"),
             ("P25", 36, "a quarter earn less"),
             ("MED", 52, "half earn less"),
             ("P75", 68, "a quarter earn more"),
             ("P90", 84, "only 10% earn more")],
    "notes_title": "Good to know",
    "notes": [
        "All figures are net monthly full-time-equivalent salaries (EUR).",
        "For high-paying occupations the top of the range can be blank — INSEE "
        "censors the open top band of the microdata.",
        "The mean/headcount vintage can be a year newer than the microdata "
        "percentiles — the caption shows both.",
        "Interface in English / Français — switch at the top of the sidebar.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "Mean, estimated percentiles, women/men and the F/M gap."),
        ("Salary distribution", "The percentile chart with the all-employee backdrop."),
        ("Trend", "Constant-euro development since 1996 for the occupation's broad "
                  "PCS group (values are already inflation-adjusted)."),
        ("Where do I stand?", "Enter a salary and see the estimated percentile."),
        ("Leaderboard", "Ranks all ~360 occupations by pay within a PCS group."),
        ("By gender / age / region", "Breakdowns — régions at PCS-GROUP level "
                                  "(occupation-level régional data is not published)."),
    ],
    "footer": "Means and headcounts come live from INSEE Melodi; percentiles from the "
              f"FD_SALAAN {_YR} microdata.",
}

_GUIDE_FR = {
    "title": "Comment utiliser l'Explorateur des salaires",
    "source": f"INSEE · Salaires nets mensuels EQTP (PCS-ESE 2017) · API Melodi + microdonnées FD_SALAAN {_YR}",
    "intro": "Consultez les salaires français par profession détaillée — données "
             "officielles INSEE, aucune connaissance technique requise. Ce guide "
             "couvre le flux en trois étapes, la recherche de professions et la "
             "lecture des graphiques.",
    "steps_title": "Pour commencer — trois étapes",
    "steps": [
        ("Choisissez vos filtres",
         "Dans le menu de gauche : secteur (privé / public) et éventuellement un sexe."),
        ("Recherchez",
         "Choisissez une ou plusieurs professions, puis appuyez sur le bouton bleu "
         "Rechercher en bas du menu."),
        ("Lisez les résultats",
         "Explorez les onglets à droite. Modifiez un filtre et relancez la recherche "
         "pour actualiser les graphiques."),
    ],
    "find_title": "Trouver la bonne profession",
    "find": [
        ("Recherche", "Tapez dans « Rechercher un métier… » — titres et codes PCS "
                      "sont reconnus."),
        ("Descendre", "Ou affinez pas à pas avec Groupe → Catégorie "
                      "(PCS 1 → 2 caractères)."),
        ("Nomenclature", "Ouvrez la Nomenclature pour parcourir tout le référentiel "
                         "PCS-ESE 2017."),
        ("Agréger", "Plusieurs métiers choisis ? Activez Agréger la sélection "
                    "au-dessus des onglets pour les fusionner en une série pondérée "
                    "par effectifs."),
    ],
    "charts_title": "Lire les graphiques",
    "charts_intro": "La moyenne vient en direct de l'API Melodi ; les centiles sont "
                    f"des estimations sur les microdonnées FD_SALAAN ({_YR}, deux "
                    "sexes confondus). La ligne grise en pointillés est la "
                    "distribution de l'ensemble des salariés :",
    "pcts": [("P10", 22, "10 % gagnent moins"),
             ("P25", 36, "un quart gagne moins"),
             ("MED", 52, "la moitié gagne moins"),
             ("P75", 68, "un quart gagne plus"),
             ("P90", 84, "seuls 10 % gagnent plus")],
    "notes_title": "À savoir",
    "notes": [
        "Tous les chiffres sont des salaires nets mensuels en équivalent temps "
        "plein (EUR).",
        "Pour les métiers très rémunérateurs, le haut de la distribution peut être "
        "vide — l'INSEE censure la tranche supérieure ouverte.",
        "Le millésime moyenne/effectifs peut être plus récent d'un an que les "
        "centiles microdonnées — la légende indique les deux.",
        "Interface en English / Français — bascule en haut du menu.",
    ],
    "tabs_title": "Les onglets",
    "tabs": [
        ("Aperçu", "Moyenne, centiles estimés, femmes/hommes et écart F/H."),
        ("Distribution", "Le graphique par centile avec la courbe de l'ensemble "
                         "des salariés."),
        ("Évolution", "En euros constants depuis 1996 pour le groupe PCS du métier "
                      "(valeurs déjà corrigées de l'inflation)."),
        ("Où en suis-je ?", "Saisissez un salaire, voyez le centile estimé."),
        ("Classement", "Classe les ~360 métiers par salaire au sein d'un groupe PCS."),
        ("Par sexe / âge / région", "Ventilations — régions au niveau du GROUPE PCS "
                                    "(pas de données régionales par profession)."),
    ],
    "footer": "Moyennes et effectifs en direct de l'API Melodi ; centiles issus des "
              f"microdonnées FD_SALAAN {_YR}.",
}

CONFIG = CountryConfig(
    slug="fr2",
    name="France v2",
    native="République française",
    iso="fr",
    eyebrow="OFFICIAL STATISTICS · FRANCE",
    source_name="INSEE (Melodi + FD_SALAAN microdata)",
    source_url="https://api.insee.fr/melodi/",
    caption=f"INSEE net FTE monthly salaries · EUR · means live, percentiles {_YR} microdata",
    currency="EUR", currency_suffix="€", period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True,      # microdata estimate (see notes)
        has_population_distribution=True,     # all-employee centile backdrop
        has_mean=True, has_median=True,
        has_sex=True, has_age=True, has_region=True,
        has_trend=True, trend_is_real=True,   # 1951→ group series, constant euros
        has_leaderboard=True, leaderboard_scope=1,   # PCS group (1 char)
        sectors=("private", "public"),
        year_range=(_YR, _YR),                # one vintage; no year slider
    ),
    tabs=("overview", "distribution", "trend", "where", "leaderboard",
          "sex", "age", "region", "import_overlay"),
    access="internal",                        # admin/master only (FR2 beta)
    fetch_mode="search",
    landing=False,                            # no home tile — admin preview only
    classification="PCS-ESE 2017",
    labels={"badge": "Beta", "source_short": "INSEE · official"},
    languages=(("EN", "English"), ("FR", "Français")),
    i18n={
        "EN": {
            "title": "French Salary Explorer (v2)",
            "caption": f"INSEE net FTE monthly salaries · EUR · means live, percentiles {_YR} microdata",
            "sector_private": "Private sector", "sector_public": "Public sector",
        },
        "FR": {
            "title": "Explorateur des salaires (v2)",
            "caption": f"Salaires nets mensuels EQTP · EUR · moyennes en direct, centiles microdonnées {_YR}",
            "sector_private": "Secteur privé", "sector_public": "Secteur public",
        },
    },
    guide={"EN": _GUIDE_EN, "FR": _GUIDE_FR},
    provider=France2Provider(),
)
