"""FSO/BFS STAT-TAB PxWeb cube px-x-0304010000_205 → bundled Switzerland snapshot.

The Swiss Earnings Structure Survey (LSE / Lohnstrukturerhebung) is published via
the FSO PxWeb API. Cube _205 gives the FULL distribution — Zentralwert (median),
P10, P25, P75, P90 — of the monthly gross wage (CHF, standardised to 4⅓ weeks /
40h) by Berufsgruppe (ISCO-08 occupation, 1- and 2-digit) × sex × biennial year
(2012→). We fetch the national figures (Grossregion = Schweiz, age = Total) in one
json-stat2 query and ship a compact snapshot: percentiles + quartiles + median +
a biennial trend + sex + ISCO hierarchy — the richest set alongside the UK.

Note the FSO API only serves de/fr/it (the `en` node 400s behind their WAF) and
needs browser-ish headers; occupation names below carry the standard ISCO-08
English titles plus the native German.
"""
from __future__ import annotations

import datetime
import gzip
import json
import os
import re
import time

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "switzerland_earnings.json.gz")
DB = "px-x-0304010000_205"
URL = f"https://www.pxweb.bfs.admin.ch/api/v1/de/{DB}/{DB}.px"
_H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*", "Accept-Language": "de-DE,de;q=0.9",
      "Referer": "https://www.pxweb.bfs.admin.ch/"}
STAT_COLS = ["median", "p10", "p25", "p75", "p90"]
DEFAULT_LATEST_YEAR = 2024

_V_YEAR, _V_REG, _V_OCC, _V_AGE, _V_SEX, _V_PCT = (
    "Jahr", "Grossregion", "Berufsgruppe", "Lebensalter", "Geschlecht",
    "Zentralwert und andere Perzentile")
_SEX = {"-1": "total", "1": "women", "2": "men"}          # FSO: 1=Frauen, 2=Männer
_PCT = {"1": "median", "2": "p10", "3": "p25", "4": "p75", "5": "p90"}

