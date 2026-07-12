"""Reusable ISCO-labels build for Finland + the pinned data year.

StatFin's Structure of Earnings table 15au (occupation) is an annual SNAPSHOT
(one year in the cube at a time), so Finland has no trend. Labels come from the
'ammatti' (occupation) metadata in EN + FI; StatFin variable codes are versioned
(ammatti_19_20180101), so they're resolved by prefix at runtime.
"""
from __future__ import annotations

import datetime
import json
import os
import time

import requests

TABLE = "15au"
_ROOTS = {"EN": f"https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin/pra/{TABLE}.px",
          "FI": f"https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/pra/{TABLE}.px"}
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "finland_labels.json")
_APP_SETTINGS = os.path.join(_ROOT, "app_settings.json")
DEFAULT_LATEST_YEAR = 2024


def latest_year() -> int:
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("finland_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def save_latest_year(year: int):
    data = {}
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    data["finland_latest_year"] = int(year)
    with open(_APP_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get(url, tries=6):
    last = None
    for _ in range(tries):
        r = requests.get(url, timeout=120)
        if r.status_code == 200:
            return r.json()
        last = f"HTTP {r.status_code}"
        time.sleep(4)
    raise RuntimeError(f"StatFin metadata unavailable: {last}")


def var_codes(meta: dict) -> dict:
    """{prefix: full_versioned_code} for the table's variables (ammatti, …)."""
    return {v["code"].split("_")[0]: v["code"] for v in meta["variables"]}


def _labels(meta: dict) -> dict[str, str]:
    occ = next(v for v in meta["variables"] if v["code"].startswith("ammatti"))
    out = {}
    for code, text in zip(occ["values"], occ["valueTexts"]):
        if not (code.isdigit() and 1 <= len(code) <= 4):
            continue                          # skip 'SSS' total
        name = text.strip()
        if name.startswith(code):
            name = name[len(code):].strip()
        out[code] = name or code
    return out


def build(out_path: str = OUT, log=print) -> dict:
    log("fetching ISCO labels (EN) from StatFin …")
    en = _labels(_get(_ROOTS["EN"]))
    log("fetching ISCO labels (FI) from StatFin …")
    fi = _labels(_get(_ROOTS["FI"]))
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": _ROOTS["EN"],
        "classification": "Classification of Occupations 2010 (ISCO-08); levels 1–4 digit",
        "codes": {"EN": en, "FI": fi},
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)
    leaves = sum(1 for c in en if len(c) == 4)
    log(f"wrote {len(en)} EN + {len(fi)} FI codes ({leaves} leaf)")
    return {"built_at": payload["built_at"], "codes": len(en), "leaves": leaves}
