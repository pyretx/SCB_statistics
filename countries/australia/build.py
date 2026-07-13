"""ABS Employee Earnings and Hours (EEH, cat 6306.0) → bundled Australia snapshot.

The ABS Data API has no occupation×earnings dataflow, but the EEH data cubes are
public XLSX downloads. Data cube 11 (Table 1) gives AVERAGE weekly total cash
earnings by detailed occupation (ANZSCO, 4-digit) × sex — Males / Females /
Persons. We parse it offline (like the UK ASHE build) and ship a compact snapshot.

Mean only (no median/percentiles in the occupation cubes), single release. Figures
are gross MONTHLY = average WEEKLY total cash earnings × 52 / 12.
"""
from __future__ import annotations

import datetime
import gzip
import io
import json
import os
import tempfile

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "australia_eeh.json.gz")
_CACHE = os.path.join(tempfile.gettempdir(), "abs_eeh_cache")
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}

RELEASE = "may-2025"
CUBE = "63060DO011_202505.xlsx"
CUBE_URL = ("https://www.abs.gov.au/statistics/labour/earnings-and-working-conditions/"
            f"employee-earnings-and-hours-australia/{RELEASE}/{CUBE}")
DEFAULT_LATEST_YEAR = 2025
STAT_COLS = ["mean"]
_WEEK_TO_MONTH = 52 / 12
# Table_1 columns (0-indexed): A=occupation, B/C/D = avg weekly Males/Females/Persons
_COL = {"men": 1, "women": 2, "total": 3}


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("australia_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def _download() -> bytes:
    os.makedirs(_CACHE, exist_ok=True)
    fp = os.path.join(_CACHE, CUBE)
    if os.path.exists(fp):
        return open(fp, "rb").read()
    r = requests.get(CUBE_URL, headers=_UA, timeout=300)
    r.raise_for_status()
    open(fp, "wb").write(r.content)
    return r.content


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def build(out_path: str = OUT, log=print) -> dict:
    import openpyxl
    log(f"downloading ABS EEH cube {CUBE} …")
    wb = openpyxl.load_workbook(io.BytesIO(_download()), read_only=True, data_only=True)
    ws = wb["Table_1"]
    codes: dict[str, str] = {}
    stats: dict = {"total": {}, "men": {}, "women": {}}
    for row in ws.iter_rows(values_only=True):
        a = row[0]
        if not a:
            continue
        s = str(a).strip()
        parts = s.split(None, 1)
        if len(parts) != 2 or not parts[0].isdigit() or len(parts[0]) != 4:
            continue
        code, name = parts[0], parts[1].strip()
        codes[code] = name
        for sex, ci in _COL.items():
            v = _num(row[ci]) if ci < len(row) else None
            if v is not None:
                stats[sex][code] = [int(round(v * _WEEK_TO_MONTH))]

    retrieved = datetime.date.today().isoformat()
    payload = {
        "built_at": retrieved, "source": CUBE_URL,
        "source_name": "Australian Bureau of Statistics, Employee Earnings and Hours",
        "classification": "ANZSCO (ABS EEH cube 11)",
        "note": "Gross MONTHLY = average WEEKLY total cash earnings × 52/12; all "
                f"employees, {RELEASE}. Mean only. Suppressed cells null.",
        "year": DEFAULT_LATEST_YEAR, "currency": "AUD",
        "stat_cols": STAT_COLS, "sexes": ["total", "men", "women"],
        "codes": {"EN": codes}, "stats": stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes)} ANZSCO occupations ({size/1e6:.3f} MB)")
    return {"built_at": retrieved, "year": DEFAULT_LATEST_YEAR, "codes": len(codes),
            "size": size}


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
