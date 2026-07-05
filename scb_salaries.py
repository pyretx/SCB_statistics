import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import json
import os
import re
from datetime import datetime
import auth
import theme

# ── SSYK 2012 hierarchy labels ─────────────────────────────────────────────────

MAJOR_GROUPS = {
    "EN": {
        "0": "0 – Armed forces",
        "1": "1 – Managers",
        "2": "2 – Professionals",
        "3": "3 – Technicians & associate professionals",
        "4": "4 – Clerical support workers",
        "5": "5 – Service & sales workers",
        "6": "6 – Agricultural, forestry & fishery",
        "7": "7 – Craft & trades workers",
        "8": "8 – Plant & machine operators",
        "9": "9 – Elementary occupations",
    },
    "SV": {
        "0": "0 – Militärt arbete",
        "1": "1 – Chefer",
        "2": "2 – Specialister",
        "3": "3 – Tekniker & associate-specialister",
        "4": "4 – Kontors- & kundservicearbete",
        "5": "5 – Service-, omsorgs- & försäljningsarbete",
        "6": "6 – Jordbruk, skogsbruk & fiske",
        "7": "7 – Hantverksarbete",
        "8": "8 – Process- & maskinoperatörsarbete",
        "9": "9 – Arbete utan krav på särskild yrkesutbildning",
    },
}

SUB_GROUPS = {
    "EN": {
        "00": "00 – Commissioned armed forces officers",
        "01": "01 – Other armed forces occupations",
        "11": "11 – Chief executives, senior officials & legislators",
        "12": "12 – Administrative & commercial managers",
        "13": "13 – Production & specialised services managers",
        "14": "14 – Hospitality, retail & other services managers",
        "21": "21 – Science & engineering professionals",
        "22": "22 – Health professionals",
        "23": "23 – Teaching professionals",
        "24": "24 – Business & administration professionals",
        "25": "25 – ICT professionals",
        "26": "26 – Legal, social & cultural professionals",
        "31": "31 – Science & engineering technicians",
        "32": "32 – Health associate professionals",
        "33": "33 – Business & administration associate professionals",
        "34": "34 – Legal, social & cultural associate professionals",
        "35": "35 – ICT technicians",
        "41": "41 – General & keyboard clerks",
        "42": "42 – Customer services clerks",
        "43": "43 – Numerical & material recording clerks",
        "44": "44 – Other clerical support workers",
        "51": "51 – Personal service workers",
        "52": "52 – Sales workers",
        "53": "53 – Personal care workers",
        "54": "54 – Protective services workers",
        "61": "61 – Skilled agricultural workers",
        "62": "62 – Skilled forestry, fishery & hunting workers",
        "71": "71 – Building & related trades workers",
        "72": "72 – Metal, machinery & related trades workers",
        "73": "73 – Handicraft & printing workers",
        "74": "74 – Electrical & electronics trades workers",
        "75": "75 – Food, woodworking & other craft workers",
        "81": "81 – Stationary plant & machine operators",
        "82": "82 – Assemblers",
        "83": "83 – Drivers & mobile plant operators",
        "91": "91 – Cleaners & helpers",
        "92": "92 – Agricultural & fishery labourers",
        "93": "93 – Construction & manufacturing labourers",
        "94": "94 – Food preparation assistants",
        "96": "96 – Refuse workers & other elementary workers",
    },
    "SV": {
        "00": "00 – Officerare",
        "01": "01 – Övrig militär personal",
        "11": "11 – Verkställande direktörer, högre ämbetsmän m.fl.",
        "12": "12 – Administrativa chefer & kommersiella chefer",
        "13": "13 – Produktionschefer & specialiserade servicechefer",
        "14": "14 – Chefer inom hotell, handel & övrig serviceverksamhet",
        "21": "21 – Naturvetare, matematiker & ingenjörer",
        "22": "22 – Hälso- & sjukvårdsspecialister",
        "23": "23 – Undervisningsspecialister",
        "24": "24 – Affärs- & förvaltningsspecialister",
        "25": "25 – IT-specialister",
        "26": "26 – Jurister, samhällsvetare & kulturarbetare",
        "31": "31 – Ingenjörer & tekniker",
        "32": "32 – Hälso- & sjukvårdsassistenter",
        "33": "33 – Affärs- & förvaltningsassistenter",
        "34": "34 – Juridiska, sociala & kulturella assistenter",
        "35": "35 – IT-tekniker",
        "41": "41 – Kontorsassistenter m.fl.",
        "42": "42 – Kundtjänstpersonal",
        "43": "43 – Ekonomi- & lagerredovisare m.fl.",
        "44": "44 – Övrig kontorspersonal",
        "51": "51 – Servicearbetare",
        "52": "52 – Försäljare",
        "53": "53 – Omsorgsarbetare",
        "54": "54 – Bevaknings- & säkerhetspersonal",
        "61": "61 – Jordbrukare m.fl.",
        "62": "62 – Skogsarbetare, fiskare & jägare",
        "71": "71 – Byggnads- & anläggningsarbetare",
        "72": "72 – Metallarbetare & verkstadsmekaniker",
        "73": "73 – Hantverkare & grafiker",
        "74": "74 – El- & elektronikmontörer",
        "75": "75 – Livsmedels-, trä- & övriga hantverksarbetare",
        "81": "81 – Maskin- & motoroperatörer",
        "82": "82 – Montörer",
        "83": "83 – Transport- & maskinförare",
        "91": "91 – Städare m.fl.",
        "92": "92 – Jord- & skogsbruksarbetare m.fl.",
        "93": "93 – Bygg-, tillverknings- & transportarbetare",
        "94": "94 – Köks- & restaurangbiträden",
        "96": "96 – Återvinningsarbetare m.fl.",
    },
}

# ── Translations ───────────────────────────────────────────────────────────────

