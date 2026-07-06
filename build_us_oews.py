"""Build us_oews.json.gz — US BLS OEWS wages by SOC occupation.

Source: the BLS OEWS bulk files (one release/year). Gives, per SOC occupation
and per SCOPE: annual mean, median, P10/P25/P75/P90 and employment — the same
shape as Sweden's percentile data.

A "scope" is the framework's 'sector' slot. OEWS publishes three cuts that do
NOT combine (there is no clean state x industry), so we fold all three into one
mutually-exclusive scope list:
  - United States, all industries        -> key "US"      (oesm{YY}nat.zip)
  - each state, all industries           -> key = 2-letter state (oesm{YY}st.zip)
  - each national industry (NAICS)        -> key = "IND"+naics (oesm{YY}in4.zip:
    sector + 3-digit + 4-digit levels — the coverage/suppression sweet spot)

Normalizations for the framework:

1. Top-coded / suppressed wages. BLS prints "#" (>= the top code, $239,200/yr in
   2024) and "*"/"**" (suppressed). Stored as null (an honest gap; the line just
   stops there). A future "simulation" layer can fill the censored upper tail.

2. SOC's hierarchy does NOT nest by string prefix, so each level is keyed by its
   SIGNIFICANT prefix and the framework's prefix drill-down works unchanged:
     major 11-0000 -> "11"  ·  minor 11-1000 -> "11-1"  ·
     broad 11-1010 -> "11-101"  ·  detailed 11-1011 -> "11-1011" (real SOC, leaf)

Output (gzipped JSON): codes (SOC titles, all levels, from national) + regions
(scope key -> label) + stats[scope][soc] = [mean, median, p10, p25, p75, p90,
count]. States and industries reuse the national SOC titles.

Run once (needs openpyxl locally; not a runtime dependency):
    python build_us_oews.py
"""
import datetime
import gzip
import io
import json
import os
import re
import tempfile
import zipfile

import openpyxl
import requests

YEAR = "2024"
YY = YEAR[-2:]
BASE = "https://www.bls.gov/oes/special-requests"
NAT_URL = f"{BASE}/oesm{YY}nat.zip"          # national, all industries
ST_URL = f"{BASE}/oesm{YY}st.zip"            # states, all industries
IN_URL = f"{BASE}/oesm{YY}in4.zip"           # national industry-specific (NAICS sector/3d/4d)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "us_oews.json.gz")
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}
_CACHE = os.path.join(tempfile.gettempdir(), "oews_build_cache")   # raw-zip cache (dev reruns)

STAT_COLS = ["mean", "median", "p10", "p25", "p75", "p90", "count"]
_SRC = {"mean": "A_MEAN", "median": "A_MEDIAN", "p10": "A_PCT10", "p25": "A_PCT25",
        "p75": "A_PCT75", "p90": "A_PCT90", "count": "TOT_EMP"}
_IND_LEVELS = {"sector", "3-digit", "4-digit"}    # NAICS levels to fold in as scopes
IND_PREFIX = "IND"                                 # scope-key prefix marking an industry


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
    print(f"downloading {url} …")
    r = requests.get(url, headers=_UA, timeout=600)
    r.raise_for_status()
    open(fp, "wb").write(r.content)
    return r.content


def _zip(url: str) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(_download(url)))


def _sheet(z: zipfile.ZipFile, member: str):
    ws = openpyxl.load_workbook(io.BytesIO(z.read(member)), read_only=True, data_only=True).active
    rows = ws.iter_rows(values_only=True)
    header = {name: i for i, name in enumerate(next(rows))}
    return rows, header


def _members(z: zipfile.ZipFile, pattern: str) -> list[str]:
    return [m for m in z.namelist() if re.search(pattern, m)]


def _detailed_stats(rows, h, region_col=None):
    """Yield (region_key, region_name, soc_sig, group, title, stat_list) per row."""
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


def main():
    # ── National, all industries → SOC titles (all levels) + the "US" scope ──
    znat = _zip(NAT_URL)
    nrows, nh = _sheet(znat, _members(znat, r"national_M\d+_dl\.xlsx$")[0])
    codes: dict[str, str] = {}
    stats: dict[str, dict] = {"US": {}}
    for _, _, sig, group, title, srow in _detailed_stats(nrows, nh):
        codes[sig] = title
        if group == "detailed":
            stats["US"][sig] = srow

    # ── States, all industries ──
    zst = _zip(ST_URL)
    srows, sh = _sheet(zst, _members(zst, r"state_M\d+_dl\.xlsx$")[0])
    regions = {"US": "United States (national)"}
    for rkey, rname, sig, group, title, srow in _detailed_stats(srows, sh, region_col="PRIM_STATE"):
        if not rkey or len(str(rkey)) != 2 or group != "detailed":
            continue
        regions.setdefault(rkey, rname)
        stats.setdefault(rkey, {})[sig] = srow
    n_states = len(regions) - 1

    # ── National industry-specific (NAICS sector + 3-digit + 4-digit) ──
    zin = _zip(IN_URL)
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
    for key in sorted(ind_names, key=lambda k: ind_names[k].lower()):   # A–Z by industry name
        regions[key] = ind_names[key]

    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": NAT_URL,
        "year": int(YEAR),
        "classification": "SOC-2018 (BLS OEWS)",
        "note": "Annual USD; '#' top-coded and suppressed values are null.",
        "industry_prefix": IND_PREFIX,
        "counts": {"occupations": len(codes), "states": n_states,
                   "industries": len(ind_names), "scopes": len(regions)},
        "stat_cols": STAT_COLS,
        "codes": {"EN": codes},
        "regions": regions,
        "stats": stats,
    }
    with gzip.open(OUT, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(OUT)
    print(f"wrote {len(codes)} occ codes · {n_states} states · {len(ind_names)} industries "
          f"· {len(regions)} scopes · {sum(len(v) for v in stats.values())} scope×occ rows")
    print(f"-> {OUT}  ({size/1e6:.2f} MB gzipped)")


if __name__ == "__main__":
    main()
