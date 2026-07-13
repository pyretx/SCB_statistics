"""INE Tempus3 (Spain) — Encuesta Cuatrienal de Estructura Salarial → snapshot.

Open INE API (no key). Table 70672 "Medias y percentiles por sexo y grupos y
subgrupos principales de la CNO-11" gives the FULL distribution — mean + P10 +
P25 + median + P75 + P90 — of gross ANNUAL earnings (EUR) by CNO-11 occupation
(major + sub-major, 2 levels) × sex, national. We present gross MONTHLY = annual
/ 12 (the SES is an annual figure; the /12 transform mirrors the UK build).
Percentiles + quartiles + mean + sex + hierarchy — the UK/Slovenia-tier set.

CNO-11 is the Spanish adaptation of ISCO-08: 1-digit major groups map 1:1 to the
ISCO majors and the 2-digit sub-major codes largely match, so EN names reuse the
standard ISCO-08 titles where the code lines up, falling back to the native ES.
"""
from __future__ import annotations

import datetime
import gzip
import json
import os
import re

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "spain_earnings.json.gz")
_B = "https://servicios.ine.es/wstempus/js/ES"
TID = "70672"
_G_OCC = "147826"
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)", "Accept": "application/json"}
STAT_COLS = ["mean", "p10", "p25", "median", "p75", "p90"]
_SEX = {"Total": "total", "Mujeres": "women", "Hombres": "men"}
_MEAS = {"Media": "mean", "10": "p10", "25": "p25", "50": "median", "75": "p75", "90": "p90"}
DEFAULT_LATEST_YEAR = 2018

