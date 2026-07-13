"""New Zealand provider — Stats NZ ADE dataflow INC_INC_004.

Reads the bundled snapshot newzealand_earnings.json.gz (built via the ADE API).
Median + average gross MONTHLY earnings (weekly × 52/12) by ANZSCO major-group
occupation × sex, with a 2009→ trend. Wage & salary earners, all ages. No
percentiles/region; occupations are the 9 ANZSCO major groups (flat).
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
_DATA = os.path.join(_ROOT, "newzealand_earnings.json.gz")
_SEX = {"total", "men", "women"}


@st.cache_data(show_spinner=False)
def _load() -> dict:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def _codes(lang="EN") -> dict:
    codes = _load().get("codes", {})
    return codes.get("EN", {})


def _slice(year: int, sex: str) -> dict:
    d = _load()
    cols = d["stat_cols"]
    raw = d["stats"].get(str(year), {}).get(sex if sex in _SEX else "total", {})
    return {c: dict(zip(cols, v)) for c, v in raw.items()}


class NewZealandProvider(CountryProvider):
    def year(self) -> int:
        return int(_load()["year"])

    def occupations(self, lang="EN"):
        return _codes(lang)

    def occupation_tree(self, lang="EN"):
        return _codes(lang)

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="EN"):
        if not occ_codes:
            return model.empty_occ_stats()
        yr = int(year or (max(years) if years else self.year()))
        data = _slice(yr, sex)
        labels = _codes(lang)
        d = _load()
        rows = []
        for occ in occ_codes:
            v = data.get(occ)
            if not v:
                continue
            rows.append({
                "country": "newzealand", "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, occ), "occ_group": occ,
                "dimension": "total", "dim_value": "total", "currency": "NZD",
                "period": "monthly", "mean": v.get("mean"), "median": v.get("median"),
                "p10": None, "p25": None, "p75": None, "p90": None, "count": None,
                "source_name": d["source_name"], "source_url": d["source"], "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def trend(self, *, sector="", occ_codes=(), sex="total", years=(),
              lang="EN", measure="median"):
        if not occ_codes or not years:
            return model.empty_trend()
        m = measure if measure in ("mean", "median") else "median"
        labels = _codes(lang)
        allyears = set(_load().get("years", []))
        rows = []
        for y in years:
            if int(y) not in allyears:
                continue
            data = _slice(int(y), sex)
            for occ in occ_codes:
                v = data.get(occ)
                rows.append({"country": "newzealand", "year": int(y),
                             "series": labels.get(occ, occ), "sex": sex,
                             "value_nominal": v.get(m) if v else None, "value_real": None})
        return pd.DataFrame(rows, columns=model.TREND_COLS)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        yr = int(year or self.year())
        data = _slice(yr, sex)
        labels = _codes(lang)
        rows = [{"occ_code": c, "occ_name": n, "mean": (data.get(c) or {}).get("mean"),
                 "median": (data.get(c) or {}).get("median"), "count": None}
                for c, n in labels.items() if c in data]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
