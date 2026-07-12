"""Finland data provider — Statistics Finland (StatFin) Structure of Earnings.

Table 15au: monthly earnings by ISCO occupation × sector × sex, an annual
SNAPSHOT (one year). Measures: mean / 1st decile (P10) / median / 9th decile
(P90) / count — so Finland shows P10·median·P90 (richer than quartiles, but no
P25/P75, and no trend). Table 15b2 (earnings by region) powers the region
simulation. Total earnings ('kokonaisansio', 'kans') in EUR per month.

StatFin variable codes are versioned (ammatti_19_20180101) and the API rate-
limits, so codes are resolved by prefix and every call is disk-cached.
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd
import requests
import streamlit as st

from core import model
from core.provider import CountryProvider

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LABELS_FILE = os.path.join(_ROOT, "finland_labels.json")
OCC_URL = "https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin/pra/15au.px"
REGION_URL = "https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin/pra/15b2.px"

SECTOR_CODE = {"all": "S0", "private": "S11_S12_S15", "central": "S13111",
               "local": "S13131", "wellbeing": "S13132"}
SEX_CODE = {"total": "SSS", "men": "1", "women": "2"}
# contentscode → normalized column (total earnings, EUR/month)
_MEASURE = {"mean": "koko_psaaja_kans_ka", "p10": "koko_psaaja_kans_p10",
            "median": "koko_psaaja_kans_med", "p90": "koko_psaaja_kans_p90",
            "count": "koko_psaaja_lkm"}
_MEASURE_COL = {v: k for k, v in _MEASURE.items()}


def _post(url, query, tries=5):
    r = None
    for i in range(tries):
        r = requests.post(url, json=query, timeout=120)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504) and i < tries - 1:
            time.sleep(2.5 * (i + 1))
            continue
        break
    r.raise_for_status()
    return {}


@st.cache_data(show_spinner=False, persist="disk")
def _meta(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def _vcodes(url):
    return {v["code"].split("_")[0]: v["code"] for v in _meta(url)["variables"]}


@st.cache_data(show_spinner=False)
def _codes(lang="EN"):
    try:
        with open(_LABELS_FILE, encoding="utf-8") as f:
            codes = json.load(f).get("codes", {})
        return codes.get(lang) or codes.get("EN", {})
    except Exception:
        return {}


def _leaves(lang="EN"):
    return {c: n for c, n in _codes(lang).items() if len(c) == 4}


def _content_dim(ds):
    return [d for d in ds["id"] if d.lower().startswith("content")][0]


def _flat(ds):
    ids, sizes, values = ds["id"], ds["size"], ds["value"]
    dims = ds["dimension"]
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    def val(sel):
        try:
            flat = sum(dims[d]["category"]["index"][sel[d]] * strides[ids.index(d)] for d in ids)
        except KeyError:
            return None
        return values[flat] if 0 <= flat < len(values) else None
    return dims, val


@st.cache_data(show_spinner=False, persist="disk")
def _fetch(sector, occ_codes, sex, year, lang="EN"):
    if not occ_codes:
        return model.empty_occ_stats()
    vc = _vcodes(OCC_URL)
    amm, sek, suk = vc["ammatti"], vc["sektoriluokitus"], vc["sukupuoli"]
    ds = _post(OCC_URL, {"query": [
        {"code": amm, "selection": {"filter": "item", "values": list(occ_codes)}},
        {"code": sek, "selection": {"filter": "item", "values": [SECTOR_CODE.get(sector, "S0")]}},
        {"code": suk, "selection": {"filter": "item", "values": [SEX_CODE.get(sex, "SSS")]}},
        {"code": "contentscode", "selection": {"filter": "item", "values": list(_MEASURE.values())}},
        {"code": "timeperiod_y", "selection": {"filter": "item", "values": [str(year)]}},
    ], "response": {"format": "json-stat2"}})
    dims, val = _flat(ds)
    cdim = _content_dim(ds)
    tdim = [d for d in ds["id"] if d not in (amm, sek, suk, cdim)][0]   # time dim
    tval = list(dims[tdim]["category"]["index"])[0]
    labels = _leaves(lang)
    rows = []
    for occ in occ_codes:
        if occ not in dims[amm]["category"]["index"]:
            continue

        def m(mc):
            return val({amm: occ, sek: SECTOR_CODE.get(sector, "S0"),
                        suk: SEX_CODE.get(sex, "SSS"), cdim: mc, tdim: tval})
        rows.append({
            "country": "finland", "year": int(year), "occ_code": occ,
            "occ_name": labels.get(occ, _codes(lang).get(occ, occ)),
            "occ_group": occ[:2], "dimension": "total", "dim_value": "total",
            "currency": "EUR", "period": "monthly",
            "mean": m(_MEASURE["mean"]), "median": m(_MEASURE["median"]),
            "p10": m(_MEASURE["p10"]), "p25": None, "p75": None,
            "p90": m(_MEASURE["p90"]), "count": m(_MEASURE["count"]),
            "source_name": "Statistics Finland (StatFin)", "source_url": OCC_URL, "notes": "",
        })
    return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_leaderboard(sector, sex, year, lang="EN"):
    leaves = _leaves(lang)
    if not leaves:
        return pd.DataFrame(columns=["occ_code", "occ_name", "mean", "median", "count"])
    vc = _vcodes(OCC_URL)
    amm, sek, suk = vc["ammatti"], vc["sektoriluokitus"], vc["sukupuoli"]
    ds = _post(OCC_URL, {"query": [
        {"code": amm, "selection": {"filter": "all", "values": ["*"]}},
        {"code": sek, "selection": {"filter": "item", "values": [SECTOR_CODE.get(sector, "S0")]}},
        {"code": suk, "selection": {"filter": "item", "values": [SEX_CODE.get(sex, "SSS")]}},
        {"code": "contentscode", "selection": {"filter": "item", "values": [
            _MEASURE["mean"], _MEASURE["median"], _MEASURE["count"]]}},
        {"code": "timeperiod_y", "selection": {"filter": "item", "values": [str(year)]}},
    ], "response": {"format": "json-stat2"}})
    dims, val = _flat(ds)
    cdim = _content_dim(ds)
    tdim = [d for d in ds["id"] if d not in (amm, sek, suk, cdim)][0]
    tval = list(dims[tdim]["category"]["index"])[0]
    idx = dims[amm]["category"]["index"]
    rows = []
    for occ, name in leaves.items():
        if occ not in idx:
            continue

        def m(mc):
            return val({amm: occ, sek: SECTOR_CODE.get(sector, "S0"),
                        suk: SEX_CODE.get(sex, "SSS"), cdim: mc, tdim: tval})
        rows.append({"occ_code": occ, "occ_name": name, "mean": m(_MEASURE["mean"]),
                     "median": m(_MEASURE["median"]), "count": m(_MEASURE["count"])})
    return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])


@st.cache_data(show_spinner=False, persist="disk")
def _region_factors(year):
    """{region_name: factor vs national} from 15b2 median monthly earnings, all
    occupations pooled. National ('SSS' whole country) excluded (baseline 1.0)."""
    vc = _vcodes(REGION_URL)
    alue, sek, suk = vc["alue"], vc["sektoriluokitus"], vc["sukupuoli"]
    ds = _post(REGION_URL, {"query": [
        {"code": alue, "selection": {"filter": "all", "values": ["*"]}},
        {"code": sek, "selection": {"filter": "item", "values": ["S0"]}},
        {"code": suk, "selection": {"filter": "item", "values": ["SSS"]}},
        {"code": "contentscode", "selection": {"filter": "item", "values": [_MEASURE["median"]]}},
        {"code": "timeperiod_y", "selection": {"filter": "item", "values": [str(year)]}},
    ], "response": {"format": "json-stat2"}})
    cat = ds["dimension"][alue]["category"]
    idx, lbl, vals = cat["index"], cat["label"], ds["value"]
    nat = vals[idx["SSS"]] if "SSS" in idx else None
    if not nat:
        return {}
    out = {}
    for code, i in idx.items():
        if code == "SSS" or vals[i] is None:
            continue
        name = lbl.get(code, code)
        # labels look like "MK01 Uusimaa" — strip the leading region code
        if len(name) > 3 and name[:2] == "MK" and " " in name:
            name = name.split(None, 1)[1].strip()
        if any(w in name.lower() for w in ("unknown", "tuntematon", "okänd", "okand")):
            continue                            # drop the 'region unknown' catch-all
        out[name] = vals[i] / nat
    return out


class FinlandProvider(CountryProvider):
    def occupations(self, lang="EN"):
        return _leaves(lang)

    def occupation_tree(self, lang="EN"):
        return dict(_codes(lang))

    def occupation_stats(self, *, sector="all", occ_codes=(), sex="total", years=(),
                         dimension="total", year=None, lang="EN"):
        from .build import latest_year
        yr = int(year or (years[-1] if years else latest_year()))
        return _fetch(sector, tuple(occ_codes), sex, yr, lang)

    def leaderboard(self, *, sector="all", sex="total", year=None, lang="EN"):
        from .build import latest_year
        return _fetch_leaderboard(sector, sex, int(year or latest_year()), lang)

    def region_sim(self, *, year=None, lang="EN"):
        from .build import latest_year
        yr = int(year or latest_year())
        regions = _region_factors(yr) or _region_factors(yr - 1)
        if not regions:
            return {}
        basis = (f"mediaanikuukausiansio, kaikki ammatit, {yr}" if lang == "FI"
                 else f"median monthly earnings, all occupations, {yr}")
        return {"regions": regions, "basis": basis}
