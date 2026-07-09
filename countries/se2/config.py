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

_GUIDE_EN = """
# 👋 Welcome to the Swedish Salary Explorer

Look up **Swedish salaries** by occupation and check **work-permit salary
requirements** — official data from Statistics Sweden (SCB). No technical
knowledge needed.

## 🚀 Getting started — 3 steps
1. **Choose your filters** in the left sidebar: sector, sex, year range and an
   occupation.
2. Click **🔍 Search**.
3. **Read the results** in the tabs that appear. Change any filter and click
   Search again to update.

## 🔎 Finding the right occupation
- Type in the **"Search occupations…"** box — it matches job titles, codes and
  common alternative titles (synonyms).
- Or drill down with **Major group → Sub-group → Minor group**.
- Not sure of the code? Open the **Code browser** to browse every SSYK code
  with a description and its own search box.
- Picked several occupations? Toggle **Aggregate selection** above the tabs to
  merge them into one headcount-weighted series.

## 📈 Reading the salary charts
Salaries are shown as **percentiles**:
- **P10** — 10% earn less than this (the lower end).
- **Median (P50)** — the middle salary; half earn more, half less.
- **P90** — only 10% earn more (the top end).
- **Average** — shown as a separate ♦ marker.

A wide gap between P10 and P90 means salaries vary a lot in that job.

## 🗂 The tabs
- **Overview** — the key figures at a glance, with a year selector.
- **Salary distribution** — the percentile chart, plus raw data + CSV export.
- **Trend** — development over time: nominal, growth vs inflation, or real
  (constant prices).
- **Where do I stand?** — enter a salary and see which percentile it falls in.
- **Leaderboard** — ranks the occupations in your selected group by pay,
  gender gap or growth.
- **By gender / age / education / region** — breakdowns, with an optional
  women-vs-men split.
- **🛂 Work permit check** — checks a proposed salary against the
  Migrationsverket floor, the occupation's own pay range, and exempt/banned
  lists. ✅ pass, ⚠️ caution or ❌ fail, with the numbers. *Always confirm
  against the relevant collective agreement.*

## 🌐 Language
Use the **English / Svenska** switch at the top of the sidebar — it changes
both the interface and the data labels.

## ❓ Good to know
- Data: **SCB Wage Structure Statistics**, 2014 → the latest published year.
  Figures are gross monthly salaries, converted to full-time equivalents.
- Some small groups show "–" — SCB suppresses figures for very small groups.
- SSYK descriptions are **auto-translated** from Swedish where no official
  English version exists.
"""

_GUIDE_SV = """
# 👋 Välkommen till Svensk löneutforskare

Slå upp **svenska löner** per yrke och kontrollera **lönekrav för
arbetstillstånd** — officiell data från SCB. Inga tekniska kunskaper behövs.

## 🚀 Kom igång — 3 steg
1. **Välj dina filter** i sidofältet till vänster: sektor, kön, årsintervall
   och ett yrke.
2. Klicka på **🔍 Sök**.
3. **Läs resultaten** i flikarna som visas. Ändra ett filter och sök igen för
   att uppdatera.

## 🔎 Hitta rätt yrke
- Skriv i rutan **”Sök yrken…”** — den matchar yrkestitlar, koder och vanliga
  alternativa titlar (synonymer).
- Eller borra dig ner via **Yrkesområde → Huvudgrupp → Yrkesgrupp**.
- Osäker på koden? Öppna **Kodbläddraren** och bläddra bland alla SSYK-koder
  med beskrivning och egen sökruta.
- Valt flera yrken? Slå på **Aggregera urvalet** ovanför flikarna för att slå
  ihop dem till en serie viktad efter antal anställda.

## 📈 Läsa lönediagrammen
Löner visas som **percentiler**:
- **P10** — 10 % tjänar mindre än detta (den lägre delen).
- **Median (P50)** — mittlönen; hälften tjänar mer, hälften mindre.
- **P90** — bara 10 % tjänar mer (toppen).
- **Medelvärde** — visas som en egen ♦-markör.

Stort avstånd mellan P10 och P90 betyder att lönerna varierar mycket i yrket.

## 🗂 Flikarna
- **Översikt** — nyckeltalen i ett svep, med årsväljare.
- **Lönefördelning** — percentildiagrammet, plus rådata + CSV-export.
- **Trend** — utveckling över tid: nominellt, tillväxt mot inflation eller
  realt (fasta priser).
- **Var står jag?** — ange en lön och se vilken percentil den hamnar på.
- **Topplista** — rangordnar yrkena i din valda grupp efter lön, lönegap
  eller tillväxt.
- **Efter kön / ålder / utbildning / region** — uppdelningar, med valbar
  kvinnor-mot-män-vy.
- **🛂 Arbetstillståndskoll** — kontrollerar en föreslagen lön mot
  Migrationsverkets golv, yrkets eget lönespann och undantags-/förbudslistor.
  ✅ godkänt, ⚠️ varning eller ❌ underkänt, med siffror. *Stäm alltid av mot
  relevant kollektivavtal.*

## 🌐 Språk
Använd **English / Svenska**-växlaren högst upp i sidofältet — den byter både
gränssnitt och dataetiketter.

## ❓ Bra att veta
- Data: **SCB:s lönestrukturstatistik**, 2014 → senaste publicerade år.
  Siffrorna är heltidsekvivalenta bruttolöner per månad.
- Små grupper kan visa ”–” — SCB döljer siffror för mycket små grupper.
- SSYK-beskrivningar är **automatöversatta** från svenska där ingen officiell
  engelsk version finns.
"""

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
