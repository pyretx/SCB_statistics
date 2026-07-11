"""Reusable STYRK-labels build for Norway.

This module SHIPS with the app (unlike the dockerignored build_styrk_labels.py
CLI), so the admin panel's "Rebuild labels" can refresh styrk_labels.json at
runtime. Fetches the 11418 'Yrke' variable metadata in EN + NO and keeps every
numeric level (1–4 digit). See build_styrk_labels.py for the CLI entry point.
"""
from __future__ import annotations

import datetime
import json
import os
import time

import requests

BASE = "https://data.ssb.no/api/v0/{lang}/table/11418"
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "styrk_labels.json")

# ── Norway's pinned data year — same pattern as Sweden's latest_data_year:
# salaries are fetched live from SSB, but the app pins the displayed year range
# in app_settings.json (key "norway_latest_year"); the admin panel's update
# service bumps it when SSB publishes a new year. ─────────────────────────────
_APP_SETTINGS = os.path.join(_ROOT, "app_settings.json")
DEFAULT_LATEST_YEAR = 2024


def latest_year() -> int:
    """The pinned newest Norway data year (app_settings.json, shared file)."""
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("norway_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def save_latest_year(year: int):
    """Bump the pinned year (preserves every other key in the shared file)."""
    data = {}
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    data["norway_latest_year"] = int(year)
    with open(_APP_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# SSB's table variable omits the 1-digit roll-up for majors 0 and 3, so the
# major-group drill-down would miss two labels. Fill any absent 1-digit code
# with the standard STYRK-08 major-group name (ISCO-08 aligned).
MAJORS = {
    "EN": {"0": "Armed forces occupations", "1": "Managers", "2": "Professionals",
           "3": "Technicians and associate professionals", "4": "Clerical support workers",
           "5": "Service and sales workers",
           "6": "Skilled agricultural, forestry and fishery workers",
           "7": "Craft and related trades workers",
           "8": "Plant and machine operators and assemblers", "9": "Elementary occupations"},
    "NO": {"0": "Militære yrker og uoppgitt", "1": "Ledere", "2": "Akademiske yrker",
           "3": "Høyskoleyrker", "4": "Kontoryrker", "5": "Salgs- og serviceyrker",
           "6": "Bønder, fiskere mv.", "7": "Håndverkere",
           "8": "Prosess- og maskinoperatører, transportarbeidere mv.",
           "9": "Renholdere, hjelpearbeidere mv."},
}


def _fetch_yrke(lang: str) -> dict[str, str]:
    """{code: name} for every numeric STYRK code (all levels) in the given
    Statbank language ('en' | 'no'). Retries the transient 503s SSB throws."""
    url = BASE.format(lang=lang)
    last = None
    for _ in range(6):
        r = requests.get(url, timeout=180)
        if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
            yrke = next(v for v in r.json()["variables"] if v["code"] == "Yrke")
            return {c: t for c, t in zip(yrke["values"], yrke["valueTexts"])
                    if c.isdigit() and 1 <= len(c) <= 4}
        last = f"HTTP {r.status_code}"
        time.sleep(4)
    raise RuntimeError(f"SSB metadata ({lang}) unavailable: {last}")


def build(out_path: str = OUT, log=print) -> dict:
    """Fetch EN + NO labels and atomically (re)write styrk_labels.json.
    Returns {built_at, codes, leaves}."""
    log("fetching STYRK labels (EN) from SSB …")
    en = _fetch_yrke("en")
    log("fetching STYRK labels (NO) from SSB …")
    no = _fetch_yrke("no")
    for one, name in MAJORS["EN"].items():
        en.setdefault(one, name)
    for one, name in MAJORS["NO"].items():
        no.setdefault(one, name)
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": BASE.format(lang="en"),
        "classification": "STYRK-08 (ISCO-08 aligned); all levels 1–4 digit",
        # one flat {code: name} per language, every level; consumers slice by
        # len(code) (4 = leaf occupation, <4 = group).
        "codes": {"EN": en, "NO": no},
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)                       # atomic swap on success
    leaves = sum(1 for c in en if len(c) == 4)
    log(f"wrote {len(en)} EN + {len(no)} NO codes ({leaves} leaf)")
    return {"built_at": payload["built_at"], "codes": len(en), "leaves": leaves}
