"""Iceland config — Hagstofa VIN02001. Quartiles + mean + median by ISCO
occupation × sex, 2014→, with trend. No sector dimension (all sectors pooled)
and no region breakdown. access='restricted' → BETA (admins + beta users)."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year, FIRST_YEAR
from .provider import IcelandProvider

_YR = latest_year()

_GUIDE_EN = {
    "title": "How to use the Icelandic Salary Explorer",
    "source": "Statistics Iceland (Hagstofa) · Earnings by occupation (ISCO) · table VIN02001",
    "intro": "Look up Icelandic salaries by occupation — official data from "
             "Statistics Iceland, no technical knowledge needed. This guide covers "
             "the three-step flow, finding occupations, and how to read the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your filters", "In the left sidebar: gender and a year range "
                                "(2014 onward)."),
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
    "charts_title": "Reading the salary charts",
    "charts_intro": "Statistics Iceland publishes quartiles, not the full "
                    "percentile range. Every chart shows three points (the average "
                    "is a separate ♦ marker):",
    "pcts": [("P25", 32, "a quarter earn less"),
             ("MED", 52, "half earn less"),
             ("P75", 72, "a quarter earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are total regular monthly earnings (ISK) for full-time employees.",
        "Very small occupation groups can be suppressed for privacy — a missing "
        "figure is not an error.",
        "The mean can sit above the median when a few high salaries pull the "
        "average up.",
        "Interface in English / Íslenska — switch at the top of the sidebar.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance, with a year selector."),
        ("Salary distribution", "The quartile chart, plus raw data + CSV export."),
        ("Trend", "Development over time (2014 onward)."),
        ("Where do I stand?", "Enter a salary and see roughly where it falls."),
        ("Leaderboard", "Ranks all occupations by pay or gender gap."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "All figures are total regular monthly earnings from Hagstofa table VIN02001, updated annually.",
}

_GUIDE_IS = {
    "title": "Hvernig á að nota íslenska launasjána",
    "source": "Hagstofa Íslands · Laun eftir starfi (ÍSTARF/ISCO) · tafla VIN02001",
    "intro": "Flettu upp íslenskum launum eftir starfi — opinber gögn frá "
             "Hagstofu Íslands. Þessi leiðarvísir fer yfir þriggja skrefa ferlið, "
             "hvernig á að finna störf og hvernig á að lesa myndritin.",
    "steps_title": "Komdu þér af stað — þrjú skref",
    "steps": [
        ("Veldu síur", "Í vinstri valmynd: kyn og árabil (frá 2014)."),
        ("Leita", "Veldu eitt eða fleiri störf og ýttu á bláa Leita-hnappinn "
                  "neðst í valmyndinni."),
        ("Lestu niðurstöður", "Skoðaðu flipana til hægri. Breyttu síu og leitaðu "
                              "aftur til að uppfæra myndritin."),
    ],
    "find_title": "Að finna rétta starfið",
    "find": [
        ("Leitarreitur", "Skrifaðu í „Leita að störfum…“ — það passar bæði "
                         "starfsheiti og ISCO-kóða."),
        ("Kafa niður", "Eða þrengdu skref fyrir skref eftir ISCO-flokkun "
                       "(1 → 2 → 3 → 4 stafa)."),
        ("Kóðavafri", "Opnaðu Kóðavafra til að skoða alla flokkunina."),
        ("Sameina", "Valdir mörg störf? Kveiktu á Sameina valið til að sameina "
                    "þau í eina röð vegna eftir fjölda."),
    ],
    "charts_title": "Að lesa launamyndritin",
    "charts_intro": "Hagstofan birtir fjórðungsmörk, ekki allt hundraðshlutabilið. "
                    "Hvert myndrit sýnir þrjá punkta (meðaltalið er sér ♦-merki):",
    "pcts": [("P25", 32, "fjórðungur er með lægri laun"),
             ("MED", 52, "helmingur er með lægri laun"),
             ("P75", 72, "fjórðungur er með hærri laun")],
    "notes_title": "Gott að vita",
    "notes": [
        "Tölurnar eru regluleg heildarmánaðarlaun (kr.) fyrir fullt starf.",
        "Mjög litlir starfahópar geta verið faldir vegna persónuverndar — vantandi "
        "tala er ekki villa.",
        "Meðaltalið getur verið yfir miðgildinu þegar fá há laun draga það upp.",
        "Viðmót á English / Íslenska — skiptu efst í valmyndinni.",
    ],
    "tabs_title": "Flipar",
    "tabs": [
        ("Yfirlit", "Lykiltölurnar á einum stað, með ársvali."),
        ("Launadreifing", "Fjórðungsmyndritið, auk hrágagna + CSV-útflutnings."),
        ("Þróun", "Þróun yfir tíma (frá 2014)."),
        ("Hvar stend ég?", "Sláðu inn laun og sjáðu um það bil hvar þau liggja."),
        ("Topplisti", "Raðar öllum störfum eftir launum eða kynjabili."),
        ("Eftir kyni", "Konur á móti körlum, með konur-sem-%-af-körlum sýn."),
    ],
    "footer": "Allar tölur eru regluleg heildarmánaðarlaun úr Hagstofu-töflu VIN02001, uppfært árlega.",
}

CONFIG = CountryConfig(
    slug="iceland",
    name="Iceland",
    native="Ísland",
    iso="is",
    eyebrow="OFFICIAL STATISTICS · ICELAND",
    source_name="Statistics Iceland (Hagstofa)",
    source_url="https://px.hagstofa.is/pxen/pxweb/en/Samfelag/",
    caption="Statistics Iceland (Hagstofa) · Monthly earnings by occupation (ISCO)",
    currency="ISK", currency_suffix="kr", period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=False,
        has_occupation_hierarchy=True,
        has_quartiles=True,
        has_mean=True, has_median=True, has_sex=True, has_trend=True,
        has_leaderboard=True,
        sectors=(),                          # VIN02001 has no sector dimension
        year_range=(FIRST_YEAR, _YR),
    ),
    tabs=("overview", "distribution", "trend", "where", "leaderboard", "sex",
          "import_overlay"),
    access="registered",                     # LIVE — any signed-in user
    fetch_mode="search",
    landing=True,
    classification="ISCO-08",
    bullets=(
        "Mean &amp; median salary · ~140 occupations (ISCO)",
        "Gender breakdown · quartiles",
        f"Monthly earnings · 2014–{_YR}",
    ),
    labels={"badge": "Live", "source_short": "Hagstofa · official"},
    languages=(("EN", "English"), ("IS", "Íslenska")),
    i18n={
        "EN": {"title": "Icelandic Salary Explorer",
               "caption": "Statistics Iceland (Hagstofa) · Monthly earnings by occupation (ISCO)"},
        "IS": {"title": "Íslensk launasjá",
               "caption": "Hagstofa Íslands · Mánaðarlaun eftir starfi (ÍSTARF/ISCO)"},
    },
    guide={"EN": _GUIDE_EN, "IS": _GUIDE_IS},
    provider=IcelandProvider(),
)
