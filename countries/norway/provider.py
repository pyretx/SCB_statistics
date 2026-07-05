"""Norway data provider — SSB Statbank table 11418 (PxWeb / json-stat2).

Verified against the live API 2026-07: monthly earnings (NOK) with measuring
methods Average / Median / Lower quartile / Upper quartile / count, by STYRK-08
occupation × sector × sex × working-hours × year (2015→). No P10/P90 (quartiles
only), so has_occupation_percentiles is False in the config.

Occupation LABELS come from the bundled styrk_labels.json (build_styrk_labels.py)
so the menu never waits on SSB; the salary VALUES are fetched per query (cached
on disk, never auto-refreshed — same discipline as france_data.py).
"""
from __future__ import annotations

import json
import os

import pandas as pd
import requests
import streamlit as st

from core import model
from core.provider import CountryProvider

TABLE_URL = "https://data.ssb.no/api/v0/en/table/11418"
CPI_URL = "https://data.ssb.no/api/v0/en/table/03013"   # Consumer Price Index (2015=100)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LABELS_FILE = os.path.join(_ROOT, "styrk_labels.json")

SECTOR_CODE = {"all": "ALLE", "private": "A+B+D+E", "local": "6500", "central": "6100"}
SEX_CODE = {"total": "0", "women": "2", "men": "1"}
# MaaleMetode codes → normalized column
_METHOD = {"mean": "02", "median": "01", "p25": "051", "p75": "061", "count": "10"}


@st.cache_data(show_spinner=False)
def _codes(lang: str = "EN") -> dict[str, str]:
    """All STYRK codes (every level) → name, for the given language (EN|NO)."""
    try:
        with open(_LABELS_FILE, encoding="utf-8") as f:
            codes = json.load(f).get("codes", {})
        return codes.get(lang) or codes.get("EN", {})
    except Exception:
        return {}


def _leaves(lang: str = "EN") -> dict[str, str]:
    """Just the detailed 4-digit occupations (the menu options)."""
    return {c: n for c, n in _codes(lang).items() if len(c) == 4}


