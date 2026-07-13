"""Brazil provider — IBGE PNAD Contínua (table 9457).

Reads the bundled snapshot brazil_earnings.json.gz. Estimated gross MONTHLY
earnings (average hourly × a standard full-time month) by the 10 ISCO major
occupational groups, with a 2012→ trend. Average only — no median, percentiles,
sex or region in this series. EN + PT occupation names.
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
_DATA = os.path.join(_ROOT, "brazil_earnings.json.gz")


@st.cache_data(show_spinner=False)
def _load() -> dict:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def _codes(lang="EN") -> dict:
    codes = _load().get("codes", {})
    return codes.get(lang) or codes.get("EN", {})


def _slice(year: int) -> dict:
    d = _load()
    cols = d["stat_cols"]
    raw = d["stats"].get(str(year), {})
    return {c: dict(zip(cols, v)) for c, v in raw.items()}


class BrazilProvider(CountryProvider):
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
        data = _slice(yr)
        labels = _codes(lang)
        d = _load()
        rows = []
        for occ in occ_codes:
            v = data.get(occ)
            if not v:
                continue
            rows.append({
                "country": "brazil", "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, occ), "occ_group": occ,
                "dimension": "total", "dim_value": "total", "currency": "BRL",
                "period": "monthly", "mean": v.get("mean"), "median": None,
                "p10": None, "p25": None, "p75": None, "p90": None, "count": None,
                "source_name": d["source_name"], "source_url": d["source"], "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def trend(self, *, sector="", occ_codes=(), sex="total", years=(),
              lang="EN", measure="mean"):
        if not occ_codes or not years:
            return model.empty_trend()
        labels = _codes(lang)
        allyears = set(_load().get("years", []))
        rows = []
        for y in years:
            if int(y) not in allyears:
                continue
            data = _slice(int(y))
            for occ in occ_codes:
                v = data.get(occ)
                rows.append({"country": "brazil", "year": int(y),
                             "series": labels.get(occ, occ), "sex": "total",
                             "value_nominal": v.get("mean") if v else None, "value_real": None})
        return pd.DataFrame(rows, columns=model.TREND_COLS)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        data = _slice(int(year or self.year()))
        labels = _codes(lang)
        rows = [{"occ_code": c, "occ_name": n, "mean": (data.get(c) or {}).get("mean"),
                 "median": None, "count": None}
                for c, n in labels.items() if c in data]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