T = {
    "EN": {
        "title": "Swedish Salary Explorer",
        "caption": "Data: Statistics Sweden (SCB) – Wage Structure Statistics, entire economy",
        "filters": "Filters",
        "sector": "Sector",
        "sex": "Sex",
        "year_range": "Year range",
        "major_group": "1. Major group",
        "sub_group": "2. Sub-group",
        "occ_select": "3. Occupation(s)",
        "occ_search_ph": "Search occupations…",
        "no_match": "No occupations match.",
        "found_n": "✓ {n} occupation(s) found",
        "select_prompt": "Select at least one occupation in the sidebar to get started.",
        "no_data": "No data returned for this combination. Try different filters.",
        "chart_title": "Salary distribution by percentile",
        "chart_year": "Chart year",
        "trend_title": "Salary trend over time",
        "trend_view": "View",
        "trend_view_help": (
            "**Nominal (kr)** — the actual monthly salary in kronor as reported each year, "
            "not adjusted for inflation.\n\n"
            "**Growth vs inflation** — salary growth and consumer-price inflation (CPI), both "
            "indexed to the first year shown (0 %). If the salary line stays above the inflation "
            "line, pay has outpaced rising prices.\n\n"
            "**Real (constant kr)** — the salary expressed in the first year's purchasing power, "
            "i.e. adjusted for inflation. A rising line means real purchasing power has grown."
        ),
        "trend_nominal": "Nominal (kr)",
        "trend_growth": "Growth vs inflation",
        "trend_real": "Real (constant kr)",
        "trend_sal_growth": "Salary growth",
        "trend_infl": "Inflation (CPI)",
        "trend_growth_axis": "Change from {base} (%)",
        "trend_real_axis": "Real monthly salary ({base} prices, SEK)",
        "trend_no_cpi": "ℹ️ Inflation data unavailable — showing nominal only.",
        "trend_summary": "**{base}→{last}:** salary {sal:+.0f}% · inflation {infl:+.0f}% → **real {real:+.0f}%**",
        "trend_table_title": "Trend data (nominal · growth · real)",
        "trend_col_nominal": "Nominal salary (kr)",
        "trend_col_growth": "Salary growth (%)",
        "trend_col_real": "Real salary ({base} kr)",
        "trend_download": "⬇ Download trend data (CSV)",
        "measure": "Measure",
        "x_pct": "Percentile",
        "y_salary": "Monthly salary (SEK)",
        "x_year": "Year",
        "raw_data": "Raw data table",
        "source": "Source: [Statistics Sweden (SCB)](https://www.scb.se) via PxWebApi · Table AM0110A",
        "loading": "Loading…",
        "fetching_data": "Fetching salary data…",
        "tab_pct": "📈 Percentile distribution",
        "tab_calc": "💰 Where do I stand?",
        "tab_lead": "🏆 Leaderboard",
        "tab_age": "👤 By age",
        "tab_region": "🗺️ By region",
        "tab_edu": "🎓 By education",
        "tab_stats": "🔢 Basic statistics",
        "tab_browse": "📖 SSYK guide",
        "ssyk_title": "Browse SSYK occupation codes",
        "ssyk_intro": "Drill down the SSYK hierarchy to find the right code. Names match the SCB data; descriptions and alternative job titles come from SCB's SSYK-Sök.",
        "ssyk_l1": "Major area (1-digit)",
        "ssyk_l2": "Major group (2-digit)",
        "ssyk_l3": "Minor group (3-digit)",
        "ssyk_l4": "Occupation (4-digit)",
        "ssyk_show3": "Show the 3-digit level (Minor group)",
        "ssyk_desc": "Description",
        "ssyk_syn": "Alternative job titles ({n})",
        "ssyk_use": "Use this occupation →",
        "ssyk_unavail": "SSYK reference data is not available.",
        "ssyk_trans_warn": "⚠️ Auto-translated from Swedish — no official English version exists.",
        "ssyk_no_desc": "No description available.",
        "ssyk_edit": "✏️ Edit content (admin)",
        "ssyk_edit_saved": "Saved.",
        "ssyk_search": "🔍 Search codes, names, job titles, descriptions…",
        "ssyk_results": "Results ({n})",
        "ssyk_pick_prompt": "Pick a level on the left (or search above) to see its description.",
        "ssyk_blank": "—",
        "calc_title": "Where does your salary stand?",
        "calc_occ": "Occupation",
        "calc_year": "Year",
        "calc_input": "Your monthly salary (SEK)",
        "calc_no_pct": "ℹ️ Percentile data isn't available for this occupation/year (SCB suppresses small samples). Try another year or occupation.",
        "calc_rank": "Your percentile",
        "calc_more_than": "You earn more than about **{p}%** of employees in this role — roughly the **top {top}%**.",
        "calc_below": "Your salary is at or below the 10th percentile — among the lowest-paid ~10% for this role.",
        "calc_above": "Your salary is at or above the 90th percentile — among the highest-paid ~10% for this role.",
        "calc_you": "You",
        "calc_context": "Based on **{occ}** · {sector} · {sex} · {year} (monthly salary).",
        "calc_curve": "Salary by percentile",
        "lead_title": "Occupation leaderboard",
        "lead_intro": "Ranks {scope} in **{sector}**. Searched occupations are highlighted in red.",
        "lead_all_occ": "all occupations",
        "lead_metric": "Rank by",
        "lead_m_median": "Median salary",
        "lead_m_avg": "Average salary",
        "lead_m_gap": "Gender pay gap",
        "lead_m_growth": "Salary growth",
        "lead_year": "Year",
        "lead_from": "From year",
        "lead_to": "To year",
        "lead_topn": "How many to show",
        "lead_order": "Order",
        "lead_high": "Highest first",
        "lead_low": "Lowest first",
        "lead_gap_big": "Biggest gap first",
        "lead_gap_small": "Most equal first",
        "lead_grow_fast": "Fastest first",
        "lead_grow_slow": "Slowest first",
        "lead_rank": "Rank",
        "lead_occ": "Occupation",
        "lead_value": "Value",
        "lead_gap_axis": "Women's salary (% of men's)",
        "lead_growth_axis": "Salary change (%)",
        "lead_your": "Your selection: **{name}** — #{rank} of {total} ({val})",
        "lead_sex_note": "Salary figures shown for: **{sex}**. Gender gap always uses men vs women.",
        "lead_table": "Full ranking",
        "lead_need_two": "Pick two different years to compare growth.",
        "tab_permit": "🛂 Work permit check",
        "wp_title": "Swedish work permit — salary & SSYK check",
        "wp_banner": "⚖️ Based on Migrationsverket rules as of **{as_of}**. Checked {today}. Figures are maintained manually — let us know when the rules change.",
        "wp_median_ok": "✓ Configured median (SEK {cfg:,}) matches the latest SCB figure ({year}).",
        "wp_median_warn": "⚠️ Configured median is SEK {cfg:,}, but the latest SCB median ({year}) is SEK {live:,}. The rule set may need updating.",
        "wp_no_occ": "Select a specific occupation in the sidebar (not an aggregated group) to run a work-permit check.",
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
        "wp_banned_full": "❌ Regular work permits cannot be granted for this occupation (SSYK {code} — personal assistants).",
        "wp_banned_partial": "⚠️ Part of SSYK {code} is banned: forest **berry pickers** cannot get a regular permit. Confirm the role is not berry-picking — other roles in this group are allowed (and exempt at 75%).",
        "wp_elig_ok": "✅ No occupation-level ban for SSYK {code}.",
        "wp_floor_pass": "✅ Proposed SEK {sal:,} meets the floor of SEK {floor:,} ({basis}). Margin +SEK {margin:,}.",
        "wp_floor_fail": "❌ Proposed SEK {sal:,} is below the floor of SEK {floor:,} ({basis}). Short by SEK {gap:,}.",
        "wp_basis_general": "90% of median",
        "wp_basis_transition": "80% of median — transition rule",
        "wp_basis_exempt": "75% of median — exempt occupation",
        "wp_basis_blue": "EU Blue Card threshold",
        "wp_market_none": "No SCB salary distribution for this occupation/sector/year — can't assess market position.",
        "wp_market": "Proposed SEK {sal:,} sits at about **P{pct:.0f}** of the market range ({sector}, {year}). Range: P10 SEK {p10:,} · median SEK {p50:,} · P90 SEK {p90:,}.",
        "wp_market_below": "⚠️ Below the occupation median — check it meets the collective agreement / customary level.",
        "wp_market_ok": "✅ At or above the occupation median.",
        "wp_market_note": "ℹ️ Market-data proxy only. The legal test is the collective agreement or customary salary — confirm against the relevant agreement.",
        "wp_plot_proposed": "Proposed",
        "wp_plot_floor": "Floor",
        "wp_ref_lines": "Reference lines — % of this occupation's median (SEK {median:,}) for the selected sector:",
        "wp_data_expander": "📊 Salary distribution data for this occupation",
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
        "stats_title": "Number of employees in the selection",
        "stat_total": "Total employees",
        "per_occ": "By occupation",
        "occupation": "Occupation",
        "stats_note": "These are SCB's estimated number of employees the salary figures are based on "
                      "(national total, sector & year as selected). Different breakdown tables can "
                      "report slightly different totals — see the source comparison below.",
        "src_compare": "Source comparison (totals per table)",
        "src_region": "Region table (Sweden total)",
        "src_edu": "Education table (all levels)",
        "age_title": "Average monthly salary by age group",
        "region_title": "Average monthly salary by region",
        "edu_title": "Average monthly salary by education level",
        "select_year": "Year",
        "measures_shown": "Measures shown",
        "measure_type": "Salary measure",
        "monthly": "Monthly salary", "basic": "Basic salary",
        "headcount": "Number of employees",
        "def_title": "ℹ️ What do these mean?",
        "def_basic": "**Basic salary** (*grundlön*) — the fixed contracted base pay only.",
        "def_monthly": "**Monthly salary** (*månadslön*) — basic salary **plus** fixed supplements "
                       "(shift / inconvenient-hours pay, fixed bonuses, benefits). "
                       "Excludes overtime and performance bonuses, so Monthly ≥ Basic.",
        "show_ratio": "Show women's salary as % of men's",
        "ratio_axis": "Women's salary (% of men's)",
        "show_region_pct": "Show as % of Sweden total",
        "men": "Men", "women": "Women",
        "no_pct_note": "ℹ️ SCB only provides average/basic salary for this breakdown — percentiles are available in the Percentile distribution tab only.",
        "agg_info": "ℹ️ Aggregated across {n} occupations in “{grp}”, weighted by number of employees.",
        "agg_pct_extra": " Percentiles are headcount-weighted averages of each occupation's percentile — an approximation, not a recomputed distribution.",
        "all_major": "— All major groups —",
        "all_sub":   "— All sub-groups —",
        "btn_search": "🔍 Search",
        "btn_clear":  "✕ Clear all",
        "sectors": {
            "0":   "All sectors",
            "1-3": "Public sector (total)",
            "1":   "Central government",
            "2":   "Municipalities",
            "3":   "County councils / Regions",
            "4-5": "Private sector (total)",
            "4":   "Private sector – manual workers",
            "5":   "Private sector – non-manual workers",
        },
        "sex_options": {"1+2": "Total", "1": "Men", "2": "Women"},
        "measures": {
            "000000C5": "Average monthly salary",
            "000000C6": "Median (P50)",
            "000000C7": "P10",
            "000000C8": "P25",
            "000000C9": "P75",
            "000000CA": "P90",
        },
    },
    "SV": {
        "title": "Svensk lönestatistik",
        "caption": "Data: Statistiska centralbyrån (SCB) – Lönestrukturstatistik, hela ekonomin",
        "filters": "Filter",
        "sector": "Sektor",
        "sex": "Kön",
        "year_range": "Årsintervall",
        "major_group": "1. Huvudgrupp",
        "sub_group": "2. Undergrupp",
        "occ_select": "3. Yrke(n)",
        "occ_search_ph": "Sök yrken…",
        "no_match": "Inga yrken matchar.",
        "found_n": "✓ {n} yrke(n) hittades",
        "select_prompt": "Välj minst ett yrke i sidofältet för att komma igång.",
        "no_data": "Inga data returnerades. Prova andra filter.",
        "chart_title": "Lönespridning per percentil",
        "chart_year": "Visningsår",
        "trend_title": "Löneutveckling över tid",
        "trend_view": "Vy",
        "trend_view_help": (
            "**Nominell (kr)** — den faktiska månadslönen i kronor som rapporterats varje år, "
            "utan justering för inflation.\n\n"
            "**Tillväxt vs inflation** — löneökning och konsumentprisinflation (KPI), båda "
            "indexerade till det första året som visas (0 %). Om lönelinjen ligger över "
            "inflationslinjen har lönen ökat snabbare än priserna.\n\n"
            "**Real (fasta kr)** — lönen uttryckt i det första årets köpkraft, dvs. justerad "
            "för inflation. En stigande linje betyder att den reala köpkraften har ökat."
        ),
        "trend_nominal": "Nominell (kr)",
        "trend_growth": "Tillväxt vs inflation",
        "trend_real": "Real (fasta kr)",
        "trend_sal_growth": "Löneökning",
        "trend_infl": "Inflation (KPI)",
        "trend_growth_axis": "Förändring från {base} (%)",
        "trend_real_axis": "Real månadslön ({base} års priser, SEK)",
        "trend_no_cpi": "ℹ️ Inflationsdata saknas — visar endast nominellt.",
        "trend_summary": "**{base}→{last}:** lön {sal:+.0f}% · inflation {infl:+.0f}% → **real {real:+.0f}%**",
        "trend_table_title": "Trenddata (nominell · tillväxt · real)",
        "trend_col_nominal": "Nominell lön (kr)",
        "trend_col_growth": "Löneökning (%)",
        "trend_col_real": "Real lön ({base} kr)",
        "trend_download": "⬇ Ladda ner trenddata (CSV)",
        "measure": "Mått",
        "x_pct": "Percentil",
        "y_salary": "Månadslön (SEK)",
        "x_year": "År",
        "raw_data": "Rådata",
        "source": "Källa: [Statistiska centralbyrån (SCB)](https://www.scb.se) via PxWebApi · Tabell AM0110A",
        "loading": "Laddar…",
        "fetching_data": "Hämtar lönedata…",
        "tab_pct": "📈 Lönespridning",
        "tab_calc": "💰 Var ligger jag?",
        "tab_lead": "🏆 Topplista",
        "tab_age": "👤 Efter ålder",
        "tab_region": "🗺️ Efter region",
        "tab_edu": "🎓 Efter utbildning",
        "tab_stats": "🔢 Grundstatistik",
        "tab_browse": "📖 SSYK-guide",
        "ssyk_title": "Bläddra bland SSYK-yrkeskoder",
        "ssyk_intro": "Borra ner i SSYK-hierarkin för att hitta rätt kod. Namnen matchar SCB-datan; beskrivningar och benämningar kommer från SCB:s SSYK-Sök.",
        "ssyk_l1": "Yrkesområde (1 siffra)",
        "ssyk_l2": "Huvudgrupp (2 siffror)",
        "ssyk_l3": "Yrkesgrupp (3 siffror)",
        "ssyk_l4": "Undergrupp (4 siffror)",
        "ssyk_show3": "Visa 3-siffernivån (Yrkesgrupp)",
        "ssyk_desc": "Beskrivning",
        "ssyk_syn": "Benämningar ({n})",
        "ssyk_use": "Använd detta yrke →",
        "ssyk_unavail": "SSYK-referensdata saknas.",
        "ssyk_trans_warn": "⚠️ Maskinöversatt från svenska — ingen officiell engelsk version finns.",
        "ssyk_no_desc": "Ingen beskrivning tillgänglig.",
        "ssyk_edit": "✏️ Redigera innehåll (admin)",
        "ssyk_edit_saved": "Sparat.",
        "ssyk_search": "🔍 Sök koder, namn, benämningar, beskrivningar…",
        "ssyk_results": "Träffar ({n})",
        "ssyk_pick_prompt": "Välj en nivå till vänster (eller sök ovan) för att se beskrivningen.",
        "ssyk_blank": "—",
        "calc_title": "Var ligger din lön?",
        "calc_occ": "Yrke",
        "calc_year": "År",
        "calc_input": "Din månadslön (SEK)",
        "calc_no_pct": "ℹ️ Percentildata saknas för detta yrke/år (SCB döljer små urval). Prova ett annat år eller yrke.",
        "calc_rank": "Din percentil",
        "calc_more_than": "Du tjänar mer än cirka **{p}%** av de anställda i detta yrke — ungefär **topp {top}%**.",
        "calc_below": "Din lön ligger på eller under 10:e percentilen — bland de ~10% lägst betalda i detta yrke.",
        "calc_above": "Din lön ligger på eller över 90:e percentilen — bland de ~10% högst betalda i detta yrke.",
        "calc_you": "Du",
        "calc_context": "Baserat på **{occ}** · {sector} · {sex} · {year} (månadslön).",
        "calc_curve": "Lön per percentil",
        "lead_title": "Yrkestopplista",
        "lead_intro": "Rangordnar {scope} i **{sector}**. Sökta yrken markeras i rött.",
        "lead_all_occ": "alla yrken",
        "lead_metric": "Rangordna efter",
        "lead_m_median": "Medianlön",
        "lead_m_avg": "Genomsnittslön",
        "lead_m_gap": "Lönegap mellan könen",
        "lead_m_growth": "Löneökning",
        "lead_year": "År",
        "lead_from": "Från år",
        "lead_to": "Till år",
        "lead_topn": "Antal att visa",
        "lead_order": "Ordning",
        "lead_high": "Högst först",
        "lead_low": "Lägst först",
        "lead_gap_big": "Störst gap först",
        "lead_gap_small": "Mest jämställt först",
        "lead_grow_fast": "Snabbast först",
        "lead_grow_slow": "Långsammast först",
        "lead_rank": "Plats",
        "lead_occ": "Yrke",
        "lead_value": "Värde",
        "lead_gap_axis": "Kvinnors lön (% av mäns)",
        "lead_growth_axis": "Löneförändring (%)",
        "lead_your": "Ditt val: **{name}** — plats {rank} av {total} ({val})",
        "lead_sex_note": "Lönesiffror visas för: **{sex}**. Lönegapet använder alltid män mot kvinnor.",
        "lead_table": "Hela rangordningen",
        "lead_need_two": "Välj två olika år för att jämföra ökning.",
        "tab_permit": "🛂 Arbetstillståndskoll",
        "wp_title": "Svenskt arbetstillstånd — löne- & SSYK-kontroll",
        "wp_banner": "⚖️ Baserat på Migrationsverkets regler per **{as_of}**. Kontrollerat {today}. Siffrorna underhålls manuellt — säg till när reglerna ändras.",
        "wp_median_ok": "✓ Konfigurerad median (SEK {cfg:,}) matchar senaste SCB-siffran ({year}).",
        "wp_median_warn": "⚠️ Konfigurerad median är SEK {cfg:,}, men senaste SCB-medianen ({year}) är SEK {live:,}. Regeluppsättningen kan behöva uppdateras.",
        "wp_no_occ": "Välj ett specifikt yrke i sidofältet (inte en aggregerad grupp) för att köra en arbetstillståndskoll.",
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
        "wp_banned_full": "❌ Vanligt arbetstillstånd kan inte beviljas för detta yrke (SSYK {code} — personliga assistenter).",
        "wp_banned_partial": "⚠️ Del av SSYK {code} är förbjuden: skogs**bärplockare** kan inte få vanligt arbetstillstånd. Bekräfta att rollen inte är bärplockning — övriga roller i gruppen är tillåtna (och undantagna vid 75%).",
        "wp_elig_ok": "✅ Inget yrkesförbud för SSYK {code}.",
        "wp_floor_pass": "✅ Föreslagna SEK {sal:,} når golvet SEK {floor:,} ({basis}). Marginal +SEK {margin:,}.",
        "wp_floor_fail": "❌ Föreslagna SEK {sal:,} är under golvet SEK {floor:,} ({basis}). Saknas SEK {gap:,}.",
        "wp_basis_general": "90% av medianen",
        "wp_basis_transition": "80% av medianen — övergångsregel",
        "wp_basis_exempt": "75% av medianen — undantaget yrke",
        "wp_basis_blue": "EU-blåkortets tröskel",
        "wp_market_none": "Ingen SCB-lönefördelning för detta yrke/sektor/år — kan inte bedöma marknadsläget.",
        "wp_market": "Föreslagna SEK {sal:,} ligger på cirka **P{pct:.0f}** av marknadsintervallet ({sector}, {year}). Intervall: P10 SEK {p10:,} · median SEK {p50:,} · P90 SEK {p90:,}.",
        "wp_market_below": "⚠️ Under yrkets median — kontrollera att det når kollektivavtal / branschpraxis.",
        "wp_market_ok": "✅ På eller över yrkets median.",
        "wp_market_note": "ℹ️ Endast marknadsdata som riktmärke. Det rättsliga testet är kollektivavtal eller branschpraxis — stäm av mot relevant avtal.",
        "wp_plot_proposed": "Föreslagen",
        "wp_plot_floor": "Golv",
        "wp_ref_lines": "Referenslinjer — % av yrkets median (SEK {median:,}) för vald sektor:",
        "wp_data_expander": "📊 Lönefördelningsdata för detta yrke",
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
        "stats_title": "Antal anställda i urvalet",
        "stat_total": "Totalt antal anställda",
        "per_occ": "Per yrke",
        "occupation": "Yrke",
        "stats_note": "Detta är SCB:s uppskattade antal anställda som lönesiffrorna baseras på "
                      "(hela Sverige, vald sektor & år). Olika tabeller kan rapportera något "
                      "olika totaler — se källjämförelsen nedan.",
        "src_compare": "Källjämförelse (totaler per tabell)",
        "src_region": "Regiontabell (Sverige totalt)",
        "src_edu": "Utbildningstabell (alla nivåer)",
        "age_title": "Genomsnittlig månadslön efter åldersgrupp",
        "region_title": "Genomsnittlig månadslön efter region",
        "edu_title": "Genomsnittlig månadslön efter utbildningsnivå",
        "select_year": "År",
        "measures_shown": "Visade mått",
        "measure_type": "Lönemått",
        "monthly": "Månadslön", "basic": "Grundlön",
        "headcount": "Antal anställda",
        "def_title": "ℹ️ Vad betyder måtten?",
        "def_basic": "**Grundlön** — den fasta avtalade grundlönen.",
        "def_monthly": "**Månadslön** — grundlön **plus** fasta tillägg "
                       "(OB-tillägg, fasta bonusar, förmåner). "
                       "Exkluderar övertid och prestationsbonus, så Månadslön ≥ Grundlön.",
        "show_ratio": "Visa kvinnors lön i % av mäns",
        "ratio_axis": "Kvinnors lön (% av mäns)",
        "show_region_pct": "Visa som % av Sverige (totalt)",
        "men": "Män", "women": "Kvinnor",
        "no_pct_note": "ℹ️ SCB ger endast genomsnitts-/grundlön för denna uppdelning — percentiler finns endast i fliken Lönespridning.",
        "agg_info": "ℹ️ Aggregerat över {n} yrken i ”{grp}”, viktat efter antal anställda.",
        "agg_pct_extra": " Percentilerna är antalsviktade medelvärden av varje yrkes percentil — en approximation, inte en omräknad fördelning.",
        "all_major": "— Alla huvudgrupper —",
        "all_sub":   "— Alla undergrupper —",
        "btn_search": "🔍 Sök",
        "btn_clear":  "✕ Rensa allt",
        "sectors": {
            "0":   "Alla sektorer",
            "1-3": "Offentlig sektor (totalt)",
            "1":   "Staten",
            "2":   "Kommuner",
            "3":   "Regioner",
            "4-5": "Privat sektor (totalt)",
            "4":   "Privat sektor – arbetare",
            "5":   "Privat sektor – tjänstemän",
        },
        "sex_options": {"1+2": "Totalt", "1": "Män", "2": "Kvinnor"},
        "measures": {
            "000000C5": "Genomsnittlig månadslön",
            "000000C6": "Median (P50)",
            "000000C7": "P10",
            "000000C8": "P25",
            "000000C9": "P75",
            "000000CA": "P90",
        },
    },
}

TABLE_BASE = "AM/AM0110/AM0110A"

# Percentile tables (two ranges merged). Each carries its OWN ContentsCodes,
# listed in the canonical order: [Average, Median, P10, P25, P75, P90].
PCT_TABLES = [
    ("LoneSpridSektorYrk4A", 2014, 2022,
     ["000000C5", "000000C6", "000000C7", "000000C8", "000000C9", "000000CA"]),
    ("LoneSpridSektYrk4AN",  2023, 2025,
     ["000007CD", "000007CE", "000007CF", "000007CG", "000007CH", "000007CI"]),
]
# Age tables
AGE_TABLES = [
    ("LonYrkeAlder4A",  2014, 2022),
    ("LonYrkeAlder4AN", 2023, 2025),
]
# Region tables
REG_TABLES = [
    ("LonYrkeRegion4A",  2014, 2022),
    ("LonYrkeRegion4AN", 2023, 2025),
]
# Education tables
EDU_TABLES = [
    ("LonYrkeUtbildning4A",  2014, 2022),
    ("LonYrkeUtbildning4AN", 2023, 2025),
]

REGIONS = {
    "EN": {
        "SE":   "Sweden (total)", "SE11": "Stockholm",
        "SE12": "East-Central Sweden", "SE21": "Småland & islands",
        "SE22": "South Sweden", "SE23": "West Sweden",
        "SE31": "North-Central Sweden", "SE32": "Central Norrland",
        "SE33": "Upper Norrland",
    },
    "SV": {
        "SE":   "Sverige (totalt)", "SE11": "Stockholm",
        "SE12": "Östra Mellansverige", "SE21": "Småland med öarna",
        "SE22": "Sydsverige", "SE23": "Västsverige",
        "SE31": "Norra Mellansverige", "SE32": "Mellersta Norrland",
        "SE33": "Övre Norrland",
    },
}

EDU_LEVELS = {
    "EN": {
        "TOTALT": "All levels",
        "1": "Primary ed. < 9 years",
        "2": "Primary ed. 9–10 years",
        "3": "Upper secondary ≤ 2 years",
        "4": "Upper secondary 3 years",
        "5": "Post-secondary < 3 years",
        "6": "Post-secondary ≥ 3 years",
        "7": "Post-graduate",
    },
    "SV": {
        "TOTALT": "Alla nivåer",
        "1": "Förgymnasial < 9 år",
        "2": "Förgymnasial 9–10 år",
        "3": "Gymnasial, högst 2 år",
        "4": "Gymnasial, 3 år",
        "5": "Eftergymnasial < 3 år",
        "6": "Eftergymnasial ≥ 3 år",
        "7": "Forskarutbildning",
    },
}

AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65-68"]

# ── Work-permit rule set (Migrationsverket) — admin-editable ──────────────────
# Defaults below; an admin can override them in-app (saved to wp_rules.json,
# which takes precedence). Pure file IO so it can run at import time safely.
WP_RULES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wp_rules.json")
WP_DEFAULTS = {
    "as_of": "2026-06-16",          # date the figures are valid from
    "median": 38300,                # official Migrationsverket median (SEK/month)
    "pct_general": 0.90,            # general salary floor = 90% of median
    "pct_transition": 0.80,         # transition (old "good living") = 80%
    "pct_exempt": 0.75,             # exempt occupations = 75%
    "blue_card_floor": 52000,       # EU Blue Card fixed threshold (SEK/month)
    "transition_end": "2026-12-01", # new 90% rule applies from 2 Dec 2026
    "bench_year": 2025,             # SCB year used for the market-position check
    # 75%-exempt occupations — Utlänningsförordningen 2006:97, 5 kap. 6 § (SFS 2026:605)
    "exempt_ssyk": ["3115", "3215", "3511", "3512", "3513", "3514",
                    "5321", "5322", "5323", "5324", "5325", "5326", "5330",
                    "6121", "6129", "6130", "6210",
                    "7212", "7215", "7233", "7413", "7611",
                    "8161", "8169", "8199", "8341", "9210"],
    "banned_full": ["5343"],        # personal assistants — regular permit impossible
    "banned_partial": ["9210"],     # forest berry pickers within 9210 — warn only
}


def load_wp_rules() -> dict:
    """Active rule set: defaults overridden by wp_rules.json if present."""
    rules = dict(WP_DEFAULTS)
    if os.path.exists(WP_RULES_FILE):
        try:
            with open(WP_RULES_FILE, encoding="utf-8") as f:
                rules.update(json.load(f))
        except Exception:
            pass
    return rules


