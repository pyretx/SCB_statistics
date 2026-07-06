"""Reusable BLS OEWS build logic for the US dataset.

This module SHIPS with the app (unlike the dockerignored build_us_oews.py CLI),
so the admin panel can trigger a data refresh at runtime: scan BLS for a newer
release, re-download + rebuild, and hot-swap the bundled snapshot.

openpyxl is imported lazily (only when a build actually runs), so the app boots
fine without it; it is listed in requirements.txt for the refresh path.

See build_us_oews.py for the CLI entry point and the data-shape notes.
"""
from __future__ import annotations

import datetime
import gzip
import io
import json
import os
import re
import tempfile
import zipfile

import requests

BASE = "https://www.bls.gov/oes/special-requests"
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "us_oews.json.gz")
_CACHE = os.path.join(tempfile.gettempdir(), "oews_build_cache")

BUNDLED_YEAR = 2024                              # reference year shipped in git
STAT_COLS = ["mean", "median", "p10", "p25", "p75", "p90", "count"]
_SRC = {"mean": "A_MEAN", "median": "A_MEDIAN", "p10": "A_PCT10", "p25": "A_PCT25",
        "p75": "A_PCT75", "p90": "A_PCT90", "count": "TOT_EMP"}
_IND_LEVELS = {"sector", "3-digit", "4-digit"}   # NAICS levels folded in as scopes
IND_PREFIX = "IND"                                # scope-key prefix marking an industry


# ── URLs / small helpers ─────────────────────────────────────────────────────
def _urls(year: int | str) -> dict:
    yy = str(year)[-2:]
    return {"nat": f"{BASE}/oesm{yy}nat.zip",
            "st": f"{BASE}/oesm{yy}st.zip",
            "in": f"{BASE}/oesm{yy}in4.zip"}


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(round(v))
    s = str(v).strip().replace(",", "")
    if s in ("#", "*", "**", ""):
        return None
    try:
        return int(round(float(s)))
    except ValueError:
        return None


def _sig(code: str, group: str) -> str:
    return {"major": code[:2], "minor": code[:4], "broad": code[:6]}.get(group, code)


def _download(url: str) -> bytes:
    os.makedirs(_CACHE, exist_ok=True)
    fp = os.path.join(_CACHE, url.rsplit("/", 1)[1])
    if os.path.exists(fp):
        return open(fp, "rb").read()
    r = requests.get(url, headers=_UA, timeout=600)
    r.raise_for_status()
    open(fp, "wb").write(r.content)
    return r.content


def _zip(url: str) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(_download(url)))


def _sheet(z: zipfile.ZipFile, member: str):
    import openpyxl
    ws = openpyxl.load_workbook(io.BytesIO(z.read(member)), read_only=True, data_only=True).active
    rows = ws.iter_rows(values_only=True)
    header = {name: i for i, name in enumerate(next(rows))}
    return rows, header


def _members(z: zipfile.ZipFile, pattern: str) -> list[str]:
    return [m for m in z.namelist() if re.search(pattern, m)]


def _detailed_stats(rows, h, region_col=None):
    for row in rows:
        group = row[h["O_GROUP"]]
        occ = str(row[h["OCC_CODE"]]).strip()
        if group == "total" or occ in ("00-0000", "", "None"):
            continue
        title = str(row[h["OCC_TITLE"]]).strip()
        stats = [_num(row[h[_SRC[c]]]) for c in STAT_COLS]
        region_key = row[h[region_col]] if region_col else "US"
        region_name = row[h["AREA_TITLE"]] if region_col else "United States (national)"
        yield region_key, region_name, _sig(occ, group), group, title, stats


# ── Public API: freshness + build ────────────────────────────────────────────
def bundled_info(path: str = OUT) -> dict:
    """Metadata of the currently-installed snapshot (built_at, year, counts, size)."""
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
        return {"built_at": d.get("built_at"), "year": d.get("year"),
                "counts": d.get("counts", {}), "size": os.path.getsize(path),
                "source": d.get("source")}
    except Exception:
        return {}


