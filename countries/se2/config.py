"""Sweden config — THE public Swedish Salary Explorer, on the framework.

Replaced the legacy scb_salaries.py as the user-facing Sweden page (the legacy
build stays registered admin-only as /sweden-old; see docs/se2-fr2-parity.md).
access='public' + url_path='sweden'; the landing page's fixed Sweden tile links
here, so landing=False (no extra gated tile).
"""
from __future__ import annotations

from core.model import CountryConfig, Capabilities

from . import career, workpermit
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

# Career Paths (beta) tab strings. EN uses the in-code defaults; only the tab label
# is centralised here. SV translates the whole tab.
_CAREER_EN = {"tab_career": "Career Paths (beta)"}
_CAREER_SV = {
    "tab_career": "Karriärvägar (beta)",
    "cp_disclaimer": "Karriärnivåer, löneintervall, percentilpositioner och karriärrelationer är "
                     "<b>Qvistin-genererade uppskattningar</b> — inte officiella karriärstrukturer "
                     "från SCB eller Arbetsförmedlingen. En SSYK-kod kan innehålla flera "
                     "senioritetsnivåer; nivåerna härleds från jobbtitlar, ansvar och erfarenhet. "
                     "Löneintervallen är uppskattningar baserade på SCB:s officiella fördelning och "
                     "överlappar normalt. Lön mäter inte individuell prestation.",
    "cp_pick": "Välj ett yrke i sidofältet för att se dess karriärvägar.",
    "cp_uncovered": "Karriärvägar täcker för närvarande ett antal professionella familjer (HR, IT, "
                    "ekonomi, försäljning & marknad, vård, juridik, logistik och ingenjör). Öppna "
                    "ett yrke i någon av dessa för att utforska dess karriärkarta.",
    "cp_selected": "Valt yrke", "cp_family": "Karriärfamilj",
    "cp_curve_h": "Officiell lönekurva",
    "cp_curve_cap": "SCB:s officiella percentilfördelning för detta yrke. Punkterna är publicerade "
                    "percentiler (P10/P25/P50/P75/P90); linjen mellan dem är interpolerad — "
                    "publiceras inte av SCB.",
    "cp_interp": "Interpolerad", "cp_published": "Publicerad (SCB)",
    "cp_no_curve": "Ingen SCB-fördelning tillgänglig för detta yrke/år.",
    "cp_levels_h": "Uppskattade karriärnivåer (efter lön)",
    "cp_levels_cap": "Varje stapel är ett Qvistin-uppskattat löneintervall för en roll, beräknat "
                     "från rollens egen officiella SSYK-fördelning. Intervallen överlappar normalt "
                     "— en stark yrkesperson kan tjäna mer än en nyutnämnd senior. Färg = karriärspår.",
    "cp_table_h": "Alla roller — detaljer",
    "cp_c_title": "Roll", "cp_c_level": "Nivå", "cp_c_track": "Spår",
    "cp_c_pct": "Uppsk. percentil", "cp_c_salary": "Uppsk. lön", "cp_c_conf": "Underlag",
    "cp_map_h": "Vart kan denna roll leda?",
    "cp_rel_progression": "Avancera inom yrket",
    "cp_rel_specialist": "Byt till ett angränsande specialistyrke",
    "cp_rel_leadership": "Gå in i ledarskap", "cp_rel_lateral": "Relaterade sidosteg",
    "cp_no_moves": "Inga kartlagda steg för detta yrke ännu.",
    "cp_gaps": "Typiska luckor", "cp_vs": "mot yrkets median (indikativt)",
    "cp_c_code": "Kod",
    "cp_c_market": "Marknadssignal", "cp_c_skills": "Vanligaste annonskrav", "cp_ads": "annonser",
    "cp_ev_strong": "Stark signal", "cp_ev_moderate": "Måttlig signal", "cp_ev_limited": "Begränsad signal",
    "cp_ev_based": "baserat på {n} annonser · Arbetsförmedlingen",
    "cp_ev_skills": "Efterfrågade färdigheter",
    "cp_ev_count": "📊 marknadssignal för {n} roll(er)",
    "cp_ms_h": "Marknadssignal (från aktuella platsannonser)",
    "cp_ms_cap": "Vad aktuella svenska platsannonser för dessa roller faktiskt efterfrågar. "
                 "Aggregerat från publika annonser (Arbetsförmedlingen / JobTech, CC BY-SA) — "
                 "indikativt, inte officiellt, och det ändrar inte SCB-lönerna ovan.",
    "cp_ms_role": "Visa roll", "cp_ms_obs": "per {d}",
    "cp_ms_exp": "Typisk erfarenhet", "cp_ms_yrs": "år",
    "cp_ms_edu": "Vanligaste utbildningskrav", "cp_ms_mgmt": "Personalansvar",
    "cp_ms_certs": "Certifikat / behörigheter", "cp_ms_langs": "Språk",
    "cp_ms_emp": "Arbetsgivare som nyligen rekryterat",
    "cp_ms_ex": "Exempelannonser · Platsbanken-referenser",
    "cp_ms_dl": "sök senast {d}", "cp_ms_ref": "ref",
    "cp_ms_expire": "Länkarna öppnar annonsen på Platsbanken och slutar gälla efter sista ansökningsdag.",
    "cp_map_from": "Vägar från {r}", "cp_you_here": "DU ÄR HÄR",
    "cp_map_axis": "positioner speglar uppskattade lönemedianer",
    "cp_map_hint": "Klicka på en roll för att se löneintervall, luckor och krav från platsannonser.",
    "cp_ms_range": "Uppskattat intervall", "cp_vs_short": "mot nuvarande (indikativt)",
    "cp_ms_fromads": "FRÅN PLATSANNONSER",
    "cp_ms_none": "Ingen aktuell annonssignal för denna roll ännu.",
    "cp_ms_region": "Region", "cp_ms_allreg": "Alla regioner",
    "cp_ms_ads_t": "Aktuella annonser", "cp_ms_noreg": "Inga exempelannonser för denna region.",
    "cp_skills": "Krav", "cp_cards_h": "Roller detta kan leda till",
    "cp_rel_entry": "Ingångsväg", "cp_rel_related": "Relaterat steg",
    "cp_map_hint2": "Klicka på en roll för att kliva in i den och utforska vart den leder vidare; "
                    "använd brödsmulan för att gå tillbaka.",
    "cp_map_pick": "Klicka på en roll för att se detaljer och krav från platsannonser.",
    "cp_map_expand": "Har vidare steg — klicka för att utforska vidare.",
    "cp_map_levels": "Antal steg att visa:",
    "cp_map_hint3": "Välj hur många steg som visas, hovra över en roll för att följa dess väg, "
                    "och klicka på en för dess krav från platsannonser.",
    "cp_ev_attr": "Marknadssignal och vanligaste krav är aggregerade från publika platsannonser "
                  "(Arbetsförmedlingen / JobTech, CC BY-SA) — indikativt, inte officiellt.",
    "cp_compare_h": "Jämför två roller", "cp_current": "Nuvarande roll",
    "cp_next": "Möjlig nästa roll", "cp_indic_diff": "Indikativ löneskillnad",
    "cp_indic_note": "median mot median; indikativt, inte garanterat",
    "cp_same_ssyk": "↔ samma SSYK",
    "cp_perf_h": "Prestationsposition — intern förhandsvisning (ej publicerad)",
    "cp_perf_filter": "Markera prestationsnivå", "cp_perf_all": "Alla nivåer",
    "cp_perf_pos": "Position", "cp_perf_within": "Inom nivån",
    "cp_perf_sal": "Illustrativ lön", "cp_perf_role": "Visa intervall för roll",
    "cp_perf_note": "Intern förhandsvisning — visas inte för användare. Publik lansering kräver "
                    "individuell, samtyckt ersättningsdata som vi inte har.",
    "cp_track_ic": "Individuell bidragsgivare", "cp_track_specialist": "Specialist",
    "cp_track_management": "Ledning",
    "cp_conf_strong": "Starkt underlag", "cp_conf_moderate": "Måttligt underlag",
    "cp_conf_limited": "Begränsat underlag", "cp_conf_experimental": "Experimentellt",
    "x_percentile": "Percentil",
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
         "In the left sidebar: sector (all, public or private), gender, and a year "
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
                                     "NUTS-2 région, with an optional split by gender."),
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
    name="Sweden",
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
    # Sweden-specific extra tabs. "career" is beta-gated (core/tabs._BETA_TABS).
    extra_tabs={"workpermit": workpermit.render, "career": career.render},
    access="public",                          # THE public Sweden page
    url_path="sweden",                        # serves /sweden (slug stays "se2")
    fetch_mode="search",
    landing=False,                            # the fixed landing tile links here
    classification="SSYK 2012",
    labels={"badge": "Live", "source_short": "SCB · official"},
    languages=(("EN", "English"), ("SV", "Svenska")),
    i18n={
        "EN": {
            "title": "Swedish Salary Explorer",
            "caption": f"SCB salary structure statistics · monthly SEK · 2014–{latest_year()}",
            **{f"sector_{c}": n for c, n in SECTORS["EN"].items()},
            **_WP_EN, **_CAREER_EN,
        },
        "SV": {
            "title": "Svensk löneutforskare",
            "caption": f"SCB:s lönestrukturstatistik · månadslön SEK · 2014–{latest_year()}",
            **{f"sector_{c}": n for c, n in SECTORS["SV"].items()},
            **_WP_SV, **_CAREER_SV,
        },
    },
    guide={"EN": _GUIDE_EN, "SV": _GUIDE_SV},
    provider=Sweden2Provider(),
)
