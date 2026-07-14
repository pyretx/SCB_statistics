"""Japan — e-Stat API, Basic Survey on Wage Structure (賃金構造基本統計調査).

Open e-Stat API (needs a free app_id in secrets [estat] app_id). Table
0003426334 (一般_職種（大分類）DB) gives 所定内給与額 (scheduled monthly cash
earnings) by the 11 major occupation groups (JSCO 2020) × sex, national, 2020–2023
(→ a trend). e-Stat serves the value in 千円 (thousand yen) → ×1000 = yen/month.
Occupation names are Japanese-only in e-Stat, so EN titles are supplied here; JA
native names come from the API. Mean monthly earnings + sex + trend.
"""
from __future__ import annotations

import datetime
import gzip
import json
import os

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "japan_earnings.json.gz")
_B = "https://api.e-stat.go.jp/rest/3.0/app/json"
TID = "0003426334"
_UA = {"User-Agent": "Mozilla/5.0 (salary-explorer; research)"}
STAT_COLS = ["mean"]
_TAB = "42"          # 所定内給与額 (scheduled monthly cash earnings)
_SIZE = "01"         # 企業規模計（10人以上）
_SEX = {"01": "total", "02": "men", "03": "women"}
# JSCO 2020 major-group code → (framework code, EN name)
_OCC = {
    "010": ("01", "Managers"),
    "020": ("02", "Professionals and engineers"),
    "030": ("03", "Clerical workers"),
    "040": ("04", "Sales workers"),
    "050": ("05", "Service workers"),
    "060": ("06", "Security and protective service workers"),
    "070": ("07", "Agriculture, forestry and fishery workers"),
    "080": ("08", "Manufacturing process workers"),
    "090": ("09", "Transport and machine operation workers"),
    "100": ("10", "Construction and mining workers"),
    "110": ("11", "Carrying, cleaning, packaging and related workers"),
}


def _app_id() -> str:
    try:
        import streamlit as st
        v = (st.secrets.get("estat") or {}).get("app_id")
        if v:
            return v
    except Exception:
        pass
    import tomllib
    for p in (os.path.join(_ROOT, ".streamlit", "secrets.toml"),
              "/root/scb-secrets.toml"):
        try:
            with open(p, "rb") as f:
                v = (tomllib.load(f).get("estat") or {}).get("app_id")
            if v:
                return v
        except Exception:
            continue
    return os.environ.get("ESTAT_APP_ID", "")


def latest_year() -> int:
    try:
        with open(os.path.join(_ROOT, "app_settings.json"), encoding="utf-8") as f:
            return int(json.load(f).get("japan_latest_year", 2023))
    except Exception:
        return 2023


def build(out_path: str = OUT, log=print) -> dict:
    app = _app_id()
    if not app:
        raise RuntimeError("e-Stat app_id missing ([estat] app_id in secrets)")
    # native JA names from the classification metadata
    m = requests.get(f"{_B}/getMetaInfo", params={"appId": app, "statsDataId": TID},
                     headers=_UA, timeout=90, verify=False).json()
    ja = {}
    for cls in m.get("GET_META_INFO", {}).get("METADATA_INF", {}).get("CLASS_INF", {}).get("CLASS_OBJ", []):
        if cls.get("@id") == "cat03":
            for o in (cls.get("CLASS") or []):
                ja[o.get("@code")] = o.get("@name")

    d = requests.get(f"{_B}/getStatsData", params={
        "appId": app, "statsDataId": TID, "cdTab": _TAB, "cdCat01": _SIZE},
        headers=_UA, timeout=120, verify=False).json()
    vals = d.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {}).get("DATA_INF", {}).get("VALUE", [])

    stats: dict = {}
    for v in vals:
        occ = v.get("@cat03")
        sx = _SEX.get(v.get("@cat02"))
        if occ not in _OCC or not sx:
            continue
        raw = v.get("$")
        try:
            yen = int(round(float(raw) * 1000))     # 千円 → yen
        except (TypeError, ValueError):
            continue
        yr = str(int(v.get("@time", "0")[:4]))
        code = _OCC[occ][0]
        (stats.setdefault(yr, {}).setdefault(sx, {})[code]) = [yen]

    codes_en = {c: n for _, (c, n) in _OCC.items()}
    codes_ja = {_OCC[k][0]: ja.get(k, _OCC[k][1]) for k in _OCC}
    years = sorted(int(y) for y in stats)
    latest = max(years) if years else latest_year()
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": "https://www.e-stat.go.jp/dbview?sid=0003426334",
        "source_name": "e-Stat — Basic Survey on Wage Structure (賃金構造基本統計調査), MHLW",
        "classification": "JSCO 2020 major occupation groups (e-Stat 0003426334)",
        "note": "Mean scheduled monthly cash earnings (JPY) by major occupation "
                "group × sex, enterprises with 10+ employees, national.",
        "years": years, "year": latest, "currency": "JPY",
        "stat_cols": STAT_COLS, "sexes": ["total", "women", "men"],
        "codes": {"EN": codes_en, "JA": codes_ja}, "stats": stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes_en)} JSCO major groups, {len(years)} years "
        f"({years[0] if years else '?'}–{latest}), {size} bytes")
    return {"built_at": payload["built_at"], "year": latest, "years": years,
            "codes": len(codes_en), "leaves": len(codes_en), "size": size}


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
