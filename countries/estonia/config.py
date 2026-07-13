"""Estonia config — Statistics Estonia table PA633. Average gross HOURLY earnings
+ headcount by DETAILED ISCO-08 occupation (446 codes, 1–4-digit hierarchy) ×
sex. Only the mean (no median/deciles) — the trade-off for detailed occupations.
Published every 4 years → snapshot 2022. Presented as an estimated MONTHLY
figure. access='restricted' → BETA (admins + beta users)."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year
from .provider import EstoniaProvider

_YR = latest_year()

_GUIDE_EN = {
    "title": "How to use the Estonian Salary Explorer",
    "source": f"Statistics Estonia · Structure of Earnings by occupation (ISCO) · table PA633 · {_YR}",
    "intro": "Look up Estonian earnings by occupation — official data from "
             "Statistics Estonia's Structure of Earnings statistics, at the full "
             "ISCO occupation detail, published every four years.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your filters", "In the left sidebar: gender, and drill down to an "
                                "occupation."),
        ("Search", "Pick one or more occupations, then press the blue Search "
                   "button at the bottom of the sidebar."),
        ("Read the results", "Explore the tabs on the right. Change a filter and "
                             "search again to update the figures."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches job "
                       "titles and ISCO codes (e.g. Software developers)."),
        ("Drill down", "Or narrow step by step through the ISCO hierarchy "
                       "(major → sub-major → minor → unit group)."),
        ("Code browser", "Open the Code browser to explore the whole ISCO-08 tree."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection to "
                      "merge them into one headcount-weighted series."),
    ],
    "notes_title": "Good to know",
    "notes": [
        "Estonia publishes only the AVERAGE at this occupation detail — no median "
        "or percentiles (the coarser 10-group table has those). So the "
        "distribution and Where-do-I-stand views don't appear.",
        "Estonia publishes gross HOURLY earnings; the figures shown are an "
        "ESTIMATED monthly amount — the hourly earnings × a standard full-time "
        "month (40 h/week, ~173 h). It is an estimate: no official monthly is "
        "published and the sample includes part-time workers.",
        "The Structure of Earnings is a four-yearly survey, so this is a snapshot "
        f"of {_YR} — there is no year-by-year trend (as with the US).",
        "Small occupation × sex cells can be suppressed for privacy — a missing "
        "figure is not an error.",
        "Interface in English / Eesti — switch at the top of the sidebar.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The average pay and headcount for the occupation."),
        ("Leaderboard", "Ranks all occupations by average pay or gender gap."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": f"Figures are an estimated monthly amount from Statistics Estonia's average gross hourly earnings, table PA633 ({_YR}).",
}

_GUIDE_ET = {
    "title": "Kuidas kasutada Eesti palgauurijat",
    "source": f"Statistikaamet · Palgastruktuur ameti järgi (ISCO) · tabel PA633 · {_YR}",
    "intro": "Vaata Eesti töötasu ameti järgi — ametlikud andmed Statistikaameti "
             "palgastruktuuri statistikast, täies ISCO ametidetailis, avaldatakse "
             "iga nelja aasta järel.",
    "steps_title": "Alustamine — kolm sammu",
    "steps": [
        ("Vali filtrid", "Vasakus menüüs: sugu ja kaeva ametini."),
        ("Otsi", "Vali üks või mitu ametit ja vajuta sinist Otsi-nuppu menüü all."),
        ("Loe tulemusi", "Uuri parempoolseid vahekaarte. Muuda filtrit ja otsi "
                         "uuesti."),
    ],
    "find_title": "Õige ameti leidmine",
    "find": [
        ("Otsingukast", "Kirjuta „Otsi ameteid…“ kasti — see sobitab ametinimed ja "
                        "ISCO-koodid (nt Tarkvaraarendajad)."),
        ("Kaeva", "Või kitsenda samm-sammult ISCO hierarhias (pearühm → allpearühm "
                  "→ rühm → allrühm)."),
        ("Koduoversikt", "Ava Koduoversikt kogu ISCO-08 puu uurimiseks."),
        ("Koonda", "Valisid mitu ametit? Lülita Koonda valik nende ühendamiseks."),
    ],
    "notes_title": "Hea teada",
    "notes": [
        "Selles ametidetailis avaldab Eesti ainult KESKMISE — mediaani ega "
        "protsentiile ei ole (need on jämedamas 10-rühma tabelis). Seega "
        "lõnadjaotust ja „Kus ma olen“ vaadet ei kuvata.",
        "Eesti avaldab brutotunnitasu; kuvatavad arvud on HINNANGULINE kuutasu — "
        "tunnitasu × standardne täistööaja kuu (40 t/nädalas, ~173 t). See on "
        "hinnang: ametlikku kuutasu ei avaldata ja valimis on ka osalise "
        "tööajaga töötajad.",
        "Palgastruktuur on neljaaastane uuring, seega on see "
        f"{_YR}. aasta hetkeseis — aastatrendi ei ole (nagu USA puhul).",
        "Väikesed amet × sugu lahtrid võivad olla privaatsuse tõttu peidetud — "
        "vantav arv ei ole viga.",
        "Liides inglise / eesti keeles — vaheta menüü ülaosas.",
    ],
    "tabs_title": "Vahekaardid",
    "tabs": [
        ("Ülevaade", "Ameti keskmine palk ja töötajate arv."),
        ("Edetabel", "Järjestab ametid keskmise palga või palgalõhe järgi."),
        ("Soo järgi", "Naised vs mehed, naised-%-meestest vaatega."),
    ],
    "footer": f"Arvud on hinnanguline kuutasu Statistikaameti keskmisest brutotunnitasust, tabel PA633 ({_YR}).",
}

CONFIG = CountryConfig(
    slug="estonia",
    name="Estonia",
    native="Eesti",
    iso="ee",
    eyebrow="OFFICIAL STATISTICS · ESTONIA",
    source_name="Statistics Estonia",
    source_url="https://andmed.stat.ee/en/stat/majandus__palk-ja-toojeukulu__tootasu",
    caption=f"Statistics Estonia · Average earnings by occupation (ISCO) · {_YR}",
    currency="EUR", currency_suffix="€", money_prefix=False, period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=False,
        has_occupation_hierarchy=True,       # full ISCO 1–4 digit
        has_quartiles=False,
        has_mean=True, has_median=False, has_sex=True,
        has_trend=False,                     # 4-yearly snapshot
        has_leaderboard=True, leaderboard_scope=2,
        sectors=(),
        year_range=(_YR, _YR),
    ),
    tabs=("overview", "leaderboard", "sex", "import_overlay"),
    access="registered",                     # LIVE — any signed-in user
    fetch_mode="search",
    landing=True,
    classification="ISCO-08",
    bullets=(
        "Average salary · ~450 occupations (ISCO)",
        "Hierarchy drill-down · gender split",
        f"Est. monthly earnings · {_YR} (4-yearly)",
    ),
    labels={"badge": "Live", "source_short": "Stat. Estonia · official"},
    languages=(("EN", "English"), ("ET", "Eesti")),
    i18n={
        "EN": {"title": "Estonian Salary Explorer",
               "caption": f"Statistics Estonia · Average earnings by occupation (ISCO) · {_YR}",
               "brlvl_1": "Major group", "brlvl_2": "Sub-major group",
               "brlvl_3": "Minor group", "brlvl_4": "Unit group"},
        "ET": {"title": "Eesti palgauurija",
               "caption": f"Statistikaamet · Keskmine töötasu ameti järgi (ISCO) · {_YR}",
               "brlvl_1": "Pearühm", "brlvl_2": "Allpearühm",
               "brlvl_3": "Rühm", "brlvl_4": "Allrühm"},
    },
    guide={"EN": _GUIDE_EN, "ET": _GUIDE_ET},
    provider=EstoniaProvider(),
)
