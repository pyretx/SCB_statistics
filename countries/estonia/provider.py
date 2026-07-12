"""Estonia data provider — Statistics Estonia (Statistikaamet) table PA623.

Structure of Earnings: gross HOURLY earnings (EUR) by ISCO-08 major group ×
sex × year. Measures: mean (GR_H) + full deciles (GR_H_D1…D9), so we surface
P10 (D1) · median (D5) · P90 (D9) — deciles, like Finland. Occupation is only
the 10 major groups (no detailed occupations, no hierarchy); published every 4
years (2010/14/18/22), so the page is a snapshot of the latest SES year.

Occupation LABELS come from bundled estonia_labels.json.
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
             "tootasu/PA623.PX")
OCC_VAR, SEX_VAR, IND_VAR, YEAR_VAR = "Ametiala pearühm", "Sugu", "Näitaja", "Vaatlusperiood"
SEX_CODE = {"total": "M_F", "men": "M", "women": "F"}
# Näitaja (indicator) codes → normalized column (deciles → P10/median/P90)
_MEASURE = {"mean": "GR_H", "p10": "GR_H_D1", "median": "GR_H_D5", "p90": "GR_H_D9"}
_MEASURE_COL = {v: k for k, v in _MEASURE.items()}
# Statistics Estonia publishes HOURLY earnings; we present an estimated MONTHLY
# figure = hourly × a standard full-time month (40 h/week × 52 / 12). It is an
# estimate (no official monthly is published, and the sample includes part-time
# workers) — a full-time-equivalent monthly.
_HOURS_PER_MONTH = 173.33


def _monthly(v):
    return v * _HOURS_PER_MONTH if v is not None else None


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
    return dict(_codes(lang))                  # the 10 major groups ARE the leaves


def _query(occ_codes, sex, year, measures):
    return {"query": [
        {"code": IND_VAR, "selection": {"filter": "item", "values": measures}},
        {"code": OCC_VAR, "selection": {"filter": "item", "values": list(occ_codes)}},
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
    ds = _post(_query(occ_codes, sex, year, list(_MEASURE.values())))
    dims, val = _flat(ds)
    labels = _leaves(lang)
    rows = []
    sc = SEX_CODE.get(sex, "M_F")
    for occ in occ_codes:
        if occ not in dims[OCC_VAR]["category"]["index"]:
            continue

        def m(mc):
            return _monthly(val({IND_VAR: mc, OCC_VAR: occ, SEX_VAR: sc, YEAR_VAR: str(year)}))
        rows.append({
            "country": "estonia", "year": int(year), "occ_code": occ,
            "occ_name": labels.get(occ, occ), "occ_group": occ, "dimension": "total",
            "dim_value": "total", "currency": "EUR", "period": "monthly",
            "mean": m(_MEASURE["mean"]), "median": m(_MEASURE["median"]),
            "p10": m(_MEASURE["p10"]), "p25": None, "p75": None,
            "p90": m(_MEASURE["p90"]), "count": None,
            "source_name": "Statistics Estonia", "source_url": TABLE_URL, "notes": "",
        })
    return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_leaderboard(sex, year, lang="EN"):
    leaves = _leaves(lang)
    if not leaves:
        return pd.DataFrame(columns=["occ_code", "occ_name", "mean", "median", "count"])
    ds = _post(_query(tuple(leaves), sex, year, ["GR_H", "GR_H_D5"]))
    dims, val = _flat(ds)
    sc = SEX_CODE.get(sex, "M_F")
    idx = dims[OCC_VAR]["category"]["index"]
    rows = []
    for occ, name in leaves.items():
        if occ not in idx:
            continue
        rows.append({"occ_code": occ, "occ_name": name,
                     "mean": _monthly(val({IND_VAR: "GR_H", OCC_VAR: occ, SEX_VAR: sc, YEAR_VAR: str(year)})),
                     "median": _monthly(val({IND_VAR: "GR_H_D5", OCC_VAR: occ, SEX_VAR: sc, YEAR_VAR: str(year)})),
                     "count": None})
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
