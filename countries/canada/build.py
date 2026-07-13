"""Statistics Canada table 14-10-0417 → bundled Canada snapshot.

StatCan's Web Data Service is fully open (no key). "Employee wages by occupation,
annual" gives average + median WEEKLY wages by NOC occupation × geography (Canada
+ 10 provinces) × gender × age × type of work. We fetch the full-table CSV once,
filter to the latest year / full-time / age-15+, and ship a compact gzipped
snapshot (like the US OEWS build).

NOC hierarchy: the table's classificationCodes are ranges/lists ('00, 10, 20…',
'11-14') — not prefix-nestable — but the members form a clean parent tree, so we
synthesize prefix-nestable codes (2/4/6-digit) from that tree; the shared
prefix drill-down + code browser then work. Figures: gross MONTHLY = official
WEEKLY wage × 52 / 12. Provinces power a real By-region tab (has_region_data),
like the US states.
"""
from __future__ import annotations

import csv
import datetime
import gzip
import io
import json
import os
import tempfile
import zipfile
from collections import defaultdict

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "canada_wages.json.gz")
_APP_SETTINGS = os.path.join(_ROOT, "app_settings.json")
_CACHE = os.path.join(tempfile.gettempdir(), "statcan_build_cache")
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}

PID = 14100417
META_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
CSV_URL = f"https://www150.statcan.gc.ca/n1/tbl/csv/{PID}-eng.zip"
STAT_COLS = ["mean", "median"]
_WEEK_TO_MONTH = 52 / 12
_GENDER = {"Total - Gender": "total", "Men+": "men", "Women+": "women"}
_WAGES = {"Average weekly wage rate": "mean", "Median weekly wage rate": "median"}
_TYPE = "Full-time employees"
_AGE = "15 years and over"
_PROV = {  # StatCan geography name → 2-letter scope code
    "Canada": "CA", "Newfoundland and Labrador": "NL", "Prince Edward Island": "PE",
    "Nova Scotia": "NS", "New Brunswick": "NB", "Quebec": "QC", "Ontario": "ON",
    "Manitoba": "MB", "Saskatchewan": "SK", "Alberta": "AB", "British Columbia": "BC",
}
DEFAULT_LATEST_YEAR = 2024


def latest_year() -> int:
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("canada_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def save_latest_year(year: int):
    data = {}
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    data["canada_latest_year"] = int(year)
    with open(_APP_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _noc_tree():
    """→ ({syncode: name}, {classificationCode: syncode}) from the NOC parent tree.
    Synthesizes 2/4/6-digit prefix-nestable codes so the drill-down works."""
    r = requests.post(META_URL, json=[{"productId": PID}], headers=_UA, timeout=60)
    dim = next(d for d in r.json()[0]["object"]["dimension"] if "NOC" in d["dimensionNameEn"])
    members = dim["member"]
    by_id = {m["memberId"]: m for m in members}
    kids = defaultdict(list)
    root = None
    for m in members:
        p = m.get("parentMemberId")
        if p is None:
            root = m["memberId"]
        else:
            kids[p].append(m["memberId"])
    names, cc2syn = {}, {}

    def dfs(mid, prefix):
        for i, k in enumerate(kids.get(mid, []), 1):
            syn = prefix + f"{i:02d}"
            m = by_id[k]
            names[syn] = m["memberNameEn"].strip()
            cc2syn[str(m.get("classificationCode"))] = syn
            dfs(k, syn)
    dfs(root, "")
    return names, cc2syn


def _download_csv() -> bytes:
    os.makedirs(_CACHE, exist_ok=True)
    fp = os.path.join(_CACHE, f"{PID}.zip")
    if os.path.exists(fp):
        return open(fp, "rb").read()
    r = requests.get(CSV_URL, headers=_UA, timeout=600)
    r.raise_for_status()
    open(fp, "wb").write(r.content)
    return r.content


def _num(v):
    if v in (None, "", "..", "...", "F", "x"):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def build(out_path: str = OUT, log=print) -> dict:
    log("fetching NOC hierarchy (StatCan WDS) …")
    names, cc2syn = _noc_tree()
    log(f"downloading full table CSV {CSV_URL} …")
    z = zipfile.ZipFile(io.BytesIO(_download_csv()))
    member = [n for n in z.namelist() if n.lower().endswith(".csv") and "metadata" not in n.lower()][0]
    reader = csv.reader(io.StringIO(z.read(member).decode("utf-8-sig", "replace"), newline=""))
    header = next(reader)
    ci = {c: i for i, c in enumerate(header)}
    iREF, iGEO, iW, iT, iN, iG, iA, iV = (ci["REF_DATE"], ci["GEO"], ci["Wages"],
        ci["Type of work"], ci["National Occupational Classification (NOC)"],
        ci["Gender"], ci["Age group"], ci["VALUE"])

    # ONE pass: collect our slice (FT, 15+, weekly avg/median) keyed by year,
    # then keep the newest year. by_year[year][scope][gender][syncode] = {mean, median}
    by_year: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
    for row in reader:
        if row[iT] != _TYPE or row[iA] != _AGE:
            continue
        measure = _WAGES.get(row[iW])
        gender = _GENDER.get(row[iG])
        scope = _PROV.get(row[iGEO])
        if not (measure and gender and scope):
            continue
        cc = row[iN].rsplit("[", 1)[-1].rstrip("]").strip() if "[" in row[iN] else ""
        syn = cc2syn.get(cc)
        if not syn:
            continue
        v = _num(row[iV])
        if v is not None:
            by_year[int(row[iREF][:4])][scope][gender][syn][measure] = int(round(v * _WEEK_TO_MONTH))

    latest = max(by_year) if by_year else DEFAULT_LATEST_YEAR
    stats = by_year[latest]
    # flatten to lists
    out_stats = {scope: {g: {c: [d.get(m) for m in STAT_COLS] for c, d in cm.items()}
                         for g, cm in gm.items()}
                 for scope, gm in stats.items()}
    regions = {c: n for n, c in _PROV.items()}   # code → name
    leaves = sum(1 for c in names if not any(o != c and o.startswith(c) for o in names))
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": f"https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid={PID}01",
        "source_name": "Statistics Canada, table 14-10-0417",
        "classification": "NOC 2021 (StatCan 14-10-0417)",
        "note": "Gross MONTHLY = official WEEKLY wage × 52/12; full-time, age 15+, "
                f"{latest}. Suppressed cells null.",
        "year": latest,
        "currency": "CAD",
        "stat_cols": STAT_COLS,
        "sexes": ["total", "men", "women"],
        "codes": {"EN": names},
        "regions": regions,
        "national": "CA",
        "stats": out_stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"wrote {len(names)} NOC codes ({leaves} leaf) × {len(out_stats)} scopes, "
        f"year {latest} ({size / 1e6:.2f} MB)")
    return {"built_at": payload["built_at"], "year": latest, "codes": len(names),
            "leaves": leaves, "scopes": len(out_stats), "size": size}


def bundled_info(path: str = OUT) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
        return {"built_at": d.get("built_at"), "year": d.get("year"),
                "size": os.path.getsize(path), "source": d.get("source")}
    except Exception:
        return {}


if __name__ == "__main__":
    print(build())
