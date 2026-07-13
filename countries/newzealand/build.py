"""Stats NZ Aotearoa Data Explorer (ADE) SDMX API → bundled New Zealand snapshot.

Dataflow INC_INC_004 "Earnings from main wage and salary job by occupation
(ANZSCO), sex, age" — median + average WEEKLY earnings by ANZSCO major-group
occupation × sex × age × ethnicity × year (2009→). We fetch the all-ages /
all-ethnicities total slice at build time (needs the ADE subscription key) and
ship a compact snapshot; the provider reads it at runtime (no key on the hot
path).

Base: https://apis.stats.govt.nz/ade-api/rest/v2/ (agency STATSNZ). Auth: header
Ocp-Apim-Subscription-Key. Figures are gross MONTHLY = WEEKLY × 52/12.
"""
from __future__ import annotations

import datetime
import gzip
import json
import os
import time

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "newzealand_earnings.json.gz")
BASE = "https://apis.stats.govt.nz/ade-api/rest/v2/"
FLOW = "STATSNZ/INC_INC_004/1.0"
SOURCE_URL = "https://explore.data.stats.govt.nz/vis?fs[0]=INC_INC_004"
STAT_COLS = ["mean", "median"]
_WEEK_TO_MONTH = 52 / 12
_SEX = {"1": "men", "2": "women", "98": "total"}
_MEASURE = {"AV_WEEK_INC": "mean", "MED_WEEK_INC": "median"}
DEFAULT_LATEST_YEAR = 2025


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("newzealand_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def _token() -> str:
    try:
        import streamlit as st
        t = (st.secrets.get("statsnz", {}) or {}).get("api_key")
        if t:
            return t
    except Exception:
        pass
    import tomllib
    for p in (os.path.join(_ROOT, ".streamlit", "secrets.toml"), "/root/scb-secrets.toml"):
        try:
            with open(p, "rb") as f:
                t = (tomllib.load(f).get("statsnz", {}) or {}).get("api_key")
                if t:
                    return t
        except Exception:
            pass
    return os.environ.get("STATSNZ_API_KEY", "")


def _fetch() -> dict:
    token = _token()
    if not token:
        raise RuntimeError("Stats NZ token missing ([statsnz] api_key in secrets.toml)")
    H = {"Ocp-Apim-Subscription-Key": token, "User-Agent": "Mozilla/5.0",
         "Accept": "application/vnd.sdmx.data+json;version=1.0"}
    url = (BASE + f"data/dataflow/{FLOW}/*.*.*.*.*.*"
           "?c[MEASURE_INC_INC_004]=AV_WEEK_INC,MED_WEEK_INC")
    last = None
    for _ in range(6):
        r = requests.get(url, headers=H, timeout=120)
        if r.status_code == 200 and r.text.strip().startswith("{"):
            return r.json()
        last = f"{r.status_code} {r.text[:100]}"
        time.sleep(2)
    raise RuntimeError(f"Stats NZ data fetch failed: {last}")


def build(out_path: str = OUT, log=print) -> dict:
    log(f"fetching Stats NZ {FLOW} …")
    j = _fetch()
    d = j["data"]
    dims = d["structure"]["dimensions"]["observation"]
    dim_by_id = {dm["id"]: (i, dm["values"]) for i, dm in enumerate(dims)}

    def pos(idkey):
        return dim_by_id[[k for k in dim_by_id if k.startswith(idkey)][0]][0]

    p_period, p_occ, p_sex = pos("PERIOD"), pos("OCC2"), pos("SEX")
    p_age, p_eth, p_meas = pos("AGEGP"), pos("ETHGP"), pos("MEASURE")
    vals = {i: dm["values"] for i, dm in enumerate(dims)}

    def total_index(i, *needles):
        for k, v in enumerate(vals[i]):
            nm = (v.get("name", "") or "").lower()
            if any(nd in nm for nd in needles):
                return k
        return None
    age_tot = total_index(p_age, "total", "all age")
    eth_tot = total_index(p_eth, "total")

    # occupation names (exclude any 'total'), by value index
    occ_names, occ_is_total = {}, set()
    for k, v in enumerate(vals[p_occ]):
        nm = v.get("name", "") or ""
        occ_names[k] = (v.get("id"), nm)
        if "total" in nm.lower():
            occ_is_total.add(k)

    obs = d["dataSets"][0]["observations"]
    codes: dict[str, str] = {}
    stats: dict = {}          # {year: {sex: {occ: {mean/median}}}}
    for key, arr in obs.items():
        idx = [int(x) for x in key.split(":")]
        if idx[p_age] != age_tot or idx[p_eth] != eth_tot or idx[p_occ] in occ_is_total:
            continue
        measure = _MEASURE.get(vals[p_meas][idx[p_meas]].get("id"))
        sex = _SEX.get(vals[p_sex][idx[p_sex]].get("id"))
        if not measure or not sex:
            continue
        occ_id, occ_nm = occ_names[idx[p_occ]]
        codes[occ_id] = occ_nm
        year = int(str(vals[p_period][idx[p_period]].get("id"))[:4])
        val = arr[0]
        if val is None:
            continue
        stats.setdefault(str(year), {}).setdefault(sex, {}).setdefault(occ_id, {})[measure] = \
            int(round(float(val) * _WEEK_TO_MONTH))

    out_stats = {y: {s: {o: [d2.get(m) for m in STAT_COLS] for o, d2 in om.items()}
                     for s, om in sm.items()} for y, sm in stats.items()}
    years = sorted(int(y) for y in out_stats)
    latest = max(years) if years else DEFAULT_LATEST_YEAR
    retrieved = datetime.date.today().isoformat()
    payload = {
        "built_at": retrieved, "retrieved": retrieved, "source": SOURCE_URL,
        "source_name": "Stats NZ – Tatauranga Aotearoa (Aotearoa Data Explorer)",
        "classification": "ANZSCO major group (Stats NZ INC_INC_004)",
        "note": "Gross MONTHLY = median/average WEEKLY earnings × 52/12; wage & "
                "salary earners, all ages. Occupation = ANZSCO major group.",
        "years": years, "year": latest, "currency": "NZD",
        "stat_cols": STAT_COLS, "sexes": ["total", "men", "women"],
        "codes": {"EN": codes}, "stats": out_stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes)} occupations, {len(years)} years ({min(years)}–{latest}) "
        f"({size/1e6:.3f} MB)")
    return {"built_at": retrieved, "year": latest, "years": years,
            "codes": len(codes), "size": size}


def bundled_info(path: str = OUT) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            dd = json.load(f)
        return {"built_at": dd.get("built_at"), "year": dd.get("year"),
                "years": dd.get("years"), "size": os.path.getsize(path),
                "source": dd.get("source")}
    except Exception:
        return {}


if __name__ == "__main__":
    print(build())
