"""UK provider — ONS ASHE Table 14 (occupation, 4-digit SOC 2020).

Reads the bundled snapshot uk_ashe.json.gz (built by build.py from the official
ONS workbooks; ONS publishes occupation earnings only as spreadsheets, no API).
Full P10·P25·median·P75·P90 + mean + jobs, by SOC occupation × sex × year, so the
UK gets the richest set of tabs: distribution, By-gender, a 4-year trend (with a
CPIH real-terms overlay), leaderboard and the salary calculator.

Figures are GROSS MONTHLY pay = official gross ANNUAL pay ÷ 12 (see build.py), so
the UK is directly comparable with the app's other monthly countries.
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
_DATA = os.path.join(_ROOT, "uk_ashe.json.gz")
_SEX = {"total", "men", "women"}


@st.cache_data(show_spinner=False)
def _load() -> dict:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def _codes(lang: str = "EN") -> dict[str, str]:
    codes = _load().get("codes", {})
    return codes.get(lang) or codes.get("EN", {})


def _leaves(lang: str = "EN") -> dict[str, str]:
    return {c: n for c, n in _codes(lang).items() if len(c) == 4}   # SOC unit groups


def _slice(year: int, sex: str) -> dict:
    """{code: {measure: value}} for one year × sex."""
    d = _load()
    cols = d["stat_cols"]
    raw = d["stats"].get(str(year), {}).get(sex if sex in _SEX else "total", {})
    return {code: dict(zip(cols, vals)) for code, vals in raw.items()}


class UkProvider(CountryProvider):
    def latest_year(self) -> int:
        return int(_load()["latest_year"])

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
        labels = _leaves(lang)
        src = _load()["source"]
        rows = []
        for occ in occ_codes:
            v = data.get(occ)
            if not v:
                continue
            rows.append({
                "country": "uk", "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, _codes(lang).get(occ, occ)),
                "occ_group": occ[:1], "dimension": "total", "dim_value": "total",
                "currency": "GBP", "period": "monthly",
                "mean": v.get("mean"), "median": v.get("median"),
                "p10": v.get("p10"), "p25": v.get("p25"),
                "p75": v.get("p75"), "p90": v.get("p90"), "count": v.get("count"),
                "source_name": "ONS ASHE (Table 14)", "source_url": src, "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def trend(self, *, sector="", occ_codes=(), sex="total", years=(),
              lang="EN", measure="median"):
        if not occ_codes or not years:
            return model.empty_trend()
        m = measure if measure in ("median", "mean", "p10", "p25", "p75", "p90") else "median"
        labels = _leaves(lang)
        allyears = _load().get("years", [])
        rows = []
        for y in years:
            if int(y) not in allyears:
                continue
            data = _slice(int(y), sex)
            for occ in occ_codes:
                v = data.get(occ)
                rows.append({"country": "uk", "year": int(y),
                             "series": labels.get(occ, _codes(lang).get(occ, occ)),
                             "sex": sex,
                             "value_nominal": v.get(m) if v else None, "value_real": None})
        return pd.DataFrame(rows, columns=model.TREND_COLS)

    def cpi_annual(self, years=()):
        return {int(y): float(v) for y, v in _load().get("cpi", {}).items()}

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        yr = int(year or self.latest_year())
        data = _slice(yr, sex)
        labels = _leaves(lang)
        rows = [{"occ_code": occ, "occ_name": name,
                 "mean": (data.get(occ) or {}).get("mean"),
                 "median": (data.get(occ) or {}).get("median"),
                 "count": (data.get(occ) or {}).get("count")}
                for occ, name in labels.items() if occ in data]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
