"""US provider — BLS OEWS national + state wages by SOC occupation.

Reads the bundled snapshot us_oews.json.gz (built by build_us_oews.py); no live
API — OEWS is one annual release, parsed offline (like France's data). Full
P10–P90 + mean + employment per occupation.

The framework's 'sector' filter slot carries the SCOPE here — US national, a
state, or a nationwide NAICS industry ("IND"+naics). These are mutually
exclusive (OEWS has no state × industry), so they share one selector. SOC codes
are keyed by their significant prefix so the prefix drill-down works (see
build_us_oews.py).
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
_DATA = os.path.join(_ROOT, "us_oews.json.gz")


@st.cache_data(show_spinner=False)
def _load() -> dict:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def _codes(lang: str = "EN") -> dict:
    codes = _load().get("codes", {})
    return codes.get(lang) or codes.get("EN", {})


def _leaves(lang: str = "EN") -> dict:
    return {c: n for c, n in _codes(lang).items() if len(c) == 7}   # detailed SOC


class UsProvider(CountryProvider):
    def occupations(self, lang: str = "EN") -> dict[str, str]:
        return _leaves(lang)

    def occupation_tree(self, lang: str = "EN") -> dict[str, str]:
        return dict(_codes(lang))

    def regions(self) -> dict[str, str]:
        return dict(_load().get("regions", {}))

    def _rows(self, region: str, occ_codes, lang: str) -> pd.DataFrame:
        d = _load()
        cols = d["stat_cols"]                       # [mean, median, p10, p25, p75, p90, count]
        rstats = d["stats"].get(region or "US", {})
        labels = _leaves(lang)
        rows = []
        for occ in occ_codes:
            v = dict(zip(cols, rstats[occ])) if occ in rstats else {}
            rows.append({
                "country": "us", "year": d["year"], "occ_code": occ,
                "occ_name": labels.get(occ, occ), "occ_group": occ[:2],
                "dimension": "total", "dim_value": "total", "currency": "USD", "period": "annual",
                "mean": v.get("mean"), "median": v.get("median"),
                "p10": v.get("p10"), "p25": v.get("p25"), "p75": v.get("p75"), "p90": v.get("p90"),
                "count": v.get("count"),
                "source_name": "BLS OEWS", "source_url": d["source"], "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def occupation_stats(self, *, sector="US", occ_codes=(), sex="total",
                         years=(), dimension="total", year=None, lang="EN") -> pd.DataFrame:
        # OEWS is a single national/state annual snapshot → sex/year are ignored.
        return self._rows(sector or "US", tuple(occ_codes), lang)

    def leaderboard(self, *, sector="US", sex="total", year=None, lang="EN") -> pd.DataFrame:
        d = _load()
        cols = d["stat_cols"]
        rstats = d["stats"].get(sector or "US", {})
        labels = _leaves(lang)
        rows = [{"occ_code": occ, "occ_name": labels.get(occ, occ),
                 "mean": dict(zip(cols, vals)).get("mean"),
                 "median": dict(zip(cols, vals)).get("median"),
                 "count": dict(zip(cols, vals)).get("count")}
                for occ, vals in rstats.items()]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
