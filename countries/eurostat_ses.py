"""Shared Eurostat SES engine — powers the coarse-but-consistent EU beta countries.

Eurostat's Structure of Earnings Survey dataset earn_ses{YY}_21 ("Mean monthly
earnings by sex, age and occupation") gives MEAN gross MONTHLY earnings by ISCO-08
major group (1-digit, 9 groups) × sex, per country (geo), for the 4-yearly SES
editions 2006–2022 (→ a trend). Open API, no key. Coarse (major groups, mean only)
but uniform across the EU and multi-year — a solid beta tier.

One country module = a thin wrapper: build.py calls build_country(geo, path);
provider.py instantiates EurostatSESProvider(slug); config.py calls make_config(...).
"""
from __future__ import annotations

import datetime
import gzip
import json
import os

import pandas as pd
import requests
import streamlit as st

from core import model
from core.model import CountryConfig, Capabilities
from core.provider import CountryProvider

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)", "Accept": "application/json"}
_EDITIONS = {2006: "earn_ses06_21", 2010: "earn_ses10_21", 2014: "earn_ses14_21",
             2018: "earn_ses18_21", 2022: "earn_ses22_21"}
_SEX = {"T": "total", "M": "men", "F": "women"}
_ISCO = {
    "OC1": ("1", "Managers"), "OC2": ("2", "Professionals"),
    "OC3": ("3", "Technicians and associate professionals"),
    "OC4": ("4", "Clerical support workers"), "OC5": ("5", "Service and sales workers"),
    "OC6": ("6", "Skilled agricultural, forestry and fishery workers"),
    "OC7": ("7", "Craft and related trades workers"),
    "OC8": ("8", "Plant and machine operators, and assemblers"),
    "OC9": ("9", "Elementary occupations"),
}
STAT_COLS = ["mean"]


# ── build ─────────────────────────────────────────────────────────────────────
def _fetch(geo: str, ds: str):
    """Returns (json, currency_dim_key). Newer editions use the `unit` dimension,
    older ones (≤2014) use `currency` — try unit first, fall back to currency."""
    base = {"format": "JSON", "geo": geo, "age": "TOTAL", "indic_se": "ERN",
            "sex": ["T", "M", "F"]}
    for key in ("unit", "currency"):
        r = requests.get(f"{_BASE}/{ds}", headers=_UA, timeout=120, verify=False,
                         params={**base, key: "EUR"})
        if r.status_code == 200:
            js = r.json()
            if key in js.get("dimension", {}):
                return js, key
    return None, None


def _cell(js, sel):
    ids, sizes, vals = js["id"], js["size"], js["value"]
    dims = js["dimension"]
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]
    try:
        flat = sum(dims[d]["category"]["index"][sel[d]] * strides[ids.index(d)]
                   for d in ids if d in sel)
    except KeyError:
        return None
    # values come as a dict keyed by flat index (sparse) or a list
    if isinstance(vals, dict):
        return vals.get(str(flat))
    return vals[flat] if 0 <= flat < len(vals) else None


