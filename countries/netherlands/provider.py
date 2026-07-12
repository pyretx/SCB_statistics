"""Netherlands data provider — Statistics Netherlands (CBS) table 85517NED.

Gross HOURLY wages (EUR) by BRC-2014 occupation × year, 2013→. Measures: 25th /
50th (median) / 75th percentile + employee count. So the Netherlands shows
P25·median·P75 (quartiles, like Norway/Denmark), with a full annual trend — but
NO mean and NO sex breakdown (this CBS table has neither).

CBS OData v3: one query per year returns every occupation, so a whole year is a
single cached round-trip. Occupation codes are the numeric BRC codes; the bundled
keymap translates them to CBS's opaque 'Beroep' keys for the query.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse

import pandas as pd
import requests
import streamlit as st

from core import model
from core.provider import CountryProvider

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LABELS_FILE = os.path.join(_ROOT, "netherlands_labels.json")
BASE = "https://opendata.cbs.nl/ODataApi/odata/85517NED/"
_SELECT = ("Beroep,k_25ePercentiel_2,k_50ePercentielMediaan_3,"
           "k_75ePercentiel_4,Werknemer_1")
# CBS publishes HOURLY wages; we present an estimated MONTHLY figure = hourly ×
# a standard full-time month (40 h/week × 52 / 12). It is an estimate (no
# official monthly is published, and the sample includes part-time workers) —
# a full-time-equivalent monthly.
_HOURS_PER_MONTH = 173.33


def _monthly(v):
    return v * _HOURS_PER_MONTH if v is not None else None


@st.cache_data(show_spinner=False)
def _bundle() -> dict:
    try:
        with open(_LABELS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _codes(lang="EN") -> dict[str, str]:
    codes = _bundle().get("codes", {})
    return codes.get(lang) or codes.get("EN", {})


def _leaves(lang="EN") -> dict[str, str]:
    return {c: n for c, n in _codes(lang).items() if len(c) == 4}


def _keymap() -> dict[str, str]:
    return _bundle().get("keymap", {})


def _get(url, tries=4):
    r = None
    for i in range(tries):
        r = requests.get(url, timeout=120)
        if r.status_code == 200:
            return r.json().get("value", [])
        if r.status_code in (429, 500, 502, 503, 504) and i < tries - 1:
            time.sleep(1.5 * (i + 1))
            continue
        break
    r.raise_for_status()
    return []


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_year(year: int) -> dict:
    """{numeric_code: {p25, median, p75, count}} for every occupation in ``year``
    (one CBS query). count is scaled from thousands to actual employees."""
    rev = {k: c for c, k in _keymap().items()}     # cbs_key → numeric
    flt = urllib.parse.quote(f"Perioden eq '{year}JJ00'")
    rows = _get(f"{BASE}TypedDataSet?$filter={flt}&$select={_SELECT}")
    out = {}
    for r in rows:
        code = rev.get(r.get("Beroep"))
        if not code:
            continue
        cnt = r.get("Werknemer_1")
        out[code] = {
            "p25": _monthly(r.get("k_25ePercentiel_2")),
            "median": _monthly(r.get("k_50ePercentielMediaan_3")),
            "p75": _monthly(r.get("k_75ePercentiel_4")),
            "count": (cnt * 1000) if cnt is not None else None,
        }
    return out


def _rows(codes, year, lang):
    data = _fetch_year(int(year))
    labels = _leaves(lang)
    rows = []
    for occ in codes:
        v = data.get(occ)
        if not v:
            continue
        rows.append({
            "country": "netherlands", "year": int(year), "occ_code": occ,
            "occ_name": labels.get(occ, _codes(lang).get(occ, occ)),
            "occ_group": occ[:2], "dimension": "total", "dim_value": "total",
            "currency": "EUR", "period": "monthly",
            "mean": None, "median": v.get("median"),
            "p10": None, "p25": v.get("p25"), "p75": v.get("p75"), "p90": None,
            "count": v.get("count"),
            "source_name": "Statistics Netherlands (CBS)",
            "source_url": "https://www.cbs.nl/", "notes": "",
        })
    return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)


class NetherlandsProvider(CountryProvider):
    def occupations(self, lang="EN"):
        return _leaves(lang)

    def occupation_tree(self, lang="EN"):
        return dict(_codes(lang))

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="EN"):
        from .build import latest_year
        yr = int(year or (years[-1] if years else latest_year()))
        return _rows(tuple(occ_codes), yr, lang) if occ_codes else model.empty_occ_stats()

    def trend(self, *, sector="", occ_codes=(), sex="total", years=(),
              lang="EN", measure="median"):
        if not occ_codes or not years:
            return model.empty_trend()
        m = measure if measure in ("p25", "median", "p75") else "median"
        labels = _leaves(lang)
        rows = []
        for y in years:
            data = _fetch_year(int(y))
            for occ in occ_codes:
                v = data.get(occ)
                rows.append({"country": "netherlands", "year": int(y),
                             "series": labels.get(occ, occ), "sex": sex,
                             "value_nominal": v.get(m) if v else None,
                             "value_real": None})
        return pd.DataFrame(rows, columns=model.TREND_COLS)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        from .build import latest_year
        data = _fetch_year(int(year or latest_year()))
        labels = _leaves(lang)
        rows = [{"occ_code": occ, "occ_name": name, "mean": None,
                 "median": (data.get(occ) or {}).get("median"),
                 "count": (data.get(occ) or {}).get("count")}
                for occ, name in labels.items() if occ in data]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
