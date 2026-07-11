"""Reusable FD_SALAAN microdata build for France — SHIPS with the app, so the
admin panel can import a new INSEE vintage at runtime (paste the parquet URL or
upload the file). The offline CLI build_pcs_microdata_percentiles.py predates
this; the method here is identical.

Method (standard technique for grouped/banded income data): restrict to
full-time (CPFD == "C"), near-full-year (DUREE >= 300) rows; per 4-digit PCS
code, weight rows by POND and interpolate linearly within the TRNNETO band that
contains each target percentile. A percentile falling in the OPEN top band
("50000 EUR et plus") is recorded as null (censored) rather than guessed.
Occupations with fewer than MIN_ROWS qualifying rows are dropped.

Safety: the result is validated (occupation count, sane year) BEFORE the
atomic swap of pcs_microdata_percentiles.json — any failure leaves the current
bundled data untouched. Requires pyarrow (runtime dep, imported lazily by
pandas.read_parquet).
"""
from __future__ import annotations

import datetime
import json
import os
import re
import tempfile

import pandas as pd
import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "pcs_microdata_percentiles.json")

PCTS = [10, 25, 50, 75, 90]
MIN_ROWS = 30          # minimum qualifying raw rows per occupation
MIN_OCCUPATIONS = 200  # validation floor — fewer means a broken/wrong file

# TRNNETO band code -> (lower, upper) annual EUR bound. Upper=None means open
# (uncensorable). Source: INSEE's official variable dictionary for this file.
BANDS = {
    "00": (0, 200),         "01": (200, 500),       "02": (500, 1000),
    "03": (1000, 1500),     "04": (1500, 2000),     "05": (2000, 3000),
    "06": (3000, 4000),     "07": (4000, 6000),     "08": (6000, 8000),
    "09": (8000, 10000),    "10": (10000, 12000),   "11": (12000, 14000),
    "12": (14000, 16000),   "13": (16000, 18000),   "14": (18000, 20000),
    "15": (20000, 22000),   "16": (22000, 24000),   "17": (24000, 26000),
    "18": (26000, 28000),   "19": (28000, 30000),   "20": (30000, 35000),
    "21": (35000, 40000),   "22": (40000, 50000),   "23": (50000, None),
}
BAND_ORDER = sorted(BANDS, key=int)


def weighted_percentiles(bands: pd.Series, weights: pd.Series) -> dict[int, float | None]:
    """Linear interpolation within grouped/banded data. ``bands`` holds TRNNETO
    codes ("00".."23"); returns {percentile: monthly EUR or None if censored}."""
    agg = weights.groupby(bands).sum()
    agg = agg.reindex(BAND_ORDER, fill_value=0.0)
    total = agg.sum()
    if total <= 0:
        return {p: None for p in PCTS}
    cum = agg.cumsum()
    out = {}
    for p in PCTS:
        target = p / 100 * total
        band = next((b for b in BAND_ORDER if cum[b] >= target), BAND_ORDER[-1])
        lo, hi = BANDS[band]
        if hi is None:                       # falls in the open top band
            out[p] = None
            continue
        before = cum[BAND_ORDER[BAND_ORDER.index(band) - 1]] if band != BAND_ORDER[0] else 0.0
        freq = agg[band]
        frac = (target - before) / freq if freq else 0.0
        annual = lo + frac * (hi - lo)
        out[p] = round(annual / 12, 1)       # annual -> monthly-FTE proxy
    return out


def infer_year(name: str) -> int | None:
    """FD_SALAAN_2024.parquet / …_2024… → 2024."""
    m = re.search(r"(20\d\d)", str(name) or "")
    return int(m.group(1)) if m else None


def bundled_info() -> dict:
    """{year, occupations, size, source} of the currently bundled estimates."""
    try:
        size = os.path.getsize(OUT)
        with open(OUT, encoding="utf-8") as f:
            d = json.load(f)
        return {"year": d.get("year"), "occupations": len(d.get("occupations", {})),
                "size": size, "source": d.get("source", "")}
    except Exception:
        return {}


def build(source, year: int | None = None, log=print) -> dict:
    """Import one FD_SALAAN vintage → pcs_microdata_percentiles.json.

    ``source``: an INSEE parquet URL (downloaded server-side), a local file
    path, or a file-like object (Streamlit upload). ``year``: the data vintage;
    inferred from the URL/filename when omitted. Validates before the atomic
    swap; raises on any problem (current data untouched)."""
    src_name = getattr(source, "name", None) or str(source)
    year = int(year or infer_year(src_name) or 0)
    if not (2000 < year < 2100):
        raise ValueError(f"cannot determine the data year from {src_name!r} — "
                         "set it explicitly")

    tmp_dl = None
    try:
        if isinstance(source, str) and source.lower().startswith("http"):
            log(f"downloading {source} …")
            r = requests.get(source, timeout=900, stream=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            fd, tmp_dl = tempfile.mkstemp(suffix=".parquet")
            got = 0
            with os.fdopen(fd, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
                    got += len(chunk)
            log(f"downloaded {got / 1e6:.1f} MB")
            reader = tmp_dl
        else:
            reader = source                     # path or file-like

        log("reading parquet …")
        df = pd.read_parquet(reader, columns=["PCS", "TRNNETO", "CPFD", "DUREE", "POND"])
        log(f"total rows: {len(df):,}")
        sub = df[(df["CPFD"] == "C") & (df["DUREE"] >= 300)]
        log(f"full-time, near-full-year rows: {len(sub):,}")

        results, skipped_small = {}, 0
        for code, g in sub.groupby("PCS"):
            if len(str(code)) != 4 or len(g) < MIN_ROWS:
                if len(str(code)) == 4:
                    skipped_small += 1
                continue
            results[str(code)] = {"year": str(year), "n_rows": int(len(g)),
                                  "pct": weighted_percentiles(g["TRNNETO"], g["POND"])}

        # ── Validate BEFORE the swap — a broken/wrong file must change nothing.
        if len(results) < MIN_OCCUPATIONS:
            raise ValueError(f"only {len(results)} occupations passed the filters "
                             f"(expected ≥ {MIN_OCCUPATIONS}) — wrong or truncated file?")
        censored = sum(1 for v in results.values()
                       if any(p is None for p in v["pct"].values()))
        log(f"occupations: {len(results)} (skipped <{MIN_ROWS} rows: {skipped_small}; "
            f"censored top band: {censored})")

        payload = {"source": src_name, "year": str(year),
                   "built_at": datetime.date.today().isoformat(),
                   "method": "band-interpolated, full-time near-full-year only, "
                             "monthly-FTE proxy (annual/12)",
                   "occupations": results}
        tmp = OUT + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        os.replace(tmp, OUT)                    # atomic swap on success
        log(f"wrote pcs_microdata_percentiles.json ({os.path.getsize(OUT) / 1e6:.1f} MB)")
        return {"year": year, "occupations": len(results), "censored": censored,
                "skipped_small": skipped_small, "rows_total": int(len(df)),
                "rows_used": int(len(sub)), "size": os.path.getsize(OUT)}
    finally:
        if tmp_dl and os.path.exists(tmp_dl):
            os.remove(tmp_dl)
