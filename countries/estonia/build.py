"""ISCO occupation labels for Estonia + the pinned data year.

Statistics Estonia table PA633 publishes average gross HOURLY earnings +
headcount by DETAILED ISCO-08 occupation (446 codes, full 1–4-digit hierarchy),
every 4 years (2010/14/18/22). The API codes are "OC" + the ISCO digits
(OC2512); we strip "OC" so the framework sees clean numeric codes (2512) and its
prefix drill-down works — the provider re-adds "OC" to query. Labels EN + ET.
"""
from __future__ import annotations

import datetime
import json
import os
import time

import requests

_ROOTS = {"EN": "https://andmed.stat.ee/api/v1/en/stat/majandus/palk-ja-toojeukulu/tootasu/PA633.PX",
          "ET": "https://andmed.stat.ee/api/v1/et/stat/majandus/palk-ja-toojeukulu/tootasu/PA633.PX"}
OCC_VAR = "Ametiala"
YEAR_VAR = "Vaatlusperiood"
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "estonia_labels.json")
_APP_SETTINGS = os.path.join(_ROOT, "app_settings.json")
DEFAULT_LATEST_YEAR = 2022


def latest_year() -> int:
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("estonia_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def save_latest_year(year: int):
    data = {}
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    data["estonia_latest_year"] = int(year)
    with open(_APP_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _meta(lang: str, tries: int = 6) -> dict:
    last = None
    for _ in range(tries):
        r = requests.get(_ROOTS[lang], timeout=120)
        if r.status_code == 200:
            return r.json()
        last = f"HTTP {r.status_code}"
        time.sleep(4)
    raise RuntimeError(f"Statistics Estonia metadata ({lang}) unavailable: {last}")


def available_years(meta: dict | None = None) -> list[int]:
    meta = meta or _meta("EN")
    yv = next(v for v in meta["variables"] if v["code"] == YEAR_VAR)
    return sorted(int(x) for x in yv["values"] if str(x).isdigit())


def _labels(meta: dict) -> dict[str, str]:
    occ = next(v for v in meta["variables"] if v["code"] == OCC_VAR)
    out = {}
    for c, t in zip(occ["values"], occ["valueTexts"]):
        if c.startswith("OC") and c[2:].isdigit() and 1 <= len(c[2:]) <= 4:
            out[c[2:]] = t.strip()             # "OC2512" → "2512"
    return out


def build(out_path: str = OUT, log=print) -> dict:
    log("fetching ISCO occupation labels (EN) from Statistics Estonia …")
    en = _labels(_meta("EN"))
    try:
        log("fetching ISCO occupation labels (ET) …")
        et = _labels(_meta("ET"))
    except Exception as e:
        log(f"ET labels unavailable ({e}) — falling back to EN")
        et = dict(en)
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": _ROOTS["EN"],
        "classification": "ISCO-08 (all levels 1–4 digit)",
        "codes": {"EN": en, "ET": et},
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)
    leaves = sum(1 for c in en if len(c) == 4)
    log(f"wrote {len(en)} EN + {len(et)} ET codes ({leaves} leaf)")
    return {"built_at": payload["built_at"], "codes": len(en), "leaves": leaves}
