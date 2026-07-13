"""Mexico provider — INEGI ENOE microdata (computed offline).

Reads the bundled snapshot mexico_earnings.json.gz (survey-weighted mean & median
monthly occupational income by 10 ENOE occupation groups × sex, from the ENOE
microdata). No percentiles/trend/region in this cut. EN + ES occupation names.
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
_DATA = os.path.join(_ROOT, "mexico_earnings.json.gz")
_SEX = {"total", "men", "women"}


@st.cache_data(show_spinner=False)
def _load() -> dict:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def _codes(lang="EN") -> dict:
    codes = _load().get("codes", {})
    return codes.get(lang) or codes.get("EN", {})


def _slice(sex: str) -> dict:
    d = _load()
    cols = d["stat_cols"]
    raw = d["stats"].get(sex if sex in _SEX else "total", {})
    return {c: dict(zip(cols, v)) for c, v in raw.items()}


class MexicoProvider(CountryProvider):
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
        data = _slice(sex)
        labels = _codes(lang)
        d = _load()
        rows = []
        for occ in occ_codes:
            v = data.get(occ)
            if not v:
                continue
            rows.append({
                "country": "mexico", "year": self.year(), "occ_code": occ,
                "occ_name": labels.get(occ, occ), "occ_group": occ,
                "dimension": "total", "dim_value": "total", "currency": "MXN",
                "period": "monthly", "mean": v.get("mean"), "median": v.get("median"),
                "p10": None, "p25": None, "p75": None, "p90": None, "count": None,
                "source_name": d["source_name"], "source_url": d["source"], "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        data = _slice(sex)
        labels = _codes(lang)
        rows = [{"occ_code": c, "occ_name": n, "mean": (data.get(c) or {}).get("mean"),
                 "median": (data.get(c) or {}).get("median"), "count": None}
                for c, n in labels.items() if c in data]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
