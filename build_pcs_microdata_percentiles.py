"""Dev tool: build pcs_microdata_percentiles.json — per-occupation P10/P25/P50/
P75/P90 estimated from INSEE's public anonymized microdata ("Description des
emplois salaries 2023 - Fichier detail", FD_SALAAN_2023.parquet).

Why this exists: Melodi (the live API) only publishes salary PERCENTILES for
ALL employees, never per detailed occupation (only the mean is published per
occupation there). This script estimates occupation-level percentiles from the
one INSEE source that has occupation-level pay at all: the microdata's banded
annual net remuneration field (TRNNETO), which has 24 bands and an OPEN top
band ("50000 EUR et plus"). Values landing in that open band cannot be
interpolated (no upper bound) and are recorded as null (censored) rather than
guessed — the app can layer a separate scaled estimate for those later.

Method (standard technique for grouped/banded income data):
  1. Restrict to full-time (CPFD == "C"), near-full-year (DUREE >= 300) rows,
     so the annual TRNNETO band can be divided by 12 as a monthly-FTE proxy
     comparable to Melodi's "net monthly FTE salary" figures.
  2. Per 4-digit PCS code, weight rows by POND and interpolate linearly WITHIN
     the band that contains each target percentile (assumes a uniform
     distribution inside each band — the standard grouped-data method).
  3. If the target percentile falls in the open top band -> null.
  4. Occupations with fewer than MIN_ROWS qualifying rows are dropped (sample
     too small to be a meaningful occupation-level estimate).

This is 2023 data (a different vintage than Melodi's 2024 occupation means) —
labelled as such wherever it's shown. Re-run only when INSEE republishes a new
microdata vintage.

Usage:  python build_pcs_microdata_percentiles.py   (needs: pip install pyarrow)
"""
import json

import pandas as pd
import requests

URL      = "https://www.insee.fr/fr/statistiques/fichier/8730395/FD_SALAAN_2023.parquet"
DEST     = "pcs_microdata_percentiles.json"
YEAR     = "2023"
PCTS     = [10, 25, 50, 75, 90]
MIN_ROWS = 30   # minimum qualifying raw rows per occupation to publish an estimate

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
    """Linear interpolation within grouped/banded data. `bands` holds TRNNETO
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


def main():
    print(f"downloading {URL} …")
    r = requests.get(URL, timeout=600, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    tmp = "FD_SALAAN_2023.parquet"
    with open(tmp, "wb") as f:
        f.write(r.content)
    print(f"saved {len(r.content)/1e6:.1f} MB, loading…")

    df = pd.read_parquet(tmp, columns=["PCS", "TRNNETO", "CPFD", "DUREE", "POND"])
    print(f"total rows: {len(df):,}")

    sub = df[(df["CPFD"] == "C") & (df["DUREE"] >= 300)].copy()
    print(f"full-time, near-full-year rows: {len(sub):,}")

    results = {}
    skipped_small = 0
    for code, g in sub.groupby("PCS"):
        if len(code) != 4 or len(g) < MIN_ROWS:
            if len(code) == 4:
                skipped_small += 1
            continue
        pcts = weighted_percentiles(g["TRNNETO"], g["POND"])
        results[code] = {
            "year": YEAR,
            "n_rows": int(len(g)),
            "pct": pcts,
        }

    censored = sum(1 for v in results.values() if any(p is None for p in v["pct"].values()))
    print(f"occupations with an estimate: {len(results)} "
          f"(skipped for <{MIN_ROWS} rows: {skipped_small})")
    print(f"occupations with >=1 censored (open-band) percentile: {censored}")

    for code in ("311C", "684A", "231A"):
        if code in results:
            print(f"  sample {code}: {results[code]}")

    with open(DEST, "w", encoding="utf-8") as f:
        json.dump({"source": URL, "year": YEAR, "method": "band-interpolated, "
                   "full-time near-full-year only, monthly-FTE proxy (annual/12)",
                   "occupations": results}, f, ensure_ascii=False, indent=1)
    print(f"wrote {DEST}")


if __name__ == "__main__":
    main()
