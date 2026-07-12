"""Estonia config — Statistics Estonia PA623. Gross HOURLY earnings (EUR) by
ISCO-08 MAJOR GROUP (10 groups) × sex; P10·median·P90 (deciles). Coarse: no
detailed occupations, no hierarchy, published every 4 years so it's a snapshot
of the latest SES year. access='restricted' → BETA (admins + beta users)."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import EstoniaProvider

_YR = latest_year()

_GUIDE_EN = {
    "title": "How to use the Estonian Salary Explorer",
    "source": f"Statistics Estonia · Structure of Earnings (ISCO major groups) · table PA623 · {_YR}",
    "intro": "Look up Estonian earnings by occupational group — official data from "
             "Statistics Estonia's Structure of Earnings statistics. Estonia "
             "publishes this by broad occupational group every four years.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your filters", "In the left sidebar: gender."),
        ("Search", "Pick one or more occupational groups, then press the blue "
                   "Search button at the bottom of the sidebar."),
        ("Read the results", "Explore the tabs on the right. Change a filter and "
                             "search again to update the charts."),
    ],
    "find_title": "Finding the right group",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches the "
                       "ISCO major-group names."),
        ("Ten groups", "Estonia publishes earnings for the ten ISCO-08 major "
                       "groups only (Managers, Professionals, … Elementary "
                       "occupations), not detailed occupations."),
        ("Aggregate", "Picked several groups? Toggle Aggregate selection to merge "
                      "them into one series."),
    ],
    "charts_title": "Reading the wage charts",
    "charts_intro": "Earnings are shown as the 1st decile, median and 9th decile "
                    "— a wide P10–P90 gap means pay varies a lot in that group "
                    "(the average is a separate ♦ marker):",
    "pcts": [("P10", 24, "10% earn less"),
             ("MED", 52, "half earn less"),
             ("P90", 84, "only 10% earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Estonia publishes gross HOURLY earnings; the figures shown are an "
        "ESTIMATED monthly amount — the hourly earnings × a standard full-time "
        "month (40 h/week, ~173 h). It is an estimate: no official monthly is "
        "published and the sample includes part-time workers.",
        "Estonia's Structure of Earnings is a four-yearly survey, so this is a "
        f"snapshot of {_YR} — there is no year-by-year trend (as with the US).",
        "Only the ten ISCO major groups are published — there are no detailed "
        "occupations.",
        "Interface in English / Eesti — switch at the top of the sidebar.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance."),
        ("Salary distribution", "The P10–median–P90 chart, plus raw data + CSV."),
        ("Where do I stand?", "Enter a monthly salary and see roughly where it falls."),
        ("Leaderboard", "Ranks the occupational groups by pay or gender gap."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": f"Figures are an estimated monthly amount from Statistics Estonia's gross hourly earnings, table PA623 ({_YR}).",
}

_GUIDE_ET = {
    "title": "Kuidas kasutada Eesti palgauurijat",
    "source": f"Statistikaamet · Palgastruktuur (ISCO pearühmad) · tabel PA623 · {_YR}",
    "intro": "Vaata Eesti töötasu ametialarühma järgi — ametlikud andmed "
             "Statistikaameti palgastruktuuri statistikast. Eesti avaldab need "
             "laiade ametialarühmade kaupa iga nelja aasta järel.",
    "steps_title": "Alustamine — kolm sammu",
    "steps": [
        ("Vali filtrid", "Vasakus menüüs: sugu."),
        ("Otsi", "Vali üks või mitu ametialarühma ja vajuta sinist Otsi-nuppu "
                 "menüü all."),
        ("Loe tulemusi", "Uuri parempoolseid vahekaarte. Muuda filtrit ja otsi "
                         "uuesti, et diagramme värskendada."),
    ],
    "find_title": "Õige rühma leidmine",
    "find": [
        ("Otsingukast", "Kirjuta „Otsi ameteid…“ kasti — see sobitab ISCO "
                        "pearühmade nimed."),
        ("Kümme rühma", "Eesti avaldab töötasu ainult kümne ISCO-08 pearühma kohta "
                        "(juhid, tippspetsialistid, … lihttöölised), mitte "
                        "üksikametite kaupa."),
        ("Koonda", "Valisid mitu rühma? Lülita Koonda valik, et need üheks reaks "
                   "ühendada."),
    ],
    "charts_title": "Palgadiagrammide lugemine",
    "charts_intro": "Töötasu näidatakse 1. detsiili, mediaani ja 9. detsiilina — "
                    "suur P10–P90 vahe tähendab suurt palgahajuvust (keskmine on "
                    "eraldi ♦-märk):",
    "pcts": [("P10", 24, "10% teenib vähem"),
             ("MED", 52, "pooled teenivad vähem"),
             ("P90", 84, "vaid 10% teenib rohkem")],
    "notes_title": "Hea teada",
    "notes": [
        "Eesti avaldab brutotunnitasu; kuvatavad arvud on HINNANGULINE kuutasu — "
        "tunnitasu × standardne täistööaja kuu (40 t/nädalas, ~173 t). See on "
        "hinnang: ametlikku kuutasu ei avaldata ja valimis on ka osalise "
        "tööajaga töötajad.",
        "Eesti palgastruktuur on neljaaastane uuring, seega on see "
        f"{_YR}. aasta hetkeseis — aastatrendi ei ole (nagu USA puhul).",
        "Avaldatakse ainult kümme ISCO pearühma — üksikameteid ei ole.",
        "Liides inglise / eesti keeles — vaheta menüü ülaosas.",
    ],
    "tabs_title": "Vahekaardid",
    "tabs": [
        ("Ülevaade", "Põhinäitajad ühe pilguga."),
        ("Palgajaotus", "P10–mediaan–P90 diagramm, pluss toorandmed + CSV."),
        ("Kus ma olen?", "Sisesta kuupalk ja vaata ligikaudu, kuhu see jääb."),
        ("Edetabel", "Järjestab ametialarühmad palga või palgalõhe järgi."),
        ("Soo järgi", "Naised vs mehed, naised-%-meestest vaatega."),
    ],
    "footer": f"Arvud on hinnanguline kuutasu Statistikaameti brutotunnitasust, tabel PA623 ({_YR}).",
}

CONFIG = CountryConfig(
    slug="estonia",
    name="Estonia",
    native="Eesti",
    iso="ee",
    eyebrow="OFFICIAL STATISTICS · ESTONIA",
    source_name="Statistics Estonia",
    source_url="https://andmed.stat.ee/en/stat/majandus__palk-ja-toojeukulu__tootasu",
    caption=f"Statistics Estonia · Structure of Earnings by occupational group (ISCO) · {_YR}",
    currency="EUR", currency_suffix="€", money_prefix=False, period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True,     # P10 · median · P90 (deciles)
        has_occupation_hierarchy=False,      # 10 flat major groups, no drill-down
        has_mean=True, has_median=True, has_sex=True,
        has_trend=False,                     # 4-yearly snapshot
        has_leaderboard=True, leaderboard_scope=1,
        sectors=(),                          # no sector dimension
        year_range=(_YR, _YR),               # single SES snapshot
    ),
    tabs=("overview", "distribution", "where", "leaderboard", "sex", "import_overlay"),
    access="restricted",                     # BETA — admins + beta users only
    fetch_mode="search",
    landing=True,
    classification="ISCO-08 major groups",
    bullets=(
        "Mean, median &amp; deciles · 10 ISCO major groups",
        "Gender breakdown · P10–P90",
        f"Est. monthly earnings · {_YR} (4-yearly)",
    ),
    labels={"badge": "Beta", "source_short": "Stat. Estonia · official"},
    languages=(("EN", "English"), ("ET", "Eesti")),
    i18n={
        "EN": {"title": "Estonian Salary Explorer",
               "caption": f"Statistics Estonia · Structure of Earnings by occupational group (ISCO) · {_YR}"},
        "ET": {"title": "Eesti palgauurija",
               "caption": f"Statistikaamet · Palgastruktuur ametialarühma järgi (ISCO) · {_YR}"},
    },
    guide={"EN": _GUIDE_EN, "ET": _GUIDE_ET},
    provider=EstoniaProvider(),
)
