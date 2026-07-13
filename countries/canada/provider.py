"""Canada provider — Statistics Canada 14-10-0417 (employee wages by occupation).

Reads the bundled snapshot canada_wages.json.gz (built offline from StatCan's open
WDS full-table CSV). Average + median gross MONTHLY wages (weekly × 52/12) by NOC
occupation × gender, with the 10 provinces as REAL region data (has_region_data →
By-region tab, like the US states). Full-time employees, age 15+, latest year. No
percentiles/trend in this cut.
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
_DATA = os.path.join(_ROOT, "canada_wages.json.gz")
_SEX = {"total", "men", "women"}


@st.cache_data(show_spinner=False)
def _load() -> dict:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def _codes(lang: str = "EN") -> dict[str, str]:
    codes = _load().get("codes", {})
    return codes.get(lang) or codes.get("EN", {})


def _leaves(lang: str = "EN") -> dict[str, str]:
    codes = _codes(lang)
    return {c: n for c, n in codes.items()
            if not any(o != c and o.startswith(c) for o in codes)}   # prefix leaves


def _slice(scope: str, sex: str) -> dict:
    d = _load()
    cols = d["stat_cols"]
    raw = d["stats"].get(scope or d["national"], {}).get(sex if sex in _SEX else "total", {})
    return {c: dict(zip(cols, v)) for c, v in raw.items()}


class CanadaProvider(CountryProvider):
    def year(self) -> int:
        return int(_load()["year"])

    def occupations(self, lang="EN"):
        return _leaves(lang)

    def occupation_tree(self, lang="EN"):
        return dict(_codes(lang))

    def regions(self) -> dict:
        return dict(_load().get("regions", {}))

    def region_choices(self, lang="EN"):
        d = _load()
        nat = d["national"]
        return sorted(((c, n) for c, n in d["regions"].items() if c != nat),
                      key=lambda cn: cn[1])

    def region_national_code(self) -> str:
        return _load()["national"]

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="EN"):
        if not occ_codes:
            return model.empty_occ_stats()
        d = _load()
        data = _slice(sector or d["national"], sex)
        labels = _codes(lang)
        yr = self.year()
        rows = []
        for occ in occ_codes:
            v = data.get(occ)
            if not v:
                continue
            rows.append({
                "country": "canada", "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, occ), "occ_group": occ[:2],
                "dimension": "total", "dim_value": "total", "currency": "CAD",
                "period": "monthly", "mean": v.get("mean"), "median": v.get("median"),
                "p10": None, "p25": None, "p75": None, "p90": None, "count": None,
                "source_name": d["source_name"], "source_url": d["source"], "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        d = _load()
        data = _slice(sector or d["national"], sex)
        labels = _leaves(lang)
        rows = [{"occ_code": c, "occ_name": n, "mean": (data.get(c) or {}).get("mean"),
                 "median": (data.get(c) or {}).get("median"), "count": None}
                for c, n in labels.items() if c in data]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
