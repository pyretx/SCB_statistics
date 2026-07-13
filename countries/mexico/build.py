"""INEGI ENOE microdata → bundled Mexico snapshot.

INEGI's indicator API and the ENOE tabulados don't expose an average/median salary
by occupation (the tabulados give income BANDS in minimum wages). The real figures
come from the ENOE MICRODATA — the open, free record-level file (no token). We
download one quarter's SDEMT table and compute the survey-WEIGHTED mean and median
monthly occupational income (ingocup, MXN) by the 10 ENOE occupation groups
(c_ocu11c, coded from SINCO) × sex, using the sampling weight fac_tri.

Big download (~39 MB zip → parse the SDEMT csv), so this ships as a bundled
snapshot the provider reads.
"""
from __future__ import annotations

import datetime
import gzip
import io
import json
import os
import tempfile
import zipfile

import numpy as np
import pandas as pd
import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "mexico_earnings.json.gz")
_CACHE = os.path.join(tempfile.gettempdir(), "enoe_micro_cache")
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}

YEAR, TRIM = 2025, 2
ZIP_URL = ("https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/microdatos/"
           f"enoe_{YEAR}_trim{TRIM}_csv.zip")
STAT_COLS = ["mean", "median"]
_SEX = {"total": None, "men": "1", "women": "2"}      # ENOE sex (string): 1=hombre, 2=mujer
# c_ocu11c → (EN name, ES name); 0/11 excluded (n/a, unspecified)
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
DEFAULT_LATEST_YEAR = YEAR


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("mexico_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def _download() -> bytes:
    os.makedirs(_CACHE, exist_ok=True)
    fp = os.path.join(_CACHE, f"enoe_{YEAR}t{TRIM}.zip")
    if os.path.exists(fp):
        return open(fp, "rb").read()
    r = requests.get(ZIP_URL, headers=_UA, timeout=600, verify=False)
    r.raise_for_status()
    open(fp, "wb").write(r.content)
    return r.content


def _wmedian(vals, wts):
    order = np.argsort(vals)
    v, w = np.asarray(vals)[order], np.asarray(wts)[order]
    cw = np.cumsum(w)
    return float(v[cw >= w.sum() / 2][0])


def build(out_path: str = OUT, log=print) -> dict:
    log(f"downloading ENOE microdata {ZIP_URL.rsplit('/', 1)[1]} …")
    z = zipfile.ZipFile(io.BytesIO(_download()))
    member = [n for n in z.namelist() if "sdem" in n.lower() and n.lower().endswith(".csv")][0]
    df = pd.read_csv(z.open(member), encoding="latin-1", low_memory=False,
                     usecols=["c_ocu11c", "ingocup", "fac_tri", "sex", "clase2"])
    emp = df[(df["clase2"] == 1) & (df["ingocup"] > 0) & (df["c_ocu11c"].between(1, 10))]
    log(f"  {len(emp):,} employed records with occupational income")

    stats: dict = {"total": {}, "men": {}, "women": {}}
    for sxname, sxcode in _SEX.items():
        sub = emp if sxcode is None else emp[emp["sex"].astype(str).str.strip() == sxcode]
        for occ, g in sub.groupby("c_ocu11c"):
            code = str(int(occ))
            mean = float(np.average(g["ingocup"], weights=g["fac_tri"]))
            median = _wmedian(g["ingocup"].values, g["fac_tri"].values)
            stats[sxname][code] = [int(round(mean)), int(round(median))]

    codes_en = {str(k): v[0] for k, v in _OCC.items()}
    codes_es = {str(k): v[1] for k, v in _OCC.items()}
    retrieved = datetime.date.today().isoformat()
    payload = {
        "built_at": retrieved,
        "source": "https://www.inegi.org.mx/programas/enoe/15ymas/",
        "source_name": "INEGI – Encuesta Nacional de Ocupación y Empleo (ENOE), microdata",
        "classification": "ENOE occupation groups (c_ocu11c, SINCO-based)",
        "note": f"Survey-weighted mean & median MONTHLY occupational income (MXN), "
                f"employed, ENOE Q{TRIM} {YEAR}. Occupation = 10 ENOE groups.",
        "year": YEAR, "period_label": f"Q{TRIM} {YEAR}", "currency": "MXN",
        "stat_cols": STAT_COLS, "sexes": ["total", "men", "women"],
        "codes": {"EN": codes_en, "ES": codes_es}, "stats": stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes_en)} occupation groups × 3 sexes, Q{TRIM} {YEAR} "
        f"({size/1e6:.3f} MB)")
    return {"built_at": retrieved, "year": YEAR, "codes": len(codes_en), "size": size}


def bundled_info(path: str = OUT) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
        return {"built_at": d.get("built_at"), "year": d.get("year"),
                "period": d.get("period_label"), "size": os.path.getsize(path),
                "source": d.get("source")}
    except Exception:
        return {}


if __name__ == "__main__":
    print(build())
