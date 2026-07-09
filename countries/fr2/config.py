"""France v2 config — the legacy france.py rebuilt on the framework.

access='internal' → admin/master ONLY (the FR2 beta the legacy page is compared
against; see docs/se2-fr2-parity.md). landing=False keeps it off the home grid.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities

from .provider import France2Provider, micro_year

_YR = micro_year()

_GUIDE_EN = """
# 👋 Welcome to the French Salary Explorer

Look up **French salaries** by detailed occupation (PCS-ESE 2017) — official
data from INSEE. No technical knowledge needed.

## 🚀 Getting started — 3 steps
1. **Choose your filters** in the left sidebar: sector (private / public),
   optionally a sex, and an occupation.
2. Click **🔍 Search**.
3. **Read the results** in the tabs. Change a filter and search again to update.

## 🔎 Finding the right occupation
- Type in the **"Search occupations…"** box — it matches titles and codes.
- Or drill down with **Group → Category** (PCS 1 → 2 characters).
- Open the **Code browser** to explore the whole nomenclature.
- Picked several occupations? Toggle **Aggregate selection** above the tabs.

## 📈 Reading the salary charts
- The **mean** comes live from INSEE's Melodi API (latest published year).
- **P10 / P25 / Median / P75 / P90** are estimates from INSEE's anonymised
  **FD_SALAAN microdata** ({yr}, both sexes together). For high-paying
  occupations the top of the range can be blank — INSEE censors the open top
  band.
- The grey dashed line is the **all-employee distribution** — how the
  occupation compares with everyone.

## 🗂 The tabs
- **Overview** — mean, estimated percentiles, women/men and the F/M gap.
- **Salary distribution** — the percentile chart with the population backdrop.
- **Trend** — constant-euro development since 1996 for the occupation's broad
  PCS group (values are already inflation-adjusted).
- **Where do I stand?** — enter a salary and see the estimated percentile.
- **Leaderboard** — ranks all ~360 occupations by pay within a PCS group.
- **By sex / age / region** — breakdowns (régions at PCS-GROUP level:
  occupation-level régional data is not published).

## ❓ Good to know
- All figures are **net monthly full-time-equivalent** salaries (EUR).
- The mean/headcount vintage can be a year newer than the microdata
  percentiles — the caption shows both.
- Interface in **English / Français** — switch at the top of the sidebar.
""".format(yr=_YR)

_GUIDE_FR = """
# 👋 Bienvenue dans l'Explorateur des salaires

Consultez les **salaires français** par profession détaillée (PCS-ESE 2017) —
données officielles INSEE. Aucune connaissance technique requise.

## 🚀 Pour commencer — 3 étapes
1. **Choisissez vos filtres** dans le menu de gauche : secteur (privé /
   public), éventuellement un sexe, et une profession.
2. Cliquez sur **🔍 Rechercher**.
3. **Lisez les résultats** dans les onglets. Modifiez un filtre et relancez la
   recherche pour actualiser.

## 🔎 Trouver la bonne profession
- Tapez dans **« Rechercher un métier… »** — titres et codes sont reconnus.
- Ou descendez par **Groupe → Catégorie** (PCS 1 → 2 caractères).
- Ouvrez la **Nomenclature** pour parcourir tous les codes.
- Plusieurs métiers choisis ? Activez **Agréger la sélection** au-dessus des
  onglets.

## 📈 Lire les graphiques
- La **moyenne** vient en direct de l'API Melodi (dernière année publiée).
- **P10 / P25 / Médiane / P75 / P90** sont des estimations sur les
  **microdonnées FD_SALAAN** ({yr}, deux sexes confondus). Pour les métiers
  très rémunérateurs, le haut de la distribution peut être vide — l'INSEE
  censure la tranche supérieure ouverte.
- La ligne grise en pointillés est la **distribution de l'ensemble des
  salariés** — pour situer le métier par rapport à tous.

## 🗂 Les onglets
- **Aperçu** — moyenne, centiles estimés, femmes/hommes et écart F/H.
- **Distribution des salaires** — le graphique par centile avec la courbe de
  l'ensemble des salariés.
- **Évolution** — en euros constants depuis 1996 pour le groupe PCS du métier
  (valeurs déjà corrigées de l'inflation).
- **Où en suis-je ?** — saisissez un salaire, voyez le centile estimé.
- **Classement** — classe les ~360 métiers par salaire au sein d'un groupe.
- **Par sexe / âge / région** — ventilations (régions au niveau du GROUPE
  PCS : les données régionales par profession ne sont pas publiées).

## ❓ À savoir
- Tous les chiffres sont des salaires **nets mensuels en équivalent temps
  plein** (EUR).
- Le millésime moyenne/effectifs peut être plus récent d'un an que les
  centiles microdonnées — la légende indique les deux.
- Interface en **English / Français** — bascule en haut du menu.
""".format(yr=_YR)

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
