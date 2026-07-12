"""Finland config — StatFin Structure of Earnings (table 15au) + region table
15b2. P10·median·P90 + mean by ISCO occupation × sector × sex, an annual
snapshot (no trend). Region-simulation overlay from 15b2. access='restricted'
→ BETA (admins + beta users)."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import FinlandProvider

_YR = latest_year()

_GUIDE_EN = {
    "title": "How to use the Finnish Salary Explorer",
    "source": "Statistics Finland (StatFin) · Structure of Earnings (ISCO) · table 15au",
    "intro": "Look up Finnish salaries by occupation — official data from "
             "Statistics Finland's Structure of Earnings statistics. This guide "
             "covers the three-step flow, finding occupations, and how to read "
             "the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your filters", "In the left sidebar: sector (all, corporations, "
                                "central/local government, wellbeing county) and "
                                "gender."),
        ("Search", "Pick one or more occupations, then press the blue Search "
                   "button at the bottom of the sidebar."),
        ("Read the results", "Explore the tabs on the right. Change any filter and "
                             "search again to update the charts."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches both "
                       "job titles and ISCO codes."),
        ("Drill down", "Or narrow step by step with the ISCO hierarchy "
                       "(1 → 2 → 3 → 4 digit)."),
        ("Code browser", "Open the Code browser to explore the whole classification."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection to "
                      "merge them into one headcount-weighted series."),
    ],
    "charts_title": "Reading the wage charts",
    "charts_intro": "Statistics Finland publishes the 1st decile, median and 9th "
                    "decile — a wide P10–P90 gap means pay varies a lot in that "
                    "job (the average is a separate ♦ marker):",
    "pcts": [("P10", 24, "10% earn less"),
             ("MED", 52, "half earn less"),
             ("P90", 84, "only 10% earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are total monthly earnings (EUR) for full-time wage and salary "
        "earners.",
        "The occupation data is a single annual snapshot, so there is no trend "
        "view (as with the US page).",
        "Small occupation groups can be suppressed for privacy — a missing figure "
        "is not an error.",
        "The “By region” tab is a simulation — it applies a region's overall pay "
        "difference to the occupation, not occupation-specific regional data.",
        "Interface in English / Suomi — switch at the top of the sidebar.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance, plus employment."),
        ("Salary distribution", "The P10–median–P90 chart, plus raw data + CSV."),
        ("Where do I stand?", "Enter a salary and see roughly where it falls."),
        ("Leaderboard", "Ranks all occupations by pay or gender gap."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
        ("By region", "Estimate a region by applying its overall pay difference "
                      "(a simulation)."),
    ],
    "footer": "All figures are from Statistics Finland's Structure of Earnings (table 15au), updated annually.",
}

_GUIDE_FI = {
    "title": "Näin käytät suomalaista palkkaselainta",
    "source": "Tilastokeskus (StatFin) · Palkkarakenne (ISCO) · taulukko 15au",
    "intro": "Katso suomalaisia palkkoja ammatin mukaan — virallista tietoa "
             "Tilastokeskuksen palkkarakennetilastosta. Tämä opas käy läpi "
             "kolmivaiheisen kulun, ammattien löytämisen ja kuvaajien lukemisen.",
    "steps_title": "Näin pääset alkuun — kolme vaihetta",
    "steps": [
        ("Valitse suodattimet", "Vasemmasta valikosta: sektori (kaikki, yritykset, "
                                "valtio/kunnat, hyvinvointialue) ja sukupuoli."),
        ("Hae", "Valitse yksi tai useampi ammatti ja paina sinistä Hae-painiketta "
                "valikon alaosassa."),
        ("Lue tulokset", "Tutki oikean puolen välilehtiä. Muuta suodatinta ja hae "
                         "uudelleen päivittääksesi kuvaajat."),
    ],
    "find_title": "Oikean ammatin löytäminen",
    "find": [
        ("Hakukenttä", "Kirjoita ”Hae ammatteja…” -kenttään — se osuu sekä "
                       "ammattinimikkeisiin että ISCO-koodeihin."),
        ("Poraudu", "Tai rajaa vaihe vaiheelta ISCO-luokituksella "
                    "(1 → 2 → 3 → 4 numeroa)."),
        ("Koodiselain", "Avaa Koodiselain tutkiaksesi koko luokitusta."),
        ("Yhdistä", "Valitsitko useita ammatteja? Kytke Yhdistä valinta "
                    "yhdistääksesi ne yhdeksi lukumäärällä painotetuksi sarjaksi."),
    ],
    "charts_title": "Palkkakuvaajien lukeminen",
    "charts_intro": "Tilastokeskus julkaisee 1. desiilin, mediaanin ja 9. desiilin "
                    "— suuri P10–P90-väli tarkoittaa suurta palkkahajontaa "
                    "(keskiarvo on erillinen ♦-merkki):",
    "pcts": [("P10", 24, "10 % ansaitsee vähemmän"),
             ("MED", 52, "puolet ansaitsee vähemmän"),
             ("P90", 84, "vain 10 % ansaitsee enemmän")],
    "notes_title": "Hyvä tietää",
    "notes": [
        "Luvut ovat kokoaikaisten palkansaajien kokonaiskuukausiansioita (euroa).",
        "Ammattitiedot ovat yhden vuoden tilannekuva, joten trendinäkymää ei ole "
        "(kuten Yhdysvaltain sivulla).",
        "Pienet ammattiryhmät voidaan salata yksityisyyden vuoksi — puuttuva luku "
        "ei ole virhe.",
        "”Alueittain”-välilehti on simulaatio — se soveltaa alueen yleistä "
        "palkkaeroa ammattiin, ei ammattikohtaista aluetietoa.",
        "Käyttöliittymä: English / Suomi — vaihda valikon yläosassa.",
    ],
    "tabs_title": "Välilehdet",
    "tabs": [
        ("Yleiskatsaus", "Avainluvut yhdellä silmäyksellä, plus lukumäärä."),
        ("Palkkajakauma", "P10–mediaani–P90-kuvaaja, plus raakadata + CSV."),
        ("Missä olen?", "Syötä palkka ja katso suunnilleen mihin se osuu."),
        ("Kärkilista", "Järjestää kaikki ammatit palkan tai palkkaeron mukaan."),
        ("Sukupuolen mukaan", "Naiset vs. miehet, naiset-%-miehistä-näkymällä."),
        ("Alueittain", "Arvioi alue soveltamalla sen yleistä palkkaeroa (simulaatio)."),
    ],
    "footer": "Kaikki luvut ovat Tilastokeskuksen palkkarakennetilastosta (taulukko 15au), päivitetään vuosittain.",
}

CONFIG = CountryConfig(
    slug="finland",
    name="Finland",
    native="Suomi",
    iso="fi",
    eyebrow="OFFICIAL STATISTICS · FINLAND",
    source_name="Statistics Finland (StatFin)",
    source_url="https://pxdata.stat.fi/PxWeb/pxweb/en/StatFin/StatFin__pra/",
    caption="Statistics Finland · Structure of Earnings by occupation (ISCO)",
    currency="EUR", currency_suffix="€", money_prefix=False, period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True,     # P10 · median · P90 (deciles)
        has_occupation_hierarchy=True,
        has_mean=True, has_median=True, has_sex=True,
        has_trend=False,                     # annual snapshot (like the US)
        has_leaderboard=True,
        has_region_sim=True,                 # StatFin 15b2 region overlay (simulation)
        sectors=("all", "private", "central", "local", "wellbeing"),
        year_range=(_YR, _YR),               # single snapshot year
    ),
    tabs=("overview", "distribution", "where", "leaderboard", "sex",
          "region_sim", "import_overlay"),
    access="restricted",                     # BETA — admins + beta users only
    fetch_mode="search",
    landing=True,
    classification="ISCO-08",
    bullets=(
        "P10–P90 + mean · ~500 occupations (ISCO)",
        "Sector &amp; gender breakdowns · region simulation",
        f"Monthly earnings · {_YR} snapshot",
    ),
    labels={"badge": "Beta", "source_short": "StatFin · official"},
    languages=(("EN", "English"), ("FI", "Suomi")),
    i18n={
        "EN": {"title": "Finnish Salary Explorer",
               "caption": "Statistics Finland · Structure of Earnings by occupation (ISCO)",
               "sector_all": "All sectors",
               "sector_private": "Private sector (corporations)",
               "sector_central": "Central government",
               "sector_local": "Local government",
               "sector_wellbeing": "Wellbeing services county"},
        "FI": {"title": "Suomalainen palkkaselain",
               "caption": "Tilastokeskus · Palkkarakenne ammatin mukaan (ISCO)",
               "sector_all": "Kaikki sektorit",
               "sector_private": "Yksityinen sektori (yritykset)",
               "sector_central": "Valtio",
               "sector_local": "Kunnat",
               "sector_wellbeing": "Hyvinvointialue"},
    },
    guide={"EN": _GUIDE_EN, "FI": _GUIDE_FI},
    provider=FinlandProvider(),
)
