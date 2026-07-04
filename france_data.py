"""France data layer — INSEE Melodi API fetchers (no auth required).

Everything here was verified against the live API on 2026-07-04:

DS_DERA_PRIVE_ANNUEL / DS_DERA_PUBLIC_ANNUEL
    Mean net FTE monthly salary (EUR) + FTE headcount for ~361 detailed
    PCS-ESE occupations × sex × age bands. National, latest year only.

DS_DERA_PRIVE_SERIES_LONGUES / DS_DERA_PUBLIC_SERIES_LONGUES
    Long series (1951→): means by broad PCS group (3–6, _T) × sex, and the
    wage DISTRIBUTION (CENTILE_10/25/50/75/90/95/99) — the distribution exists
    ONLY for ALL employees (PCS_ESE=_T) × sex × working-time (FT / all).
    Values in constant euros, index 100=1996, and y/y evolution.

DS_IPC_PRINC
    Consumer price index. Annual all-items index via
    FREQ=A & COICOP_2018=00 & IDX_TYPE=CPI & IND_TYPE=IX & TPH_CPI=_T.

API mechanics: plain GET with dimension=value query params; paging via &page=N
(maxResult ≤ 10000, loop until a page comes back empty); invalid dimension code
→ HTTP 400, valid-but-absent → 200 with zero observations. Fair use ~30 req/min.
"""
import json
import os

import requests
import pandas as pd
import streamlit as st

MELODI_BASE = "https://api.insee.fr/melodi/V2"
_HEADERS    = {"Accept": "application/json"}

# Dataset ids per market sector (mirrors Sweden's private/public sector split)
DERA_ANNUAL = {"private": "DS_DERA_PRIVE_ANNUEL",        "public": "DS_DERA_PUBLIC_ANNUEL"}
DERA_SERIES = {"private": "DS_DERA_PRIVE_SERIES_LONGUES", "public": "DS_DERA_PUBLIC_SERIES_LONGUES"}

# DERA_MEASURE codes
M_MEAN_SALARY = "SALAIRE_NET_EQTP_MENSUEL_MOYENNE"                # annual dataset (current €)
M_HEADCOUNT   = "EFFECTIFS_EQTP"                                  # annual dataset (FTE count)
M_CONST_EUR   = "SALAIRE_NET_EQTP_MENSUEL_MOYEN_EUROS_CONSTANTS"  # long series (constant €)

# QUANTILE codes carried by the long-series distribution, in display order.
# Private serves C10/25/50/75/90/95/99; public serves deciles C10…C90 — use
# centile_pct() and the data itself rather than assuming a fixed set.
CENTILES = ["CENTILE_10", "CENTILE_25", "CENTILE_50", "CENTILE_75",
            "CENTILE_90", "CENTILE_95", "CENTILE_99"]


def centile_pct(code: str) -> int | None:
    """'CENTILE_25' → 25; '_T'/anything else → None."""
    if isinstance(code, str) and code.startswith("CENTILE_"):
        try:
            return int(code.split("_", 1)[1])
        except ValueError:
            return None
    return None

# "Everything = total" filter for the annual detail pull. The two datasets have
# different dimension sets (private: NAF activity + establishment size; public:
# civil-servant status + legal form), hence per-sector params.
_DETAIL_TOTALS = {
    "private": {"ACTIVITY": "_T", "WKTIME": "_T", "NUMBER_EMPL": "_T", "QUANTILE": "_T"},
    "public":  {"CIVILSERVANT_STATUS": "_T", "PUBLIC_LEGAL_FORM": "_T",
                "WKTIME": "_T", "QUANTILE": "_T"},
}


def _get_observations(dataset: str, params: dict) -> list[dict]:
    """GET all observations for a Melodi dataset, following &page=N pagination.
    Raises on HTTP/network errors so st.cache_data never caches a bad result."""
    out, page = [], 1
    while True:
        q = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{MELODI_BASE}/data/{dataset}?{q}&maxResult=10000&page={page}"
        r = requests.get(url, timeout=120, headers=_HEADERS)
        r.raise_for_status()
        obs = r.json().get("observations", [])
        out.extend(obs)
        if len(obs) < 10000:
            return out
        page += 1


def _value(o: dict) -> float | None:
    """First measure value of an observation (Melodi has one measure per row)."""
    for m in o.get("measures", {}).values():
        return m.get("value")
    return None


