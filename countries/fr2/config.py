"""France v2 config — the legacy france.py rebuilt on the framework.

access='internal' → admin/master ONLY (the FR2 beta the legacy page is compared
against; see docs/se2-fr2-parity.md). landing=False keeps it off the home grid.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities

from .provider import France2Provider, micro_year

_YR = micro_year()

_GUIDE_EN = """
**What this shows.** Net monthly full-time-equivalent salaries for ~360 detailed
occupations (PCS-ESE 2017) in France: the **mean** (live from INSEE's Melodi
API, private or public sector) and an estimated **P10 / P25 / median / P75 /
P90 distribution** per occupation (from INSEE's anonymised FD_SALAAN microdata,
both sexes together).

**How to use it**
1. Pick a **sector** (private / public) and optionally a **sex**.
2. Narrow by PCS group → category, pick occupation(s), press **Search**.

**Good to know**
- This is **France v2** — the framework rebuild of the original France page.
  The long-run (1951→) constant-euro series and the population distribution
  view still live on the original page.
- Percentiles are **microdata estimates** ({yr}, both sexes); the mean and
  headcount are the latest official Melodi figures and can be a year newer.
""".format(yr=_YR)

_GUIDE_FR = """
**Ce que montre cette page.** Salaires nets mensuels en équivalent temps plein
pour ~360 professions détaillées (PCS-ESE 2017) : la **moyenne** (en direct de
l'API Melodi de l'INSEE, secteur privé ou public) et une **distribution estimée
P10 / P25 / médiane / P75 / P90** par profession (microdonnées anonymisées
FD_SALAAN, deux sexes confondus).

**Mode d'emploi**
1. Choisissez un **secteur** (privé / public) et éventuellement un **sexe**.
2. Affinez par groupe → catégorie PCS, choisissez la ou les professions,
   puis **Rechercher**.

**À savoir**
- Ceci est **France v2** — la version « framework » de la page France
  d'origine. Les séries longues (1951→) en euros constants et la distribution
  de la population restent sur la page d'origine.
- Les centiles sont des **estimations sur microdonnées** ({yr}, deux sexes) ;
  la moyenne et les effectifs sont les derniers chiffres officiels Melodi et
  peuvent être plus récents d'un an.
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
        has_mean=True, has_median=True,
        has_sex=True,
        has_leaderboard=True, leaderboard_scope=1,   # PCS group (1 char)
        sectors=("private", "public"),
        year_range=(_YR, _YR),                # one vintage; no year slider
    ),
    tabs=("overview", "distribution", "where", "leaderboard", "sex"),
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
