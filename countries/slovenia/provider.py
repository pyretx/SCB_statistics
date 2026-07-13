"""Slovenia provider — SURS PxWeb table 0711335S.

Reads the bundled snapshot slovenia_earnings.json.gz. Gross monthly earnings (EUR)
with the full distribution — mean, median, P10, P25, P75, P90 — by SKP-08 (ISCO-08)
occupation × sex × year (2011→). Percentiles + quartiles + mean + median + a
12-year trend + hierarchy: the richest capability set after the UK.
"""
from __future__ import annotations

import gzip
import json
import os

import pandas as pd
import streamlit as st

from core import model
from core.provider import CountryProvider

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DATA = os.path.join(_ROOT, "slovenia_earnings.json.gz")
_SEX = {"total", "men", "women"}


@st.cache_data(show_spinner=False)
def _load() -> dict:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def _codes(lang="EN") -> dict:
    return _load().get("codes", {}).get("EN", {})


def _leaves(lang="EN") -> dict:
    codes = _codes(lang)
    return {c: n for c, n in codes.items()
            if not any(o != c and o.startswith(c) for o in codes)}


def _slice(year: int, sex: str) -> dict:
    d = _load()
    cols = d["stat_cols"]
    raw = d["stats"].get(str(year), {}).get(sex if sex in _SEX else "total", {})
    return {c: dict(zip(cols, v)) for c, v in raw.items()}


class SloveniaProvider(CountryProvider):
    def latest_year(self) -> int:
        return int(_load()["year"])

    def occupations(self, lang="EN"):
        return _leaves(lang)

    def occupation_tree(self, lang="EN"):
        return dict(_codes(lang))

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="EN"):
        if not occ_codes:
            return model.empty_occ_stats()
        yr = int(year or (max(years) if years else self.latest_year()))
        data = _slice(yr, sex)
        labels = _codes(lang)
        d = _load()
        rows = []
        for occ in occ_codes:
            v = data.get(occ)
            if not v:
                continue
            rows.append({
                "country": "slovenia", "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, occ), "occ_group": occ[:1],
                "dimension": "total", "dim_value": "total", "currency": "EUR",
                "period": "monthly", "mean": v.get("mean"), "median": v.get("median"),
                "p10": v.get("p10"), "p25": v.get("p25"), "p75": v.get("p75"),
                "p90": v.get("p90"), "count": None,
                "source_name": d["source_name"], "source_url": d["source"], "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def trend(self, *, sector="", occ_codes=(), sex="total", years=(),
              lang="EN", measure="median"):
        if not occ_codes or not years:
            return model.empty_trend()
        m = measure if measure in ("median", "mean", "p10", "p25", "p75", "p90") else "median"
        labels = _codes(lang)
        allyears = set(_load().get("years", []))
        rows = []
        for y in years:
            if int(y) not in allyears:
                continue
            data = _slice(int(y), sex)
            for occ in occ_codes:
                v = data.get(occ)
                rows.append({"country": "slovenia", "year": int(y),
                             "series": labels.get(occ, occ), "sex": sex,
                             "value_nominal": v.get(m) if v else None, "value_real": None})
        return pd.DataFrame(rows, columns=model.TREND_COLS)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        yr = int(year or self.latest_year())
        data = _slice(yr, sex)
        labels = _leaves(lang)
        rows = [{"occ_code": c, "occ_name": n, "mean": (data.get(c) or {}).get("mean"),
                 "median": (data.get(c) or {}).get("median"), "count": None}
                for c, n in labels.items() if c in data]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
