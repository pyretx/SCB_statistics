"""Denmark data provider — DST StatBank table LONS20 (api.statbank.dk).

Verified against the live API 2026-07: STANDARDIZED HOURLY EARNINGS (DKK) with
mean (STAND) / median (MEDIANST) / lower quartile (NEDREST) / upper quartile
(OVREST) / full-time employee count (ANTAL), by DISCO-08 occupation × sector ×
sex × year (2013→2024). No P10/P90 (quartiles only, like Norway), so
has_occupation_percentiles is False in the config.

Fixed query slots: AFLOEN=TIFA (all forms of pay), LONGRP=LTOT (employee group
total). DST returns suppressed cells as 0 (tableinfo suppressedDataValue="0"),
so zeros are normalized to None — a published hourly wage of 0 DKK does not
occur.

Occupation LABELS come from the bundled disco_labels.json (countries/denmark/
build.py) so the menu never waits on DST; salary VALUES are fetched per query
(cached on disk, never auto-refreshed — same discipline as Norway/Sweden).
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd
import requests
import streamlit as st

from core import model
from core.provider import CountryProvider

BASE = "https://api.statbank.dk/v1"
TABLE = "LONS20"
CPI_TABLE = "PRIS111"                     # Consumer Price Index (2015=100), monthly
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LABELS_FILE = os.path.join(_ROOT, "disco_labels.json")

SECTOR_CODE = {"all": "1000", "private": "1046", "local": "1018", "central": "1016"}
SEX_CODE = {"total": "MOK", "women": "K", "men": "M"}
# LØNMÅL codes → normalized column (standardized hourly earnings)
_MEASURE = {"mean": "STAND", "median": "MEDIANST", "p25": "NEDREST",
            "p75": "OVREST", "count": "ANTAL"}
_MEASURE_COL = {v: k for k, v in _MEASURE.items()}


def _data_rows(variables: list[dict], table: str = TABLE,
               tries: int = 4) -> list[dict]:
    """POST /data as CSV with code-valued cells → list of row dicts. Retries the
    transient 5xx errors; suppressed/absent values ('..', '', 0) → None."""
    body = {"table": table, "format": "CSV", "valuePresentation": "Code",
            "lang": "en", "variables": variables}
    r = None
    for i in range(tries):
        r = requests.post(f"{BASE}/data", json=body, timeout=120)
        if r.status_code == 200:
            break
        if r.status_code in (500, 502, 503, 504) and i < tries - 1:
            time.sleep(1.2 * (i + 1))
            continue
        r.raise_for_status()
    lines = r.content.decode("utf-8-sig").strip().splitlines()
    if not lines:
        return []
    header = lines[0].split(";")
    rows = []
    for ln in lines[1:]:
        cells = ln.split(";")
        row = dict(zip(header, cells))
        v = row.get("INDHOLD", "")
        try:
            f = float(v)
            row["INDHOLD"] = f if f != 0 else None    # 0 = DST suppression
        except (TypeError, ValueError):
            row["INDHOLD"] = None
        rows.append(row)
    return rows


@st.cache_data(show_spinner=False)
def _codes(lang: str = "EN") -> dict[str, str]:
    """All DISCO codes (every level) → name, for the given language (EN|DA)."""
    try:
        with open(_LABELS_FILE, encoding="utf-8") as f:
            codes = json.load(f).get("codes", {})
        return codes.get(lang) or codes.get("EN", {})
    except Exception:
        return {}


def _leaves(lang: str = "EN") -> dict[str, str]:
    """Just the detailed 4-digit occupations (the menu options)."""
    return {c: n for c, n in _codes(lang).items() if len(c) == 4}


def _base_vars(sector: str, sex: str) -> list[dict]:
    return [
        {"code": "SEKTOR", "values": [SECTOR_CODE.get(sector, "1000")]},
        {"code": "AFLOEN", "values": ["TIFA"]},
        {"code": "LONGRP", "values": ["LTOT"]},
        {"code": "KØN", "values": [SEX_CODE.get(sex, "MOK")]},
    ]


@st.cache_data(show_spinner=False, persist="disk")
def _fetch(sector: str, occ_codes: tuple[str, ...], sex: str, year: int,
           lang: str = "EN") -> pd.DataFrame:
    """One DST query → normalized OccupationStat rows (dimension='total')."""
    if not occ_codes:
        return model.empty_occ_stats()
    rows_raw = _data_rows([
        {"code": "ARBF", "values": list(occ_codes)},
        *_base_vars(sector, sex),
        {"code": "LØNMÅL", "values": list(_MEASURE.values())},
        {"code": "Tid", "values": [str(year)]},
    ])
    by_occ: dict[str, dict] = {}
    for r in rows_raw:
        col = _MEASURE_COL.get(r.get("LØNMÅL", ""))
        if col:
            by_occ.setdefault(r.get("ARBF", ""), {})[col] = r["INDHOLD"]

    labels = _leaves(lang)
    rows = []
    for occ in occ_codes:
        v = by_occ.get(occ)
        if not v:
            continue
        rows.append({
            "country": "denmark", "year": year, "occ_code": occ,
            "occ_name": labels.get(occ, _codes(lang).get(occ, occ)),
            "occ_group": occ[:2], "dimension": "total", "dim_value": "total",
            "currency": "DKK", "period": "hourly",
            "mean": v.get("mean"), "median": v.get("median"),
            "p10": None, "p25": v.get("p25"), "p75": v.get("p75"), "p90": None,
            "count": v.get("count"),
            "source_name": "Statistics Denmark (DST)",
            "source_url": f"https://www.statbank.dk/{TABLE}", "notes": "",
        })
    return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_trend(sector: str, occ_codes: tuple[str, ...], sex: str,
                 years: tuple[int, ...], lang: str = "EN",
                 measure: str = "mean") -> pd.DataFrame:
    """One measure per occupation × year → normalized trend rows. A single DST
    query spanning all selected years."""
    if not occ_codes or not years:
        return model.empty_trend()
    mm = _MEASURE.get(measure, "STAND")
    yrs = [str(y) for y in years]
    rows_raw = _data_rows([
        {"code": "ARBF", "values": list(occ_codes)},
        *_base_vars(sector, sex),
        {"code": "LØNMÅL", "values": [mm]},
        {"code": "Tid", "values": yrs},
    ])
    val = {(r.get("ARBF", ""), r.get("TID", "")): r["INDHOLD"] for r in rows_raw}
    labels = _leaves(lang)
    rows = []
    for occ in occ_codes:
        name = labels.get(occ, occ)
        for yr in yrs:
            rows.append({"country": "denmark", "year": int(yr), "series": name,
                         "sex": sex, "value_nominal": val.get((occ, yr)),
                         "value_real": None})
    return pd.DataFrame(rows, columns=model.TREND_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_cpi_annual(years: tuple[int, ...]) -> dict:
    """Annual-average all-item CPI (2015=100) → {year: index}, from DST PRIS111,
    averaged over the 12 months of each year (mirrors Norway/Sweden)."""
    if not years:
        return {}
    yrs = sorted(set(int(y) for y in years))
    months = [f"{y}M{m:02d}" for y in range(yrs[0], yrs[-1] + 1) for m in range(1, 13)]
    try:
        rows = _data_rows([
            {"code": "VAREGR", "values": ["000000"]},
            {"code": "ENHED", "values": ["100"]},
            {"code": "Tid", "values": months},
        ], table=CPI_TABLE)
    except Exception:
        return {}
    by_year: dict[int, list] = {}
    for r in rows:
        v, tid = r["INDHOLD"], r.get("TID", "")
        if v is not None and len(tid) >= 4 and tid[:4].isdigit():
            by_year.setdefault(int(tid[:4]), []).append(v)
    return {y: sum(vs) / len(vs) for y, vs in by_year.items() if vs}


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_leaderboard(sector: str, sex: str, year: int, lang: str = "EN") -> pd.DataFrame:
    """Mean + median + count for EVERY 4-digit occupation, one year — powers the
    Leaderboard ranking. One DST query over all ARBF codes ('*')."""
    rows_raw = _data_rows([
        {"code": "ARBF", "values": ["*"]},
        *_base_vars(sector, sex),
        {"code": "LØNMÅL", "values": ["STAND", "MEDIANST", "ANTAL"]},
        {"code": "Tid", "values": [str(year)]},
    ])
    by_occ: dict[str, dict] = {}
    for r in rows_raw:
        col = _MEASURE_COL.get(r.get("LØNMÅL", ""))
        if col:
            by_occ.setdefault(r.get("ARBF", ""), {})[col] = r["INDHOLD"]
    labels = _leaves(lang)               # only detailed (4-digit) occupations
    rows = [{"occ_code": occ, "occ_name": name,
             "mean": by_occ[occ].get("mean"), "median": by_occ[occ].get("median"),
             "count": by_occ[occ].get("count")}
            for occ, name in labels.items() if occ in by_occ]
    return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])


class DenmarkProvider(CountryProvider):
    def occupations(self, lang: str = "EN") -> dict[str, str]:
        return _leaves(lang)

    def occupation_tree(self, lang: str = "EN") -> dict[str, str]:
        return dict(_codes(lang))

    def occupation_stats(self, *, sector="all", occ_codes=(), sex="total",
                         years=(), dimension="total", year=None,
                         lang="EN") -> pd.DataFrame:
        from .build import latest_year
        yr = int(year or (years[-1] if years else latest_year()))
        return _fetch(sector, tuple(occ_codes), sex, yr, lang)

    def trend(self, *, sector="all", occ_codes=(), sex="total", years=(),
              lang="EN", measure="mean") -> pd.DataFrame:
        return _fetch_trend(sector, tuple(occ_codes), sex, tuple(years), lang, measure)

    def cpi_annual(self, years=()) -> dict:
        return _fetch_cpi_annual(tuple(years))

    def leaderboard(self, *, sector="all", sex="total", year=None, lang="EN") -> pd.DataFrame:
        from .build import latest_year
        return _fetch_leaderboard(sector, sex, int(year or latest_year()), lang)