def save_wp_rules(rules: dict):
    with open(WP_RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


# ── General app settings (admin-editable) ─────────────────────────────────────
APP_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "app_settings.json")
APP_DEFAULTS = {"ssyk_show_3digit": True, "latest_data_year": 2025}


def load_app_settings() -> dict:
    s = dict(APP_DEFAULTS)
    if os.path.exists(APP_SETTINGS_FILE):
        try:
            with open(APP_SETTINGS_FILE, encoding="utf-8") as f:
                s.update(json.load(f))
        except Exception:
            pass
    return s


def save_app_settings(s: dict):
    with open(APP_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


# ── User guide (markdown, admin-editable) ─────────────────────────────────────
GUIDE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guide.json")
GUIDE_DEFAULTS = {
    "en": """# 👋 Welcome to the SCB Salary Explorer

This tool lets you look up **Swedish salaries** by occupation and check **work-permit salary requirements** — using official data from Statistics Sweden (SCB). No technical knowledge needed.

## 🚀 Getting started — 3 steps
1. **Choose your filters** in the left sidebar: sector, sex, year range and an occupation.
2. Click **🔍 Search**.
3. **Read the results** in the tabs that appear.

Change any filter and click Search again to update.

## 🔎 Finding the right occupation
- Type in the **"Search occupations"** box in the sidebar — it matches job titles, codes and common alternative titles (e.g. type *"borgarråd"* to find *Politician*).
- Or drill down with **Major group → Sub-group**.
- Not sure of the code? Open the **📖 SSYK guide** tab to browse every occupation with a description and a search box.

## 📈 Reading the salary charts
Salaries are shown as **percentiles**:
- **P10** — 10% earn less than this (the lower end).
- **P50 (Median)** — the middle salary; half earn more, half less.
- **P90** — only 10% earn more (the top end).
- **Average** — shown as a separate ♦ marker.

A wide gap between P10 and P90 means salaries vary a lot in that job.

## 💰 "Where do I stand?"
Enter a monthly salary and an occupation, and the tool tells you **which percentile it falls in** — e.g. *"higher than ~68% of people in this role"*.

## 🛂 Work permit check
Enter the proposed salary and occupation. The tool checks:
- whether it meets the **salary floor** (a % of the national median),
- where it sits in the **occupation's own pay range**,
- whether the occupation is **exempt or restricted**.

Each check shows ✅ pass, ⚠️ caution or ❌ fail with the numbers. *Always confirm against the relevant collective agreement.*

## 🏆 Leaderboard
Ranks the occupations in your selected group by pay, gender pay gap or salary growth.

## 👤 🗺️ 🎓 Age, region & education
These tabs break the salary down by **age group**, **region** and **education level**, with an optional women-vs-men comparison.

## 🌐 Language
Use the **English / Svenska** switch at the top of the sidebar — it changes both the interface and the data labels.

## 🔐 For administrators
Logged-in admins get an **Admin** section to refresh SCB data, manage users, edit the work-permit rules, change display settings and edit this guide.

## ❓ Good to know
- Data comes from **SCB Wage Structure Statistics** and currently covers up to **2025**.
- Some small occupations show "–" — SCB hides figures for very small groups.
- SSYK descriptions are **auto-translated** from Swedish where no official English version exists.
""",
    "sv": """# 👋 Välkommen till SCB Lönestatistik

Med det här verktyget kan du slå upp **svenska löner** per yrke och kontrollera **lönekrav för arbetstillstånd** — med officiell data från Statistiska centralbyrån (SCB). Inga tekniska kunskaper behövs.

## 🚀 Kom igång — 3 steg
1. **Välj dina filter** i sidofältet till vänster: sektor, kön, årsintervall och ett yrke.
2. Klicka på **🔍 Sök**.
3. **Läs resultaten** i flikarna som visas.

Ändra valfritt filter och klicka på Sök igen för att uppdatera.

## 🔎 Hitta rätt yrke
- Skriv i rutan **"Sök yrken"** i sidofältet — den matchar yrkestitlar, koder och vanliga benämningar (skriv t.ex. *"borgarråd"* för att hitta *Politiker*).
- Eller borra ner med **Huvudgrupp → Undergrupp**.
- Osäker på koden? Öppna fliken **📖 SSYK-guide** för att bläddra bland alla yrken med beskrivning och en sökruta.

## 📈 Läsa lönediagrammen
Löner visas som **percentiler**:
- **P10** — 10% tjänar mindre än så här (nedre delen).
- **P50 (Median)** — mittenlönen; hälften tjänar mer, hälften mindre.
- **P90** — bara 10% tjänar mer (övre delen).
- **Genomsnitt** — visas som en separat ♦-markör.

Ett stort gap mellan P10 och P90 betyder att lönerna varierar mycket i yrket.

## 💰 "Var ligger jag?"
Ange en månadslön och ett yrke, så visar verktyget **vilken percentil den hamnar i** — t.ex. *"högre än ca 68% i detta yrke"*.

## 🛂 Arbetstillståndskoll
Ange föreslagen lön och yrke. Verktyget kontrollerar:
- om den når **lönegolvet** (en % av nationella medianen),
- var den ligger i **yrkets eget löneintervall**,
- om yrket är **undantaget eller begränsat**.

Varje kontroll visar ✅ godkänt, ⚠️ varning eller ❌ ej godkänt med siffror. *Stäm alltid av mot relevant kollektivavtal.*

## 🏆 Topplista
Rangordnar yrkena i din valda grupp efter lön, lönegap mellan könen eller löneökning.

## 👤 🗺️ 🎓 Ålder, region & utbildning
Dessa flikar delar upp lönen efter **åldersgrupp**, **region** och **utbildningsnivå**, med valfri jämförelse kvinnor mot män.

## 🌐 Språk
Använd **English / Svenska**-väljaren högst upp i sidofältet — den ändrar både gränssnittet och dataetiketterna.

## 🔐 För administratörer
Inloggade administratörer får en **Admin**-sektion för att uppdatera SCB-data, hantera användare, redigera reglerna för arbetstillstånd, ändra visningsinställningar och redigera den här guiden.

## ❓ Bra att veta
- Data kommer från **SCB:s lönestrukturstatistik** och omfattar för närvarande till och med **2025**.
- Vissa små yrken visar "–" — SCB döljer siffror för mycket små grupper.
- Beskrivningar i SSYK-guiden är **maskinöversatta** från svenska där officiell engelsk version saknas.
""",
}


def load_guide() -> dict:
    g = dict(GUIDE_DEFAULTS)
    if os.path.exists(GUIDE_FILE):
        try:
            with open(GUIDE_FILE, encoding="utf-8") as f:
                g.update(json.load(f))
        except Exception:
            pass
    return g


def save_guide(g: dict):
    with open(GUIDE_FILE, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)


# Derived module-level values (re-read from file on every Streamlit rerun).
_wp = load_wp_rules()
WP_RULES_AS_OF     = _wp["as_of"]
WP_MEDIAN_SALARY   = _wp["median"]
WP_PCT_GENERAL     = _wp["pct_general"]
WP_PCT_TRANSITION  = _wp["pct_transition"]
WP_PCT_EXEMPT      = _wp["pct_exempt"]
WP_BLUE_CARD_FLOOR = _wp["blue_card_floor"]
WP_TRANSITION_END  = _wp["transition_end"]
WP_BENCH_YEAR      = _wp["bench_year"]
WP_EXEMPT_SSYK     = set(_wp["exempt_ssyk"])
WP_BANNED_FULL     = set(_wp["banned_full"])
WP_BANNED_PARTIAL  = set(_wp["banned_partial"])

# ── Newest available SCB data year ────────────────────────────────────────────
# Admin-controlled, persisted in app_settings.json. A forced "check for new data"
# in the admin panel rolls this forward, updating the year slider, every API
# query bound and the leaderboard for ALL users at once — no code changes needed.
LATEST_DATA_YEAR = int(load_app_settings().get("latest_data_year", 2025))
# First year of the current ("…4AN") table generation; the older "…4A" tables end 2022.
NEW_GEN_START    = 2023


def new_gen_years():
    """Year strings covered by the current table generation (2023 … latest)."""
    return [str(y) for y in range(NEW_GEN_START, LATEST_DATA_YEAR + 1)]


def _cap_newest(table_list):
    """Extend the newest table generation's upper year bound to LATEST_DATA_YEAR
    (the 'hi' is at index 2 for both the 4-tuple and 3-tuple table rows)."""
    row = list(table_list[-1])
    row[2] = LATEST_DATA_YEAR
    table_list[-1] = tuple(row)


for _tl in (PCT_TABLES, AGE_TABLES, REG_TABLES, EDU_TABLES):
    _cap_newest(_tl)


def wp_floor(ssyk: str, permit_type: str, is_transition: bool, app_date_iso: str):
    """Return (floor_sek, basis_key) for the applicable salary floor."""
    if permit_type == "blue":
        return WP_BLUE_CARD_FLOOR, "blue"
    if is_transition and app_date_iso <= WP_TRANSITION_END:
        return round(WP_MEDIAN_SALARY * WP_PCT_TRANSITION), "transition"
    if ssyk in WP_EXEMPT_SSYK:
        return round(WP_MEDIAN_SALARY * WP_PCT_EXEMPT), "exempt"
    return round(WP_MEDIAN_SALARY * WP_PCT_GENERAL), "general"


def interp_percentile(salary, points):
    """points: sorted [(level, value)]. Returns (estimated_percentile, position)."""
    levs = [lv for lv, _ in points]
    vals = [v for _, v in points]
    if salary <= vals[0]:
        return levs[0], "below"
    if salary >= vals[-1]:
        return levs[-1], "above"
    for i in range(len(points) - 1):
        v0, v1 = vals[i], vals[i + 1]
        if v0 <= salary <= v1:
            frac = (salary - v0) / (v1 - v0) if v1 > v0 else 0.0
            return levs[i] + frac * (levs[i + 1] - levs[i]), "in"
    return levs[-1], "in"

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "occupations_cache.json")

# ── Occupation cache (disk + session) ─────────────────────────────────────────

def _fetch_occupations_from_api(lang: str) -> dict[str, str]:
    base = f"https://api.scb.se/OV0104/v1/doris/{lang.lower()}/ssd"
    url  = f"{base}/{TABLE_BASE}/LoneSpridSektorYrk4A"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    for var in r.json()["variables"]:
        if var["code"] == "Yrke2012":
            return dict(zip(var["values"], var["valueTexts"]))
    return {}


def refresh_cache() -> str:
    """Fetch EN + SV occupations from API, save to disk. Returns timestamp string."""
    data = {
        "EN": _fetch_occupations_from_api("EN"),
        "SV": _fetch_occupations_from_api("SV"),
        "cached_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Update session state
    st.session_state["occupations_EN"] = data["EN"]
    st.session_state["occupations_SV"] = data["SV"]
    st.session_state["cache_ts"] = data["cached_at"]
    return data["cached_at"]


def load_occupations(lang: str) -> dict[str, str]:
    """Return occupations: session_state → disk cache → API (auto-builds cache)."""
    key = f"occupations_{lang}"
    if key in st.session_state:
        return st.session_state[key]

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        st.session_state["occupations_EN"] = data.get("EN", {})
        st.session_state["occupations_SV"] = data.get("SV", {})
        st.session_state["cache_ts"] = data.get("cached_at", "unknown")
        return st.session_state[key]

    # No cache on disk — fetch and save
    refresh_cache()
    return st.session_state[key]


# ── SSYK code browser data (scraped descriptions + synonyms) ──────────────────
SSYK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ssyk_descriptions.json")
SSYK_OVERRIDES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "ssyk_overrides.json")


def load_ssyk_nodes() -> dict:
    """SSYK nodes from disk, with admin overrides merged in. Cached per session."""
    if "ssyk_nodes" in st.session_state:
        return st.session_state["ssyk_nodes"]
    nodes = {}
    if os.path.exists(SSYK_FILE):
        with open(SSYK_FILE, encoding="utf-8") as f:
            nodes = json.load(f).get("nodes", {})
    if os.path.exists(SSYK_OVERRIDES_FILE):
        try:
            with open(SSYK_OVERRIDES_FILE, encoding="utf-8") as f:
                for code, ov in json.load(f).items():
                    if code in nodes:
                        nodes[code].update(ov)
        except Exception:
            pass
    st.session_state["ssyk_nodes"] = nodes
    return nodes


