"""Germany provider — Destatis GENESIS-Online, earnings by KldB 2010 occupation.

Reads the bundled snapshot germany_kldb.json.gz (built by build.py from GENESIS
table 62361-0030). Gross MONTHLY earnings (EUR, full-time, excl. special payments)
with the mean AND median per occupation × sex (total / men / women), across the
full KldB 2010 hierarchy (2 / 3 / 5-digit). Official EN + DE occupation names. A
single annual snapshot — no percentiles, region or trend in this table.

Data source: Statistisches Bundesamt (Destatis), GENESIS-Online; used under
Datenlizenz Deutschland – Namensnennung – Version 2.0.
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
_SEX = {"total", "men", "women"}


@st.cache_data(show_spinner=False)
def _load() -> dict:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def _codes(lang: str = "EN") -> dict[str, str]:
    codes = _load().get("codes", {})
    return codes.get(lang) or codes.get("EN") or next(iter(codes.values()), {})


def _leaves(lang: str = "EN") -> dict[str, str]:
    return {c: n for c, n in _codes(lang).items() if len(c) == 5}   # KldB Berufsgattung


def _slice(sex: str) -> dict:
    """{code: {mean, median}} for one sex."""
    d = _load()
    cols = d["stat_cols"]
    raw = d["stats"].get(sex if sex in _SEX else "total", {})
    return {code: dict(zip(cols, vals)) for code, vals in raw.items()}


class GermanyProvider(CountryProvider):
    def year(self) -> int:
        return int(_load()["year"])

    def occupations(self, lang="EN"):
        return _leaves(lang)

    def occupation_tree(self, lang="EN"):
        return dict(_codes(lang))

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="EN"):
        if not occ_codes:
            return model.empty_occ_stats()
        d = _load()
        data = _slice(sex)
        labels = _leaves(lang)
        yr = self.year()
        rows = []
        for occ in occ_codes:
            v = data.get(occ)
            if not v:
                continue
            rows.append({
                "country": "germany", "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, _codes(lang).get(occ, occ)),
                "occ_group": occ[:2], "dimension": "total", "dim_value": "total",
                "currency": "EUR", "period": "monthly",
                "mean": v.get("mean"), "median": v.get("median"),
                "p10": None, "p25": None, "p75": None, "p90": None, "count": None,
                "source_name": "Destatis · GENESIS 62361-0030", "source_url": d["source"],
                "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        data = _slice(sex)
        labels = _leaves(lang)
        rows = [{"occ_code": occ, "occ_name": name,
                 "mean": (data.get(occ) or {}).get("mean"),
                 "median": (data.get(occ) or {}).get("median"), "count": None}
                for occ, name in labels.items() if occ in data]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
