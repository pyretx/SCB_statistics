"""INEGI ENOE microdata → bundled Mexico snapshot (multi-quarter, incremental).

INEGI's indicator API is macro-only and the ENOE tabulados give income as BANDS,
so the real salary figures come from the ENOE MICRODATA — the open, free
record-level file (no token). For each quarter from 2024 Q1 to the latest
available, we parse the SDEMT table and compute the survey-WEIGHTED mean & median
monthly occupational income (ingocup, MXN) by the 10 ENOE occupation groups
(c_ocu11c) × sex (weight fac_tri). Quarterly aggregates are cached in the snapshot
so a rebuild only processes NEW quarters, and the admin update-check detects a
newly-released quarter (see updates.py).

The framework trend is annual (the average of each year's available quarters),
2024 → latest.
"""
from __future__ import annotations

import datetime
import gzip
import io
import json
import os
import tempfile

import numpy as np
import pandas as pd
import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "mexico_earnings.json.gz")
_CACHE = os.path.join(tempfile.gettempdir(), "enoe_micro_cache")
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}
_MICRO = ("https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/microdatos/"
          "enoe_{y}_trim{q}_csv.zip")
START = (2024, 1)                                     # oldest quarter to include
STAT_COLS = ["mean", "median"]
_SEX = {"total": None, "men": "1", "women": "2"}      # ENOE sex (string): 1=hombre, 2=mujer
_OCC = {
    1: ("Professionals, technicians and arts workers", "Profesionales, técnicos y trabajadores del arte"),
    2: ("Education workers", "Trabajadores de la educación"),
    3: ("Officials and executives", "Funcionarios y directivos"),
    4: ("Office clerks", "Oficinistas"),
    5: ("Industrial workers, artisans and helpers", "Trabajadores industriales, artesanos y ayudantes"),
    6: ("Merchants and sales workers", "Comerciantes"),
    7: ("Transport operators", "Operadores de transporte"),
    8: ("Personal service workers", "Trabajadores en servicios personales"),
    9: ("Protection and security workers", "Trabajadores en protección y vigilancia"),
    10: ("Agricultural workers", "Trabajadores agropecuarios"),
}


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("mexico_latest_year", 2026))
    except Exception:
        return 2026


# ── quarter helpers ──────────────────────────────────────────────────────────
def _label(y, q):
    return f"{y}Q{q}"


def _next_q(y, q):
    return (y, q + 1) if q < 4 else (y + 1, 1)


def _url(y, q):
    return _MICRO.format(y=y, q=q)


def _exists(y, q) -> bool:
    try:
        r = requests.head(_url(y, q), headers=_UA, timeout=25, verify=False, allow_redirects=True)
        return r.status_code == 200 and int(r.headers.get("content-length", 0)) > 1_000_000
    except Exception:
        return False


def available_quarters() -> list[tuple[int, int]]:
    """Every released quarter from START to the newest available."""
    out, (y, q) = [], START
    while _exists(y, q):
        out.append((y, q))
        y, q = _next_q(y, q)
    return out


def latest_available() -> tuple[int, int] | None:
    qs = available_quarters()
    return qs[-1] if qs else None


# ── aggregation ──────────────────────────────────────────────────────────────
def _download(y, q) -> bytes:
    os.makedirs(_CACHE, exist_ok=True)
    fp = os.path.join(_CACHE, f"enoe_{y}t{q}.zip")
    if os.path.exists(fp):
        return open(fp, "rb").read()
    r = requests.get(_url(y, q), headers=_UA, timeout=600, verify=False)
    r.raise_for_status()
    open(fp, "wb").write(r.content)
    return r.content


def _wmedian(vals, wts):
    order = np.argsort(vals)
    v, w = np.asarray(vals)[order], np.asarray(wts)[order]
    cw = np.cumsum(w)
    return float(v[cw >= w.sum() / 2][0])


