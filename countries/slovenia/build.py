"""SURS (Statistical Office of Slovenia) PxWeb table 0711335S → bundled snapshot.

Open PxWeb API (no key). "Average monthly earning (EUR) (SKP-08) by occupational
group, sex, year, earnings and measures" gives the FULL distribution — mean,
median, lower/upper quartile (P25/P75) and 10th/90th percentile — by SKP-08
(ISCO-08) occupation × sex × year (2011→). Gross, monthly EUR. We fetch it per
year (PxWeb cell limits) and ship a compact snapshot; the richest capability set
after the UK (percentiles + quartiles + mean + trend + sex + hierarchy).
"""
from __future__ import annotations

import datetime
import gzip
import json
import os
import time

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "slovenia_earnings.json.gz")
URL = "https://pxweb.stat.si/SiStatData/api/v1/en/Data/0711335S.px"
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}
STAT_COLS = ["mean", "median", "p10", "p25", "p75", "p90"]
_SEX = {"TOT": "total", "1": "men", "2": "women"}
_MEASURE = {"1": "mean", "2": "median", "3": "p25", "4": "p75", "5": "p10", "6": "p90"}
DEFAULT_LATEST_YEAR = 2022
_V_OCC, _V_SEX, _V_YEAR, _V_PAY, _V_MEAS = (
    "SKUPINA POKLICEV", "SPOL", "LETO", "PLAČA", "MERITVE")


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("slovenia_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def _meta():
    r = requests.get(URL, headers=_UA, timeout=60)
    r.raise_for_status()
    return r.json()


def _post(query):
    for i in range(5):
        r = requests.post(URL, json={"query": query, "response": {"format": "json-stat2"}},
                          headers=_UA, timeout=120)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503) and i < 4:
            time.sleep(2 * (i + 1))
            continue
        r.raise_for_status()
    return {}


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


def build(out_path: str = OUT, log=print) -> dict:
    meta = _meta()
    years = [v for v in next(x for x in meta["variables"] if x["code"] == _V_YEAR)["values"]]
    occs = next(x for x in meta["variables"] if x["code"] == _V_OCC)
    occ_codes = [c for c in occs["values"] if c != "TOT"]
    names = {c: t.split(None, 1)[1].strip() if " " in t else t
             for c, t in zip(occs["values"], occs["valueTexts"]) if c != "TOT"}

    stats: dict = {}
    for yr in years:
        log(f"fetching {yr} …")
        ds = _post([
            {"code": _V_OCC, "selection": {"filter": "item", "values": occ_codes}},
            {"code": _V_SEX, "selection": {"filter": "item", "values": ["TOT", "1", "2"]}},
            {"code": _V_YEAR, "selection": {"filter": "item", "values": [yr]}},
            {"code": _V_PAY, "selection": {"filter": "item", "values": ["1"]}},  # gross
            {"code": _V_MEAS, "selection": {"filter": "item", "values": list(_MEASURE)}},
        ])
        dims, val = _flat(ds)
        ysm = {}
        for scode, sx in _SEX.items():
            occ_map = {}
            for occ in occ_codes:
                vals = {}
                for mcode, mname in _MEASURE.items():
                    v = val({_V_OCC: occ, _V_SEX: scode, _V_YEAR: yr,
                             _V_PAY: "1", _V_MEAS: mcode})
                    vals[mname] = None if v is None else int(round(v))
                if any(v is not None for v in vals.values()):
                    occ_map[occ] = [vals.get(m) for m in STAT_COLS]
            if occ_map:
                ysm[sx] = occ_map
        stats[str(int(yr))] = ysm

    yrs_int = sorted(int(y) for y in stats)
    latest = max(yrs_int) if yrs_int else DEFAULT_LATEST_YEAR
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": "https://pxweb.stat.si/SiStatData/pxweb/en/Data/-/0711335S.px",
        "source_name": "Statistical Office of the Republic of Slovenia (SURS)",
        "classification": "SKP-08 / ISCO-08 (SURS 0711335S)",
        "note": "Gross monthly earnings (EUR); mean/median/P10/P25/P75/P90 by "
                "occupation × sex × year.",
        "years": yrs_int, "year": latest, "currency": "EUR",
        "stat_cols": STAT_COLS, "sexes": ["total", "men", "women"],
        "codes": {"EN": names}, "stats": stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    leaves = sum(1 for c in names if not any(o != c and o.startswith(c) for o in names))
    size = os.path.getsize(out_path)
    log(f"wrote {len(names)} SKP codes ({leaves} leaf), {len(yrs_int)} years "
        f"({size/1e6:.2f} MB)")
    return {"built_at": payload["built_at"], "year": latest, "years": yrs_int,
            "codes": len(names), "leaves": leaves, "size": size}


def bundled_info(path: str = OUT) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
        return {"built_at": d.get("built_at"), "year": d.get("year"),
                "years": d.get("years"), "size": os.path.getsize(path),
                "source": d.get("source")}
    except Exception:
        return {}


if __name__ == "__main__":
    print(build())
