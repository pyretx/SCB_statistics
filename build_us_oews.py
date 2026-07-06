"""Build us_oews.json.gz — US BLS OEWS wages by SOC occupation, national + states.

Source: the BLS OEWS national and state files (one release/year). Gives, per SOC
occupation and per area: annual mean, median, P10/P25/P75/P90 and employment —
the same shape as Sweden's percentile data.

Normalizations for the framework:

1. Top-coded / suppressed wages. BLS prints "#" (>= the top code, $239,200/yr in
   2024) and "*"/"**" (suppressed). Stored as null (an honest gap; the line just
   stops there). A future "simulation" layer can fill the censored upper tail.

2. SOC's hierarchy does NOT nest by string prefix, so each level is keyed by its
   SIGNIFICANT prefix and the framework's prefix drill-down works unchanged:
     major 11-0000 -> "11"  ·  minor 11-1000 -> "11-1"  ·
     broad 11-1010 -> "11-101"  ·  detailed 11-1011 -> "11-1011" (real SOC, leaf)

Output (gzipped JSON): codes (SOC titles, all levels, from national) + regions
(US national + states) + stats[region][soc] = [mean, median, p10, p25, p75, p90,
count]. States reuse the national SOC titles.

Run once (needs openpyxl locally; not a runtime dependency):
    python build_us_oews.py
"""
import datetime
import gzip
import io
import json
import os
import zipfile

import openpyxl
import requests

YEAR = "2024"
YY = YEAR[-2:]
NAT_URL = f"https://www.bls.gov/oes/special-requests/oesm{YY}nat.zip"
ST_URL = f"https://www.bls.gov/oes/special-requests/oesm{YY}st.zip"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "us_oews.json.gz")
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}

STAT_COLS = ["mean", "median", "p10", "p25", "p75", "p90", "count"]
_SRC = {"mean": "A_MEAN", "median": "A_MEDIAN", "p10": "A_PCT10", "p25": "A_PCT25",
        "p75": "A_PCT75", "p90": "A_PCT90", "count": "TOT_EMP"}


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


def _sheet(url: str):
    r = requests.get(url, headers=_UA, timeout=300)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    mem = [m for m in z.namelist() if m.endswith(".xlsx")][0]
    ws = openpyxl.load_workbook(io.BytesIO(z.read(mem)), read_only=True, data_only=True).active
    rows = ws.iter_rows(values_only=True)
    header = {name: i for i, name in enumerate(next(rows))}
    return rows, header


def _detailed_stats(rows, h, region_col=None):
    """Yield (region_key, region_name, soc_code, group, title, stat_list) per row."""
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
    print(f"downloading national {NAT_URL} …")
    nrows, nh = _sheet(NAT_URL)
    codes: dict[str, str] = {}
    stats: dict[str, dict] = {"US": {}}
    for _, _, sig, group, title, srow in _detailed_stats(nrows, nh):
        codes[sig] = title
        if group == "detailed":
            stats["US"][sig] = srow

    print(f"downloading state {ST_URL} …")
    srows, sh = _sheet(ST_URL)
    regions = {"US": "United States (national)"}
    for rkey, rname, sig, group, title, srow in _detailed_stats(srows, sh, region_col="PRIM_STATE"):
        if not rkey or len(str(rkey)) != 2 or group != "detailed":
            continue
        regions.setdefault(rkey, rname)
        stats.setdefault(rkey, {})[sig] = srow

    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": NAT_URL,
        "year": int(YEAR),
        "classification": "SOC-2018 (BLS OEWS)",
        "note": "Annual USD; '#' top-coded and suppressed values are null.",
        "stat_cols": STAT_COLS,
        "codes": {"EN": codes},
        "regions": regions,
        "stats": stats,
    }
    with gzip.open(OUT, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(OUT)
    print(f"wrote {len(codes)} codes, {len(regions)} regions, "
          f"{sum(len(v) for v in stats.values())} region×occ stat rows -> {OUT} "
          f"({size/1e6:.2f} MB gzipped)")


if __name__ == "__main__":
    main()