def build_country(geo: str, out_path: str, log=print) -> dict:
    stats: dict = {}
    for year, ds in _EDITIONS.items():
        js, ukey = _fetch(geo, ds)
        if not js:
            continue
        ysm = {}
        for scode, sx in _SEX.items():
            occ_map = {}
            for oc, (code, _name) in _ISCO.items():
                v = None
                for sc in ("TOTAL", "GE10"):     # some countries only report GE10
                    sel = {"geo": geo, "time": str(year), "age": "TOTAL", "indic_se": "ERN",
                           ukey: "EUR", "sizeclas": sc, "sex": scode, "isco08": oc, "freq": "A"}
                    v = _cell(js, sel)
                    if v is not None:
                        break
                if v is not None:
                    occ_map[code] = [int(round(float(v)))]
            if occ_map:
                ysm[sx] = occ_map
        if ysm:
            stats[str(year)] = ysm
    years = sorted(int(y) for y in stats)
    latest = max(years) if years else 2022
    codes_en = {c: n for c, n in _ISCO.values()}
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": f"https://ec.europa.eu/eurostat/databrowser/view/{_EDITIONS[latest]}/default/table?lang=en",
        "source_name": "Eurostat — Structure of Earnings Survey (earn_ses_21)",
        "classification": "ISCO-08 major groups (Eurostat SES)",
        "note": "Mean gross MONTHLY earnings (EUR) by ISCO-08 major group × sex; "
                "4-yearly SES editions 2006–2022 (EUR, comparable across years).",
        "years": years, "year": latest, "geo": geo,
        "stat_cols": STAT_COLS, "sexes": ["total", "women", "men"],
        "codes": {"EN": codes_en}, "stats": stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"[{geo}] wrote {len(codes_en)} ISCO majors, {len(years)} years "
        f"({years[0] if years else '?'}–{latest}), {size} bytes")
    return {"built_at": payload["built_at"], "year": latest, "years": years,
            "codes": len(codes_en), "leaves": len(codes_en), "geo": geo, "size": size}


def leaves(slug: str, lang="EN") -> dict:
    """Occupation code→name map for a built country (used by the admin card)."""
    try:
        with gzip.open(os.path.join(_ROOT, f"{slug}_earnings.json.gz"), "rt", encoding="utf-8") as f:
            return json.load(f).get("codes", {}).get("EN", {})
    except Exception:
        return {c: n for c, n in _ISCO.values()}


def bundled_info(path: str) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
        return {"built_at": d.get("built_at"), "year": d.get("year"),
                "years": d.get("years"), "size": os.path.getsize(path),
                "source": d.get("source")}
    except Exception:
        return {}


# ── provider ──────────────────────────────────────────────────────────────────
class EurostatSESProvider(CountryProvider):
    """Generic provider over a <slug>_earnings.json.gz built by build_country()."""

    def __init__(self, slug: str, currency: str):
        self.slug = slug
        self.currency = currency
        self._path = os.path.join(_ROOT, f"{slug}_earnings.json.gz")

    def _load(self) -> dict:
        @st.cache_data(show_spinner=False)
        def _rd(path):
            with gzip.open(path, "rt", encoding="utf-8") as f:
                return json.load(f)
        return _rd(self._path)

    def _codes(self, lang="EN"):
        return self._load().get("codes", {}).get("EN", {})

    def _slice(self, year, sex):
        d = self._load()
        cols = d["stat_cols"]
        raw = d["stats"].get(str(year), {}).get(sex if sex in _SEX.values() else "total", {})
        return {c: dict(zip(cols, v)) for c, v in raw.items()}

    def latest_year(self):
        return int(self._load()["year"])

    def occupations(self, lang="EN"):
        return dict(self._codes(lang))

    def occupation_tree(self, lang="EN"):
        return dict(self._codes(lang))

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="EN"):
        if not occ_codes:
            return model.empty_occ_stats()
        yr = int(year or (max(years) if years else self.latest_year()))
        data = self._slice(yr, sex)
        labels = self._codes(lang)
        d = self._load()
        rows = []
        for occ in occ_codes:
            v = data.get(occ)
            if not v:
                continue
            rows.append({
                "country": self.slug, "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, occ), "occ_group": occ,
                "dimension": "total", "dim_value": "total", "currency": self.currency,
                "period": "monthly", "mean": v.get("mean"), "median": None,
                "p10": None, "p25": None, "p75": None, "p90": None, "count": None,
                "source_name": d["source_name"], "source_url": d["source"], "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def trend(self, *, sector="", occ_codes=(), sex="total", years=(),
              lang="EN", measure="mean"):
        if not occ_codes or not years:
            return model.empty_trend()
        labels = self._codes(lang)
        allyears = set(self._load().get("years", []))
        rows = []
        for y in years:
            if int(y) not in allyears:
                continue
            data = self._slice(int(y), sex)
            for occ in occ_codes:
                v = data.get(occ)
                rows.append({"country": self.slug, "year": int(y),
                             "series": labels.get(occ, occ), "sex": sex,
                             "value_nominal": v.get("mean") if v else None, "value_real": None})
        return pd.DataFrame(rows, columns=model.TREND_COLS)

    def leaderboard(self, *, sector="", sex="total", year=None, lang="EN"):
        yr = int(year or self.latest_year())
        data = self._slice(yr, sex)
        labels = self._codes(lang)
        rows = [{"occ_code": c, "occ_name": n, "mean": (data.get(c) or {}).get("mean"),
                 "median": None, "count": None}
                for c, n in labels.items() if c in data]
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])