# ISCO-08 English titles (1-digit majors + 2-digit sub-majors) — reused for EN.
_ISCO_EN = {
    "0": "Armed forces occupations", "1": "Managers", "2": "Professionals",
    "3": "Technicians and associate professionals", "4": "Clerical support workers",
    "5": "Service and sales workers",
    "6": "Skilled agricultural, forestry and fishery workers",
    "7": "Craft and related trades workers",
    "8": "Plant and machine operators, and assemblers", "9": "Elementary occupations",
    "11": "Chief executives, senior officials and legislators",
    "12": "Administrative and commercial managers",
    "13": "Production and specialised services managers",
    "14": "Hospitality, retail and other services managers",
    "21": "Science and engineering professionals", "22": "Health professionals",
    "23": "Teaching professionals", "24": "Business and administration professionals",
    "25": "Information and communications technology professionals",
    "26": "Legal, social and cultural professionals",
    "31": "Science and engineering associate professionals",
    "32": "Health associate professionals",
    "33": "Business and administration associate professionals",
    "34": "Legal, social, cultural and related associate professionals",
    "35": "Information and communications technicians",
    "41": "General and keyboard clerks", "42": "Customer services clerks",
    "43": "Numerical and material recording clerks", "44": "Other clerical support workers",
    "51": "Personal service workers", "52": "Sales workers", "53": "Personal care workers",
    "54": "Protective services workers",
    "61": "Market-oriented skilled agricultural workers",
    "62": "Market-oriented skilled forestry, fishery and hunting workers",
    "63": "Subsistence farmers, fishers, hunters and gatherers",
    "71": "Building and related trades workers, excluding electricians",
    "72": "Metal, machinery and related trades workers",
    "73": "Handicraft and printing workers",
    "74": "Electrical and electronic trades workers",
    "75": "Food processing, wood working, garment and other craft workers",
    "81": "Stationary plant and machine operators", "82": "Assemblers",
    "83": "Drivers and mobile plant operators", "91": "Cleaners and helpers",
    "92": "Agricultural, forestry and fishery labourers",
    "93": "Labourers in mining, construction, manufacturing and transport",
    "94": "Food preparation assistants",
    "95": "Street and related sales and service workers",
    "96": "Refuse workers and other elementary workers",
}


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("spain_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def _get(url, **params):
    r = requests.get(url, params=params or None, headers=_UA, timeout=120, verify=False)
    r.raise_for_status()
    return r.json()


def _occ_map() -> tuple[dict, dict, dict]:
    """Return (name→fw_code, codes_ES, codes_EN). Majors (letter codes) are
    recoded to the 1-digit group derived from their sub-groups' 2-digit codes."""
    vals = _get(f"{_B}/VALORES_GRUPOSTABLA/{TID}/{_G_OCC}")

    def _parents(v):
        p = v.get("FK_JerarquiaPadres")
        if isinstance(p, list):
            return [x.get("Id") if isinstance(x, dict) else x for x in p]
        return [p] if p else []

    children: dict = {}
    for v in vals:
        for pid in _parents(v):
            children.setdefault(pid, []).append(v)

    def fw(v):
        cod = (v.get("Codigo") or "").strip()
        if not cod:                                   # "Todas las ocupaciones"
            return None
        if cod.isdigit():                             # 2-digit sub-major
            return cod
        for c in children.get(v["Id"], []):           # major (letter) → child 1st digit
            cc = (c.get("Codigo") or "").strip()
            if cc.isdigit():
                return cc[0]
        return None

    name2code, es, en = {}, {}, {}
    for v in vals:
        code = fw(v)
        if not code:
            continue
        nom = v["Nombre"].strip()
        name2code[nom] = code
        es[code] = nom
        en[code] = _ISCO_EN.get(code, nom)
    return name2code, es, en


def build(out_path: str = OUT, log=print) -> dict:
    name2code, codes_es, codes_en = _occ_map()
    log(f"ES CNO occupations: {len(codes_es)} codes")
    data = _get(f"{_B}/DATOS_TABLA/{TID}", nult=1)

    stats: dict = {}
    for ser in data:
        segs = [p.strip() for p in ser.get("Nombre", "").rstrip(". ").split(". ") if p.strip()]
        if len(segs) < 5:
            continue
        sx = _SEX.get(segs[2])
        meas = _MEAS.get(segs[-1])
        occ_name = ". ".join(segs[3:-1])
        code = name2code.get(occ_name)
        if not (sx and meas and code):
            continue
        for pt in ser.get("Data", []):
            yr = str(pt.get("Anyo"))
            val = pt.get("Valor")
            if val is None:
                continue
            monthly = int(round(float(val) / 12.0))    # annual EUR → monthly
            (stats.setdefault(yr, {}).setdefault(sx, {})
                  .setdefault(code, {})[meas]) = monthly

    # flatten to STAT_COLS lists
    out_stats: dict = {}
    for yr, sexes in stats.items():
        out_stats[yr] = {}
        for sx, occs in sexes.items():
            out_stats[yr][sx] = {c: [v.get(m) for m in STAT_COLS] for c, v in occs.items()}

    years = sorted(int(y) for y in out_stats)
    latest = max(years) if years else DEFAULT_LATEST_YEAR
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": "https://www.ine.es/jaxiT3/Tabla.htm?t=70672",
        "source_name": "Instituto Nacional de Estadística (INE) — Encuesta de Estructura Salarial",
        "classification": "CNO-11 (ISCO-08) occupation groups (INE table 70672)",
        "note": "Gross monthly earnings (EUR) = official gross ANNUAL / 12; "
                "mean/P10/P25/median/P75/P90 by occupation × sex, national.",
        "years": years, "year": latest, "currency": "EUR",
        "stat_cols": STAT_COLS, "sexes": ["total", "women", "men"],
        "codes": {"EN": codes_en, "ES": codes_es}, "stats": out_stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    leaves = sum(1 for c in codes_en if not any(o != c and o.startswith(c) for o in codes_en))
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes_en)} CNO codes ({leaves} leaf), {len(years)} year(s) "
        f"({size/1e6:.3f} MB)")
    return {"built_at": payload["built_at"], "year": latest, "years": years,
            "codes": len(codes_en), "leaves": leaves, "size": size}


def bundled_info(path: str = OUT) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
        return {"built_at": d.get("built_at"), "year": d.get("year"),
                "years": d.get("years"), "size": os.path.getsize(path),
                "source": d.get("source")}
    except Exception:
        return {}


if __name__ == "__main__":
    print(build())
