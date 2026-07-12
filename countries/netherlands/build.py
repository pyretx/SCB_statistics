"""Occupation labels + code map for the Netherlands (CBS table 85517NED).

CBS's OData occupation dimension ('Beroep') uses OPAQUE keys (A000164) whose
Title carries the BRC-2014 numeric code + Dutch name ("0112 Docenten
beroepsgerichte vakken"). The framework wants the numeric code (so its
prefix-hierarchy drill-down works), so we split each title into
  numeric_code (01 / 011 / 0111)  +  name
and keep a keymap {numeric_code: opaque CBS key} for querying. Names are Dutch —
CBS publishes no English occupation names for this table.
"""
from __future__ import annotations

import datetime
import json
import os
import time

import requests

BASE = "https://opendata.cbs.nl/ODataApi/odata/85517NED/"
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "netherlands_labels.json")
_APP_SETTINGS = os.path.join(_ROOT, "app_settings.json")
DEFAULT_LATEST_YEAR = 2024


def latest_year() -> int:
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("netherlands_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def save_latest_year(year: int):
    data = {}
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    data["netherlands_latest_year"] = int(year)
    with open(_APP_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get(path, tries=6):
    last = None
    for _ in range(tries):
        r = requests.get(BASE + path, timeout=120)
        if r.status_code == 200:
            return r.json()["value"]
        last = f"HTTP {r.status_code}"
        time.sleep(4)
    raise RuntimeError(f"CBS metadata unavailable ({path}): {last}")


def available_years() -> list[int]:
    per = _get("Perioden")
    return sorted(int(p["Key"][:4]) for p in per if p["Key"][:4].isdigit())


def _parse() -> tuple[dict, dict]:
    """→ (codes {numeric: dutch_name}, keymap {numeric: cbs_key})."""
    codes, keymap = {}, {}
    for v in _get("Beroep"):
        key, title = v["Key"], (v.get("Title") or "").strip()
        parts = title.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit() and 1 <= len(parts[0]) <= 4:
            codes[parts[0]] = parts[1]
            keymap[parts[0]] = key
    return codes, keymap


def build(out_path: str = OUT, log=print) -> dict:
    log("fetching BRC occupation labels from CBS (85517NED) …")
    codes, keymap = _parse()
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": BASE,
        "classification": "BRC 2014 (Beroepenindeling ROA-CBS); levels 2–4 digit",
        "codes": {"EN": codes, "NL": codes},     # Dutch names (no English published)
        "keymap": keymap,
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)
    leaves = sum(1 for c in codes if len(c) == 4)
    log(f"wrote {len(codes)} BRC codes ({leaves} leaf)")
    return {"built_at": payload["built_at"], "codes": len(codes), "leaves": leaves}