# Standard ISCO-08 English titles (major 1-digit + sub-major 2-digit) for the
# groups present in the cube — paired with the native German at build time.
_ISCO_EN = {
    "1": "Managers", "2": "Professionals",
    "3": "Technicians and associate professionals", "4": "Clerical support workers",
    "5": "Service and sales workers",
    "6": "Skilled agricultural, forestry and fishery workers",
    "7": "Craft and related trades workers",
    "8": "Plant and machine operators, and assemblers", "9": "Elementary occupations",
    "11": "Chief executives, senior officials and legislators",
    "12": "Administrative and commercial managers",
    "13": "Production and specialised services managers",
    "14": "Hospitality, retail and other services managers",
    "21": "Science and engineering professionals", "22": "Health professionals",
    "23": "Teaching professionals",
    "24": "Business and administration professionals",
    "25": "Information and communications technology professionals",
    "26": "Legal, social and cultural professionals",
    "31": "Science and engineering associate professionals",
    "32": "Health associate professionals",
    "33": "Business and administration associate professionals",
    "34": "Legal, social, cultural and related associate professionals",
    "35": "Information and communications technicians",
    "41": "General and keyboard clerks", "42": "Customer services clerks",
    "43": "Numerical and material recording clerks",
    "44": "Other clerical support workers", "51": "Personal service workers",
    "52": "Sales workers", "53": "Personal care workers",
    "54": "Protective services workers",
    "61": "Market-oriented skilled agricultural workers",
    "62": "Market-oriented skilled forestry, fishery and hunting workers",
    "71": "Building and related trades workers, excluding electricians",
    "72": "Metal, machinery and related trades workers",
    "73": "Handicraft and printing workers",
    "74": "Electrical and electronic trades workers",
    "75": "Food processing, wood working, garment and other craft workers",
    "81": "Stationary plant and machine operators", "82": "Assemblers",
    "83": "Drivers and mobile plant operators", "91": "Cleaners and helpers",
    "92": "Agricultural, forestry and fishery labourers",
    "93": "Labourers in mining, construction, manufacturing and transport",
    "94": "Food preparation assistants",
    "96": "Refuse workers and other elementary workers",
}


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("switzerland_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def _recode(cube_code: str) -> str:
    """Cube Berufsgruppe code → framework occupation code.
    Majors are '10','20',…,'90' (ISCO 1-digit ×10) → '1'…'9'; sub-groups
    '11'…'96' (ISCO 2-digit) stay as-is so prefix nesting works."""
    if len(cube_code) == 2 and cube_code.endswith("0"):
        return cube_code[0]
    return cube_code


def _clean_de(txt: str) -> str:
    return re.sub(r"^>?\s*\d+\s+", "", txt).strip()


def _session():
    s = requests.Session()
    s.headers.update(_H)
    return s


def _meta(s):
    r = s.get(URL, timeout=60, verify=False)
    r.raise_for_status()
    return r.json()


def _post(s, query):
    body = {"query": query, "response": {"format": "json-stat2"}}
    for i in range(5):
        r = s.post(URL, json=body, timeout=120, verify=False)
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
    s = _session()
    meta = _meta(s)
    var = {v["code"]: v for v in meta["variables"]}
    years = list(var[_V_YEAR]["values"])
    occ_pairs = [(c, t) for c, t in zip(var[_V_OCC]["values"], var[_V_OCC]["valueTexts"])
                 if c != "-1"]

    # occupation code map (framework code → EN/DE names)
    codes_en, codes_de = {}, {}
    cube_codes = []
    for cc, tt in occ_pairs:
        fc = _recode(cc)
        cube_codes.append(cc)
        codes_de[fc] = _clean_de(tt)
        codes_en[fc] = _ISCO_EN.get(fc, _clean_de(tt))

    log(f"CH LSE {DB}: {len(cube_codes)} occupation groups, {len(years)} years "
        f"({years[-1]}–{years[0]})")
    ds = _post(s, [
        {"code": _V_YEAR, "selection": {"filter": "item", "values": years}},
        {"code": _V_REG, "selection": {"filter": "item", "values": ["-1"]}},   # Schweiz
        {"code": _V_OCC, "selection": {"filter": "item", "values": cube_codes}},
        {"code": _V_AGE, "selection": {"filter": "item", "values": ["-1"]}},    # all ages
        {"code": _V_SEX, "selection": {"filter": "item", "values": ["-1", "1", "2"]}},
        {"code": _V_PCT, "selection": {"filter": "item", "values": list(_PCT)}},
    ])
    dims, val = _flat(ds)

    stats: dict = {}
    for yr in years:
        ysm = {}
        for scode, sx in _SEX.items():
            occ_map = {}
            for cc in cube_codes:
                fc = _recode(cc)
                vals = {}
                for pcode, pname in _PCT.items():
                    v = val({_V_YEAR: yr, _V_REG: "-1", _V_OCC: cc, _V_AGE: "-1",
                             _V_SEX: scode, _V_PCT: pcode})
                    vals[pname] = None if v is None else int(round(v))
                if any(v is not None for v in vals.values()):
                    occ_map[fc] = [vals.get(m) for m in STAT_COLS]
            if occ_map:
                ysm[sx] = occ_map
        stats[str(int(yr))] = ysm

    yrs_int = sorted(int(y) for y in stats)
    latest = max(yrs_int) if yrs_int else DEFAULT_LATEST_YEAR
    retrieved = datetime.date.today().isoformat()
    payload = {
        "built_at": retrieved,
        "source": "https://www.pxweb.bfs.admin.ch/pxweb/de/px-x-0304010000_205",
        "source_name": "Swiss Federal Statistical Office (FSO) — Earnings Structure Survey (LSE)",
        "classification": "ISCO-08 occupation groups (FSO Berufsgruppe, cube 0304010000_205)",
        "note": "Standardised monthly gross wage (CHF, 4⅓ weeks / 40h); "
                "median/P10/P25/P75/P90 by occupation × sex × year, national.",
        "years": yrs_int, "year": latest, "currency": "CHF",
        "stat_cols": STAT_COLS, "sexes": ["total", "women", "men"],
        "codes": {"EN": codes_en, "DE": codes_de}, "stats": stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    leaves = sum(1 for c in codes_en if not any(o != c and o.startswith(c) for o in codes_en))
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes_en)} ISCO codes ({leaves} leaf), {len(yrs_int)} years "
        f"({size/1e6:.3f} MB)")
    return {"built_at": retrieved, "year": latest, "years": yrs_int,
            "codes": len(codes_en), "leaves": leaves, "size": size}


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
