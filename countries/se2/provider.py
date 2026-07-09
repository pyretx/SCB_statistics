"""Sweden v2 data provider — SCB PxWebApi (AM0110), the framework port of the
legacy scb_salaries.py data layer.

Same tables, codes and merge logic as the legacy page:
  percentiles  LoneSpridSektorYrk4A (2014–22) + LoneSpridSektYrk4AN (2023→)
               → mean · median · P10 · P25 · P75 · P90 per occupation
  age          LonYrkeAlder4A/4AN        (mean by age band)
  region       LonYrkeRegion4A/4AN       (mean + headcount by NUTS-2 région)
  education    LonYrkeUtbildning4A/4AN   (mean by education level)
  CPI          PR0101 KPI2020M shadow index (2020=100), annual average
  leaderboard  the percentile tables with Yrke2012 = * (mean + median, all occs)

Occupation LABELS come from the bundled occupations_cache.json (EN + SV, shared
with the legacy page and refreshable from the admin panel) plus
ssyk_descriptions.json for 3-digit names; salary VALUES are fetched per query
and disk-cached, never auto-refreshed.
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd
import requests
import streamlit as st

from core import model
from core.provider import CountryProvider

from .labels import AGE_GROUPS, EDU_LEVELS, MAJOR_GROUPS, REGIONS, SUB_GROUPS

TABLE_BASE = "AM/AM0110/AM0110A"
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_OCC_CACHE = os.path.join(_ROOT, "occupations_cache.json")
_SSYK_FILE = os.path.join(_ROOT, "ssyk_descriptions.json")
_SETTINGS = os.path.join(_ROOT, "app_settings.json")

SEX_CODE = {"total": "1+2", "women": "2", "men": "1"}

# Measure keys in canonical order ↔ each table generation's ContentsCodes.
_MEASURES = ("mean", "median", "p10", "p25", "p75", "p90")
PCT_TABLES = [
    ("LoneSpridSektorYrk4A", 2014, 2022,
     ["000000C5", "000000C6", "000000C7", "000000C8", "000000C9", "000000CA"]),
    ("LoneSpridSektYrk4AN", 2023, 2099,   # upper bound = latest_year() at call time
     ["000007CD", "000007CE", "000007CF", "000007CG", "000007CH", "000007CI"]),
]
AGE_TABLES = [("LonYrkeAlder4A", 2014, 2022), ("LonYrkeAlder4AN", 2023, 2099)]
REG_TABLES = [("LonYrkeRegion4A", 2014, 2022), ("LonYrkeRegion4AN", 2023, 2099)]
EDU_TABLES = [("LonYrkeUtbildning4A", 2014, 2022), ("LonYrkeUtbildning4AN", 2023, 2099)]


def latest_year() -> int:
    """Newest SCB data year — shared with the legacy page's admin setting
    (app_settings.json, rolled forward by the data-year check)."""
    try:
        with open(_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("latest_data_year", 2025))
    except Exception:
        return 2025


# ── labels ───────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _occ_cache() -> dict:
    try:
        with open(_OCC_CACHE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@st.cache_data(show_spinner=False)
def _ssyk_nodes() -> dict:
    try:
        with open(_SSYK_FILE, encoding="utf-8") as f:
            return json.load(f).get("nodes", {})
    except Exception:
        return {}


def _leaves(lang: str = "EN") -> dict[str, str]:
    occ = _occ_cache().get(lang) or _occ_cache().get("EN") or {}
    return {c: n for c, n in occ.items() if len(c) == 4 and c != "0000"}


def _tree(lang: str = "EN") -> dict[str, str]:
    """All SSYK levels → name: 1/2-digit from the official group lists, 3-digit
    from ssyk_descriptions.json, 4-digit from the occupations cache."""
    out: dict[str, str] = {}
    out.update(MAJOR_GROUPS.get(lang, MAJOR_GROUPS["EN"]))
    out.update(SUB_GROUPS.get(lang, SUB_GROUPS["EN"]))
    for code, node in _ssyk_nodes().items():
        if len(code) == 3:
            out[code] = ((node.get("name_en") or node.get("name_sv", code))
                         if lang == "EN" else node.get("name_sv", code))
    out.update(_leaves(lang))
    return out


# ── fetch plumbing (PxWeb "json" format, ported from the legacy page) ─────────
def _post(table: str, query: list, lang: str, tries: int = 3) -> pd.DataFrame | None:
    url = f"https://api.scb.se/OV0104/v1/doris/{lang.lower()}/ssd/{TABLE_BASE}/{table}"
    r = None
    for i in range(tries):
        try:
            r = requests.post(url, json={"query": query, "response": {"format": "json"}},
                              timeout=30)
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(1.0 * (i + 1))
            continue
        if r.status_code in (400, 404):
            return None                       # combination not published
        if r.status_code == 200:
            break
        if r.status_code in (429, 500, 502, 503, 504) and i < tries - 1:
            time.sleep(1.0 * (i + 1))
            continue
        return None
    if r is None or r.status_code != 200:
        return None
    raw = r.json()
    cols = [c["text"] for c in raw["columns"]]
    rows = [item["key"] + item["values"] for item in raw["data"]]
    return pd.DataFrame(rows, columns=cols) if rows else None


_BAD = ("confidence", "interval", "percent", "konfidens", "intervall", "procent", "95")


def _pick_col(cols, kw: str) -> str | None:
    cands = [c for c in cols if kw in c.lower() and not any(b in c.lower() for b in _BAD)]
    return cands[0] if cands else None


def _salary_col(cols, lang: str) -> str | None:
    return _pick_col(cols, "monthly" if lang == "EN" else "månadslön")


def _count_col(cols, lang: str) -> str | None:
    return _pick_col(cols, "number of employees" if lang == "EN" else "antal anställda")


def _tables_for(table_list, years: list[int]):
    """(table, [years-in-range], extra…) per generation actually needed."""
    cap = latest_year()
    for row in table_list:
        tname, lo, hi = row[0], row[1], min(row[2], cap)
        yr = [y for y in years if lo <= y <= hi]
        if yr:
            yield (tname, yr) + tuple(row[3:])


# ── percentile (total) slice ─────────────────────────────────────────────────
# SCB's API latency is per-CALL (~a flat round-trip whatever the size), so the
# strategy is: as few calls as possible, each carrying as much as possible.
# ONE call per table generation fetches ALL sexes (1 / 2 / 1+2) × the FULL year
# span (2014→latest); the generations run in PARALLEL. Every year switch, the
# overview (incl. its women/men gap), the by-gender tab, the distribution tab
# AND the whole trend tab then slice this one disk-cached frame locally.
_ALL_KON = ["1", "2", "1+2"]


def _key_cols(df, occ_codes):
    """Identify the occupation / sex / year key columns by VALUE (PxWeb returns
    key columns in TABLE order, not query order)."""
    occ_set, kon_set = set(occ_codes), set(_ALL_KON)
    occ_c = kon_c = yr_c = None
    for c in df.columns:
        vals = set(df[c].astype(str).str.strip())
        if occ_c is None and vals <= occ_set:
            occ_c = c
        elif kon_c is None and vals <= kon_set:
            kon_c = c
        elif yr_c is None and vals and all(v.isdigit() and len(v) == 4 for v in vals):
            yr_c = c
    return occ_c, kon_c, yr_c


def _parallel(jobs):
    """Run the per-table-generation fetches concurrently (SCB's latency is per
    call, so two generations in flight ≈ the cost of one)."""
    from concurrent.futures import ThreadPoolExecutor
    if len(jobs) == 1:
        return [jobs[0]()]
    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        return list(ex.map(lambda f: f(), jobs))


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_pct(sector: str, occ_codes: tuple[str, ...], lang: str) -> pd.DataFrame:
    """Tidy [occ, kon, yr, mean…p90] for ALL sexes × ALL years, min. API calls."""
    all_years = list(range(2014, latest_year() + 1))

    def job(tname, yr, codes):
        def run():
            q = [
                {"code": "Sektor", "selection": {"filter": "item", "values": [sector]}},
                {"code": "Yrke2012", "selection": {"filter": "item", "values": list(occ_codes)}},
                {"code": "Kon", "selection": {"filter": "item", "values": _ALL_KON}},
                {"code": "ContentsCode", "selection": {"filter": "item", "values": codes}},
                {"code": "Tid", "selection": {"filter": "item", "values": [str(y) for y in yr]}},
            ]
            df = _post(tname, q, lang)
            if df is None:
                return None
            keys = df.columns[:-len(codes)].tolist()
            df.columns = keys + list(_MEASURES)
            occ_c, kon_c, yr_c = _key_cols(df[keys], occ_codes)
            if not all((occ_c, kon_c, yr_c)):
                return None
            return df.rename(columns={occ_c: "occ", kon_c: "kon", yr_c: "yr"})[
                ["occ", "kon", "yr", *_MEASURES]]
        return run

    frames = [f for f in _parallel([job(t, y, c) for t, y, c
                                    in _tables_for(PCT_TABLES, all_years)])
              if f is not None]
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    for c in ("occ", "kon"):
        out[c] = out[c].astype(str).str.strip()
    out["yr"] = pd.to_numeric(out["yr"], errors="coerce")
    for c in _MEASURES:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_counts(sector: str, occ_codes: tuple[str, ...], lang: str) -> dict:
    """{(occ, kon, year): headcount} from the region table's national (SE) row —
    the percentile table carries no count (same trick as the legacy page).
    ALL sexes × ALL years, generations in parallel."""
    all_years = list(range(2014, latest_year() + 1))

    def job(tname, yr):
        def run():
            q = [
                {"code": "Region", "selection": {"filter": "item", "values": ["SE"]}},
                {"code": "Sektor", "selection": {"filter": "item", "values": [sector]}},
                {"code": "Yrke2012", "selection": {"filter": "item", "values": list(occ_codes)}},
                {"code": "Kon", "selection": {"filter": "item", "values": _ALL_KON}},
                {"code": "Tid", "selection": {"filter": "item", "values": [str(y) for y in yr]}},
            ]
            return _post(tname, q, lang)
        return run

    out: dict = {}
    for df in _parallel([job(t, y) for t, y in _tables_for(REG_TABLES, all_years)]):
        if df is None:
            continue
        cc = _count_col(df.columns, lang)
        if not cc:
            continue
        occ_c, kon_c, yr_c = _key_cols(df, occ_codes)
        if not all((occ_c, kon_c, yr_c)):
            continue
        for _, r in df.iterrows():
            out[(str(r[occ_c]).strip(), str(r[kon_c]).strip(), int(r[yr_c]))] = \
                pd.to_numeric(r[cc], errors="coerce")
    return out


# ── dimension slices (age / region / education) ──────────────────────────────
def _dim_meta(dim: str, lang: str):
    if dim == "age":
        return AGE_TABLES, "Alder", AGE_GROUPS, {v: v for v in AGE_GROUPS}
    if dim == "region":
        m = REGIONS.get(lang, REGIONS["EN"])
        return REG_TABLES, "Region", list(m), m
    if dim == "education":
        m = EDU_LEVELS.get(lang, EDU_LEVELS["EN"])
        return EDU_TABLES, "UtbildningsNiva", list(m), m
    return None, None, [], {}


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_dim_all(dim: str, sector: str, occ_codes: tuple[str, ...],
                   lang: str) -> pd.DataFrame:
    """Tidy [occ, dv(code), kon, yr, mean, count] — ALL sexes × ALL years in one
    call per table generation (generations in parallel). Year/sex switches and
    the split-by-sex toggle then slice locally, no extra API calls."""
    tables, var, values, _ = _dim_meta(dim, lang)
    if not tables:
        return pd.DataFrame()
    all_years = list(range(2014, latest_year() + 1))

    def job(tname, yr):
        def run():
            q = [
                {"code": var, "selection": {"filter": "item", "values": values}},
                {"code": "Sektor", "selection": {"filter": "item", "values": [sector]}},
                {"code": "Yrke2012", "selection": {"filter": "item", "values": list(occ_codes)}},
                {"code": "Kon", "selection": {"filter": "item", "values": _ALL_KON}},
                {"code": "Tid", "selection": {"filter": "item", "values": [str(y) for y in yr]}},
            ]
            # the education table has no "1+2" total → retry with 1 & 2 only
            df = _post(tname, q, lang)
            if df is None:
                q[3] = {"code": "Kon", "selection": {"filter": "item", "values": ["1", "2"]}}
                df = _post(tname, q, lang)
            return df
        return run

    frames = []
    for df in _parallel([job(t, y) for t, y in _tables_for(tables, all_years)]):
        if df is None:
            continue
        sal = _salary_col(df.columns, lang)
        if sal is None:
            continue
        cnt = _count_col(df.columns, lang)
        occ_c, kon_c, yr_c = _key_cols(df, occ_codes)
        # dimension column: largest overlap with the expected category codes
        dim_set, dim_c, best = set(values), None, 0
        for c in df.columns:
            if c in (occ_c, kon_c, yr_c):
                continue
            overlap = len(set(df[c].astype(str).str.strip()) & dim_set)
            if overlap > best:
                best, dim_c = overlap, c
        if not all((occ_c, kon_c, yr_c, dim_c)):
            continue
        d = df.rename(columns={occ_c: "occ", kon_c: "kon", yr_c: "yr", dim_c: "dv"})
        d["mean"] = pd.to_numeric(d[sal], errors="coerce")
        d["count"] = pd.to_numeric(d[cnt], errors="coerce") if cnt else None
        frames.append(d[["occ", "dv", "kon", "yr", "mean", "count"]])
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    for c in ("occ", "dv", "kon"):
        out[c] = out[c].astype(str).str.strip()
    out["yr"] = pd.to_numeric(out["yr"], errors="coerce")
    return out


def _fetch_dim(dim: str, sector: str, occ_codes: tuple[str, ...], sex: str,
               year: int, lang: str) -> pd.DataFrame:
    """[occ, dv(display), mean, count] for one (sex, year) — a local slice of
    the all-sex/all-year frame. When the table has no '1+2' total (education),
    the total is a headcount-weighted mean of men + women."""
    _, _, values, disp = _dim_meta(dim, lang)
    d = _fetch_dim_all(dim, sector, occ_codes, lang)
    if d.empty:
        return d
    d = d[d["yr"] == year]
    kon = SEX_CODE.get(sex, "1+2")
    sl = d[d["kon"] == kon]
    if sl.empty and sex == "total":            # aggregate 1 + 2, weighted
        rows = []
        for (occ, dv), g in d[d["kon"].isin(["1", "2"])].groupby(["occ", "dv"]):
            w = g["count"].fillna(0) if g["count"].notna().any() else pd.Series([1.0] * len(g))
            vals = g["mean"]
            tot = w.where(vals.notna(), 0).sum()
            mean = (vals.fillna(0) * w).sum() / tot if tot > 0 else vals.mean()
            rows.append({"occ": occ, "dv": dv, "mean": mean,
                         "count": g["count"].sum() if g["count"].notna().any() else None})
        sl = pd.DataFrame(rows)
    if sl.empty:
        return pd.DataFrame()
    order = {v: i for i, v in enumerate(values)}
    sl = sl[sl["dv"].isin(order)].copy()
    sl["__o"] = sl["dv"].map(order)
    sl["dv"] = sl["dv"].map(lambda v: disp.get(v, v))
    return sl.sort_values(["occ", "__o"])[["occ", "dv", "mean", "count"]]


# ── trend / CPI / leaderboard ────────────────────────────────────────────────
def _fetch_trend(sector: str, occ_codes: tuple[str, ...], sex: str,
                 years: tuple[int, ...], lang: str, measure: str) -> pd.DataFrame:
    """Trend = a slice of the SAME full-span percentile frame — no extra API
    call, so measure/view switches in the trend tab are instant."""
    m = measure if measure in _MEASURES else "mean"
    d = _fetch_pct(sector, occ_codes, lang)
    if d.empty:
        return model.empty_trend()
    d = d[d["kon"] == SEX_CODE.get(sex, "1+2")]
    if years:
        want = {int(y) for y in years}
        d = d[d["yr"].isin(want)]
    labels = _leaves(lang)
    rows = [{"country": "se2", "year": int(r["yr"]), "series": labels.get(r["occ"], r["occ"]),
             "sex": sex, "value_nominal": r[m], "value_real": None}
            for _, r in d.iterrows()]
    return pd.DataFrame(rows, columns=model.TREND_COLS)


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_cpi(years: tuple[int, ...]) -> dict:
    """Annual-average Swedish CPI (KPI2020M shadow index, 2020=100) → {year: idx}."""
    if not years:
        return {}
    yrs = sorted(set(int(y) for y in years))
    url = "https://api.scb.se/OV0104/v1/doris/en/ssd/PR/PR0101/PR0101A/KPI2020M"
    months = [f"{y}M{m:02d}" for y in range(yrs[0], yrs[-1] + 1) for m in range(1, 13)]
    body = {"query": [
        {"code": "ContentsCode", "selection": {"filter": "item", "values": ["00000807"]}},
        {"code": "Tid", "selection": {"filter": "item", "values": months}},
    ], "response": {"format": "json"}}
    try:
        r = requests.post(url, json=body, timeout=30)
        r.raise_for_status()
        raw = r.json()
    except Exception:
        return {}
    by_year: dict[int, list] = {}
    for item in raw.get("data", []):
        v = item["values"][0]
        if v not in ("..", "", None):
            by_year.setdefault(int(item["key"][0][:4]), []).append(float(v))
    return {y: sum(vs) / len(vs) for y, vs in by_year.items() if vs}


@st.cache_data(show_spinner=False, persist="disk")
def _fetch_leaderboard(sector: str, sex: str, year: int, lang: str) -> pd.DataFrame:
    for tname, yr, codes in _tables_for(PCT_TABLES, [year]):
        q = [
            {"code": "Sektor", "selection": {"filter": "item", "values": [sector]}},
            {"code": "Yrke2012", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Kon", "selection": {"filter": "item", "values": [SEX_CODE.get(sex, "1+2")]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": codes[:2]}},
            {"code": "Tid", "selection": {"filter": "item", "values": [str(y) for y in yr]}},
        ]
        df = _post(tname, q, lang)
        if df is None:
            continue
        keys = df.columns[:-2].tolist()
        df.columns = keys + ["mean", "median"]
        occ_c = keys[1]
        labels = _leaves(lang)
        df["occ_code"] = df[occ_c].astype(str).str.strip()
        df = df[df["occ_code"].isin(labels)]
        df["occ_name"] = df["occ_code"].map(labels)
        for c in ("mean", "median"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["count"] = None
        return df[["occ_code", "occ_name", "mean", "median", "count"]].reset_index(drop=True)
    return pd.DataFrame(columns=["occ_code", "occ_name", "mean", "median", "count"])


@st.cache_data(show_spinner=False)
def _synonym_index() -> dict:
    """{4-digit code: lowercased joined synonyms} for the sidebar search
    (matches the legacy page's ssyk_synonym_index)."""
    return {code: " | ".join((n.get("synonyms") or []) + (n.get("synonyms_en") or [])).lower()
            for code, n in _ssyk_nodes().items() if len(code) == 4}


# ── provider ─────────────────────────────────────────────────────────────────
class Sweden2Provider(CountryProvider):
    def occupations(self, lang: str = "EN") -> dict[str, str]:
        return _leaves(lang)

    def occupation_tree(self, lang: str = "EN") -> dict[str, str]:
        return _tree(lang)

    def occupation_details(self, code: str, lang: str = "EN") -> dict:
        """SSYK descriptions + synonyms (ssyk_descriptions.json) for the code
        browser. English descriptions are auto-translated where no official
        source exists (same note as the legacy page)."""
        n = _ssyk_nodes().get(code, {})
        desc = ((n.get("desc_en") or n.get("desc_sv")) if lang == "EN"
                else (n.get("desc_sv") or n.get("desc_en")))
        syn = ((n.get("synonyms_en") if lang == "EN" else n.get("synonyms"))
               or n.get("synonyms") or [])
        return {"description": desc, "synonyms": list(syn)}

    def occupation_synonyms(self, lang: str = "EN") -> dict:
        return _synonym_index()

    def occupation_stats(self, *, sector="0", occ_codes=(), sex="total",
                         years=(), dimension="total", year=None,
                         lang="EN") -> pd.DataFrame:
        occ_codes = tuple(occ_codes)
        if not occ_codes:
            return model.empty_occ_stats()
        yr = int(year or (years[-1] if years else latest_year()))
        labels = _leaves(lang)

        if dimension != "total":
            d = _fetch_dim(dimension, sector or "0", occ_codes, sex, yr, lang)
            rows = [{
                "country": "se2", "year": yr, "occ_code": r["occ"],
                "occ_name": labels.get(str(r["occ"]).strip(), r["occ"]),
                "occ_group": str(r["occ"])[:2], "dimension": dimension,
                "dim_value": r["dv"], "currency": "SEK", "period": "monthly",
                "mean": r["mean"], "median": None, "p10": None, "p25": None,
                "p75": None, "p90": None, "count": r["count"],
                "source_name": "Statistics Sweden (SCB)", "source_url": TABLE_BASE,
                "notes": "",
            } for _, r in d.iterrows()]
            return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

        # Fire the two SCB fetches CONCURRENTLY on a cold cache (each is a flat
        # ~full round-trip); both frames carry every sex × every year, so all
        # subsequent slicing is local.
        sec = sector or "0"
        res = _parallel([lambda: _fetch_pct(sec, occ_codes, lang),
                         lambda: _fetch_counts(sec, occ_codes, lang)])
        d, counts = res[0], res[1]
        kon = SEX_CODE.get(sex, "1+2")
        if not d.empty:
            d = d[(d["yr"] == yr) & (d["kon"] == kon)]
        rows = []
        for occ in occ_codes:
            sl = d[d["occ"] == occ] if not d.empty else d
            v = sl.iloc[0] if sl is not None and not sl.empty else {}
            rows.append({
                "country": "se2", "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, occ), "occ_group": occ[:2],
                "dimension": "total", "dim_value": "total",
                "currency": "SEK", "period": "monthly",
                "mean": v.get("mean") if len(v) else None,
                "median": v.get("median") if len(v) else None,
                "p10": v.get("p10") if len(v) else None,
                "p25": v.get("p25") if len(v) else None,
                "p75": v.get("p75") if len(v) else None,
                "p90": v.get("p90") if len(v) else None,
                "count": counts.get((occ, kon, yr)),
                "source_name": "Statistics Sweden (SCB)",
                "source_url": f"https://api.scb.se/OV0104/v1/doris/en/ssd/{TABLE_BASE}",
                "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def trend(self, *, sector="0", occ_codes=(), sex="total", years=(),
              lang="EN", measure="mean") -> pd.DataFrame:
        return _fetch_trend(sector or "0", tuple(occ_codes), sex, tuple(years),
                            lang, measure)

    def cpi_annual(self, years=()) -> dict:
        return _fetch_cpi(tuple(years))

    def leaderboard(self, *, sector="0", sex="total", year=None, lang="EN") -> pd.DataFrame:
        return _fetch_leaderboard(sector or "0", sex, int(year or latest_year()), lang)