def _has_release(year: int) -> bool:
    try:
        r = requests.get(_urls(year)["nat"], headers=_UA, stream=True, timeout=30)
        ok = r.status_code == 200
        r.close()
        return ok
    except Exception:
        return False


def latest_available_year(after: int | None = None, look_ahead: int = 3) -> int | None:
    """Newest reference year BLS has published (scanning forward from the bundled
    year). Used by the admin auto-scan to flag when a refresh is worthwhile."""
    start = int(after or bundled_info().get("year") or BUNDLED_YEAR)
    newest = start if _has_release(start) else None
    for y in range(start + 1, start + look_ahead + 1):
        if _has_release(y):
            newest = y
    return newest


def build(year: int | None = None, out_path: str = OUT, log=print) -> dict:
    """Download the OEWS national + state + national-industry files for ``year``
    (default: the newest BLS has published) and (re)write the gzipped snapshot.

    Writes to a temp file first and atomically replaces ``out_path`` on success,
    so a failed refresh never corrupts the live dataset. Returns a stats dict."""
    year = int(year or latest_available_year() or BUNDLED_YEAR)
    url = _urls(year)

    log(f"downloading national {url['nat']} …")
    znat = _zip(url["nat"])
    nrows, nh = _sheet(znat, _members(znat, r"national_M\d+_dl\.xlsx$")[0])
    codes: dict[str, str] = {}
    stats: dict[str, dict] = {"US": {}}
    for _, _, sig, group, title, srow in _detailed_stats(nrows, nh):
        codes[sig] = title
        if group == "detailed":
            stats["US"][sig] = srow

    log(f"downloading state {url['st']} …")
    zst = _zip(url["st"])
    srows, sh = _sheet(zst, _members(zst, r"state_M\d+_dl\.xlsx$")[0])
    regions = {"US": "United States (national)"}
    for rkey, rname, sig, group, title, srow in _detailed_stats(srows, sh, region_col="PRIM_STATE"):
        if not rkey or len(str(rkey)) != 2 or group != "detailed":
            continue
        regions.setdefault(rkey, rname)
        stats.setdefault(rkey, {})[sig] = srow
    n_states = len(regions) - 1

    log(f"downloading national industries {url['in']} …")
    zin = _zip(url["in"])
    ind_names: dict[str, str] = {}
    for mem in _members(zin, r"(natsector|nat3d|nat4d)_M\d+_dl\.xlsx$"):
        irows, ih = _sheet(zin, mem)
        for row in irows:
            if row[ih["I_GROUP"]] not in _IND_LEVELS or row[ih["O_GROUP"]] != "detailed":
                continue
            naics = str(row[ih["NAICS"]]).strip()
            occ = str(row[ih["OCC_CODE"]]).strip()
            if not naics or naics in ("000000", "None") or occ in ("00-0000", "", "None"):
                continue
            key = IND_PREFIX + naics
            ind_names.setdefault(key, str(row[ih["NAICS_TITLE"]]).strip())
            stats.setdefault(key, {})[occ] = [_num(row[ih[_SRC[c]]]) for c in STAT_COLS]
    for key in sorted(ind_names, key=lambda k: ind_names[k].lower()):
        regions[key] = ind_names[key]

    counts = {"occupations": len(codes), "states": n_states,
              "industries": len(ind_names), "scopes": len(regions)}
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": url["nat"],
        "year": year,
        "classification": "SOC-2018 (BLS OEWS)",
        "note": "Annual USD; '#' top-coded and suppressed values are null.",
        "industry_prefix": IND_PREFIX,
        "counts": counts,
        "stat_cols": STAT_COLS,
        "codes": {"EN": codes},
        "regions": regions,
        "stats": stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)                         # atomic swap on success
    size = os.path.getsize(out_path)
    log(f"wrote {counts['occupations']} occ · {n_states} states · "
        f"{counts['industries']} industries · {counts['scopes']} scopes "
        f"({size / 1e6:.2f} MB)")
    return {"year": year, "built_at": payload["built_at"], "size": size,
            "rows": sum(len(v) for v in stats.values()), **counts}
