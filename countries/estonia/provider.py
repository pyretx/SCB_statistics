"""Estonia data provider — Statistics Estonia table PA633.

Average gross HOURLY earnings + headcount by DETAILED ISCO-08 occupation (446
codes, full 1–4-digit hierarchy) × sex × year. This table has ONLY the mean (no
median, no deciles) — the trade-off for detailed occupations (the coarse
10-group table PA623 has deciles). Published every 4 years → snapshot 2022.

We present an estimated MONTHLY figure = hourly × a standard full-time month
(40 h/week × 52 / 12) — an estimate, since Estonia publishes no monthly and the
sample includes part-timers. Occupation codes are the numeric ISCO codes; the
API is queried with "OC" + the code.
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

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LABELS_FILE = os.path.join(_ROOT, "estonia_labels.json")
TABLE_URL = ("https://andmed.stat.ee/api/v1/en/stat/majandus/palk-ja-toojeukulu/"
             "tootasu/PA633.PX")
OCC_VAR, SEX_VAR, IND_VAR, YEAR_VAR = "Ametiala", "Sugu", "Näitaja", "Vaatlusperiood"
SEX_CODE = {"total": "M_F", "men": "M", "women": "F"}
_MEAN, _COUNT = "GR_H", "EMP_AVG_FTE"
_HOURS_PER_MONTH = 173.33                       # 40 h/week × 52 / 12 (estimate)


def _monthly(v):
    return v * _HOURS_PER_MONTH if v is not None else None


def _api(code: str) -> str:
    return "OC" + code


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


@st.cache_data(show_spinner=False)
def _codes(lang: str = "EN") -> dict[str, str]:
    try:
        with open(_LABELS_FILE, encoding="utf-8") as f:
            codes = json.load(f).get("codes", {})
        return codes.get(lang) or codes.get("EN", {})
    except Exception:
        return {}


def _leaves(lang: str = "EN") -> dict[str, str]:
    codes = _codes(lang)
    return {c: n for c, n in codes.items()
            if not any(o != c and o.startswith(c) for o in codes)}   # no children


def _query(occ_codes, sex, year, measures):
    return {"query": [
        {"code": IND_VAR, "selection": {"filter": "item", "values": measures}},
        {"code": OCC_VAR, "selection": {"filter": "item", "values": [_api(c) for c in occ_codes]}},
        {"code": SEX_VAR, "selection": {"filter": "item", "values": [SEX_CODE.get(sex, "M_F")]}},
        {"code": YEAR_VAR, "selection": {"filter": "item", "values": [str(year)]}},
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
    ds = _post(_query(occ_codes, sex, year, [_MEAN, _COUNT]))
    dims, val = _flat(ds)
    labels = _codes(lang)
    sc = SEX_CODE.get(sex, "M_F")
    rows = []
    for occ in occ_codes:
        if _api(occ) not in dims[OCC_VAR]["category"]["index"]:
            continue

        def g(mc):
            return val({IND_VAR: mc, OCC_VAR: _api(occ), SEX_VAR: sc, YEAR_VAR: str(year)})
        rows.append({
            "country": "estonia", "year": int(year), "occ_code": occ,
            "occ_name": labels.get(occ, occ), "occ_group": occ[:2], "dimension": "total",
            "dim_value": "total", "currency": "EUR", "period": "monthly",
            "mean": _monthly(g(_MEAN)), "median": None,
            "p10": None, "p25": None, "p75": None, "p90": None,
            "count": g(_COUNT),
            "source_name": "Statistics Estonia", "source_url": TABLE_URL, "notes": "",
        })
    return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_leaderboard(sex, year, lang="EN"):
    leaves = _leaves(lang)
    if not leaves:
        return pd.DataFrame(columns=["occ_code", "occ_name", "mean", "median", "count"])
    # one query over ALL occupation codes (filter=all) → filter to leaves in post
    ds = _post({"query": [
        {"code": IND_VAR, "selection": {"filter": "item", "values": [_MEAN, _COUNT]}},
        {"code": OCC_VAR, "selection": {"filter": "all", "values": ["*"]}},
        {"code": SEX_VAR, "selection": {"filter": "item", "values": [SEX_CODE.get(sex, "M_F")]}},
        {"code": YEAR_VAR, "selection": {"filter": "item", "values": [str(year)]}},
    ], "response": {"format": "json-stat2"}})
    dims, val = _flat(ds)
    sc = SEX_CODE.get(sex, "M_F")
    idx = dims[OCC_VAR]["category"]["index"]
    rows = []
    for occ, name in leaves.items():
        if _api(occ) not in idx:
            continue
        rows.append({"occ_code": occ, "occ_name": name,
                     "mean": _monthly(val({IND_VAR: _MEAN, OCC_VAR: _api(occ),
                                           SEX_VAR: sc, YEAR_VAR: str(year)})),
                     "median": None,
                     "count": val({IND_VAR: _COUNT, OCC_VAR: _api(occ),
                                   SEX_VAR: sc, YEAR_VAR: str(year)})})
    return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])


class EstoniaProvider(CountryProvider):
    def occupations(self, lang="EN"):
        return _leaves(lang)

    def occupation_tree(self, lang="EN"):
        return dict(_codes(lang))

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="EN"):
        from .build import latest_year
        yr = int(year or (years[-1] if years else latest_year()))
        return _fetch(tuple(occ_codes), sex, yr, lang)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        from .build import latest_year
        return _fetch_leaderboard(sex, int(year or latest_year()), lang)
