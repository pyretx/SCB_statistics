"""Germany provider — Destatis Verdiensterhebung, earnings by KldB 2010 occupation.

Reads the bundled snapshot germany_kldb.json.gz (built by build.py from the public
Destatis statistical report; the GENESIS API needs an account, the report XLSX does
not). Gross MONTHLY earnings (EUR, full-time, excl. special payments) with the mean
AND median per occupation, across the full KldB 2010 hierarchy (2 / 3 / 5-digit).
A single annual snapshot — no sex, percentiles, region or trend in this release.

Occupation names are the official German KldB 2010 titles (Destatis publishes no
English names for this table).
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
_DATA = os.path.join(_ROOT, "germany_kldb.json.gz")


@st.cache_data(show_spinner=False)
def _load() -> dict:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def _codes(lang: str = "DE") -> dict[str, str]:
    codes = _load().get("codes", {})
    return codes.get("DE") or next(iter(codes.values()), {})   # names are German


def _leaves(lang: str = "DE") -> dict[str, str]:
    return {c: n for c, n in _codes(lang).items() if len(c) == 5}   # KldB Berufsgattung


class GermanyProvider(CountryProvider):
    def year(self) -> int:
        return int(_load()["year"])

    def occupations(self, lang="DE"):
        return _leaves(lang)

    def occupation_tree(self, lang="DE"):
        return dict(_codes(lang))

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="DE"):
        if not occ_codes:
            return model.empty_occ_stats()
        d = _load()
        cols = d["stat_cols"]
        stats = d["stats"]
        labels = _leaves(lang)
        yr = self.year()
        rows = []
        for occ in occ_codes:
            if occ not in stats:
                continue
            v = dict(zip(cols, stats[occ]))
            rows.append({
                "country": "germany", "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, _codes(lang).get(occ, occ)),
                "occ_group": occ[:2], "dimension": "total", "dim_value": "total",
                "currency": "EUR", "period": "monthly",
                "mean": v.get("mean"), "median": v.get("median"),
                "p10": None, "p25": None, "p75": None, "p90": None, "count": None,
                "source_name": "Destatis (Verdiensterhebung)", "source_url": d["source"],
                "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="DE"):
        d = _load()
        cols = d["stat_cols"]
        stats = d["stats"]
        labels = _leaves(lang)
        rows = [{"occ_code": occ, "occ_name": name,
                 "mean": dict(zip(cols, stats[occ])).get("mean"),
                 "median": dict(zip(cols, stats[occ])).get("median"), "count": None}
                for occ, name in labels.items() if occ in stats]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
