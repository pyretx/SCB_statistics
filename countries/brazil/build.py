"""IBGE (PNAD Contínua) via the open SIDRA/aggregates API → bundled Brazil snapshot.

IBGE's aggregates API is fully open (no key). Table 9457 (SDG indicator 8.5.1)
gives the average HOURLY earnings by occupational grouping (ISCO major group) for
2012→, nationally. Brazil's PNAD publishes occupation only at the 10 ISCO major
groups (finer CBO detail lives in RAIS microdata), and this series has no sex or
median — just the average, but a long 2012→ trend.

We present a gross MONTHLY figure = average HOURLY earnings × a standard full-time
month (44 h/week × 52 / 12 ≈ 190.7 h) — a full-time-equivalent estimate, clearly
labelled. Occupation names are the official ISCO major groups (EN + PT).
"""
from __future__ import annotations

import datetime
import gzip
import json
import os

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "brazil_earnings.json.gz")
AGG = "https://servicodados.ibge.gov.br/api/v3/agregados"
TABLE, VAR, OCC_CLASSIF = "9457", "8828", "694"
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}
STAT_COLS = ["mean"]
_HOURS_PER_MONTH = 44 * 52 / 12          # Brazilian full-time month ≈ 190.7 h
# IBGE occupation-category id → (ISCO major-group code, EN name, PT name)
_OCC = {
    "33370": ("1", "Managers", "Diretores e gerentes"),
    "33371": ("2", "Professionals", "Profissionais das ciências e intelectuais"),
    "33372": ("3", "Technicians and associate professionals", "Técnicos e profissionais de nível médio"),
    "33373": ("4", "Clerical support workers", "Trabalhadores de apoio administrativo"),
    "33374": ("5", "Service and sales workers", "Trabalhadores dos serviços e vendedores"),
    "33375": ("6", "Skilled agricultural, forestry and fishery workers", "Trabalhadores qualificados da agropecuária"),
    "33376": ("7", "Craft and related trades workers", "Trabalhadores qualificados da construção e artesãos"),
    "33377": ("8", "Plant and machine operators, and assemblers", "Operadores de instalações e máquinas"),
    "33378": ("9", "Elementary occupations", "Ocupações elementares"),
    "33379": ("0", "Armed forces occupations", "Membros das forças armadas e policiais"),
}
DEFAULT_LATEST_YEAR = 2025


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("brazil_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def _num(v):
    if v in (None, "", "-", "..", "...", "X"):
        return None
    try:
        return float(str(v).replace(",", "."))
    except (ValueError, TypeError):
        return None


def build(out_path: str = OUT, log=print) -> dict:
    log(f"fetching IBGE table {TABLE} (national, all years) …")
    url = (f"{AGG}/{TABLE}/periodos/all/variaveis/{VAR}"
           f"?localidades=N1[all]&classificacao={OCC_CLASSIF}[all]")
    d = requests.get(url, headers=_UA, timeout=120).json()
    codes_en, codes_pt = {}, {}
    stats: dict = {}          # {year: {occ_code: [mean_monthly]}}
    for res in d[0]["resultados"]:
        cat = res["classificacoes"][0]["categoria"]
        catid = next(iter(cat))
        if catid not in _OCC:
            continue
        code, en, pt = _OCC[catid]
        codes_en[code], codes_pt[code] = en, pt
        for serie in res["series"]:
            for yr, val in serie["serie"].items():
                h = _num(val)
                if h is None:
                    continue
                stats.setdefault(str(int(yr)), {})[code] = [int(round(h * _HOURS_PER_MONTH))]

    years = sorted(int(y) for y in stats)
    latest = max(years) if years else DEFAULT_LATEST_YEAR
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": f"https://sidra.ibge.gov.br/tabela/{TABLE}",
        "source_name": "IBGE – Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua)",
        "classification": "ISCO-08 major groups (IBGE PNAD Contínua, table 9457)",
        "note": "Est. gross MONTHLY = average HOURLY earnings × 190.7 h (full-time "
                "month); average only, no sex; occupation = 10 ISCO major groups.",
        "years": years, "year": latest, "currency": "BRL",
        "stat_cols": STAT_COLS, "sexes": ["total"],
        "codes": {"EN": codes_en, "PT": codes_pt}, "stats": stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes_en)} occupation groups, {len(years)} years "
        f"({min(years)}–{latest}) ({size/1e6:.3f} MB)")
    return {"built_at": payload["built_at"], "year": latest, "years": years,
            "codes": len(codes_en), "size": size}


def bundled_info(path: str = OUT) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            dd = json.load(f)
        return {"built_at": dd.get("built_at"), "year": dd.get("year"),
                "years": dd.get("years"), "size": os.path.getsize(path),
                "source": dd.get("source")}
    except Exception:
        return {}


if __name__ == "__main__":
    print(build())
