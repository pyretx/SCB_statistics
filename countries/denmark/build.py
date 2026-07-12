"""Reusable DISCO-labels build for Denmark + the pinned data year.

Ships with the app (same pattern as countries/norway/build.py) so the admin
panel can refresh disco_labels.json at runtime. Labels come from the LONS20
table metadata in EN + DA; every numeric level (1–4 digit) is kept — consumers
slice by len(code) (4 = leaf occupation, <4 = group).
"""
from __future__ import annotations

import datetime
import json
import os
import time

import requests

BASE = "https://api.statbank.dk/v1"
TABLE = "LONS20"
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "disco_labels.json")

# ── Denmark's pinned data year — same pattern as Norway/Sweden: values are
# fetched live from DST, but the displayed year range is pinned in
# app_settings.json (key "denmark_latest_year"); the admin panel's update
# service bumps it when DST publishes a new year. ─────────────────────────────
_APP_SETTINGS = os.path.join(_ROOT, "app_settings.json")
DEFAULT_LATEST_YEAR = 2024
FIRST_YEAR = 2013


def latest_year() -> int:
    """The pinned newest Denmark data year (app_settings.json, shared file)."""
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("denmark_latest_year", DEFAULT_LATEST_YEAR))
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
    data["denmark_latest_year"] = int(year)
    with open(_APP_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _tableinfo(lang: str, tries: int = 6) -> dict:
    """POST /tableinfo for LONS20 in 'en' | 'da', retrying transient errors."""
    last = None
    for _ in range(tries):
        r = requests.post(f"{BASE}/tableinfo",
                          json={"lang": lang, "table": TABLE}, timeout=120)
        if r.status_code == 200:
            return r.json()
        last = f"HTTP {r.status_code}"
        time.sleep(4)
    raise RuntimeError(f"DST metadata ({lang}) unavailable: {last}")


def available_years(info: dict | None = None) -> list[int]:
    """Published Tid values from the table metadata (update checks)."""
    info = info or _tableinfo("en")
    tid = next(v for v in info["variables"] if v["id"] == "Tid")
    return sorted(int(x["id"]) for x in tid["values"] if x["id"].isdigit())


def _labels(info: dict) -> dict[str, str]:
    """{code: name} for every numeric DISCO code. DST prefixes each text with
    the code itself ('0110 Commissioned …') — strip it."""
    arbf = next(v for v in info["variables"] if v["id"] == "ARBF")
    out = {}
    for x in arbf["values"]:
        code, text = x["id"], x["text"]
        if not (code.isdigit() and 1 <= len(code) <= 4):
            continue                       # skip the TOT roll-up
        if text.startswith(code):
            text = text[len(code):].strip()
        out[code] = text
    return out


def build(out_path: str = OUT, log=print) -> dict:
    """Fetch EN + DA labels and atomically (re)write disco_labels.json.
    Returns {built_at, codes, leaves}."""
    log("fetching DISCO labels (EN) from DST …")
    en = _labels(_tableinfo("en"))
    log("fetching DISCO labels (DA) from DST …")
    da = _labels(_tableinfo("da"))
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": f"{BASE}/tableinfo · {TABLE}",
        "classification": "DISCO-08 (ISCO-08 aligned); all levels 1–4 digit",
        "codes": {"EN": en, "DA": da},
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)                       # atomic swap on success
    leaves = sum(1 for c in en if len(c) == 4)
    log(f"wrote {len(en)} EN + {len(da)} DA codes ({leaves} leaf)")
    return {"built_at": payload["built_at"], "codes": len(en), "leaves": leaves}