@st.cache_data(show_spinner=False, persist="disk")
def fetch_detail_salaries(sector: str = "private") -> pd.DataFrame:
    """Mean net FTE monthly salary + FTE headcount per detailed PCS occupation.

    Returns tidy columns: pcs, sex (F/M/_T), age (band code or _T), year,
    mean_salary, headcount. National totals slice (all activities/statuses,
    all working-time, all sizes). Note: public lags private by one year."""
    obs = _get_observations(DERA_ANNUAL[sector], _DETAIL_TOTALS[sector])
    rows = {}
    for o in obs:
        d = o["dimensions"]
        key = (d["PCS_ESE"], d["SEX"], d["AGE"], d["TIME_PERIOD"])
        rec = rows.setdefault(key, {})
        if d["DERA_MEASURE"] == M_MEAN_SALARY:
            rec["mean_salary"] = _value(o)
        elif d["DERA_MEASURE"] == M_HEADCOUNT:
            rec["headcount"] = _value(o)
    df = pd.DataFrame(
        [{"pcs": k[0], "sex": k[1], "age": k[2], "year": k[3], **v}
         for k, v in rows.items()]
    )
    for col in ("mean_salary", "headcount"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False, persist="disk")
def fetch_series_longues(sector: str = "private") -> pd.DataFrame:
    """Constant-euro long series (1951→): means per broad PCS group × sex, plus
    the all-employee wage distribution (centile != _T only where pcs == '_T').

    Returns tidy columns: year, pcs (_T/3/4/5/6), sex, wktime (_T/FT),
    centile (_T or CENTILE_xx), salary_const_eur.
    (Column is named 'centile', not 'quantile', because df.quantile is a
    pandas method and attribute access would silently shadow the column.)"""
    obs = _get_observations(DERA_SERIES[sector], {"DERA_MEASURE": M_CONST_EUR})
    # .get defaults: the PUBLIC series has no PCS_ESE dimension at all, and its
    # distribution uses deciles CENTILE_10…90 (vs private C10/25/50/75/90/95/99).
    df = pd.DataFrame([{
        "year":     o["dimensions"]["TIME_PERIOD"],
        "pcs":      o["dimensions"].get("PCS_ESE", "_T"),
        "sex":      o["dimensions"].get("SEX", "_T"),
        "wktime":   o["dimensions"].get("WKTIME", "_T"),
        "centile":  o["dimensions"].get("QUANTILE", "_T"),
        "salary_const_eur": _value(o),
    } for o in obs])
    df["salary_const_eur"] = pd.to_numeric(df["salary_const_eur"], errors="coerce")
    return df.sort_values("year", ignore_index=True)


@st.cache_data(show_spinner=False, persist="disk", ttl=86400)
def fetch_cpi_annual() -> dict[str, float]:
    """Annual all-items CPI index → {year: index}. Used for nominal/real views."""
    obs = _get_observations("DS_IPC_PRINC", {
        "FREQ": "A", "COICOP_2018": "00", "IDX_TYPE": "CPI",
        "IND_TYPE": "IX", "TPH_CPI": "_T",
    })
    out = {}
    for o in obs:
        d = o["dimensions"]
        # Defensive re-filter: the API can ignore unknown/extra params silently.
        if (d.get("FREQ") == "A" and d.get("COICOP_2018") == "00"
                and d.get("IND_TYPE") == "IX" and d.get("TPH_CPI") == "_T"):
            v = _value(o)
            if v is not None:
                out[d["TIME_PERIOD"]] = float(v)
    return out


_PCS_LABELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "pcs_labels.json")


@st.cache_data(show_spinner=False)
def load_pcs_labels() -> dict[str, dict]:
    """PCS-ESE 2017 labels {code: {"fr": str, "en": str|None}} — groups (1 char),
    categories (2) and detailed professions (4). Built by build_pcs_labels.py."""
    try:
        with open(_PCS_LABELS_FILE, encoding="utf-8") as f:
            return json.load(f).get("labels", {})
    except Exception:
        return {}


def pcs_name(code: str, lang: str = "FR") -> str:
    """Display name for a PCS code; falls back to the code itself."""
    entry = load_pcs_labels().get(code, {})
    if lang == "EN" and entry.get("en"):
        return entry["en"]
    return entry.get("fr", code)


@st.cache_data(show_spinner=False, ttl=86400)
def fetch_available_year(sector: str = "private") -> int | None:
    """Newest reference year of the detailed annual dataset (for the admin
    data-year check). Reads the catalog's temporal coverage — one light GET."""
    try:
        r = requests.get(f"{MELODI_BASE}/catalog/{DERA_ANNUAL[sector]}",
                         timeout=30, headers=_HEADERS)
        r.raise_for_status()
        end = r.json().get("temporal", {}).get("endPeriod", "")
        return int(end[:4]) if end[:4].isdigit() else None
    except Exception:
        return None