def _aggregate(y, q, log) -> dict:
    """{sex: {occ_code: [mean, median]}} for one quarter."""
    import zipfile
    log(f"  processing {_label(y, q)} …")
    z = zipfile.ZipFile(io.BytesIO(_download(y, q)))
    member = [n for n in z.namelist() if "sdem" in n.lower() and n.lower().endswith(".csv")][0]
    df = pd.read_csv(z.open(member), encoding="latin-1", low_memory=False,
                     usecols=["c_ocu11c", "ingocup", "fac_tri", "sex", "clase2"])
    emp = df[(df["clase2"] == 1) & (df["ingocup"] > 0) & (df["c_ocu11c"].between(1, 10))]
    out = {}
    for sxname, sxcode in _SEX.items():
        sub = emp if sxcode is None else emp[emp["sex"].astype(str).str.strip() == sxcode]
        sm = {}
        for occ, g in sub.groupby("c_ocu11c"):
            sm[str(int(occ))] = [int(round(float(np.average(g["ingocup"], weights=g["fac_tri"])))),
                                 int(round(_wmedian(g["ingocup"].values, g["fac_tri"].values)))]
        out[sxname] = sm
    return out


def _annualize(quarters: dict) -> dict:
    """Per-quarter aggregates → annual (mean of the year's quarterly values)."""
    by_year: dict = {}
    for label, sm in quarters.items():
        yr = label[:4]
        by_year.setdefault(yr, []).append(sm)
    annual = {}
    for yr, qlist in by_year.items():
        asx = {}
        for sx in ("total", "men", "women"):
            occs = {}
            for occ in (str(i) for i in _OCC):
                vals = [q[sx][occ] for q in qlist if occ in q.get(sx, {})]
                if vals:
                    occs[occ] = [int(round(np.mean([v[i] for v in vals]))) for i in range(len(STAT_COLS))]
            asx[sx] = occs
        annual[yr] = asx
    return annual


def build(out_path: str = OUT, log=print) -> dict:
    # reuse quarterly aggregates already in the snapshot (incremental rebuild)
    existing = {}
    try:
        with gzip.open(out_path, "rt", encoding="utf-8") as f:
            existing = json.load(f).get("quarters", {})
    except Exception:
        pass
    qs = available_quarters()
    if not qs:
        raise RuntimeError("no ENOE quarters available from INEGI")
    log(f"ENOE quarters {_label(*qs[0])}..{_label(*qs[-1])} ({len(qs)}); "
        f"{len(existing)} already in snapshot")
    quarters = {}
    for (y, q) in qs:
        lab = _label(y, q)
        quarters[lab] = existing.get(lab) or _aggregate(y, q, log)

    annual = _annualize(quarters)
    years = sorted(int(y) for y in annual)
    latest_y, latest_q = qs[-1]
    codes_en = {str(k): v[0] for k, v in _OCC.items()}
    codes_es = {str(k): v[1] for k, v in _OCC.items()}
    retrieved = datetime.date.today().isoformat()
    payload = {
        "built_at": retrieved,
        "source": "https://www.inegi.org.mx/programas/enoe/15ymas/",
        "source_name": "INEGI – Encuesta Nacional de Ocupación y Empleo (ENOE), microdata",
        "classification": "ENOE occupation groups (c_ocu11c, SINCO-based)",
        "note": "Survey-weighted mean & median MONTHLY occupational income (MXN), "
                "employed, ENOE microdata. Trend = annual mean of quarters.",
        "years": years, "year": latest_y,
        "latest_quarter": _label(latest_y, latest_q),
        "period_label": _label(latest_y, latest_q),
        "quarter_list": [_label(*yq) for yq in qs],
        "currency": "MXN", "stat_cols": STAT_COLS, "sexes": ["total", "men", "women"],
        "codes": {"EN": codes_en, "ES": codes_es},
        "stats": annual,          # {year: {sex: {occ: [mean, median]}}}  (framework trend)
        "quarters": quarters,     # {label: {sex: {occ: [mean, median]}}} (incremental cache)
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes_en)} occupation groups × 3 sexes, {len(qs)} quarters "
        f"({_label(*qs[0])}–{_label(*qs[-1])}), {len(years)} years ({size/1e6:.3f} MB)")
    return {"built_at": retrieved, "year": latest_y, "codes": len(codes_en),
            "quarters": len(qs), "latest_quarter": _label(latest_y, latest_q), "size": size}


def bundled_info(path: str = OUT) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
        return {"built_at": d.get("built_at"), "year": d.get("year"),
                "period": d.get("period_label"), "latest_quarter": d.get("latest_quarter"),
                "quarters": d.get("quarter_list"), "size": os.path.getsize(path),
                "source": d.get("source")}
    except Exception:
        return {}


if __name__ == "__main__":
    print(build())
