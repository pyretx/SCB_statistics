"""Iceland data provider — Statistics Iceland (Hagstofa) PxWeb table VIN02001.

Verified against the live API 2026-07: monthly earnings by ISCO occupation × sex
× earnings-type × measure × year (2014→). Measures: Mean / Lower quartile /
Median / Upper quartile / Observations. No P10/P90 (quartiles only, like
Norway/Denmark). No sector dimension in the occupation table (VIN02001 is all
sectors pooled) — so Iceland has no sector slicer.

UNIT: Hagstofa publishes these wage figures in THOUSANDS of ISK, so every money
value is multiplied by 1000 to present full monthly ISK.

Earnings type fixed to 'Total regular earnings' (code 2) — the standard
full-time comparable (excludes irregular overtime), closest to Norway's
Månedslønn. Occupation LABELS come from bundled iceland_labels.json.
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
from .build import api_code

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LABELS_FILE = os.path.join(_ROOT, "iceland_labels.json")
TABLE_URL = ("https://px.hagstofa.is/pxen/api/v1/en/Samfelag/launogtekjur/"
             "1_laun/1_laun/VIN02001.px")
_UNIT_SCALE = 1000.0                       # source is in thousand ISK → full ISK
_PAY_TYPE = "2"                            # Total regular earnings
SEX_CODE = {"total": "0", "men": "1", "women": "2"}
# Eining (measure) codes → normalized column
_MEASURE = {"mean": "0", "p25": "1", "median": "2", "p75": "3", "count": "4"}
_MEASURE_COL = {v: k for k, v in _MEASURE.items()}
_MONEY = {"mean", "median", "p25", "p75"}


def _post(query: dict, tries: int = 4) -> dict:
    r = None
    for i in range(tries):
        r = requests.post(TABLE_URL, json=query, timeout=120)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504) and i < tries - 1:
            time.sleep(1.5 * (i + 1))
            continue
        break
    r.raise_for_status()
    return {}


def _scaled(col: str, v):
    if v is None:
        return None
    return v * _UNIT_SCALE if col in _MONEY else v


@st.cache_data(show_spinner=False)
def _codes(lang: str = "EN") -> dict[str, str]:
    try:
        with open(_LABELS_FILE, encoding="utf-8") as f:
            codes = json.load(f).get("codes", {})
        return codes.get(lang) or codes.get("EN", {})
    except Exception:
        return {}


def _leaves(lang: str = "EN") -> dict[str, str]:
    return {c: n for c, n in _codes(lang).items() if len(c) == 4}


def _query(occ_codes, sex, years, measures):
    return {"query": [
        {"code": "Starf", "selection": {"filter": "item",
            "values": [api_code(c) for c in occ_codes]}},
        {"code": "Kyn", "selection": {"filter": "item", "values": [SEX_CODE.get(sex, "0")]}},
        {"code": "Laun og vinnutími", "selection": {"filter": "item", "values": [_PAY_TYPE]}},
        {"code": "Eining", "selection": {"filter": "item", "values": measures}},
        {"code": "Ár", "selection": {"filter": "item", "values": [str(y) for y in years]}},
    ], "response": {"format": "json-stat2"}}


def _flat(ds):
    ids, sizes, values = ds["id"], ds["size"], ds["value"]
    dims = ds["dimension"]
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    def val(sel):
        try:
            flat = sum(dims[d]["category"]["index"][sel[d]] * strides[ids.index(d)] for d in ids)
        except KeyError:
            return None
        return values[flat] if 0 <= flat < len(values) else None
    return dims, val


@st.cache_data(show_spinner=False, persist="disk")
def _fetch(occ_codes: tuple[str, ...], sex: str, year: int, lang: str = "EN") -> pd.DataFrame:
    if not occ_codes:
        return model.empty_occ_stats()
    ds = _post(_query(occ_codes, sex, [year], list(_MEASURE.values())))
    dims, val = _flat(ds)
    labels = _leaves(lang)
    rows = []
    for occ in occ_codes:
        ac = api_code(occ)
        if ac not in dims["Starf"]["category"]["index"]:
            continue

        def m(mc):
            return _scaled(_MEASURE_COL[mc], val({"Starf": ac, "Kyn": SEX_CODE.get(sex, "0"),
                          "Laun og vinnutími": _PAY_TYPE, "Eining": mc, "Ár": str(year)}))
        rows.append({
            "country": "iceland", "year": int(year), "occ_code": occ,
            "occ_name": labels.get(occ, _codes(lang).get(occ, occ)),
            "occ_group": occ[:2], "dimension": "total", "dim_value": "total",
            "currency": "ISK", "period": "monthly",
            "mean": m("0"), "median": m("2"),
            "p10": None, "p25": m("1"), "p75": m("3"), "p90": None,
            "count": m("4"),
            "source_name": "Statistics Iceland (Hagstofa)", "source_url": TABLE_URL, "notes": "",
        })
    return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_trend(occ_codes, sex, years, lang="EN", measure="mean"):
    if not occ_codes or not years:
        return model.empty_trend()
    mc = _MEASURE.get(measure, "0")
    ds = _post(_query(occ_codes, sex, years, [mc]))
    dims, val = _flat(ds)
    col = _MEASURE_COL[mc]
    labels = _leaves(lang)
    rows = []
    for occ in occ_codes:
        ac = api_code(occ)
        if ac not in dims["Starf"]["category"]["index"]:
            continue
        name = labels.get(occ, occ)
        for y in years:
            v = _scaled(col, val({"Starf": ac, "Kyn": SEX_CODE.get(sex, "0"),
                        "Laun og vinnutími": _PAY_TYPE, "Eining": mc, "Ár": str(y)}))
            rows.append({"country": "iceland", "year": int(y), "series": name,
                         "sex": sex, "value_nominal": v, "value_real": None})
    return pd.DataFrame(rows, columns=model.TREND_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_leaderboard(sex, year, lang="EN"):
    leaves = _leaves(lang)
    if not leaves:
        return pd.DataFrame(columns=["occ_code", "occ_name", "mean", "median", "count"])
    # Select ALL occupations in one query (listing 139 codes trips a PxWeb
    # per-selection limit → 400); filter to 4-digit leaves in post.
    ds = _post({"query": [
        {"code": "Starf", "selection": {"filter": "all", "values": ["*"]}},
        {"code": "Kyn", "selection": {"filter": "item", "values": [SEX_CODE.get(sex, "0")]}},
        {"code": "Laun og vinnutími", "selection": {"filter": "item", "values": [_PAY_TYPE]}},
        {"code": "Eining", "selection": {"filter": "item", "values": ["0", "2", "4"]}},
        {"code": "Ár", "selection": {"filter": "item", "values": [str(year)]}},
    ], "response": {"format": "json-stat2"}})
    dims, val = _flat(ds)
    idx = dims["Starf"]["category"]["index"]
    rows = []
    for occ, name in leaves.items():
        ac = api_code(occ)
        if ac not in idx:
            continue

        def m(mc):
            return _scaled(_MEASURE_COL[mc], val({"Starf": ac, "Kyn": SEX_CODE.get(sex, "0"),
                          "Laun og vinnutími": _PAY_TYPE, "Eining": mc, "Ár": str(year)}))
        rows.append({"occ_code": occ, "occ_name": name, "mean": m("0"),
                     "median": m("2"), "count": m("4")})
    return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])


class IcelandProvider(CountryProvider):
    def occupations(self, lang="EN"):
        return _leaves(lang)

    def occupation_tree(self, lang="EN"):
        return dict(_codes(lang))

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="EN"):
        from .build import latest_year
        yr = int(year or (years[-1] if years else latest_year()))
        return _fetch(tuple(occ_codes), sex, yr, lang)

    def trend(self, *, sector="", occ_codes=(), sex="total", years=(),
              lang="EN", measure="mean"):
        return _fetch_trend(tuple(occ_codes), sex, tuple(years), lang, measure)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        from .build import latest_year
        return _fetch_leaderboard(sex, int(year or latest_year()), lang)
