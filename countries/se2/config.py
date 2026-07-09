"""Sweden v2 config — the legacy scb_salaries.py rebuilt on the framework.

access='internal' → admin/master ONLY (the SE2 beta the legacy page is compared
against; see docs/se2-fr2-parity.md). landing=False keeps it off the home grid;
admins reach it from the admin panel's Open-a-country or /se2.
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities

from . import workpermit
from .labels import SECTORS
from .provider import Sweden2Provider, latest_year

_WP_EN = {
    "tab_workpermit": "🛂 Work permit check",
    "wp_title": "Swedish work permit — salary & SSYK check",
    "wp_banner": "⚖️ Based on Migrationsverket rules as of **{as_of}**. Checked {today}. "
                 "Figures are maintained manually — let us know when the rules change.",
    "wp_no_occ": "Select a specific occupation in the sidebar to run a work-permit check.",
    "wp_occ": "Occupation (SSYK)",
    "wp_salary": "Proposed monthly salary (SEK, gross incl. fixed supplements)",
    "wp_type": "Permit type",
    "wp_type_regular": "Regular work permit",
    "wp_type_blue": "EU Blue Card",
    "wp_sector": "Compare market salary in sector",
    "wp_transition": "Extension of a permit granted before 1 June 2026 (transition rule)",
    "wp_app_date": "Application date",
    "wp_h_elig": "1 · Eligibility",
    "wp_h_floor": "2 · Salary floor",
    "wp_h_market": "3 · Market / customary pay",
    "wp_h_docs": "4 · Documentation & process",
    "wp_banned_full": "❌ Regular work permits cannot be granted for this occupation "
                      "(SSYK {code} — personal assistants).",
    "wp_banned_partial": "⚠️ Part of SSYK {code} is banned: forest **berry pickers** cannot "
                         "get a regular permit. Confirm the role is not berry-picking — other "
                         "roles in this group are allowed (and exempt at 75%).",
    "wp_elig_ok": "✅ No occupation-level ban for SSYK {code}.",
    "wp_floor_pass": "✅ Proposed SEK {sal:,} meets the floor of SEK {floor:,} ({basis}). "
                     "Margin +SEK {margin:,}.",
    "wp_floor_fail": "❌ Proposed SEK {sal:,} is below the floor of SEK {floor:,} ({basis}). "
                     "Short by SEK {gap:,}.",
    "wp_basis_general": "90% of median",
    "wp_basis_transition": "80% of median — transition rule",
    "wp_basis_exempt": "75% of median — exempt occupation",
    "wp_basis_blue": "EU Blue Card threshold",
    "wp_market_none": "No SCB salary distribution for this occupation/sector/year — "
                      "can't assess market position.",
    "wp_market": "Proposed SEK {sal:,} sits at about **P{pct:.0f}** of the market range "
                 "({sector}, {year}). Range: P10 SEK {p10:,} · median SEK {p50:,} · P90 SEK {p90:,}.",
    "wp_market_below": "⚠️ Below the occupation median — check it meets the collective "
                       "agreement / customary level.",
    "wp_market_ok": "✅ At or above the occupation median.",
    "wp_market_note": "ℹ️ Market-data proxy only. The legal test is the collective agreement "
                      "or customary salary — confirm against the relevant agreement.",
    "wp_plot_proposed": "Proposed",
    "wp_plot_floor": "Floor",
    "wp_ref_lines": "Reference lines — % of this occupation's median (SEK {median:,}) "
                    "for the selected sector:",
    "wp_exempt_header": "Exempt SSYK codes (75% floor):",
    "wp_docs_note": "Not auto-checked — the employer must provide/confirm:",
    "wp_docs_items": [
        "Occupation **and SSYK code** in the application",
        "Work duties, employment form, start date and scope",
        "Salary and collective-agreement date",
        "Insurance companies and job advertisement ID",
        "Relevant **trade union given the opportunity to comment** on the terms",
    ],
    "wp_rules_expander": "Rule figures used",
}
_WP_SV = {
    "tab_workpermit": "🛂 Arbetstillståndskoll",
    "wp_title": "Svenskt arbetstillstånd — löne- & SSYK-kontroll",
    "wp_banner": "⚖️ Baserat på Migrationsverkets regler per **{as_of}**. Kontrollerat {today}. "
                 "Siffrorna underhålls manuellt — säg till när reglerna ändras.",
    "wp_no_occ": "Välj ett specifikt yrke i sidofältet för att köra en arbetstillståndskoll.",
    "wp_occ": "Yrke (SSYK)",
    "wp_salary": "Föreslagen månadslön (SEK, brutto inkl. fasta tillägg)",
    "wp_type": "Typ av tillstånd",
    "wp_type_regular": "Vanligt arbetstillstånd",
    "wp_type_blue": "EU-blåkort",
    "wp_sector": "Jämför marknadslön i sektor",
    "wp_transition": "Förlängning av tillstånd beviljat före 1 juni 2026 (övergångsregel)",
    "wp_app_date": "Ansökningsdatum",
    "wp_h_elig": "1 · Behörighet",
    "wp_h_floor": "2 · Lönegolv",
    "wp_h_market": "3 · Marknads-/branschlön",
    "wp_h_docs": "4 · Dokumentation & process",
    "wp_banned_full": "❌ Vanligt arbetstillstånd kan inte beviljas för detta yrke "
                      "(SSYK {code} — personliga assistenter).",
    "wp_banned_partial": "⚠️ Del av SSYK {code} är förbjuden: skogs**bärplockare** kan inte få "
                         "vanligt arbetstillstånd. Bekräfta att rollen inte är bärplockning — "
                         "övriga roller i gruppen är tillåtna (och undantagna vid 75%).",
    "wp_elig_ok": "✅ Inget yrkesförbud för SSYK {code}.",
    "wp_floor_pass": "✅ Föreslagna SEK {sal:,} når golvet SEK {floor:,} ({basis}). "
                     "Marginal +SEK {margin:,}.",
    "wp_floor_fail": "❌ Föreslagna SEK {sal:,} är under golvet SEK {floor:,} ({basis}). "
                     "Saknas SEK {gap:,}.",
    "wp_basis_general": "90% av medianen",
    "wp_basis_transition": "80% av medianen — övergångsregel",
    "wp_basis_exempt": "75% av medianen — undantaget yrke",
    "wp_basis_blue": "EU-blåkortets tröskel",
    "wp_market_none": "Ingen SCB-lönefördelning för detta yrke/sektor/år — "
                      "kan inte bedöma marknadsläget.",
    "wp_market": "Föreslagna SEK {sal:,} ligger på cirka **P{pct:.0f}** av marknadsintervallet "
                 "({sector}, {year}). Intervall: P10 SEK {p10:,} · median SEK {p50:,} · P90 SEK {p90:,}.",
    "wp_market_below": "⚠️ Under yrkets median — kontrollera att det når kollektivavtal / "
                       "branschpraxis.",
    "wp_market_ok": "✅ På eller över yrkets median.",
    "wp_market_note": "ℹ️ Endast marknadsdata som riktmärke. Det rättsliga testet är "
                      "kollektivavtal eller branschpraxis — stäm av mot relevant avtal.",
    "wp_plot_proposed": "Föreslagen",
    "wp_plot_floor": "Golv",
    "wp_ref_lines": "Referenslinjer — % av yrkets median (SEK {median:,}) för vald sektor:",
    "wp_exempt_header": "Undantagna SSYK-koder (75%-golv):",
    "wp_docs_note": "Kontrolleras inte automatiskt — arbetsgivaren måste ange/bekräfta:",
    "wp_docs_items": [
        "Yrke **och SSYK-kod** i ansökan",
        "Arbetsuppgifter, anställningsform, startdatum och omfattning",
        "Lön och kollektivavtalsdatum",
        "Försäkringsbolag och annons-ID",
        "Relevant **facklig organisation har fått yttra sig** om villkoren",
    ],
    "wp_rules_expander": "Regelsiffror som används",
}

_SECTOR_CODES = ("0", "1-3", "1", "2", "3", "4-5", "4", "5")

# Structured guides (the approved User-Guide design; rendered by core/panels.py)
_GUIDE_EN = {
    "title": "How to use the Swedish Salary Explorer",
    "source": f"Statistics Sweden (SCB) · Wage structure statistics (SSYK 2012) · 2014–{latest_year()}",
    "intro": "Look up Swedish salaries by occupation and check work-permit salary "
             "requirements — official data from Statistics Sweden, no technical "
             "knowledge needed. This guide covers the three-step flow, finding "
             "occupations, and how to read the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Choose your filters",
         "In the left sidebar: sector (all, public or private), sex, and a year "
         "range (2014 onward)."),
        ("Search",
         "Pick one or more occupations, then press the blue Search button at the "
         "bottom of the sidebar."),
        ("Read the results",
         "Explore the tabs on the right. Change any filter and search again to "
         "update the charts."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches job "
                       "titles, SSYK codes and common alternative titles (synonyms)."),
        ("Drill down", "Or narrow step by step with Major group → Sub-group → Minor "
                       "group (SSYK 1 → 2 → 3 digit)."),
        ("Code browser", "Open the Code browser to explore every SSYK code with its "
                         "description and synonyms."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection above "
                      "the tabs to merge them into one headcount-weighted series."),
    ],
    "charts_title": "Reading the salary charts",
    "charts_intro": "Salaries are shown as percentiles — a wide gap between P10 and "
                    "P90 means pay varies a lot in that job (the average is a "
                    "separate ♦ marker):",
    "pcts": [("P10", 22, "10% earn less"),
             ("P25", 36, "a quarter earn less"),
             ("MED", 52, "half earn less"),
             ("P75", 68, "a quarter earn more"),
             ("P90", 84, "only 10% earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are gross monthly salaries (SEK), converted to full-time equivalents.",
        "Some small groups show “–” — SCB suppresses figures for very small groups.",
        "SSYK descriptions are auto-translated from Swedish where no official "
        "English version exists.",
        "Interface in English / Svenska — switch at the top of the sidebar; data "
        "labels follow the language too.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance, with a year selector."),
        ("Salary distribution", "The percentile chart, plus raw data + CSV export."),
        ("Trend", "Development over time: nominal, growth vs inflation (KPI), or "
                  "real (constant prices)."),
        ("Where do I stand?", "Enter a salary and see which percentile it falls in."),
        ("Leaderboard", "Ranks the occupations in your selected group by pay, "
                        "gender gap or growth."),
        ("By gender", "Women vs men, with a women-as-%-of-men view."),
        ("Age / education / region", "Breakdowns by age band, education level and "
                                     "NUTS-2 région, with an optional split by sex."),
        ("Work permit check", "Checks a proposed salary against the Migrationsverket "
                              "floor, the occupation's own pay range and exempt/banned "
                              "lists — always confirm against the collective agreement."),
    ],
    "footer": f"All figures are from SCB's wage structure statistics, 2014–{latest_year()}, "
              "updated annually.",
}

_GUIDE_SV = {
    "title": "Så använder du Svensk löneutforskare",
    "source": f"Statistiska centralbyrån (SCB) · Lönestrukturstatistik (SSYK 2012) · 2014–{latest_year()}",
    "intro": "Slå upp svenska löner per yrke och kontrollera lönekrav för "
             "arbetstillstånd — officiell data från SCB, inga tekniska kunskaper "
             "behövs. Guiden går igenom tre-stegs-flödet, hur du hittar yrken och "
             "hur du läser diagrammen.",
    "steps_title": "Kom igång — tre steg",
    "steps": [
        ("Välj dina filter",
         "I sidofältet till vänster: sektor (alla, offentlig eller privat), kön "
         "och ett årsintervall (från 2014)."),
        ("Sök",
         "Välj ett eller flera yrken och tryck på den blå Sök-knappen längst ner "
         "i sidofältet."),
        ("Läs resultaten",
         "Utforska flikarna till höger. Ändra ett filter och sök igen för att "
         "uppdatera diagrammen."),
    ],
    "find_title": "Hitta rätt yrke",
    "find": [
        ("Sökruta", "Skriv i rutan ”Sök yrken…” — den matchar yrkestitlar, "
                    "SSYK-koder och vanliga alternativa titlar (synonymer)."),
        ("Borra ner", "Eller avgränsa steg för steg via Yrkesområde → Huvudgrupp → "
                      "Yrkesgrupp (SSYK 1 → 2 → 3 siffror)."),
        ("Kodbläddrare", "Öppna Kodbläddraren för att utforska varje SSYK-kod med "
                         "beskrivning och synonymer."),
        ("Aggregera", "Valt flera yrken? Slå på Aggregera urvalet ovanför flikarna "
                      "för att slå ihop dem till en serie viktad efter antal anställda."),
    ],
    "charts_title": "Läsa lönediagrammen",
    "charts_intro": "Löner visas som percentiler — stort avstånd mellan P10 och P90 "
                    "betyder att lönerna varierar mycket i yrket (medelvärdet är en "
                    "egen ♦-markör):",
    "pcts": [("P10", 22, "10 % tjänar mindre"),
             ("P25", 36, "en fjärdedel tjänar mindre"),
             ("MED", 52, "hälften tjänar mindre"),
             ("P75", 68, "en fjärdedel tjänar mer"),
             ("P90", 84, "bara 10 % tjänar mer")],
    "notes_title": "Bra att veta",
    "notes": [
        "Siffrorna är heltidsekvivalenta bruttolöner per månad (SEK).",
        "Små grupper kan visa ”–” — SCB döljer siffror för mycket små grupper.",
        "SSYK-beskrivningar är automatöversatta från svenska där ingen officiell "
        "engelsk version finns.",
        "Gränssnitt på English / Svenska — växla högst upp i sidofältet; även "
        "dataetiketterna följer språket.",
    ],
    "tabs_title": "Flikarna",
    "tabs": [
        ("Översikt", "Nyckeltalen i ett svep, med årsväljare."),
        ("Lönefördelning", "Percentildiagrammet, plus rådata + CSV-export."),
        ("Trend", "Utveckling över tid: nominellt, tillväxt mot inflation (KPI) "
                  "eller realt (fasta priser)."),
        ("Var står jag?", "Ange en lön och se vilken percentil den hamnar på."),
        ("Topplista", "Rangordnar yrkena i din valda grupp efter lön, lönegap "
                      "eller tillväxt."),
        ("Efter kön", "Kvinnor mot män, med kvinnor-i-%-av-män-vy."),
        ("Ålder / utbildning / region", "Uppdelningar efter åldersgrupp, "
                                        "utbildningsnivå och region, med valbar könsuppdelning."),
        ("Arbetstillståndskoll", "Kontrollerar en föreslagen lön mot Migrationsverkets "
                                 "golv, yrkets eget lönespann och undantags-/förbudslistor — "
                                 "stäm alltid av mot kollektivavtalet."),
    ],
    "footer": f"Alla siffror kommer från SCB:s lönestrukturstatistik, 2014–{latest_year()}, "
              "uppdateras årligen.",
}

CONFIG = CountryConfig(
    slug="se2",
    name="Sweden v2",
    native="Sverige",
    iso="se",
    eyebrow="OFFICIAL STATISTICS · SWEDEN",
    source_name="Statistics Sweden (SCB)",
    source_url="https://www.scb.se/en/finding-statistics/statistics-by-subject-area/labour-market/",
    caption="SCB salary structure statistics · monthly SEK · 2014–{yr}".format(yr=latest_year()),
    currency="SEK", currency_suffix="kr", period="monthly",
    capabilities=Capabilities(
        has_occupation_percentiles=True,      # full P10..P90 + mean + median
        has_mean=True, has_median=True,
        has_sex=True, has_age=True, has_education=True, has_region=True,
        has_trend=True,
        has_leaderboard=True, leaderboard_scope=2,   # SSYK sub-major group
        sectors=_SECTOR_CODES,
        year_range=(2014, latest_year()),
    ),
    tabs=("overview", "distribution", "trend", "where", "leaderboard",
          "sex", "age", "education", "region", "import_overlay"),
    extra_tabs={"workpermit": workpermit.render},   # Sweden-specific extra tab
    access="internal",                        # admin/master only (SE2 beta)
    fetch_mode="search",
    landing=False,                            # no home tile — admin preview only
    classification="SSYK 2012",
    labels={"badge": "Beta", "source_short": "SCB · official"},
    languages=(("EN", "English"), ("SV", "Svenska")),
    i18n={
        "EN": {
            "title": "Swedish Salary Explorer (v2)",
            "caption": f"SCB salary structure statistics · monthly SEK · 2014–{latest_year()}",
            **{f"sector_{c}": n for c, n in SECTORS["EN"].items()},
            **_WP_EN,
        },
        "SV": {
            "title": "Svensk löneutforskare (v2)",
            "caption": f"SCB:s lönestrukturstatistik · månadslön SEK · 2014–{latest_year()}",
            **{f"sector_{c}": n for c, n in SECTORS["SV"].items()},
            **_WP_SV,
        },
    },
    guide={"EN": _GUIDE_EN, "SV": _GUIDE_SV},
    provider=Sweden2Provider(),
)
