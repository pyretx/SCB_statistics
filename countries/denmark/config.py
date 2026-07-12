"""Denmark config — the entire country-specific surface (this + provider.py).
access='restricted' → BETA: admins + beta users (incl. per-country grants) only;
everyone else sees a locked tile on the landing catalog."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .build import latest_year, FIRST_YEAR
from .provider import DenmarkProvider

_YR = latest_year()   # pinned in app_settings.json; bumped via the admin panel

# Structured guides (the approved User-Guide design; rendered by core/panels.py)
_GUIDE_EN = {
    "title": "How to use the Danish Salary Explorer",
    "source": "Statistics Denmark (DST) · Standardized hourly earnings by occupation (DISCO-08) · table LONS20",
    "intro": "Look up Danish salaries by occupation — official data from Statistics "
             "Denmark, no technical knowledge needed. This guide covers the three-step "
             "flow, finding occupations, and how to read the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your filters",
         "In the left sidebar: sector (all, corporations & organizations, "
         "municipal / regional, or central government), gender, and a year range "
         "(2013 onward)."),
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
                       "titles and DISCO codes."),
        ("Drill down", "Or narrow step by step with Main group → Sub-group → Minor "
                       "group (DISCO 1 → 2 → 3 digit)."),
        ("Code browser", "Open the Code browser to explore the entire DISCO-08 "
                         "classification tree."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection above "
                      "the tabs to merge them into one headcount-weighted series."),
    ],
    "charts_title": "Reading the salary charts",
    "charts_intro": "DST publishes quartiles, not the full percentile range. "
                    "Every chart shows three points (the average is a separate ♦ marker):",
    "pcts": [("P25", 32, "a quarter earn less"),
             ("MED", 52, "half earn less"),
             ("P75", 72, "a quarter earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are standardized HOURLY earnings (DKK) — DST's headline measure, "
        "computed per standard hour so absence doesn't distort the comparison. "
        "For a rough monthly figure, multiply by about 160 (a standard month).",
        "Earnings include pension contributions, holiday allowance and fringe "
        "benefits — Danish pay is usually quoted this way.",
        "Small groups can be suppressed by DST for privacy — a missing occupation "
        "or year is not an error.",
        "The mean can sit above the median when a few high salaries pull the "
        "average up.",
        "Interface in English / Dansk — switch at the top of the sidebar.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance, with a year selector."),
        ("Salary distribution", "The quartile chart, plus raw data + CSV export."),
        ("Trend", "Development over time: nominal, growth vs inflation (CPI), or "
                  "real (constant prices)."),
        ("Where do I stand?", "Enter an hourly wage and see roughly where it falls."),
        ("Leaderboard", "Ranks all occupations by pay, gender gap or growth."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
    ],
    "footer": "All figures are standardized hourly earnings from DST table LONS20, updated annually.",
}

_GUIDE_DA = {
    "title": "Sådan bruger du den danske lønudforsker",
    "source": "Danmarks Statistik (DST) · Standardberegnet timefortjeneste efter arbejdsfunktion (DISCO-08) · tabel LONS20",
    "intro": "Slå danske lønninger op efter arbejdsfunktion — officielle data fra "
             "Danmarks Statistik, ingen tekniske forudsætninger kræves. Denne guide "
             "dækker tre-trins-flowet, hvordan du finder arbejdsfunktioner, og "
             "hvordan du læser diagrammerne.",
    "steps_title": "Kom i gang — tre trin",
    "steps": [
        ("Vælg dine filtre",
         "I menuen til venstre: sektor (alle, virksomheder og organisationer, "
         "kommuner og regioner, eller staten), køn og et årsinterval (fra 2013)."),
        ("Søg",
         "Vælg en eller flere arbejdsfunktioner, og tryk på den blå Søg-knap "
         "nederst i menuen."),
        ("Læs resultaterne",
         "Udforsk fanerne til højre. Ændr et filter og søg igen for at opdatere "
         "diagrammerne."),
    ],
    "find_title": "Find den rigtige arbejdsfunktion",
    "find": [
        ("Søgefelt", "Skriv i »Søg arbejdsfunktioner…«-feltet — det matcher både "
                     "titler og DISCO-koder."),
        ("Trin for trin", "Eller indsnævr trin for trin med Hovedgruppe → "
                          "Undergruppe → Mellemgruppe (DISCO 1 → 2 → 3 cifre)."),
        ("Kodeoversigt", "Åbn Kodeoversigten for at udforske hele DISCO-08-træet."),
        ("Aggregér", "Valgt flere arbejdsfunktioner? Slå Aggregér udvalget til over "
                     "fanerne for at samle dem i én serie vægtet efter antal ansatte."),
    ],
    "charts_title": "Læs løndiagrammerne",
    "charts_intro": "DST offentliggør kvartiler, ikke hele percentilspektret. Hvert "
                    "diagram viser tre punkter (gennemsnittet er en separat ♦-markør):",
    "pcts": [("P25", 32, "en fjerdedel tjener mindre"),
             ("MED", 52, "halvdelen tjener mindre"),
             ("P75", 72, "en fjerdedel tjener mere")],
    "notes_title": "Godt at vide",
    "notes": [
        "Tallene er standardberegnet TIMEFORTJENESTE (kr.) — DST's hovedmål, "
        "beregnet pr. standardtime så fravær ikke forvrider sammenligningen. "
        "Gang med ca. 160 (en standardmåned) for et groft månedstal.",
        "Fortjenesten inkluderer pension, feriepenge og personalegoder — dansk "
        "løn opgøres normalt sådan.",
        "Små grupper kan være diskretioneret af DST — en manglende "
        "arbejdsfunktion eller et manglende år er ikke en fejl.",
        "Gennemsnittet kan ligge over medianen, når få høje lønninger trækker "
        "snittet op.",
        "Grænseflade på English / Dansk — skift øverst i menuen.",
    ],
    "tabs_title": "Fanerne",
    "tabs": [
        ("Overblik", "Nøgletallene samlet, med årsvælger."),
        ("Lønfordeling", "Kvartildiagrammet, plus rådata + CSV-eksport."),
        ("Udvikling", "Udvikling over tid: nominelt, vækst mod inflation "
                      "(forbrugerprisindeks) eller realløn (faste priser)."),
        ("Hvor står jeg?", "Angiv en timeløn og se cirka hvor den ligger."),
        ("Rangliste", "Rangerer alle arbejdsfunktioner efter løn, løngab eller vækst."),
        ("Efter køn", "Kvinder mod mænd, med kvinder-i-%-af-mænd-visning."),
    ],
    "footer": "Alle tal er standardberegnet timefortjeneste fra DST-tabel LONS20, opdateret årligt.",
}

CONFIG = CountryConfig(
    slug="denmark",
    name="Denmark",
    native="Danmark",
    iso="dk",
    eyebrow="OFFICIAL STATISTICS · DENMARK",
    source_name="Statistics Denmark (DST)",
    source_url="https://www.statbank.dk/LONS20",
    caption="Statistics Denmark (DST) · Standardized hourly earnings by occupation (DISCO-08)",
    currency="DKK", currency_suffix="kr", period="hourly",
    capabilities=Capabilities(
        has_occupation_percentiles=False,   # DST LONS20 has quartiles, not P10/P90
        has_occupation_hierarchy=True,       # DISCO-08 nests (ISCO-08 aligned)
        has_quartiles=True,                  # P25 · median · P75 spread
        has_mean=True, has_median=True, has_sex=True, has_trend=True,
        has_leaderboard=True,
        sectors=("all", "private", "local", "central"),
        year_range=(FIRST_YEAR, _YR),
    ),
    # standard order (docs/architecture.md); Basic statistics is merged into Overview
    tabs=("overview", "distribution", "trend", "where", "leaderboard", "sex",
          "import_overlay"),
    access="restricted",                    # BETA — admins + beta users only
    fetch_mode="search",                    # commit-on-Search, like Sweden/Norway
    landing=True,                           # gated tile on the landing page
    classification="DISCO-08",
    bullets=(
        "Mean &amp; median hourly earnings · ~420 occupations (DISCO-08)",
        "Sector &amp; gender breakdowns · quartiles",
        f"Standardized hourly earnings · 2013–{_YR}",
    ),
    # flat, language-independent strings the landing tile reads
    labels={
        "badge": "Beta",
        "source_short": "DST · official",
    },
    # in-app strings that follow the language toggle (generic UI comes from
    # core.i18n; only Denmark-specific strings live here)
    languages=(("EN", "English"), ("DA", "Dansk")),
    i18n={
        "EN": {
            "title": "Danish Salary Explorer",
            "caption": "Statistics Denmark (DST) · Standardized hourly earnings by occupation (DISCO-08)",
            "sector_all": "All sectors",
            "sector_private": "Corporations and organizations",
            "sector_local": "Municipal and regional government",
            "sector_central": "Central government",
        },
        "DA": {
            "title": "Dansk lønudforsker",
            "caption": "Danmarks Statistik (DST) · Standardberegnet timefortjeneste efter arbejdsfunktion (DISCO-08)",
            "sector_all": "Alle sektorer",
            "sector_private": "Virksomheder og organisationer",
            "sector_local": "Kommuner og regioner",
            "sector_central": "Staten mv.",
        },
    },
    guide={"EN": _GUIDE_EN, "DA": _GUIDE_DA},
    provider=DenmarkProvider(),
)