# ── config factory ────────────────────────────────────────────────────────────
def make_config(*, slug, name, native, iso, currency, currency_suffix,
                money_prefix=False, years) -> CountryConfig:
    prov = EurostatSESProvider(slug, currency)
    yr = max(years) if years else 2022
    cap = f"Eurostat SES · Mean earnings by occupation (ISCO major groups) · monthly, {currency}"
    guide = {
        "title": f"How to use the {name} Salary Explorer",
        "source": f"Eurostat — Structure of Earnings Survey · {yr}",
        "intro": f"Look up {name} earnings by broad occupation group — harmonised "
                 "EU data from Eurostat's Structure of Earnings Survey.",
        "steps_title": "Getting started",
        "steps": [("Search", "Pick one or more occupation groups in the sidebar, "
                             "then press the blue Search button."),
                  ("Read the results", "Explore the tabs — including the trend and By gender.")],
        "find_title": "Finding the right occupation",
        "find": [("Occupations", "The data covers the 9 ISCO-08 major groups.")],
        "charts_title": "Reading the figures",
        "charts_intro": "Figures are the MEAN gross monthly earnings per occupation group:",
        "pcts": [("MEAN", 52, "average earnings")],
        "notes_title": "Good to know",
        "notes": [f"Figures are MEAN gross MONTHLY earnings ({currency}) by ISCO-08 "
                  "major group — Eurostat's harmonised EU survey (coarse but comparable).",
                  "The trend covers the 4-yearly SES editions (2006–2022); the "
                  "By-gender tab splits women vs men."],
        "tabs_title": "The tabs",
        "tabs": [("Overview", "Mean earnings at a glance."),
                 ("Salary distribution", "The 2006→ trend + a forward projection."),
                 ("Leaderboard", "Ranks the occupation groups by pay."),
                 ("By gender", "Women vs men.")],
        "footer": "Data from Eurostat's Structure of Earnings Survey (earn_ses_21).",
    }
    return CountryConfig(
        slug=slug, name=name, native=native, iso=iso,
        eyebrow=f"OFFICIAL STATISTICS · {name.upper()}",
        source_name="Eurostat — Structure of Earnings Survey",
        source_url="https://ec.europa.eu/eurostat/web/labour-market/earnings",
        caption=cap, currency=currency, currency_suffix=currency_suffix,
        money_prefix=money_prefix, period="monthly",
        capabilities=Capabilities(
            has_occupation_hierarchy=False, has_mean=True, has_median=False,
            has_sex=True, has_trend=True, has_leaderboard=True, leaderboard_scope=1,
            sectors=(), year_range=(min(years), max(years)) if years else (2006, 2022),
        ),
        tabs=("overview", "distribution", "leaderboard", "sex"),
        access="restricted", fetch_mode="search", landing=True,
        classification="ISCO-08 major groups (Eurostat SES)",
        bullets=(
            "Mean earnings & gender split · 9 ISCO-08 major groups",
            "Harmonised EU survey · 2006–2022 trend",
            f"Gross monthly earnings · Eurostat SES · {yr}",
        ),
        labels={"badge": "Beta", "source_short": "Eurostat SES · official"},
        languages=(("EN", "English"),),
        i18n={"EN": {"title": f"{name} Salary Explorer", "caption": cap}},
        guide={"EN": guide},
        provider=prov,
    )