@st.cache_data(show_spinner=False, persist="disk")
def _fetch(sector: str, occ_codes: tuple[str, ...], sex: str, year: int,
          lang: str = "EN") -> pd.DataFrame:
    """One SSB query → normalized OccupationStat rows (dimension='total')."""
    if not occ_codes:
        return model.empty_occ_stats()
    query = {"query": [
        {"code": "MaaleMetode", "selection": {"filter": "item",
            "values": list(_METHOD.values())}},
        {"code": "Yrke", "selection": {"filter": "item", "values": list(occ_codes)}},
        {"code": "Sektor", "selection": {"filter": "item",
            "values": [SECTOR_CODE.get(sector, "ALLE")]}},
        {"code": "Kjonn", "selection": {"filter": "item", "values": [SEX_CODE.get(sex, "0")]}},
        {"code": "AvtaltVanlig", "selection": {"filter": "item", "values": ["0"]}},
        {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Manedslonn"]}},
        {"code": "Tid", "selection": {"filter": "item", "values": [str(year)]}},
    ], "response": {"format": "json-stat2"}}
    r = requests.post(TABLE_URL, json=query, timeout=120)
    r.raise_for_status()
    ds = r.json()
    ids, sizes, values = ds["id"], ds["size"], ds["value"]
    dims = ds["dimension"]
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    def val(method: str, occ: str):
        sel = {"MaaleMetode": method, "Yrke": occ, "Sektor": SECTOR_CODE.get(sector, "ALLE"),
               "Kjonn": SEX_CODE.get(sex, "0"), "AvtaltVanlig": "0",
               "ContentsCode": "Manedslonn", "Tid": str(year)}
        try:
            flat = sum(dims[d]["category"]["index"][sel[d]] * strides[ids.index(d)] for d in ids)
        except KeyError:
            return None
        return values[flat] if 0 <= flat < len(values) else None

    labels = _leaves(lang)
    rows = []
    for occ in occ_codes:
        if occ not in dims["Yrke"]["category"]["index"]:
            continue
        rows.append({
            "country": "norway", "year": year, "occ_code": occ,
            "occ_name": labels.get(occ, dims["Yrke"]["category"]["label"].get(occ, occ)),
            "occ_group": occ[:2], "dimension": "total", "dim_value": "total",
            "currency": "NOK", "period": "monthly",
            "mean": val("02", occ), "median": val("01", occ),
            "p10": None, "p25": val("051", occ), "p75": val("061", occ), "p90": None,
            "count": val("10", occ),
            "source_name": "Statistics Norway (SSB)", "source_url": TABLE_URL, "notes": "",
        })
    return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_trend(sector: str, occ_codes: tuple[str, ...], sex: str,
                 years: tuple[int, ...], lang: str = "EN") -> pd.DataFrame:
    """Mean monthly earnings per occupation × year → normalized trend rows. One
    SSB query spanning all selected years."""
    if not occ_codes or not years:
        return model.empty_trend()
    yrs = [str(y) for y in years]
    query = {"query": [
        {"code": "MaaleMetode", "selection": {"filter": "item", "values": ["02"]}},  # mean
        {"code": "Yrke", "selection": {"filter": "item", "values": list(occ_codes)}},
        {"code": "Sektor", "selection": {"filter": "item",
            "values": [SECTOR_CODE.get(sector, "ALLE")]}},
        {"code": "Kjonn", "selection": {"filter": "item", "values": [SEX_CODE.get(sex, "0")]}},
        {"code": "AvtaltVanlig", "selection": {"filter": "item", "values": ["0"]}},
        {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Manedslonn"]}},
        {"code": "Tid", "selection": {"filter": "item", "values": yrs}},
    ], "response": {"format": "json-stat2"}}
    r = requests.post(TABLE_URL, json=query, timeout=120)
    r.raise_for_status()
    ds = r.json()
    ids, sizes, values = ds["id"], ds["size"], ds["value"]
    dims = ds["dimension"]
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    def val(occ: str, yr: str):
        sel = {"MaaleMetode": "02", "Yrke": occ, "Sektor": SECTOR_CODE.get(sector, "ALLE"),
               "Kjonn": SEX_CODE.get(sex, "0"), "AvtaltVanlig": "0",
               "ContentsCode": "Manedslonn", "Tid": yr}
        try:
            flat = sum(dims[d]["category"]["index"][sel[d]] * strides[ids.index(d)] for d in ids)
        except KeyError:
            return None
        return values[flat] if 0 <= flat < len(values) else None

    labels = _leaves(lang)
    rows = []
    for occ in occ_codes:
        if occ not in dims["Yrke"]["category"]["index"]:
            continue
        name = labels.get(occ, occ)
        for yr in yrs:
            rows.append({"country": "norway", "year": int(yr), "series": name,
                         "sex": sex, "value_nominal": val(occ, yr), "value_real": None})
    return pd.DataFrame(rows, columns=model.TREND_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_cpi_annual(years: tuple[int, ...]) -> dict:
    """Annual-average all-item CPI (2015=100) → {year: index}, from SSB table
    03013, averaged over the 12 months of each year (mirrors the Swedish page)."""
    if not years:
        return {}
    yrs = sorted(set(int(y) for y in years))
    months = [f"{y}M{m:02d}" for y in range(yrs[0], yrs[-1] + 1) for m in range(1, 13)]
    query = {"query": [
        {"code": "Konsumgrp", "selection": {"filter": "item", "values": ["TOTAL"]}},
        {"code": "ContentsCode", "selection": {"filter": "item", "values": ["KpiIndMnd"]}},
        {"code": "Tid", "selection": {"filter": "item", "values": months}},
    ], "response": {"format": "json-stat2"}}
    try:
        r = requests.post(CPI_URL, json=query, timeout=120)
        r.raise_for_status()
        ds = r.json()
    except Exception:
        return {}
    idx = ds["dimension"]["Tid"]["category"]["index"]   # only Tid varies → flat index
    values = ds["value"]
    by_year: dict[int, list] = {}
    for tid, i in idx.items():
        v = values[i]
        if v is not None:
            by_year.setdefault(int(tid[:4]), []).append(v)
    return {y: sum(vs) / len(vs) for y, vs in by_year.items() if vs}


class NorwayProvider(CountryProvider):
    def occupations(self, lang: str = "EN") -> dict[str, str]:
        return _leaves(lang)

    def occupation_tree(self, lang: str = "EN") -> dict[str, str]:
        return dict(_codes(lang))

    def occupation_stats(self, *, sector="all", occ_codes=(), sex="total",
                         years=(), dimension="total", year=None,
                         lang="EN") -> pd.DataFrame:
        yr = int(year or (years[-1] if years else 2024))
        return _fetch(sector, tuple(occ_codes), sex, yr, lang)

    def trend(self, *, sector="all", occ_codes=(), sex="total", years=(),
              lang="EN") -> pd.DataFrame:
        return _fetch_trend(sector, tuple(occ_codes), sex, tuple(years), lang)

    def cpi_annual(self, years=()) -> dict:
        return _fetch_cpi_annual(tuple(years))
