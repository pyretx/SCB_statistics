"""ISCO major-group labels for Estonia + the pinned data year.

Statistics Estonia's Structure of Earnings table PA623 publishes earnings only
by ISCO-08 MAJOR GROUP (OC0–OC9, 10 groups) — no detailed occupations — every
4 years (2010/14/18/22). Labels come from the table's 'Ametiala pearühm'
variable in EN + ET; codes are the OCx groups (flat, no hierarchy).
"""
from __future__ import annotations

import datetime
import json
import os
import time

import requests

_ROOTS = {"EN": "https://andmed.stat.ee/api/v1/en/stat/majandus/palk-ja-toojeukulu/tootasu/PA623.PX",
          "ET": "https://andmed.stat.ee/api/v1/et/stat/majandus/palk-ja-toojeukulu/tootasu/PA623.PX"}
OCC_VAR = "Ametiala pearühm"
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
    return {c: t.strip() for c, t in zip(occ["values"], occ["valueTexts"])
            if c != "_T"}                     # OC0–OC9, drop the Total row


def build(out_path: str = OUT, log=print) -> dict:
    log("fetching ISCO major-group labels (EN) from Statistics Estonia …")
    en = _labels(_meta("EN"))
    try:
        log("fetching ISCO major-group labels (ET) …")
        et = _labels(_meta("ET"))
    except Exception as e:
        log(f"ET labels unavailable ({e}) — falling back to EN")
        et = dict(en)
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": _ROOTS["EN"],
        "classification": "ISCO-08 major groups (OC0–OC9)",
        "codes": {"EN": en, "ET": et},
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)
    log(f"wrote {len(en)} EN + {len(et)} ET major groups")
    return {"built_at": payload["built_at"], "codes": len(en), "leaves": len(en)}