def save_ssyk_override(code: str, fields: dict):
    """Persist an admin edit for one code to ssyk_overrides.json, refresh cache."""
    data = {}
    if os.path.exists(SSYK_OVERRIDES_FILE):
        try:
            with open(SSYK_OVERRIDES_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data.setdefault(code, {}).update(fields)
    with open(SSYK_OVERRIDES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    st.session_state.pop("ssyk_nodes", None)   # force reload with the override


def ssyk_name(code: str, lang: str, nodes: dict) -> str:
    """Display name: official API/standard names for 1/2/4-digit, translated
    name for 3-digit (no API source exists there)."""
    occ = st.session_state.get(f"occupations_{lang}", {})
    n = nodes.get(code, {})
    if len(code) == 4:
        return occ.get(code, n.get("name_sv", code))
    if len(code) == 1:
        v = MAJOR_GROUPS[lang].get(code, "")
        return v.split("–", 1)[-1].strip() if v else n.get("name_sv", code)
    if len(code) == 2:
        v = SUB_GROUPS[lang].get(code, "")
        return v.split("–", 1)[-1].strip() if v else n.get("name_sv", code)
    if len(code) == 3:
        return (n.get("name_en") or n.get("name_sv", code)) if lang == "EN" \
            else n.get("name_sv", code)
    return code


def ssyk_synonym_index() -> dict[str, str]:
    """{4-digit code: lowercased joined synonym titles} for the occupation search."""
    if "ssyk_syn_idx" in st.session_state:
        return st.session_state["ssyk_syn_idx"]
    idx = {code: " | ".join(v.get("synonyms", []) + v.get("synonyms_en", [])).lower()
           for code, v in load_ssyk_nodes().items() if len(code) == 4}
    st.session_state["ssyk_syn_idx"] = idx
    return idx

# ── Data fetching ──────────────────────────────────────────────────────────────

def _post(table_name: str, query: list, lang: str) -> pd.DataFrame | None:
    """Generic POST to a PxWebApi table. Returns raw DataFrame or None."""
    url = f"https://api.scb.se/OV0104/v1/doris/{lang.lower()}/ssd/{TABLE_BASE}/{table_name}"
    try:
        r = requests.post(url, json={"query": query, "response": {"format": "json"}}, timeout=25)
        if r.status_code in (400, 404):
            return None
        r.raise_for_status()
        raw = r.json()
    except Exception:
        return None
    columns = [c["text"] for c in raw["columns"]]
    rows    = [item["key"] + item["values"] for item in raw["data"]]
    return pd.DataFrame(rows, columns=columns) if rows else None


SALARY_COL = "__monthly__"  # canonical name for the monthly-salary column
BASIC_COL  = "__basic__"    # canonical name for the basic-salary column
COUNT_COL  = "__count__"    # canonical name for the headcount column

_BAD = ("confidence", "interval", "percent", "konfidens", "intervall", "procent", "95")


def _pick_col(cols, kw) -> str | None:
    cands = [c for c in cols if kw in c.lower() and not any(b in c.lower() for b in _BAD)]
    return cands[0] if cands else None


def _pick_salary_col(cols, lang) -> str | None:
    return _pick_col(cols, "monthly" if lang == "EN" else "månadslön")


def _merge_tables(table_list, build_query, lang, years, measure_labels):
    """Percentile path: each table has its own ContentsCodes mapped to canonical labels."""
    frames = []
    for tname, lo, hi, codes in table_list:
        yr = [y for y in years if lo <= int(y) <= hi]
        if not yr:
            continue
        df = _post(tname, build_query(yr, codes), lang)
        if df is None:
            continue
        # Last len(codes) columns are the measures, in canonical order
        key_cols = df.columns[:-len(codes)].tolist()
        df.columns = key_cols + list(measure_labels)
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    for col in measure_labels:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _merge_simple(table_list, build_query, lang, years):
    """Single-measure path: keep API column names, select salary col by name."""
    frames = []
    for tname, lo, hi in table_list:
        yr = [y for y in years if lo <= int(y) <= hi]
        if not yr:
            continue
        df = _post(tname, build_query(yr), lang)
        if df is not None:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    df  = pd.concat(frames, ignore_index=True)
    sal = _pick_salary_col(df.columns, lang)
    if sal is None:
        return pd.DataFrame()
    rename = {sal: SALARY_COL}
    basic  = _pick_col(df.columns, "basic salary" if lang == "EN" else "grundlön")
    count  = _pick_col(df.columns, "number of employees" if lang == "EN" else "antal anställda")
    if basic: rename[basic] = BASIC_COL
    if count: rename[count] = COUNT_COL
    df = df.rename(columns=rename)
    for c in (SALARY_COL, BASIC_COL, COUNT_COL):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


@st.cache_data(show_spinner=False, persist="disk")
def fetch_percentile_data(sector, occ_codes, sex, years, lang, measure_keys, measure_labels):
    def q(yr, codes):
        return [
            {"code": "Sektor",       "selection": {"filter": "item", "values": [sector]}},
            {"code": "Yrke2012",     "selection": {"filter": "item", "values": list(occ_codes)}},
            {"code": "Kon",          "selection": {"filter": "item", "values": [sex]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": codes}},
            {"code": "Tid",          "selection": {"filter": "item", "values": yr}},
        ]
    return _merge_tables(PCT_TABLES, q, lang, years, measure_labels)


@st.cache_data(show_spinner=False, persist="disk")
def fetch_age_data(sector, occ_codes, year, lang):
    def q(yr):
        return [
            {"code": "Sektor",   "selection": {"filter": "item", "values": [sector]}},
            {"code": "Yrke2012", "selection": {"filter": "item", "values": list(occ_codes)}},
            {"code": "Kon",      "selection": {"filter": "item", "values": ["1", "2", "1+2"]}},
            {"code": "Alder",    "selection": {"filter": "item", "values": AGE_GROUPS}},
            {"code": "Tid",      "selection": {"filter": "item", "values": yr}},
        ]
    return _merge_simple(AGE_TABLES, q, lang, [str(year)])


@st.cache_data(show_spinner=False, persist="disk")
def fetch_region_data(sector, occ_codes, sex, year, lang):
    reg_codes = list(REGIONS[lang].keys())
    def q(yr):
        return [
            {"code": "Region",   "selection": {"filter": "item", "values": reg_codes}},
            {"code": "Sektor",   "selection": {"filter": "item", "values": [sector]}},
            {"code": "Yrke2012", "selection": {"filter": "item", "values": list(occ_codes)}},
            {"code": "Kon",      "selection": {"filter": "item", "values": [sex]}},
            {"code": "Tid",      "selection": {"filter": "item", "values": yr}},
        ]
    return _merge_simple(REG_TABLES, q, lang, [str(year)])


@st.cache_data(show_spinner=False, persist="disk")
def fetch_edu_data(sector, occ_codes, year, lang):
    edu_codes = list(EDU_LEVELS[lang].keys())
    def q(yr):
        return [
            {"code": "Sektor",          "selection": {"filter": "item", "values": [sector]}},
            {"code": "Yrke2012",        "selection": {"filter": "item", "values": list(occ_codes)}},
            {"code": "Kon",             "selection": {"filter": "item", "values": ["1", "2"]}},
            {"code": "UtbildningsNiva", "selection": {"filter": "item", "values": edu_codes}},
            {"code": "Tid",             "selection": {"filter": "item", "values": yr}},
        ]
    return _merge_simple(EDU_TABLES, q, lang, [str(year)])


@st.cache_data(show_spinner=False, persist="disk")
def fetch_stats_data(sector, occ_codes, year, lang):
    """Employee counts (national total) by sex from the region table."""
    def q(yr):
        return [
            {"code": "Region",   "selection": {"filter": "item", "values": ["SE"]}},
            {"code": "Sektor",   "selection": {"filter": "item", "values": [sector]}},
            {"code": "Yrke2012", "selection": {"filter": "item", "values": list(occ_codes)}},
            {"code": "Kon",      "selection": {"filter": "item", "values": ["1", "2", "1+2"]}},
            {"code": "Tid",      "selection": {"filter": "item", "values": yr}},
        ]
    return _merge_simple(REG_TABLES, q, lang, [str(year)])


@st.cache_data(show_spinner=False, persist="disk")
def fetch_edu_total_count(sector, occ_codes, year, lang):
    """Total employee count from the education table (all education levels, both sexes)."""
    def q(yr):
        return [
            {"code": "Sektor",          "selection": {"filter": "item", "values": [sector]}},
            {"code": "Yrke2012",        "selection": {"filter": "item", "values": list(occ_codes)}},
            {"code": "Kon",             "selection": {"filter": "item", "values": ["1", "2"]}},
            {"code": "UtbildningsNiva", "selection": {"filter": "item", "values": ["TOTALT"]}},
            {"code": "Tid",             "selection": {"filter": "item", "values": yr}},
        ]
    return _merge_simple(EDU_TABLES, q, lang, [str(year)])


# Average + Median ContentsCodes per percentile table (for the leaderboard).
_LEAD_TABLES = [
    ("LoneSpridSektorYrk4A", 2014, 2022, ["000000C5", "000000C6"]),
    ("LoneSpridSektYrk4AN",  2023, 2025, ["000007CD", "000007CE"]),
]
_cap_newest(_LEAD_TABLES)


def fetch_available_year():
    """Newest year SCB actually publishes for the current wage table.
    Reads the table's 'Tid' metadata (a plain GET). Returns int or None on failure.
    Deliberately uncached — it's only called when an admin forces a check."""
    url = f"https://api.scb.se/OV0104/v1/doris/en/ssd/{TABLE_BASE}/LoneSpridSektYrk4AN"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        for var in r.json().get("variables", []):
            if var.get("code") == "Tid":
                yrs = [int(v) for v in var.get("values", []) if str(v).isdigit()]
                return max(yrs) if yrs else None
    except Exception:
        return None
    return None


@st.cache_data(show_spinner=False, persist="disk")
def fetch_live_median(lang):
    """Latest SCB national median (all sectors, all occupations, total) → (year, value)."""
    tables = [("LoneSpridSektYrk4AN", NEW_GEN_START, LATEST_DATA_YEAR, ["000007CE"])]
    def q(yr, codes):
        return [
            {"code": "Sektor",       "selection": {"filter": "item", "values": ["0"]}},
            {"code": "Yrke2012",     "selection": {"filter": "item", "values": ["0000"]}},
            {"code": "Kon",          "selection": {"filter": "item", "values": ["1+2"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": codes}},
            {"code": "Tid",          "selection": {"filter": "item", "values": yr}},
        ]
    df = _merge_tables(tables, q, lang, new_gen_years(), ("median",))
    if df.empty:
        return None, None
    ycol = df.columns[-2]
    df = df.dropna(subset=["median"])
    if df.empty:
        return None, None
    latest = df.sort_values(ycol).iloc[-1]
    return str(latest[ycol]).strip(), int(latest["median"])


@st.cache_data(show_spinner=False, persist="disk", ttl=86400)
def fetch_cpi_annual(end_year: int = 2025):
    """Annual-average Swedish CPI index (2020=100) → {year: index}.
    Uses SCB KPI2020M Shadow Index (00000807), averaged across the 12 months."""
    url = "https://api.scb.se/OV0104/v1/doris/en/ssd/PR/PR0101/PR0101A/KPI2020M"
    months = [f"{y}M{m:02d}" for y in range(2014, end_year + 1) for m in range(1, 13)]
    body = {"query": [
        {"code": "ContentsCode", "selection": {"filter": "item", "values": ["00000807"]}},
        {"code": "Tid",          "selection": {"filter": "item", "values": months}},
    ], "response": {"format": "json"}}
    try:
        r = requests.post(url, json=body, timeout=30)
        r.raise_for_status()
        raw = r.json()
    except Exception:
        return {}
    by_year = {}
    for item in raw.get("data", []):
        v = item["values"][0]
        if v not in ("..", "", None):
            by_year.setdefault(item["key"][0][:4], []).append(float(v))
    return {yr: sum(vs) / len(vs) for yr, vs in by_year.items() if vs}


@st.cache_data(show_spinner=False, persist="disk")
def fetch_market_salaries(sector, years, lang):
    """Median + average monthly salary for ALL occupations × sex (men/women/total),
    across the selected years. One query powers every leaderboard ranking."""
    def q(yr, codes):
        return [
            {"code": "Sektor",       "selection": {"filter": "item", "values": [sector]}},
            {"code": "Yrke2012",     "selection": {"filter": "all",  "values": ["*"]}},
            {"code": "Kon",          "selection": {"filter": "item", "values": ["1", "2", "1+2"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": codes}},
            {"code": "Tid",          "selection": {"filter": "item", "values": yr}},
        ]
    return _merge_tables(_LEAD_TABLES, q, lang, [str(y) for y in years], ("avg", "median"))


AGG_CODE = "__agg__"  # synthetic occupation code for an aggregated group


@st.cache_data(show_spinner=False, persist="disk")
def fetch_occ_weights(sector, occ_codes, sex, years, lang):
    """Per-occupation employee counts (national total) → {(occ_code, year): count}.
    Used to headcount-weight the percentile aggregation (that table has no count)."""
    def q(yr):
        return [
            {"code": "Region",   "selection": {"filter": "item", "values": ["SE"]}},
            {"code": "Sektor",   "selection": {"filter": "item", "values": [sector]}},
            {"code": "Yrke2012", "selection": {"filter": "item", "values": list(occ_codes)}},
            {"code": "Kon",      "selection": {"filter": "item", "values": [sex]}},
            {"code": "Tid",      "selection": {"filter": "item", "values": yr}},
        ]
    df = _merge_simple(REG_TABLES, q, lang, [str(y) for y in years])
    if df.empty or COUNT_COL not in df.columns:
        return {}
    occ_c  = df.columns[2]
    year_c = [c for c in df.columns if c.lower() in ("year", "år", "tid")][0]
    out = {}
    for _, r in df.iterrows():
        out[(str(r[occ_c]).strip(), str(r[year_c]).strip())] = r[COUNT_COL]
    return out


def collapse_df(df, occ_col, salary_cols, weight_col=None, ext_weights=None,
                year_col=None, count_col=None, group_cols=None):
    """Collapse many occupations into one synthetic AGG_CODE row per other-dimension
    cell, taking a headcount-weighted mean of salary_cols and a sum of count_col.
    group_cols, when given, are the only dimensions kept (drops extra measure columns)."""
    d = df.copy()
    if ext_weights is not None:
        d["__w__"] = [ext_weights.get((str(o).strip(), str(y).strip()), 0)
                      for o, y in zip(d[occ_col], d[year_col])]
    elif weight_col and weight_col in d.columns:
        d["__w__"] = pd.to_numeric(d[weight_col], errors="coerce").fillna(0)
    else:
        d["__w__"] = 1.0

    if group_cols is None:
        group_cols = [c for c in d.columns
                      if c not in salary_cols and c not in (occ_col, "__w__", count_col)]
        out_cols = df.columns.tolist()
    else:
        out_cols = (group_cols + [occ_col] + list(salary_cols)
                    + ([count_col] if count_col and count_col in d.columns else []))

    rows = []
    for keys, g in d.groupby(group_cols, dropna=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        rec = dict(zip(group_cols, keys))
        rec[occ_col] = AGG_CODE
        for v in salary_cols:
            vals = pd.to_numeric(g[v], errors="coerce")
            w    = g["__w__"].where(vals.notna(), 0)
            tot  = w.sum()
            rec[v] = (vals.fillna(0) * w).sum() / tot if tot > 0 else vals.mean()
        if count_col and count_col in g.columns:
            rec[count_col] = pd.to_numeric(g[count_col], errors="coerce").sum()
        rows.append(rec)
    return pd.DataFrame(rows)[out_cols]


# ── App layout ─────────────────────────────────────────────────────────────────

_ASSETS   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_ICON_PNG = os.path.join(_ASSETS, "logo_sweden.png")   # blue-yellow-blue bars

# NOTE: st.set_page_config / st.logo / global CSS now live in app.py — this file
# runs as a page inside the multi-country st.navigation app (see app.py).

# Full-page / modal panels are mutually exclusive — opening one closes the rest.
_PANEL_FLAGS = ("show_user_mgmt", "show_wp_config", "show_app_settings",
                "show_guide_edit", "show_user_guide", "show_ssyk_guide",
                "show_data_year")


def _open_panel(name):
    for k in _PANEL_FLAGS:
        st.session_state[k] = (k == name)
    st.rerun()


with st.sidebar:
    st.markdown(theme.SIDEBAR_CSS, unsafe_allow_html=True)
    # Logo (→ Home) on the left, a compact country switcher on the right so you
    # can jump straight to another country without going Home first.
    _logo_col, _sw_col = st.columns([1.7, 1], vertical_alignment="center")
    with _logo_col:
        st.page_link("landing.py", label="Salary Explorer", icon=":material/language:")
    with _sw_col:
        auth.country_switcher("sweden")
    auth.sidebar_identity()   # show who's signed in (avatar + name + role) + Log out
    st.markdown('<div style="height:1px;background:#EEF0F3;margin:12px 0 4px;"></div>',
                unsafe_allow_html=True)

    _lang_prev = st.session_state.get("_lang_val", "EN")
    lang = st.segmented_control(
        "Language / Språk", ["EN", "SV"],
        format_func=lambda k: {"EN": "English", "SV": "Svenska"}[k],
        default=_lang_prev, key="lang_seg") or _lang_prev
    st.session_state["_lang_val"] = lang
    t = T[lang]

    gc1, gc2 = st.columns(2)
    if gc1.button("User guide" if lang == "EN" else "Användarguide",
                  use_container_width=True):
        _open_panel("show_user_guide")
    if gc2.button("SSYK guide" if lang == "EN" else "SSYK-guide",
                  use_container_width=True):
        _open_panel("show_ssyk_guide")

    sector_labels = list(t["sectors"].values())
    sector_code   = list(t["sectors"].keys())[
        sector_labels.index(st.selectbox(t["sector"], sector_labels, key="sector_sel"))
    ]

    sex_labels = list(t["sex_options"].values())
    _sex_sel = st.segmented_control(t["sex"], sex_labels, default=sex_labels[0], key="sex_seg")
    if _sex_sel not in sex_labels:      # None (deselected) or stale after a language switch
        _sex_sel = sex_labels[0]
    sex_code = list(t["sex_options"].keys())[sex_labels.index(_sex_sel)]

    all_years = [str(y) for y in range(2014, LATEST_DATA_YEAR + 1)]
    yr_from, yr_to = st.select_slider(t["year_range"], options=all_years,
                                      value=(all_years[-3], all_years[-1]))
    selected_years = tuple(y for y in all_years if yr_from <= y <= yr_to)
    # Descending year options for the breakdown tabs (respect the range)
    year_opts = [int(y) for y in reversed(selected_years)]

    # Load occupations (from disk cache if available)
    occupations = load_occupations(lang)

    # ── 3-level drill-down (all levels optional) ───────────────────────────────
    major_map    = MAJOR_GROUPS[lang]
    major_none   = t["all_major"]
    major_opts   = [major_none] + list(major_map.values())
    major_label  = st.selectbox(t["major_group"], major_opts,
                                index=st.session_state.get("major_idx", 0),
                                key="major_sel")
    major_digit  = None if major_label == major_none else \
                   [k for k, v in major_map.items() if v == major_label][0]

    # Sub-group — only shown when a major group is selected
    sub_digit = None
    if major_digit is not None:
        sub_map_full = SUB_GROUPS[lang]
        present_subs = {code[:2] for code in occupations
                        if code[:1] == major_digit and code != "0000"}
        sub_map  = {k: v for k, v in sub_map_full.items()
                    if k.startswith(major_digit) and k in present_subs}
        sub_none = t["all_sub"]
        sub_opts = [sub_none] + list(sub_map.values())
        sub_label = st.selectbox(t["sub_group"], sub_opts,
                                 index=st.session_state.get("sub_idx", 0),
                                 key="sub_sel")
        sub_digit = None if sub_label == sub_none else \
                    [k for k, v in sub_map.items() if v == sub_label][0]

    # Occupation pool based on how specific the selection is
    if sub_digit:
        pool = {k: v for k, v in occupations.items()
                if k.startswith(sub_digit) and k != "0000"}
    elif major_digit:
        pool = {k: v for k, v in occupations.items()
                if k[:1] == major_digit and k != "0000"}
    else:
        pool = {k: v for k, v in occupations.items() if k != "0000"}

    search = st.text_input("🔍", placeholder=t["occ_search_ph"],
                           label_visibility="collapsed", key="occ_search")
    if search:
        # Search globally across ALL occupations (name, code, OR SSYK synonym title)
        s = search.strip().lower()
        syn = ssyk_synonym_index()
        pool = {k: v for k, v in occupations.items()
                if k != "0000" and (s in v.lower() or s in k.lower() or s in syn.get(k, ""))}
        st.caption(t["found_n"].format(n=len(pool)) if pool else t["no_match"])

    occ_options = [f"{v}  ({k})" for k, v in pool.items()]

    selected_labels = st.multiselect(
        t["occ_select"],
        options=occ_options,
        default=[],
        max_selections=8,
        key="occ_selection",
    )

    def _clear_all():
        st.session_state["sector_sel"] = sector_labels[0]
        st.session_state["sex_sel"]    = sex_labels[0]
        for k in ["occ_selection", "occ_search", "query", "major_sel", "sub_sel"]:
            st.session_state.pop(k, None)

    col_search, col_clear = st.columns(2)
    with col_search:
        search_clicked = st.button(t["btn_search"], type="primary", use_container_width=True)
    with col_clear:
        st.button(t["btn_clear"], use_container_width=True, on_click=_clear_all)

    # Commit query to session_state only when Search is clicked
    if search_clicked:
        # Close any open full-page panel (user guide, SSYK guide, admin panels)
        # so results render instead of the panel stopping the run early.
        for _pf in _PANEL_FLAGS:
            st.session_state[_pf] = False
        aggregate, agg_name = False, ""
        if selected_labels:
            # Specific occupations chosen — show each individually
            codes = tuple(lbl.rsplit("(", 1)[-1].rstrip(")").strip()
                          for lbl in selected_labels)
        elif search and pool:
            # Active search, nothing explicitly picked — use the search matches
            codes = tuple(pool.keys())
        elif sub_digit or major_digit:
            # Drilled into a group with no occupation picked — aggregate the group
            codes = tuple(pool.keys())
            aggregate = True
            agg_name  = sub_label if sub_digit else major_label
        else:
            # No drill-down at all — use "0000" (SCB aggregate for all occupations)
            codes = ("0000",)
        # Group scope (used to limit the leaderboard to the drilled-into group)
        if sub_digit:
            scope_prefix, scope_label = sub_digit, sub_label
        elif major_digit:
            scope_prefix, scope_label = major_digit, major_label
        else:
            scope_prefix, scope_label = "", ""
        st.session_state["query"] = {
            "sector":       sector_code,
            "codes":        codes,
            "sex":          sex_code,
            "aggregate":    aggregate,
            "agg_name":     agg_name,
            "scope_prefix": scope_prefix,
            "scope_label":  scope_label,
        }

    selected_occ_codes = st.session_state.get("query", {}).get("codes", ())

    # ── Authentication / Admin ────────────────────────────────────────────────
    # The signed-in identity + Log out now live at the TOP of the sidebar
    # (auth.sidebar_identity), so this section only carries admin tools / the
    # admin-login form.
    auth_user = st.session_state.get("auth_user")
    if not auth.supabase_configured():
        st.divider()
        st.caption("🔒 Admin login not configured")
    elif auth_user:
        if auth_user["role"] in ("admin", "master"):
            st.divider()
            with st.expander("🔐 Admin", expanded=False):
                cache_ts = st.session_state.get("cache_ts", "")
                if st.button(f"↻ Refresh SCB codes · {cache_ts}", use_container_width=True):
                    with st.spinner("Fetching from SCB API…"):
                        ts = refresh_cache()
                    st.success(f"Updated {ts}")
                    st.rerun()
                if st.button(f"📅 Check data year · {LATEST_DATA_YEAR}",
                             use_container_width=True):
                    _open_panel("show_data_year")
                if st.button("👥 Manage users", use_container_width=True):
                    _open_panel("show_user_mgmt")
                if st.button("⚙️ Work permit rules", use_container_width=True):
                    _open_panel("show_wp_config")
                if st.button("🎛️ App settings", use_container_width=True):
                    _open_panel("show_app_settings")
                if st.button("📝 Edit user guide", use_container_width=True):
                    _open_panel("show_guide_edit")
    else:
        st.divider()
        with st.expander("🔐 Admin login", expanded=False):
            le = st.text_input("Email", key="login_email")
            lp = st.text_input("Password", type="password", key="login_pw")
            if st.button("Log in", use_container_width=True):
                user, err = auth.sign_in(le.strip(), lp)
                if user:
                    st.session_state["auth_user"] = user
                    st.session_state.pop("login_pw", None)
                    st.rerun()
                else:
                    st.error("Login failed — check email/password.")


@st.dialog("User management", width="large")
def _user_mgmt_dialog():
    me = st.session_state.get("auth_user", {})
    st.markdown("**Create user**")
    c1, c2, c3 = st.columns([3, 2, 2])
    ne = c1.text_input("Email", key="nu_email")
    npw = c2.text_input("Password", type="password", key="nu_pw")
    nr = c3.selectbox("Role", auth.ROLES, key="nu_role")
    if st.button("Create user", type="primary"):
        try:
            auth.create_user(ne.strip(), npw, nr)
            st.success(f"Created {ne}")
            st.rerun()
        except Exception as e:
            st.error(f"Could not create user: {e}")

    st.divider()
    st.markdown("**Existing users**")
    try:
        users = auth.list_users()
    except Exception as e:
        st.error(f"Could not list users: {e}")
        users = []
    for u in users:
        c1, c2, c3, c4 = st.columns([4, 3, 1, 1])
        c1.write(u["email"])
        if u["role"] == "master":
            c2.write("👑 master")
        elif u["id"] == me.get("id"):
            c2.write(f"{u['role']} (you)")
        else:
            nrole = c2.selectbox("role", auth.ROLES,
                                 index=auth.ROLES.index(u["role"]) if u["role"] in auth.ROLES else 0,
                                 key=f"role_{u['id']}", label_visibility="collapsed")
            if nrole != u["role"]:
                try:
                    auth.set_role(u["id"], nrole)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        # Password reset — available for every account (incl. your own / master)
        with c3.popover("🔑", help="Set password"):
            pw_label = "Your new password" if u["id"] == me.get("id") else f"New password for {u['email']}"
            newpw = st.text_input(pw_label, type="password", key=f"pw_{u['id']}")
            if st.button("Update password", key=f"pwbtn_{u['id']}"):
                try:
                    auth.set_password(u["id"], newpw)
                    st.success("Password updated.")
                except Exception as e:
                    st.error(str(e))
        # Delete — not allowed for master or yourself
        if u["role"] != "master" and u["id"] != me.get("id"):
            if c4.button("🗑", key=f"del_{u['id']}", help="Delete user"):
                try:
                    auth.delete_user(u["id"])
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    st.divider()
    if st.button("Close"):
        st.session_state["show_user_mgmt"] = False
        st.rerun()


def _wp_code_table(title, state_key, help_txt):
    """Interactive SSYK-code list: row per code (name + 🗑), plus an add box."""
    st.markdown(f"**{title}**")
    st.caption(help_txt)
    codes = st.session_state[state_key]
    if codes:
        for code in sorted(codes):
            r1, r2, r3 = st.columns([2, 6, 1])
            r1.write(code)
            r2.write(occupations.get(code, "—"))
            if r3.button("🗑", key=f"{state_key}_del_{code}", help="Remove"):
                st.session_state[state_key] = [c for c in codes if c != code]
                st.rerun()
    else:
        st.caption("— none —")
    a1, a2 = st.columns([5, 1])
    newc = a1.text_input("Add SSYK code", key=f"{state_key}_add_{len(codes)}",
                         placeholder="e.g. 2512", label_visibility="collapsed")
    if a2.button("➕ Add", key=f"{state_key}_addbtn"):
        nc = newc.strip()
        if nc and nc not in codes:
            st.session_state[state_key] = codes + [nc]
        st.rerun()


def render_wp_config():
    """Admin editor for the Work permit rule set (saved to wp_rules.json)."""
    rules = load_wp_rules()
    st.header("⚙️ Work permit rules")
    st.caption("Edit the figures the Work permit check uses. Saved values override the "
               "built-in defaults and apply immediately across the app.")

    # Editable code lists held in session_state (initialised once per open)
    for sk, src in [("wp_exempt", "exempt_ssyk"),
                    ("wp_banned_full", "banned_full"),
                    ("wp_banned_partial", "banned_partial")]:
        if sk not in st.session_state:
            st.session_state[sk] = list(rules[src])

    # ── Numeric / date settings (batched in a form) ───────────────────────────
    with st.form("wp_rules_form"):
        c1, c2, c3 = st.columns(3)
        as_of = c1.text_input("Rules valid from (YYYY-MM-DD)", rules["as_of"],
                              help="Shown in the banner at the top of the Work permit tab.")
        median = c2.number_input("National median salary (SEK)", value=int(rules["median"]),
                                 step=100,
                                 help="Migrationsverket's official median. Every % floor is "
                                      "computed from this number.")
        bench_year = c3.number_input("Market benchmark year", value=int(rules["bench_year"]),
                                     step=1,
                                     help="SCB year used for the occupation market-position chart.")
        c4, c5, c6 = st.columns(3)
        pct_general = c4.number_input("General floor (% of median)",
                                      value=float(rules["pct_general"]) * 100, step=1.0,
                                      help="Default 90%. The standard salary floor.")
        pct_transition = c5.number_input("Transition floor (%)",
                                         value=float(rules["pct_transition"]) * 100, step=1.0,
                                         help="Default 80%. Applies to extensions of permits "
                                              "granted before the reform, until the transition end date.")
        pct_exempt = c6.number_input("Exempt floor (%)",
                                     value=float(rules["pct_exempt"]) * 100, step=1.0,
                                     help="Default 75%. Applies to the exempt SSYK list below.")
        c7, c8 = st.columns(2)
        blue = c7.number_input("EU Blue Card threshold (SEK)",
                               value=int(rules["blue_card_floor"]), step=100,
                               help="Fixed monthly threshold for the EU Blue Card route.")
        transition_end = c8.text_input("Transition ends (YYYY-MM-DD)", rules["transition_end"],
                                       help="From the day after this date the general floor "
                                            "applies even to extensions.")
        saved = st.form_submit_button("💾 Save rules", type="primary")

    if saved:
        new = dict(rules)
        new.update({
            "as_of": as_of.strip(),
            "median": int(median),
            "bench_year": int(bench_year),
            "pct_general": round(pct_general / 100, 4),
            "pct_transition": round(pct_transition / 100, 4),
            "pct_exempt": round(pct_exempt / 100, 4),
            "blue_card_floor": int(blue),
            "transition_end": transition_end.strip(),
            "exempt_ssyk": sorted(st.session_state["wp_exempt"]),
            "banned_full": sorted(st.session_state["wp_banned_full"]),
            "banned_partial": sorted(st.session_state["wp_banned_partial"]),
        })
        try:
            save_wp_rules(new)
            for k in ("wp_exempt", "wp_banned_full", "wp_banned_partial"):
                st.session_state.pop(k, None)
            st.success("Rules saved.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not save: {e}")

    # ── SSYK code lists (interactive tables — add/remove apply on Save) ────────
    st.divider()
    _wp_code_table("Exempt SSYK codes — 75% floor", "wp_exempt",
                   "Occupations that use the 75% floor. Add/remove here, then **Save rules**.")
    _wp_code_table("Banned — full (hard block)", "wp_banned_full",
                   "Cannot get a regular permit at all (e.g. 5343).")
    _wp_code_table("Banned — partial (warning)", "wp_banned_partial",
                   "Partly banned — shows a warning (e.g. 9210 berry pickers).")

    st.divider()
    if st.button("← Back to app"):
        for k in ("wp_exempt", "wp_banned_full", "wp_banned_partial"):
            st.session_state.pop(k, None)
        st.session_state["show_wp_config"] = False
        st.rerun()


@st.dialog("Check SCB data year")
def _data_year_dialog():
    """Admin-forced check for a newer SCB data year, with an update/keep prompt.
    Separate from the SSYK-codes refresh — this only touches the data-year setting."""
    cur = LATEST_DATA_YEAR
    st.markdown(f"Newest year currently used across the app: **{cur}**")
    st.caption("SCB publishes each year's wage statistics roughly the following June. "
               "Updating rolls the year slider, all charts, the leaderboard and the "
               "work-permit check forward for every user at once.")

    if st.button("🔄 Check SCB now", type="primary"):
        with st.spinner("Asking SCB…"):
            st.session_state["_scb_latest_found"] = fetch_available_year()

    checked = "_scb_latest_found" in st.session_state
    found = st.session_state.get("_scb_latest_found")
    if checked and found is None:
        st.error("Couldn't reach SCB. Try again in a moment.")
    elif found is not None:
        if found > cur:
            st.info(f"SCB now publishes data up to **{found}**.")
            c1, c2 = st.columns(2)
            if c1.button(f"✅ Update to {found}", type="primary"):
                s = load_app_settings()
                save_app_settings({**s, "latest_data_year": int(found)})
                st.cache_data.clear()  # drop cached fetches so the new year loads
                st.session_state.pop("_scb_latest_found", None)
                st.session_state["show_data_year"] = False
                st.rerun()
            if c2.button(f"Keep {cur}"):
                st.session_state.pop("_scb_latest_found", None)
                st.session_state["show_data_year"] = False
                st.rerun()
        elif found == cur:
            st.success(f"Already up to date — SCB's newest year is {cur}.")
        else:
            st.warning(f"SCB's newest reported year is {found}, older than the "
                       f"current setting ({cur}). Keeping {cur}.")

    if st.button("Close"):
        st.session_state.pop("_scb_latest_found", None)
        st.session_state["show_data_year"] = False
        st.rerun()


def render_app_settings():
    """Admin editor for general app/display settings (saved to app_settings.json)."""
    s = load_app_settings()
    st.header("⚙️ App settings")
    st.caption("Display options for all users. Saved values apply immediately.")
    show3 = st.toggle("Show the 3-digit level (Minor group) in the SSYK guide",
                      value=s.get("ssyk_show_3digit", True),
                      help="When off, the SSYK guide drills 1 → 2 → 4 digits.")
    if st.button("💾 Save settings", type="primary"):
        save_app_settings({**s, "ssyk_show_3digit": show3})
        st.success("Saved.")
        st.rerun()
    if st.button("← Back to app"):
        st.session_state["show_app_settings"] = False
        st.rerun()


def render_user_guide():
    """Full-page user guide (markdown), visible to everyone."""
    g = load_guide()
    st.markdown(g.get("sv" if lang == "SV" else "en", ""))
    st.divider()
    if st.button("← Back to app", key="guide_back"):
        st.session_state["show_user_guide"] = False
        st.rerun()


def render_guide_edit():
    """Admin editor for the user guide (markdown, EN + SV) with live preview."""
    g = load_guide()
    st.header("📝 Edit user guide")
    st.caption("Plain Markdown. Use # for headings, ** for bold, - for bullet lists. "
               "Saved values apply immediately for everyone.")
    en_tab, sv_tab = st.tabs(["🇬🇧 English", "🇸🇪 Svenska"])
    with en_tab:
        en = st.text_area("Markdown (English)", g.get("en", ""), height=420, key="guide_en")
        with st.expander("👁 Preview"):
            st.markdown(en)
    with sv_tab:
        sv = st.text_area("Markdown (Svenska)", g.get("sv", ""), height=420, key="guide_sv")
        with st.expander("👁 Preview"):
            st.markdown(sv)
    c1, c2 = st.columns(2)
    if c1.button("💾 Save guide", type="primary"):
        save_guide({"en": en, "sv": sv})
        st.success("Saved.")
        st.rerun()
    if c2.button("← Back to app"):
        st.session_state["show_guide_edit"] = False
        st.rerun()


def render_ssyk_browser(prefix: str):
    """Drill-down SSYK navigator. Labels use the official SCB/API names; the
    3-digit level uses a (flagged) translation; descriptions/synonyms are scraped."""
    nodes = load_ssyk_nodes()
    if not nodes:
        st.info(t["ssyk_unavail"])
        return
    st.caption(t["ssyk_intro"])
    is_admin = st.session_state.get("auth_user", {}).get("role") in ("admin", "master")
    BLANK = "__none__"

    def fmt(code):
        return f"{code} – {ssyk_name(code, lang, nodes)}"

    def panel_for(cur):
        if not cur:
            st.info(t["ssyk_pick_prompt"])
            return
        node = nodes[cur]
        st.markdown(f"#### {cur} · {ssyk_name(cur, lang, nodes)}")
        desc = (node.get("desc_en") if lang == "EN" and node.get("desc_en")
                else node.get("desc_sv", ""))
        st.markdown(f"**{t['ssyk_desc']}**")
        if desc:
            st.write(desc)
        else:
            st.caption(t["ssyk_no_desc"])
        if lang == "EN" and (desc or (len(cur) == 3 and node.get("name_en"))):
            st.caption(t["ssyk_trans_warn"])
        syns = (node.get("synonyms_en") if lang == "EN" and node.get("synonyms_en")
                else node.get("synonyms", []))
        if syns:
            with st.expander(t["ssyk_syn"].format(n=len(syns))):
                st.write(", ".join(syns))
        if len(cur) == 4:
            if st.button(t["ssyk_use"], key=prefix + "_use", type="primary"):
                st.session_state["query"] = {
                    "sector": sector_code, "codes": (cur,), "sex": sex_code,
                    "aggregate": False, "agg_name": "",
                    "scope_prefix": cur[:2],
                    "scope_label": ssyk_name(cur[:2], lang, nodes),
                }
                st.rerun()
        if is_admin:
            with st.expander(t["ssyk_edit"]):
                with st.form(f"{prefix}_edit_{cur}"):
                    e_sv = st.text_area("desc_sv (Swedish)", node.get("desc_sv", ""))
                    e_en = st.text_area("desc_en (English)", node.get("desc_en", ""))
                    e_syn = st.text_area("Synonyms (comma-separated)",
                                         ", ".join(node.get("synonyms", [])))
                    e_name_en = st.text_input("name_en (3-digit only)",
                                              node.get("name_en", "")) \
                        if len(cur) == 3 else None
                    if st.form_submit_button("💾 Save content"):
                        fields = {
                            "desc_sv": e_sv.strip(),
                            "desc_en": e_en.strip(),
                            "synonyms": [s.strip() for s in e_syn.split(",") if s.strip()],
                        }
                        if e_name_en is not None:
                            fields["name_en"] = e_name_en.strip()
                        save_ssyk_override(cur, fields)
                        st.success(t["ssyk_edit_saved"])
                        st.rerun()

    # ── Global search across every field ──────────────────────────────────────
    query = st.text_input(t["ssyk_search"], key=prefix + "_search",
                          placeholder=t["ssyk_search"], label_visibility="collapsed")
    if query.strip():
        qs = query.strip().lower()
        matches = []
        for code, n in nodes.items():
            if len(code) == 1 and not n.get("children"):
                continue
            hay = " ".join([
                code, ssyk_name(code, lang, nodes),
                n.get("name_sv", ""), n.get("name_en", ""),
                n.get("desc_sv", ""), n.get("desc_en", ""),
                " ".join(n.get("synonyms", [])), " ".join(n.get("synonyms_en", [])),
            ]).lower()
            if qs in hay:
                matches.append(code)
        matches.sort(key=lambda c: (len(c), c))
        if not matches:
            st.info(t["no_match"])
            return
        sel = st.selectbox(t["ssyk_results"].format(n=len(matches)), matches[:300],
                           format_func=fmt, key=prefix + "_results")
        panel_for(sel)
        return

    # ── Drill-down (blank-able; start empty) ──────────────────────────────────
    show3 = load_app_settings().get("ssyk_show_3digit", True)  # admin-controlled
    nav, panel = st.columns([1, 1.3])
    with nav:
        def pick(label, opts):
            v = st.selectbox(label, [BLANK] + opts,
                             format_func=lambda c: t["ssyk_blank"] if c == BLANK else fmt(c))
            return None if v == BLANK else v
        l1 = sorted(c for c in nodes if len(c) == 1 and nodes[c].get("children"))
        s1 = pick(t["ssyk_l1"], l1)
        s2 = pick(t["ssyk_l2"], sorted(nodes[s1]["children"])) if s1 else None
        s3 = pick(t["ssyk_l3"], sorted(nodes[s2]["children"])) if (show3 and s2) else None
        parent3 = s3 or s2
        if parent3 and len(parent3) == 3:
            l4 = sorted(nodes[parent3]["children"])
        elif s2:
            l4 = sorted(c for c in nodes if len(c) == 4 and c.startswith(s2))
        else:
            l4 = []
        s4 = pick(t["ssyk_l4"], l4) if l4 else None
        current = s4 or s3 or s2 or s1
    with panel:
        panel_for(current)

# ── Main ───────────────────────────────────────────────────────────────────────

# Header per design-system.md §4: mono eyebrow, H1, source line. The signed-in
# identity lives in the sidebar (auth.sidebar_identity), so no header avatar.
st.markdown(f"""
<div style="margin-bottom:6px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
              letter-spacing:.16em;color:#0A63A6;margin-bottom:10px;">OFFICIAL STATISTICS · SWEDEN</div>
  <div style="display:flex;align-items:center;gap:14px;">
    <img class="se-hflag" src="{theme.flag_uri('se')}" alt="Sweden flag">
    <h1 style="margin:0;font-size:34px;font-weight:800;letter-spacing:-.025em;color:#0C1119;line-height:1.05;">{t['title']}</h1>
  </div>
  <p style="margin:8px 0 0;font-size:14px;color:#7A828F;">{t['caption']}</p>
</div>
""", unsafe_allow_html=True)

# Admin user-management modal (open across reruns via a session flag)
if st.session_state.get("show_user_mgmt") and \
        st.session_state.get("auth_user", {}).get("role") in ("admin", "master"):
    _user_mgmt_dialog()

# Admin data-year check — modal dialog (gated to admin/master)
if st.session_state.get("show_data_year") and \
        st.session_state.get("auth_user", {}).get("role") in ("admin", "master"):
    _data_year_dialog()

# Full-page exclusive views (admin panels, the guides, and the no-occupation
# landing browser) ALL render into one st.empty mount point. On a normal charts
# run this placeholder is created but left empty, which clears whatever a panel
# rendered on the previous run — otherwise Streamlit's st.stop() leaves those
# elements ghosting ("leaking through", faded) behind the charts.
_view = st.empty()

# Admin work-permit rules editor — full-page panel (gated to admin/master)
if st.session_state.get("show_wp_config") and \
        st.session_state.get("auth_user", {}).get("role") in ("admin", "master"):
    with _view.container():
        render_wp_config()
    st.stop()

# Admin app/display settings — full-page panel (gated to admin/master)
if st.session_state.get("show_app_settings") and \
        st.session_state.get("auth_user", {}).get("role") in ("admin", "master"):
    with _view.container():
        render_app_settings()
    st.stop()

# User guide — full-page, visible to everyone (no login needed)
if st.session_state.get("show_user_guide"):
    with _view.container():
        render_user_guide()
    st.stop()

# SSYK guide — full-page, visible to everyone (no login needed)
if st.session_state.get("show_ssyk_guide"):
    with _view.container():
        st.subheader(t["ssyk_title"])
        render_ssyk_browser("page")
        st.divider()
        if st.button("← Back to app", key="ssyk_back"):
            st.session_state["show_ssyk_guide"] = False
            st.rerun()
    st.stop()

# Admin user-guide editor — full-page panel (gated to admin/master)
if st.session_state.get("show_guide_edit") and \
        st.session_state.get("auth_user", {}).get("role") in ("admin", "master"):
    with _view.container():
        render_guide_edit()
    st.stop()

if not selected_occ_codes:
    with _view.container():
        st.info(t["select_prompt"])
        st.markdown(f"### {t['ssyk_title']}")
        render_ssyk_browser("landing")
    st.stop()

# Use the values that were active when Search was clicked
q            = st.session_state.get("query", {})
query_sector = q.get("sector", sector_code)
query_sex    = q.get("sex",    sex_code)
agg_mode     = q.get("aggregate", False)
agg_name     = q.get("agg_name", "")

def occ_name(code):
    """Display name for an occupation code, incl. the synthetic aggregate code."""
    if code == AGG_CODE:
        return agg_name
    return occupations.get(code, code)

# Codes used for chart series / display (one synthetic series when aggregating)
display_codes = (AGG_CODE,) if agg_mode else selected_occ_codes

measure_keys   = tuple(t["measures"].keys())
measure_labels = tuple(t["measures"].values())
_order_en = ["P10", "P25", "Median (P50)", "P75", "P90", "Average monthly salary"]
_order_sv = ["P10", "P25", "Median (P50)", "P75", "P90", "Genomsnittlig månadslön"]
pct_order = [m for m in (_order_en if lang == "EN" else _order_sv) if m in measure_labels]

with st.spinner(t["fetching_data"]):
    df = fetch_percentile_data(query_sector, selected_occ_codes, query_sex, selected_years,
                               lang, measure_keys, measure_labels)

if df.empty:
    st.warning(t["no_data"])
    st.stop()

key_cols = [c for c in df.columns if c not in measure_labels]
year_col = key_cols[-1]
occ_col  = key_cols[1]

if agg_mode:
    weights = fetch_occ_weights(query_sector, selected_occ_codes, query_sex,
                                selected_years, lang)
    df = collapse_df(df, occ_col, list(measure_labels),
                     ext_weights=weights, year_col=year_col)

colors = theme.SERIES

def measure_toggle(key):
    """Monthly vs Basic salary radio + definitions. Returns (column_name, axis_label)."""
    choice = st.radio(t["measure_type"], [t["monthly"], t["basic"]],
                      horizontal=True, key=key)
    with st.popover(t["def_title"]):
        st.markdown(t["def_monthly"])
        st.markdown(t["def_basic"])
    return (BASIC_COL, t["basic"]) if choice == t["basic"] else (SALARY_COL, t["monthly"])


def show_breakdown_raw(df_in, dim_col, dim_label, dim_map=None, sex_col=None):
    """Raw data expander for breakdown tabs."""
    with st.expander(t["raw_data"]):
        out = pd.DataFrame()
        out[dim_label] = df_in[dim_col].str.strip().map(dim_map) if dim_map else df_in[dim_col]
        if sex_col is not None:
            sm = {"1": t["men"], "2": t["women"], "1+2": "Total" if lang == "EN" else "Totalt"}
            out[t["sex"]] = df_in[sex_col].str.strip().map(sm)
        for canon, lbl in [(SALARY_COL, t["monthly"]), (BASIC_COL, t["basic"]), (COUNT_COL, t["headcount"])]:
            if canon in df_in.columns:
                out[lbl] = df_in[canon].map(lambda v: f"{int(v):,}" if pd.notna(v) else "–")
        st.dataframe(out, use_container_width=True, hide_index=True)


# Clean, underlined tabs (mockup) — strip the leading emoji from each label.
_notab = lambda s: re.sub(r"^\W+", "", s).strip()
tab_pct, tab_calc, tab_permit, tab_lead, tab_age, tab_reg, tab_edu, tab_stats = \
    st.tabs([_notab(x) for x in (
        t["tab_pct"], t["tab_calc"], t["tab_permit"], t["tab_lead"], t["tab_age"],
        t["tab_region"], t["tab_edu"], t["tab_stats"]
    )])

# ── Tab 1: Percentile distribution ────────────────────────────────────────────
with tab_pct:
    st.subheader(t["chart_title"])
    if agg_mode:
        st.caption(t["agg_info"].format(n=len(selected_occ_codes), grp=agg_name)
                   + t["agg_pct_extra"])
    c_yr, c_meas = st.columns([1, 2])
    with c_yr:
        available_years = sorted(df[year_col].unique(), reverse=True)
        chart_year = st.selectbox(t["chart_year"], options=available_years, index=0, key="pct_year")
    with c_meas:
        def _sort_pct_measures():
            cur = st.session_state.get("pct_measures", [])
            st.session_state["pct_measures"] = [m for m in pct_order if m in cur]
        shown_measures = st.multiselect(t["measures_shown"], options=pct_order,
                                        default=pct_order, key="pct_measures",
                                        on_change=_sort_pct_measures)
    if not shown_measures:
        shown_measures = pct_order
    # Always display in the canonical order, regardless of click/re-add order
    shown_measures = [m for m in pct_order if m in shown_measures]
    df_chart = df[df[year_col] == chart_year]

    # The average is not a percentile — plot it as a standalone marker, not on the line
    is_avg   = lambda m: "average" in m.lower() or "genomsnitt" in m.lower()
    avg_label = next((m for m in shown_measures if is_avg(m)), None)
    pct_pts   = [m for m in shown_measures if not is_avg(m)]

    fig = go.Figure()
    for i, code in enumerate(display_codes):
        row = df_chart[df_chart[occ_col].str.strip() == code]
        if row.empty:
            continue
        row   = row.iloc[0]
        name  = occ_name(code)
        color = colors[i % len(colors)]
        legend_name = name if code == AGG_CODE else f"{name} ({code})"
        # Percentile line (P10…P90)
        if pct_pts:
            fig.add_trace(go.Scatter(
                x=pct_pts, y=[row[m] for m in pct_pts], mode="lines+markers",
                name=legend_name,
                line=dict(color=color, width=2.5), marker=theme.series_marker(color),
            ))
        # Average — standalone diamond, disconnected from the percentile line
        if avg_label is not None:
            fig.add_trace(go.Scatter(
                x=[avg_label], y=[row[avg_label]], mode="markers",
                name=f"{name} – {t['measure']}: {avg_label}" if not pct_pts else None,
                showlegend=not pct_pts,
                marker=dict(size=12, symbol="diamond", color=color,
                            line=dict(width=1, color="white")),
            ))
    fig.update_layout(
        xaxis_title=t["x_pct"], yaxis_title=t["y_salary"],
        xaxis=dict(categoryorder="array", categoryarray=shown_measures),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=420, margin=dict(t=60, b=40), hovermode="x unified",
    )
    theme.style_fig(fig)
    st.plotly_chart(fig, use_container_width=True)

    # Trend (single occupation or aggregated group)
    if len(display_codes) == 1:
        st.subheader(t["trend_title"])
        tc1, tc2 = st.columns([2, 3])
        with tc1:
            trend_measure = st.selectbox(t["measure"], pct_order, index=2, key="trend_measure")
        with tc2:
            view = st.radio(t["trend_view"],
                            [t["trend_nominal"], t["trend_growth"], t["trend_real"]],
                            horizontal=True, key="trend_view",
                            help=t["trend_view_help"])
        code     = display_codes[0]
        df_trend = df[df[occ_col].str.strip() == code].sort_values(year_col)
        pairs = [(str(y).strip(), float(s))
                 for y, s in zip(df_trend[year_col],
                                 pd.to_numeric(df_trend[trend_measure], errors="coerce"))
                 if pd.notna(s)]
        if not pairs:
            st.info(t["no_data"])
        else:
            base_y, base_s = pairs[0]
            cpi = fetch_cpi_annual(int(pairs[-1][0]))
            cpi_base = cpi.get(base_y)
            years = [y for y, _ in pairs]
            fig2 = go.Figure()
            yaxis = t["y_salary"]

            if view == t["trend_growth"] and cpi_base:
                fig2.add_trace(go.Scatter(
                    x=years, y=[(s / base_s - 1) * 100 for _, s in pairs],
                    mode="lines+markers", name=t["trend_sal_growth"],
                    line=dict(color=theme.ACCENT, width=2.5),
                    marker=theme.series_marker(theme.ACCENT)))
                fig2.add_trace(go.Scatter(
                    x=years, y=[(cpi[y] / cpi_base - 1) * 100 if cpi.get(y) else None
                                for y in years],
                    mode="lines+markers", name=t["trend_infl"],
                    line=dict(color=theme.MEAN, width=2, dash="dash"), marker=dict(size=6)))
                yaxis = t["trend_growth_axis"].format(base=base_y)
            elif view == t["trend_real"] and cpi_base:
                fig2.add_trace(go.Scatter(
                    x=years,
                    y=[s * cpi_base / cpi[y] if cpi.get(y) else None for y, s in pairs],
                    mode="lines+markers", name=t["trend_real"],
                    line=dict(color=theme.ACCENT, width=2.5),
                    marker=theme.series_marker(theme.ACCENT)))
                yaxis = t["trend_real_axis"].format(base=base_y)
            else:
                if view != t["trend_nominal"] and not cpi_base:
                    st.caption(t["trend_no_cpi"])
                fig2.add_trace(go.Scatter(
                    x=years, y=[s for _, s in pairs], mode="lines+markers",
                    name=trend_measure,
                    line=dict(color=theme.ACCENT, width=2.5),
                    marker=theme.series_marker(theme.ACCENT)))

            fig2.update_layout(xaxis_title=t["x_year"], yaxis_title=yaxis,
                               xaxis=dict(type="category"), height=340,
                               margin=dict(t=40, b=40),
                               legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                           xanchor="left", x=0))
            theme.style_fig(fig2)
            st.plotly_chart(fig2, use_container_width=True)

            # Summary of salary vs inflation over the shown span
            if cpi_base and len(pairs) > 1:
                last_y, last_s = pairs[-1]
                if cpi.get(last_y):
                    sal_chg = (last_s / base_s - 1) * 100
                    infl_chg = (cpi[last_y] / cpi_base - 1) * 100
                    real_chg = ((1 + sal_chg / 100) / (1 + infl_chg / 100) - 1) * 100
                    st.caption(t["trend_summary"].format(
                        base=base_y, last=last_y, sal=sal_chg, infl=infl_chg, real=real_chg))

    with st.expander(t["raw_data"]):
        display_df = df.copy()
        display_df[occ_col] = display_df[occ_col].map(
            lambda c: agg_name if isinstance(c, str) and c.strip() == AGG_CODE
            else (f"{occupations.get(c.strip(), c)}  ({c.strip()})" if isinstance(c, str) else c)
        )
        for col in measure_labels:
            display_df[col] = display_df[col].map(lambda v: f"{int(v):,}" if pd.notna(v) else "–")
        st.dataframe(display_df[key_cols + shown_measures], use_container_width=True)

    # Extractable per-year trend table: nominal, growth vs inflation, and real
    # in one table (single occupation / aggregated group only).
    if len(display_codes) == 1 and pairs:
        with st.expander(t["trend_table_title"]):
            growth_col = t["trend_col_growth"]
            infl_col   = t["trend_infl"] + " (%)"
            real_col   = t["trend_col_real"].format(base=base_y)
            rows = []
            for y, s in pairs:
                has_cpi = bool(cpi_base) and cpi.get(y) is not None
                infl = (cpi[y] / cpi_base - 1) * 100 if has_cpi else None
                real = s * cpi_base / cpi[y] if has_cpi else None
                rows.append({
                    t["x_year"]:            y,
                    t["trend_col_nominal"]: round(s),
                    growth_col:             round((s / base_s - 1) * 100, 1),
                    infl_col:               round(infl, 1) if infl is not None else None,
                    real_col:               round(real) if real is not None else None,
                })
            trend_tbl = pd.DataFrame(rows)
            st.dataframe(trend_tbl, use_container_width=True, hide_index=True)
            st.download_button(
                t["trend_download"],
                trend_tbl.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"salary_trend_{code}.csv",
                mime="text/csv",
                key="trend_csv_dl",
            )

# ── Tab: Where do I stand? (salary calculator) ────────────────────────────────
PCT_POINTS = [("P10", 10), ("P25", 25), ("Median (P50)", 50), ("P75", 75), ("P90", 90)]

with tab_calc:
    st.subheader(t["calc_title"])

    c1, c2 = st.columns(2)
    with c1:
        if len(display_codes) > 1:
            calc_code = st.selectbox(t["calc_occ"], options=list(display_codes),
                                     format_func=occ_name, key="calc_occ_sel")
        else:
            calc_code = display_codes[0]
            st.markdown(f"**{occ_name(calc_code)}**")
    with c2:
        calc_years = sorted(df[year_col].unique(), reverse=True)
        calc_year  = st.selectbox(t["calc_year"], options=calc_years, index=0, key="calc_year_sel")

    # Pull this occupation/year's percentile points from the data already fetched
    row_df = df[(df[occ_col].str.strip() == calc_code) & (df[year_col] == calc_year)]
    points = []
    if not row_df.empty:
        r = row_df.iloc[0]
        for label, lvl in PCT_POINTS:
            if label in df.columns and pd.notna(r[label]):
                points.append((lvl, float(r[label])))
    points.sort(key=lambda p: p[0])

    if len(points) < 2:
        st.info(t["calc_no_pct"])
    else:
        levs = [lvl for lvl, _ in points]
        vals = [val for _, val in points]
        default_salary = int(round(vals[len(vals) // 2]))
        salary = st.number_input(t["calc_input"], min_value=0, value=default_salary,
                                 step=500, key="calc_salary")

        sex_lbl    = {"1": t["men"], "2": t["women"],
                      "1+2": "Total" if lang == "EN" else "Totalt"}.get(query_sex, query_sex)
        sector_lbl = t["sectors"].get(query_sector, query_sector)
        st.caption(t["calc_context"].format(occ=occ_name(calc_code), sector=sector_lbl,
                                            sex=sex_lbl, year=calc_year))

        # Estimate the percentile rank by piecewise-linear interpolation
        if salary <= vals[0]:
            est, pos = levs[0], "below"
        elif salary >= vals[-1]:
            est, pos = levs[-1], "above"
        else:
            est, pos = levs[-1], "in"
            for i in range(len(points) - 1):
                v0, v1 = vals[i], vals[i + 1]
                if v0 <= salary <= v1:
                    frac = (salary - v0) / (v1 - v0) if v1 > v0 else 0.0
                    est  = levs[i] + frac * (levs[i + 1] - levs[i])
                    break

        m1, m2 = st.columns([1, 2])
        with m1:
            st.metric(t["calc_rank"], f"P{est:.0f}")
        with m2:
            if pos == "below":
                st.warning(t["calc_below"])
            elif pos == "above":
                st.success(t["calc_above"])
            else:
                st.info(t["calc_more_than"].format(p=f"{est:.0f}", top=f"{100 - est:.0f}"))

        # Percentile curve with the user's position marked
        fig_c = go.Figure()
        fig_c.add_trace(go.Scatter(
            x=levs, y=vals, mode="lines+markers", name=t["calc_curve"],
            line=dict(color="#4e79a7", width=2), marker=dict(size=8),
        ))
        fig_c.add_hline(y=salary, line=dict(color="#e15759", width=1, dash="dot"))
        fig_c.add_trace(go.Scatter(
            x=[est], y=[salary], mode="markers+text", text=[t["calc_you"]],
            textposition="top center", textfont=dict(color="#e15759"),
            marker=dict(size=16, symbol="star", color="#e15759",
                        line=dict(width=1, color="white")),
            showlegend=False,
        ))
        fig_c.update_layout(
            xaxis_title=t["x_pct"], yaxis_title=t["y_salary"],
            xaxis=dict(tickvals=levs, ticktext=[f"P{l:.0f}" for l in levs],
                       range=[5, 95]),
            height=380, margin=dict(t=40, b=40), showlegend=False,
        )
        theme.style_fig(fig_c)
        st.plotly_chart(fig_c, use_container_width=True)

# ── Tab: Work permit check ────────────────────────────────────────────────────
with tab_permit:
    st.subheader(t["wp_title"])
    today_iso = datetime.now().strftime("%Y-%m-%d")
    st.info(t["wp_banner"].format(as_of=WP_RULES_AS_OF, today=today_iso))

    # Live cross-check of the manually-set median against SCB
    ly, live_med = fetch_live_median(lang)
    if live_med:
        if live_med != WP_MEDIAN_SALARY:
            st.warning(t["wp_median_warn"].format(cfg=WP_MEDIAN_SALARY, year=ly, live=live_med))
        else:
            st.caption(t["wp_median_ok"].format(cfg=WP_MEDIAN_SALARY, year=ly))

    permit_codes = [c for c in selected_occ_codes if c != "0000"]
    if not permit_codes:
        st.info(t["wp_no_occ"])
    else:
        c1, c2 = st.columns(2)
        with c1:
            pcode = st.selectbox(t["wp_occ"], permit_codes,
                                 format_func=lambda c: f"{c} – {occupations.get(c, c)}",
                                 key="wp_occ")
            wp_salary = st.number_input(t["wp_salary"], min_value=0, value=35000,
                                        step=500, key="wp_salary")
            ptype = st.radio(t["wp_type"], [t["wp_type_regular"], t["wp_type_blue"]],
                             key="wp_type", horizontal=True)
            permit_type = "blue" if ptype == t["wp_type_blue"] else "regular"
        with c2:
            sector_codes_list = list(t["sectors"].keys())
            default_sec_idx = sector_codes_list.index(query_sector) \
                if query_sector in sector_codes_list else 0
            # Key scoped to the searched sector so it re-defaults when that changes,
            # while still letting the user override within a given search.
            wp_sector_label = st.selectbox(t["wp_sector"], sector_labels,
                                           index=default_sec_idx,
                                           key=f"wp_sector_{query_sector}")
            wp_sector_code  = sector_codes_list[sector_labels.index(wp_sector_label)]
            is_transition = st.checkbox(t["wp_transition"], key="wp_transition")
            app_date = st.date_input(t["wp_app_date"], key="wp_app_date")
        app_date_iso = app_date.strftime("%Y-%m-%d")

        st.divider()

        # 1 — Eligibility ------------------------------------------------------
        st.markdown(f"**{t['wp_h_elig']}**")
        hard_block = pcode in WP_BANNED_FULL
        if hard_block:
            st.error(t["wp_banned_full"].format(code=pcode))
        elif pcode in WP_BANNED_PARTIAL:
            st.warning(t["wp_banned_partial"].format(code=pcode))
        else:
            st.success(t["wp_elig_ok"].format(code=pcode))

        # 2 — Salary floor -----------------------------------------------------
        st.markdown(f"**{t['wp_h_floor']}**")
        floor, basis = wp_floor(pcode, permit_type, is_transition, app_date_iso)
        basis_txt = t[f"wp_basis_{basis}"]
        if wp_salary >= floor:
            st.success(t["wp_floor_pass"].format(sal=wp_salary, floor=floor,
                       basis=basis_txt, margin=wp_salary - floor))
        else:
            st.error(t["wp_floor_fail"].format(sal=wp_salary, floor=floor,
                     basis=basis_txt, gap=floor - wp_salary))

        # 3 — Market / customary pay ------------------------------------------
        st.markdown(f"**{t['wp_h_market']}**")
        ctx = pd.DataFrame([{
            t["occupation"]: f"{pcode} – {occupations.get(pcode, pcode)}",
            t["sector"]:     wp_sector_label,
            t["select_year"]: WP_BENCH_YEAR,
        }])
        st.dataframe(ctx, use_container_width=True, hide_index=True)
        with st.spinner(t["fetching_data"]):
            mdf = fetch_percentile_data(wp_sector_code, (pcode,), "1+2",
                                        (str(WP_BENCH_YEAR),), lang,
                                        measure_keys, measure_labels)
        pts = []
        if not mdf.empty:
            mrow = mdf.iloc[0]
            for label, lvl in [("P10", 10), ("P25", 25), ("Median (P50)", 50),
                               ("P75", 75), ("P90", 90)]:
                if label in mdf.columns and pd.notna(mrow.get(label)):
                    pts.append((lvl, float(mrow[label])))
        pts.sort(key=lambda p: p[0])
        if len(pts) < 2:
            st.info(t["wp_market_none"])
        else:
            est, _pos = interp_percentile(wp_salary, pts)
            pv = {lvl: val for lvl, val in pts}
            st.write(t["wp_market"].format(
                sal=wp_salary, pct=est, sector=wp_sector_label, year=WP_BENCH_YEAR,
                p10=int(pv.get(10, pts[0][1])), p50=int(pv.get(50, pts[len(pts)//2][1])),
                p90=int(pv.get(90, pts[-1][1]))))
            if 50 in pv and wp_salary < pv[50]:
                st.warning(t["wp_market_below"])
            else:
                st.success(t["wp_market_ok"])

            # Reference lines: % of THIS occupation's median (selected sector) —
            # a feel for the salary level within the occupation, not the legal floor.
            occ_median = pv.get(50) or pts[len(pts) // 2][1]
            v90 = round(occ_median * WP_PCT_GENERAL)
            v80 = round(occ_median * WP_PCT_TRANSITION)
            v75 = round(occ_median * WP_PCT_EXEMPT)
            st.caption(t["wp_ref_lines"].format(median=int(occ_median)))
            rc1, rc2, rc3 = st.columns(3)
            show90 = rc1.checkbox(f"90% ({v90:,})", key="wp_ref90")
            show80 = rc2.checkbox(f"80% ({v80:,})", key="wp_ref80")
            show75 = rc3.checkbox(f"75% ({v75:,})", key="wp_ref75")

            # Plot: percentile curve + proposed salary (★) + salary floor line
            levs = [lv for lv, _ in pts]
            vals = [v for _, v in pts]
            fig_wp = go.Figure()
            fig_wp.add_trace(go.Scatter(
                x=levs, y=vals, mode="lines+markers",
                line=dict(color="#4e79a7", width=2), marker=dict(size=8)))
            fig_wp.add_hline(y=floor, line=dict(color="#59a14f", width=1, dash="dash"),
                             annotation_text=f"{t['wp_plot_floor']} {int(floor):,}",
                             annotation_position="bottom left")
            for show, val, col, lbl in [(show90, v90, "#b07aa1", "90%"),
                                        (show80, v80, "#f28e2b", "80%"),
                                        (show75, v75, "#76b7b2", "75%")]:
                if show:
                    fig_wp.add_hline(y=val, line=dict(color=col, width=1, dash="dot"),
                                     annotation_text=f"{lbl} {int(val):,}",
                                     annotation_position="top left")
            fig_wp.add_hline(y=wp_salary, line=dict(color="#e15759", width=1, dash="dot"))
            fig_wp.add_trace(go.Scatter(
                x=[est], y=[wp_salary], mode="markers+text",
                text=[f"{t['wp_plot_proposed']} ({int(wp_salary):,})"],
                textposition="top center", textfont=dict(color="#e15759"),
                marker=dict(size=16, symbol="star", color="#e15759",
                            line=dict(width=1, color="white"))))
            fig_wp.update_layout(
                xaxis_title=t["x_pct"], yaxis_title=t["y_salary"],
                xaxis=dict(tickvals=levs, ticktext=[f"P{lv}" for lv in levs], range=[5, 95]),
                height=360, margin=dict(t=30, b=40), showlegend=False)
            theme.style_fig(fig_wp)
            st.plotly_chart(fig_wp, use_container_width=True)
            st.caption(t["wp_market_note"])

        # 4 — Documentation & process -----------------------------------------
        st.markdown(f"**{t['wp_h_docs']}**")
        st.caption(t["wp_docs_note"])
        for item in t["wp_docs_items"]:
            st.checkbox(item, key=f"wp_doc_{item[:20]}")

        with st.expander(t["wp_rules_expander"]):
            st.markdown(
                f"- Median: **SEK {WP_MEDIAN_SALARY:,}** (as of {WP_RULES_AS_OF})\n"
                f"- General 90% → **SEK {round(WP_MEDIAN_SALARY*WP_PCT_GENERAL):,}**\n"
                f"- Transition 80% → **SEK {round(WP_MEDIAN_SALARY*WP_PCT_TRANSITION):,}**\n"
                f"- Exempt 75% → **SEK {round(WP_MEDIAN_SALARY*WP_PCT_EXEMPT):,}**\n"
                f"- EU Blue Card → **SEK {WP_BLUE_CARD_FLOOR:,}**\n"
                f"- Transition ends: **{WP_TRANSITION_END}**\n"
                f"- Banned: 5343 (full), 9210 (berry pickers, partial)"
            )
            st.markdown(f"**{t['wp_exempt_header']}**")
            exempt_tbl = pd.DataFrame(
                [{"SSYK": c, t["occupation"]: occupations.get(c, "—")}
                 for c in sorted(WP_EXEMPT_SSYK)])
            st.dataframe(exempt_tbl, use_container_width=True, hide_index=True)

        # Salary distribution data table for the selected occupation
        with st.expander(t["wp_data_expander"]):
            ddf = fetch_percentile_data(wp_sector_code, (pcode,), "1+2",
                                        tuple(new_gen_years()), lang,
                                        measure_keys, measure_labels)
            if ddf.empty:
                st.info(t["wp_market_none"])
            else:
                dcols = [c for c in ddf.columns if c not in measure_labels]
                yrc = dcols[-1]
                ddf = ddf[ddf[yrc] == ddf[yrc].max()]  # latest year only
                order = [m for m in ["P10", "P25", "Median (P50)", "P75", "P90"]
                         if m in ddf.columns]
                avg = next((m for m in measure_labels
                            if "average" in m.lower() or "genomsnitt" in m.lower()), None)
                show_cols = order + ([avg] if avg else [])
                out = pd.DataFrame()
                out[t["select_year"]] = ddf[yrc]
                for m in show_cols:
                    out[m] = ddf[m].map(lambda v: f"{int(v):,}" if pd.notna(v) else "–")
                st.dataframe(out, use_container_width=True, hide_index=True)

# ── Tab: Leaderboard ──────────────────────────────────────────────────────────
with tab_lead:
    st.subheader(t["lead_title"])
    sector_lbl   = t["sectors"].get(query_sector, query_sector)
    scope_prefix = q.get("scope_prefix", "")
    scope_label  = q.get("scope_label", "")
    scope_disp   = scope_label if scope_prefix else t["lead_all_occ"]
    st.caption(t["lead_intro"].format(scope=scope_disp, sector=sector_lbl))

    with st.spinner(t["fetching_data"]):
        dfm = fetch_market_salaries(query_sector, selected_years, lang)

    if dfm.empty:
        st.warning(t["no_data"])
    else:
        m_occ, m_sex, m_yr = dfm.columns[1], dfm.columns[2], dfm.columns[3]
        dfm = dfm[dfm[m_occ].str.strip() != "0000"].copy()
        dfm["code"] = dfm[m_occ].str.strip()
        dfm["sx"]   = dfm[m_sex].str.strip()
        # Limit the ranking to the major/sub-group the user drilled into
        if scope_prefix:
            dfm = dfm[dfm["code"].str.startswith(scope_prefix)]
        lead_years  = sorted(dfm[m_yr].unique(), reverse=True)

        metric_opts = {
            "median": t["lead_m_median"], "avg": t["lead_m_avg"],
            "gap":    t["lead_m_gap"],    "growth": t["lead_m_growth"],
        }
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            metric = st.selectbox(t["lead_metric"], list(metric_opts),
                                  format_func=lambda k: metric_opts[k], key="lead_metric")
        # Build the ranking frame -> columns: code, name, val
        ranked, axis_title, value_fmt, valid = None, t["y_salary"], None, True

        if metric in ("median", "avg"):
            with c2:
                ly = st.selectbox(t["lead_year"], lead_years, index=0, key="lead_year_ma")
            with c3:
                asc = st.selectbox(t["lead_order"], [t["lead_high"], t["lead_low"]],
                                   key="lead_ord_ma") == t["lead_low"]
            sub = dfm[(dfm[m_yr] == ly) & (dfm["sx"] == query_sex)].dropna(subset=[metric])
            ranked = sub[["code", metric]].rename(columns={metric: "val"})
            ranked = ranked.sort_values("val", ascending=asc)
            value_fmt = lambda v: f"{int(round(v)):,} SEK"

        elif metric == "gap":
            with c2:
                ly = st.selectbox(t["lead_year"], lead_years, index=0, key="lead_year_gap")
            with c3:
                asc = st.selectbox(t["lead_order"], [t["lead_gap_big"], t["lead_gap_small"]],
                                   key="lead_ord_gap") == t["lead_gap_big"]
            men   = dfm[(dfm[m_yr] == ly) & (dfm["sx"] == "1")][["code", "median"]]
            women = dfm[(dfm[m_yr] == ly) & (dfm["sx"] == "2")][["code", "median"]]
            g = men.merge(women, on="code", suffixes=("_m", "_w")).dropna()
            g["val"] = (g["median_w"] / g["median_m"] * 100).round(1)
            ranked = g[["code", "val"]].sort_values("val", ascending=asc)
            axis_title = t["lead_gap_axis"]
            value_fmt = lambda v: f"{v:.1f}%"

        else:  # growth
            with c2:
                yf = st.selectbox(t["lead_from"], lead_years,
                                  index=len(lead_years) - 1, key="lead_from_y")
            with c3:
                yt = st.selectbox(t["lead_to"], lead_years, index=0, key="lead_to_y")
            order_fast = st.selectbox(t["lead_order"],
                                      [t["lead_grow_fast"], t["lead_grow_slow"]],
                                      key="lead_ord_grow") == t["lead_grow_slow"]
            if yf == yt:
                st.info(t["lead_need_two"]); valid = False
            else:
                base = dfm[(dfm[m_yr] == yf) & (dfm["sx"] == query_sex)][["code", "median"]]
                comp = dfm[(dfm[m_yr] == yt) & (dfm["sx"] == query_sex)][["code", "median"]]
                gr = base.merge(comp, on="code", suffixes=("_0", "_1")).dropna()
                gr = gr[gr["median_0"] > 0]
                gr["val"] = ((gr["median_1"] / gr["median_0"] - 1) * 100).round(1)
                ranked = gr[["code", "val"]].sort_values("val", ascending=order_fast)
                axis_title = t["lead_growth_axis"]
                value_fmt = lambda v: f"{v:+.1f}%"

        if valid and ranked is not None and not ranked.empty:
            ranked = ranked.reset_index(drop=True)
            ranked.insert(0, "rank", ranked.index + 1)
            ranked["name"] = ranked["code"].map(lambda c: occupations.get(c, c))

            sex_lbl = {"1": t["men"], "2": t["women"],
                       "1+2": "Total" if lang == "EN" else "Totalt"}.get(query_sex, query_sex)
            if metric != "gap":
                st.caption(t["lead_sex_note"].format(sex=sex_lbl))

            topn = st.slider(t["lead_topn"], 5, 40, 15, key="lead_topn")
            show = ranked.head(topn).iloc[::-1]  # reversed so #1 is on top of the bar chart
            user_codes = set(selected_occ_codes)
            bar_colors = [theme.ACCENT if c in user_codes else theme.SOFT for c in show["code"]]

            fig_l = go.Figure(go.Bar(
                x=show["val"], y=show["name"], orientation="h",
                marker_color=bar_colors,
                text=[value_fmt(v) for v in show["val"]], textposition="auto",
            ))
            fig_l.update_layout(
                xaxis_title=axis_title, yaxis_title="",
                height=max(360, 26 * len(show) + 80),
                margin=dict(t=30, b=40, l=260),
            )
            theme.style_fig(fig_l, horizontal=True)
            st.plotly_chart(fig_l, use_container_width=True)

            # Where do the user's searched occupations land?
            if not agg_mode:
                for c in selected_occ_codes:
                    if c == "0000":
                        continue
                    r = ranked[ranked["code"] == c]
                    if not r.empty:
                        row = r.iloc[0]
                        st.markdown(t["lead_your"].format(
                            name=occupations.get(c, c), rank=int(row["rank"]),
                            total=len(ranked), val=value_fmt(row["val"])))

            with st.expander(t["lead_table"]):
                tbl = ranked.copy()
                tbl[t["lead_value"]] = tbl["val"].map(value_fmt)
                tbl[t["lead_occ"]]   = tbl["name"] + "  (" + tbl["code"] + ")"
                tbl = tbl.rename(columns={"rank": t["lead_rank"]})
                st.dataframe(tbl[[t["lead_rank"], t["lead_occ"], t["lead_value"]]],
                             use_container_width=True, hide_index=True)

# ── Tab 2: By age ──────────────────────────────────────────────────────────────
with tab_age:
    st.subheader(t["age_title"])
    age_year = st.selectbox(t["select_year"], options=year_opts, index=0, key="age_year")
    with st.spinner(t["fetching_data"]):
        df_age = fetch_age_data(query_sector, selected_occ_codes, age_year, lang)

    st.caption(t["no_pct_note"])
    c_m, c_r = st.columns([2, 1])
    with c_m:
        sal_col, _ = measure_toggle("age_measure")
    with c_r:
        show_ratio = st.toggle(t["show_ratio"], key="age_ratio")

    if df_age.empty:
        st.warning(t["no_data"])
    else:
        age_col  = [c for c in df_age.columns if c.lower() in ("age", "ålder", "alder")][0]
        sex_col  = [c for c in df_age.columns if c.lower() in ("sex", "kön", "kon")][0]
        occ_col2 = df_age.columns[1]
        if agg_mode:
            yr_c = [c for c in df_age.columns if c.lower() in ("year", "år", "tid")][0]
            df_age = collapse_df(
                df_age, occ_col2, [c for c in (SALARY_COL, BASIC_COL) if c in df_age.columns],
                weight_col=COUNT_COL, count_col=COUNT_COL,
                group_cols=[df_age.columns[0], sex_col, age_col, yr_c])
            st.caption(t["agg_info"].format(n=len(selected_occ_codes), grp=agg_name))

        multi_age = len(display_codes) > 1
        fig_age = go.Figure()
        for code in display_codes:
            sub = df_age[df_age[occ_col2].str.strip() == code]
            oname = occ_name(code)
            vals = {}
            for sex_code_val, sex_label, color in [("1", t["men"], theme.SEX_MEN),
                                                    ("2", t["women"], theme.SEX_WOMEN)]:
                rows = sub[sub[sex_col].str.strip() == sex_code_val].copy()
                rows = rows[rows[age_col].isin(AGE_GROUPS)].set_index(age_col).reindex(AGE_GROUPS)
                vals[sex_code_val] = rows[sal_col]
                fig_age.add_trace(go.Bar(
                    name=f"{sex_label}" + (f" – {oname}" if multi_age else ""),
                    x=AGE_GROUPS,
                    y=rows[sal_col].tolist(),
                    marker_color=color,
                ))
            # Women's salary as % of men's, on a secondary axis
            if show_ratio and "1" in vals and "2" in vals:
                ratio = (vals["2"] / vals["1"] * 100).round(1)
                fig_age.add_trace(go.Scatter(
                    name=t["ratio_axis"] + (f" – {oname}" if multi_age else ""),
                    x=AGE_GROUPS, y=ratio.tolist(),
                    mode="lines+markers+text",
                    text=[f"{v:.0f}%" if pd.notna(v) else "" for v in ratio],
                    textposition="top center",
                    line=dict(color="#e15759", width=2, dash="dot"),
                    marker=dict(size=7), yaxis="y2",
                ))

        layout = dict(
            barmode="group",
            xaxis_title="Age group" if lang == "EN" else "Åldersgrupp",
            yaxis_title=t["y_salary"],
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            height=420, margin=dict(t=60, b=40),
        )
        if show_ratio:
            layout["yaxis2"] = dict(title=t["ratio_axis"], overlaying="y", side="right",
                                    range=[0, 110], showgrid=False)
        fig_age.update_layout(**layout)
        theme.style_fig(fig_age)
        st.plotly_chart(fig_age, use_container_width=True)
        show_breakdown_raw(df_age, age_col,
                           "Age group" if lang == "EN" else "Åldersgrupp",
                           sex_col=sex_col)

# ── Tab 3: By region ───────────────────────────────────────────────────────────
with tab_reg:
    st.subheader(t["region_title"])
    reg_year = st.selectbox(t["select_year"], options=year_opts, index=0, key="reg_year")
    with st.spinner(t["fetching_data"]):
        df_reg = fetch_region_data(query_sector, selected_occ_codes, query_sex, reg_year, lang)

    st.caption(t["no_pct_note"])
    c_m, c_r = st.columns([2, 1])
    with c_m:
        sal_col, _ = measure_toggle("reg_measure")
    with c_r:
        show_region_pct = st.toggle(t["show_region_pct"], key="reg_pct")

    if df_reg.empty:
        st.warning(t["no_data"])
    else:
        reg_col    = df_reg.columns[0]
        occ_col3   = df_reg.columns[2]
        region_map = REGIONS[lang]
        if agg_mode:
            sex_c = [c for c in df_reg.columns if c.lower() in ("sex", "kön", "kon")][0]
            yr_c  = [c for c in df_reg.columns if c.lower() in ("year", "år", "tid")][0]
            df_reg = collapse_df(
                df_reg, occ_col3, [c for c in (SALARY_COL, BASIC_COL) if c in df_reg.columns],
                weight_col=COUNT_COL, count_col=COUNT_COL,
                group_cols=[reg_col, df_reg.columns[1], sex_c, yr_c])
            st.caption(t["agg_info"].format(n=len(selected_occ_codes), grp=agg_name))

        TOTAL_COLOR = theme.MEAN  # distinct colour for the national total (code "SE")
        multi = len(display_codes) > 1

        fig_reg = go.Figure()
        for i, code in enumerate(display_codes):
            sub = df_reg[df_reg[occ_col3].str.strip() == code].copy()
            sub["reg_code"]    = sub[reg_col].str.strip()
            sub["region_name"] = sub["reg_code"].map(region_map)
            sub = sub.dropna(subset=[sal_col, "region_name"])
            sub = sub.sort_values(sal_col)
            oname = occ_name(code)
            base = colors[i % len(colors)]
            # Per-bar colours: highlight the "SE" national total
            bar_colors = [TOTAL_COLOR if rc == "SE" else base for rc in sub["reg_code"]]

            # Optional % of Sweden total, shown as bar labels
            text, textpos = None, "auto"
            if show_region_pct:
                se_rows = sub.loc[sub["reg_code"] == "SE", sal_col]
                se_val  = se_rows.iloc[0] if not se_rows.empty else None
                if se_val:
                    text = [f"{v / se_val * 100:.0f}%" if pd.notna(v) else "" for v in sub[sal_col]]
                    textpos = "outside"

            fig_reg.add_trace(go.Bar(
                name=f"{oname} ({code})" if multi else "",
                x=sub[sal_col],
                y=sub["region_name"],
                orientation="h",
                marker_color=(base if multi else bar_colors),
                text=text, textposition=textpos,
            ))

        fig_reg.update_layout(
            barmode="group",
            xaxis_title=t["y_salary"],
            yaxis_title="Region",
            height=420, margin=dict(t=40, b=40, l=180),
            showlegend=len(selected_occ_codes) > 1,
        )
        theme.style_fig(fig_reg, horizontal=True)
        st.plotly_chart(fig_reg, use_container_width=True)
        show_breakdown_raw(df_reg, reg_col, "Region", dim_map=region_map)

# ── Tab 4: By education ────────────────────────────────────────────────────────
with tab_edu:
    st.subheader(t["edu_title"])
    edu_year = st.selectbox(t["select_year"], options=year_opts, index=0, key="edu_year")
    with st.spinner(t["fetching_data"]):
        df_edu = fetch_edu_data(query_sector, selected_occ_codes, edu_year, lang)

    st.caption(t["no_pct_note"])
    c_m, c_r = st.columns([2, 1])
    with c_m:
        sal_col, _ = measure_toggle("edu_measure")
    with c_r:
        show_edu_ratio = st.toggle(t["show_ratio"], key="edu_ratio")

    if df_edu.empty:
        st.warning(t["no_data"])
    else:
        edu_col  = [c for c in df_edu.columns if "utbildn" in c.lower() or "educ" in c.lower()][0]
        sex_col2 = [c for c in df_edu.columns if c.lower() in ("sex", "kön", "kon")][0]
        occ_col4 = df_edu.columns[1]
        edu_map  = EDU_LEVELS[lang]
        edu_order = [v for k, v in edu_map.items() if k != "TOTALT"]
        if agg_mode:
            yr_c = [c for c in df_edu.columns if c.lower() in ("year", "år", "tid")][0]
            df_edu = collapse_df(
                df_edu, occ_col4, [c for c in (SALARY_COL, BASIC_COL) if c in df_edu.columns],
                weight_col=COUNT_COL, count_col=COUNT_COL,
                group_cols=[df_edu.columns[0], sex_col2, edu_col, yr_c])
            st.caption(t["agg_info"].format(n=len(selected_occ_codes), grp=agg_name))

        multi_edu = len(display_codes) > 1
        fig_edu = go.Figure()
        for code in display_codes:
            sub = df_edu[df_edu[occ_col4].str.strip() == code].copy()
            vals_edu = {}
            for sex_code_val, sex_label, color in [
                ("1", t["men"],   theme.SEX_MEN),
                ("2", t["women"], theme.SEX_WOMEN),
            ]:
                rows = sub[sub[sex_col2].str.strip() == sex_code_val].copy()
                rows["edu_name"] = rows[edu_col].str.strip().map(edu_map)
                rows = rows.dropna(subset=[sal_col, "edu_name"])
                rows = rows[rows["edu_name"] != edu_map.get("TOTALT")]
                rows = rows.set_index("edu_name").reindex(edu_order)
                vals_edu[sex_code_val] = rows[sal_col]
                oname = occ_name(code)
                fig_edu.add_trace(go.Bar(
                    name=f"{sex_label}" + (f" – {oname}" if multi_edu else ""),
                    x=rows[sal_col].tolist(),
                    y=edu_order,
                    orientation="h",
                    marker_color=color,
                ))
            # Women's salary as % of men's, on a secondary axis
            if show_edu_ratio and "1" in vals_edu and "2" in vals_edu:
                ratio = (vals_edu["2"] / vals_edu["1"] * 100).round(1)
                fig_edu.add_trace(go.Scatter(
                    name=t["ratio_axis"] + (f" – {occ_name(code)}" if multi_edu else ""),
                    x=ratio.tolist(),
                    y=edu_order,
                    mode="markers+text",
                    text=[f"{v:.0f}%" if pd.notna(v) else "" for v in ratio],
                    textposition="middle right",
                    marker=dict(size=9, symbol="diamond", color="#e15759"),
                    xaxis="x2",
                ))

        layout_edu = dict(
            barmode="group",
            xaxis_title=t["y_salary"],
            yaxis_title="Education level" if lang == "EN" else "Utbildningsnivå",
            yaxis=dict(categoryorder="array", categoryarray=edu_order),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            height=480, margin=dict(t=60, b=40, l=220),
        )
        if show_edu_ratio:
            layout_edu["xaxis2"] = dict(title=t["ratio_axis"], overlaying="x", side="top",
                                        range=[0, 110], showgrid=False)
        fig_edu.update_layout(**layout_edu)
        theme.style_fig(fig_edu, horizontal=True)
        st.plotly_chart(fig_edu, use_container_width=True)
        show_breakdown_raw(df_edu, edu_col,
                           "Education level" if lang == "EN" else "Utbildningsnivå",
                           dim_map=edu_map, sex_col=sex_col2)

# ── Tab 5: Basic statistics ────────────────────────────────────────────────────
with tab_stats:
    st.subheader(t["stats_title"])
    stats_year = st.selectbox(t["select_year"], options=year_opts, index=0, key="stats_year")
    with st.spinner(t["fetching_data"]):
        df_stats = fetch_stats_data(query_sector, selected_occ_codes, stats_year, lang)

    if df_stats.empty or COUNT_COL not in df_stats.columns:
        st.warning(t["no_data"])
    else:
        sex_col_s = [c for c in df_stats.columns if c.lower() in ("sex", "kön", "kon")][0]
        occ_col_s = df_stats.columns[2]

        def _count(d, sx):
            r = d.loc[d[sex_col_s].str.strip() == sx, COUNT_COL]
            return int(r.iloc[0]) if not r.empty and pd.notna(r.iloc[0]) else 0

        # Aggregate metric cards across all selected occupations
        total = sum(_count(df_stats[df_stats[occ_col_s].str.strip() == c], "1+2")
                    for c in selected_occ_codes)
        men   = sum(_count(df_stats[df_stats[occ_col_s].str.strip() == c], "1")
                    for c in selected_occ_codes)
        women = sum(_count(df_stats[df_stats[occ_col_s].str.strip() == c], "2")
                    for c in selected_occ_codes)

        m1, m2, m3 = st.columns(3)
        m1.metric(t["stat_total"], f"{total:,}")
        m2.metric(t["men"],   f"{men:,}",   f"{men/total*100:.0f}%" if total else None)
        m3.metric(t["women"], f"{women:,}", f"{women/total*100:.0f}%" if total else None)

        st.caption(t["stats_note"])

        # Per-occupation table
        st.markdown(f"**{t['per_occ']}**")
        rows = []
        for c in selected_occ_codes:
            d = df_stats[df_stats[occ_col_s].str.strip() == c]
            rows.append({
                t["occupation"]:  f"{occupations.get(c, c)} ({c})",
                t["men"]:         f"{_count(d, '1'):,}",
                t["women"]:       f"{_count(d, '2'):,}",
                t["stat_total"]:  f"{_count(d, '1+2'):,}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Source comparison: same selection from a different table
        with st.expander(t["src_compare"]):
            df_edu_c = fetch_edu_total_count(query_sector, selected_occ_codes, stats_year, lang)
            edu_total = 0
            if not df_edu_c.empty and COUNT_COL in df_edu_c.columns:
                edu_total = int(pd.to_numeric(df_edu_c[COUNT_COL], errors="coerce").fillna(0).sum())
            comp = pd.DataFrame({
                "": [t["src_region"], t["src_edu"]],
                t["stat_total"]: [f"{total:,}", f"{edu_total:,}"],
            })
            st.dataframe(comp, use_container_width=True, hide_index=True)

st.caption(t["source"])
