import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import json
import os
from datetime import datetime

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
        "title": "SCB Salary Explorer",
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
        "select_prompt": "Select at least one occupation in the sidebar to get started.",
        "no_data": "No data returned for this combination. Try different filters.",
        "chart_title": "Salary distribution by percentile",
        "chart_year": "Chart year",
        "trend_title": "Salary trend over time",
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
        "tab_age": "👤 By age",
        "tab_region": "🗺️ By region",
        "tab_edu": "🎓 By education",
        "tab_stats": "🔢 Basic statistics",
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
        "title": "SCB Lönestatistik",
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
        "select_prompt": "Välj minst ett yrke i sidofältet för att komma igång.",
        "no_data": "Inga data returnerades. Prova andra filter.",
        "chart_title": "Lönespridning per percentil",
        "chart_year": "Visningsår",
        "trend_title": "Löneutveckling över tid",
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
        "tab_age": "👤 Efter ålder",
        "tab_region": "🗺️ Efter region",
        "tab_edu": "🎓 Efter utbildning",
        "tab_stats": "🔢 Grundstatistik",
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
    ("LoneSpridSektYrk4AN",  2023, 2024,
     ["000007CD", "000007CE", "000007CF", "000007CG", "000007CH", "000007CI"]),
]
# Age tables
AGE_TABLES = [
    ("LonYrkeAlder4A",  2014, 2022),
    ("LonYrkeAlder4AN", 2023, 2024),
]
# Region tables
REG_TABLES = [
    ("LonYrkeRegion4A",  2014, 2022),
    ("LonYrkeRegion4AN", 2023, 2024),
]
# Education tables
EDU_TABLES = [
    ("LonYrkeUtbildning4A",  2014, 2022),
    ("LonYrkeUtbildning4AN", 2023, 2024),
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

st.set_page_config(page_title="SCB Salary Explorer", page_icon="📊", layout="wide")

with st.sidebar:
    lang = st.radio("🌐 Language / Språk", ["EN", "SV"],
                    format_func=lambda k: {"EN": "English", "SV": "Svenska"}[k],
                    horizontal=True)
    t = T[lang]

    sector_labels = list(t["sectors"].values())
    sector_code   = list(t["sectors"].keys())[
        sector_labels.index(st.selectbox(t["sector"], sector_labels, key="sector_sel"))
    ]

    sex_labels = list(t["sex_options"].values())
    sex_code   = list(t["sex_options"].keys())[
        sex_labels.index(st.radio(t["sex"], sex_labels, horizontal=True, key="sex_sel"))
    ]

    all_years = [str(y) for y in range(2014, 2025)]
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
        # Search globally across ALL occupations (ignore group restriction)
        s = search.strip().lower()
        pool = {k: v for k, v in occupations.items()
                if k != "0000" and (s in v.lower() or s in k.lower())}

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

    cache_ts = st.session_state.get("cache_ts", "")
    if st.button(f"↻ Refresh SCB  ·  📦 {cache_ts}", use_container_width=True):
        with st.spinner("Fetching from SCB API…"):
            ts = refresh_cache()
        st.success(f"Updated {ts}")
        st.rerun()

    # Commit query to session_state only when Search is clicked
    if search_clicked:
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
        st.session_state["query"] = {
            "sector":    sector_code,
            "codes":     codes,
            "sex":       sex_code,
            "aggregate": aggregate,
            "agg_name":  agg_name,
        }

    selected_occ_codes = st.session_state.get("query", {}).get("codes", ())

# ── Main ───────────────────────────────────────────────────────────────────────

st.title(f"📊 {t['title']}")
st.caption(t["caption"])

if not selected_occ_codes:
    st.info(t["select_prompt"])
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

colors = ["#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1","#ff9da7"]

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


tab_pct, tab_calc, tab_age, tab_reg, tab_edu, tab_stats = st.tabs([
    t["tab_pct"], t["tab_calc"], t["tab_age"], t["tab_region"], t["tab_edu"], t["tab_stats"]
])

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
                line=dict(color=color, width=2), marker=dict(size=8),
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
    st.plotly_chart(fig, use_container_width=True)

    # Trend (single occupation or aggregated group)
    if len(display_codes) == 1:
        st.subheader(t["trend_title"])
        trend_measure = st.selectbox(t["measure"], pct_order, index=2)
        code     = display_codes[0]
        df_trend = df[df[occ_col].str.strip() == code].sort_values(year_col)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_trend[year_col], y=df_trend[trend_measure],
            mode="lines+markers", name=trend_measure,
            line=dict(color="#4e79a7", width=2), marker=dict(size=7),
        ))
        fig2.update_layout(xaxis_title=t["x_year"], yaxis_title=t["y_salary"],
                           xaxis=dict(type="category"),
                           height=320, margin=dict(t=40, b=40))
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander(t["raw_data"]):
        display_df = df.copy()
        display_df[occ_col] = display_df[occ_col].map(
            lambda c: agg_name if isinstance(c, str) and c.strip() == AGG_CODE
            else (f"{occupations.get(c.strip(), c)}  ({c.strip()})" if isinstance(c, str) else c)
        )
        for col in measure_labels:
            display_df[col] = display_df[col].map(lambda v: f"{int(v):,}" if pd.notna(v) else "–")
        st.dataframe(display_df[key_cols + shown_measures], use_container_width=True)

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
        st.plotly_chart(fig_c, use_container_width=True)

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
            for sex_code_val, sex_label, color in [("1", t["men"], "#1a3a6b"),
                                                    ("2", t["women"], "#9ba8cc")]:
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

        TOTAL_COLOR = "#e15759"  # distinct colour for the national total (code "SE")
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
                ("1", t["men"],   "#1a3a6b"),
                ("2", t["women"], "#9ba8cc"),
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
