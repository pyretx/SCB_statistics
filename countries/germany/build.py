"""Destatis GENESIS-Online table 62361-0030 → bundled Germany snapshot.

Statistisches Bundesamt (Destatis), GENESIS-Online REST API 2020. Table
62361-0030 "Gross hourly earnings, gross monthly earnings: Germany, reference
month, sex, occupations" — gross MONTHLY mean (VST047) and median (VST052) by
KldB 2010 occupation × sex, with official EN + DE occupation names. We fetch it
at build time (needs the GENESIS API token) and ship a small gzipped snapshot
the provider reads at runtime (no token on the hot path).

Data licence: this data is used under "Datenlizenz Deutschland – Namensnennung –
Version 2.0" (dl-de/by-2-0). Required attribution is emitted on the page (see
config.py ATTRIBUTION) and stored in the snapshot meta.

The GENESIS ffcsv (flat CSV, ';'-separated, returned zipped) carries one row per
occupation × sex × measure:
  col4  time            e.g. 2025-04P1M (reference month April 2025)
  col11 sex code        '' = Total · GESM = Male · GESW = Female
  col15 occupation code KB10-<digits> (KldB 2010; 2 / 3 / 5-digit levels)
  col16 occupation name (in the requested language)
  col17 value · col19 measure code (VST047 mean- / VST052 median-monthly EUR;
        VST045/VST051 are the hourly pair, ignored)
KldB nests by prefix (5-digit 11101 → 3-digit 111 → 2-digit 11).
"""
from __future__ import annotations

import csv
import datetime
import gzip
import io
import json
import os
import zipfile

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "germany_kldb.json.gz")
_APP_SETTINGS = os.path.join(_ROOT, "app_settings.json")

GENESIS = "https://www-genesis.destatis.de/genesisWS/rest/2020/"
TABLE = "62361-0030"
SOURCE_URL = f"https://www-genesis.destatis.de/datenbank/online/statistic/62361/table/{TABLE}"
STAT_COLS = ["mean", "median"]
_SEX = {"": "total", "GESM": "men", "GESW": "women"}
_MEASURE = {"VST047": "mean", "VST052": "median"}     # gross MONTHLY (excl. special pay)
DEFAULT_LATEST_YEAR = 2025


def latest_year() -> int:
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("germany_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def save_latest_year(year: int):
    data = {}
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    data["germany_latest_year"] = int(year)
    with open(_APP_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _token() -> str:
    """GENESIS API token — from Streamlit secrets (app/admin, incl. the server's
    mounted secrets), a known secrets.toml, or the GENESIS_API_KEY env var."""
    try:
        import streamlit as st
        t = (st.secrets.get("genesis", {}) or {}).get("api_key")
        if t:
            return t
    except Exception:
        pass
    import tomllib
    for p in (os.path.join(_ROOT, ".streamlit", "secrets.toml"), "/root/scb-secrets.toml"):
        try:
            with open(p, "rb") as f:
                t = (tomllib.load(f).get("genesis", {}) or {}).get("api_key")
                if t:
                    return t
        except Exception:
            pass
    return os.environ.get("GENESIS_API_KEY", "")


def _fetch_ffcsv(lang: str) -> list[list[str]]:
    token = _token()
    if not token:
        raise RuntimeError("GENESIS API token missing ([genesis] api_key in secrets.toml)")
    r = requests.post(GENESIS + "data/tablefile",
                      headers={"username": token, "password": ""},
                      data={"name": TABLE, "area": "all", "format": "ffcsv",
                            "language": lang, "compress": "false"}, timeout=240)
    r.raise_for_status()
    raw = r.content
    if raw[:2] == b"PK":                              # GENESIS returns a zip
        z = zipfile.ZipFile(io.BytesIO(raw))
        raw = z.read([n for n in z.namelist() if n.endswith(".csv")][0])
    return list(csv.reader(io.StringIO(raw.decode("utf-8-sig", "replace"), newline=""),
                           delimiter=";"))


def _num(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", ".")
    if not s or s in ("-", ".", "...", "/", "x", "()", "…"):
        return None
    try:
        return int(round(float(s)))
    except ValueError:
        return None


def build(out_path: str = OUT, log=print) -> dict:
    log(f"fetching GENESIS {TABLE} (en + de) …")
    rows_en = _fetch_ffcsv("en")
    rows_de = _fetch_ffcsv("de")

    # names per language, stats + year from the EN pull (values are language-agnostic)
    names_en, names_de = {}, {}
    for r in rows_de[1:]:
        if len(r) > 16:
            names_de[r[15].replace("KB10-", "")] = r[16].strip()
    stats: dict[str, dict] = {"total": {}, "men": {}, "women": {}}
    year = DEFAULT_LATEST_YEAR
    for r in rows_en[1:]:
        if len(r) <= 20:
            continue
        sex = _SEX.get(r[11])
        measure = _MEASURE.get(r[19])
        if sex is None or measure is None:
            continue
        code = r[15].replace("KB10-", "")
        if not code.isdigit() or len(code) not in (2, 3, 5):
            continue
        names_en[code] = r[16].strip()
        slot = stats[sex].setdefault(code, {})
        slot[measure] = _num(r[17])
        t = r[4]
        if t[:4].isdigit():
            year = int(t[:4])

    # Synthesize 4-digit KldB base occupations (Berufsuntergruppe) from the
    # 5-digit skill-level leaves, so the drill-down groups skill levels under
    # their occupation and the Skill-levels tab can pick a base directly. The
    # base name is the leaf name minus its ' - <level>' suffix. There is no
    # earnings figure at this level (the table publishes 2/3/5-digit only), so
    # these are navigation-only group nodes — not leaves, no stats row.
    def _add_bases(names):
        for c in [c for c in names if len(c) == 5]:
            names.setdefault(c[:4], names[c].rsplit(" - ", 1)[0])
    _add_bases(names_en)
    _add_bases(names_de)

    # flatten each occupation's measures to STAT_COLS order
    codes = names_en
    out_stats = {sex: {c: [d.get(m) for m in STAT_COLS] for c, d in cmap.items()}
                 for sex, cmap in stats.items()}
    leaves = sum(1 for c in codes if len(c) == 5)
    retrieved = datetime.date.today().isoformat()
    payload = {
        "built_at": retrieved,
        "retrieved": retrieved,
        "source": SOURCE_URL,
        "source_name": "Statistisches Bundesamt (Destatis), GENESIS-Online",
        "table": TABLE,
        "licence": "Datenlizenz Deutschland – Namensnennung – Version 2.0 (dl-de/by-2-0)",
        "classification": "KldB 2010 (Destatis GENESIS 62361-0030)",
        "note": "Gross MONTHLY earnings (EUR, excl. special payments), full-time; "
                "mean (VST047) + median (VST052), by occupation × sex.",
        "year": year,
        "currency": "EUR",
        "stat_cols": STAT_COLS,
        "sexes": ["total", "men", "women"],
        "codes": {"EN": codes, "DE": names_de},
        "stats": out_stats,
    }
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, out_path)
    size = os.path.getsize(out_path)
    log(f"wrote {len(codes)} KldB codes ({leaves} leaf) × 3 sexes, year {year} "
        f"({size / 1e6:.2f} MB)")
    return {"built_at": retrieved, "year": year, "codes": len(codes),
            "leaves": leaves, "size": size}


def bundled_info(path: str = OUT) -> dict:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
        return {"built_at": d.get("built_at"), "year": d.get("year"),
                "size": os.path.getsize(path), "source": d.get("source"),
                "retrieved": d.get("retrieved")}
    except Exception:
        return {}


if __name__ == "__main__":
    print(build())
