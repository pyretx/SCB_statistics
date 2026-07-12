"""Reusable ISCO-labels build for Iceland + the pinned data year.

Ships with the app (same pattern as countries/norway/build.py) so the admin
panel can refresh iceland_labels.json at runtime. Labels come from the VIN02001
occupation ('Starf') metadata in EN + IS; every numeric level (1–4 digit) is
kept — consumers slice by len(code).

Iceland's PxWeb occupation codes are space-padded and star-suffixed ('1   *',
'12  *', '122 *', '1222*'); the CLEAN code (stripped) is what the menu/hierarchy
use, and the provider re-pads it to query the API.
"""
from __future__ import annotations

import datetime
import json
import os
import time

import requests

_PATH = "Samfelag/launogtekjur/1_laun/1_laun/VIN02001.px"
# EN and IS PxWeb roots (Hagstofa serves Icelandic under /pxis/…/is/).
_ROOTS = {"EN": f"https://px.hagstofa.is/pxen/api/v1/en/{_PATH}",
          "IS": f"https://px.hagstofa.is/pxis/api/v1/is/{_PATH}"}
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "iceland_labels.json")

_APP_SETTINGS = os.path.join(_ROOT, "app_settings.json")
DEFAULT_LATEST_YEAR = 2025
FIRST_YEAR = 2014


def latest_year() -> int:
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            return int(json.load(f).get("iceland_latest_year", DEFAULT_LATEST_YEAR))
    except Exception:
        return DEFAULT_LATEST_YEAR


def save_latest_year(year: int):
    data = {}
    try:
        with open(_APP_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    data["iceland_latest_year"] = int(year)
    with open(_APP_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clean_code(c: str) -> str:
    """'1222*' → '1222', '12  *' → '12' (strip padding + star)."""
    return c.replace("*", "").strip()


def api_code(clean: str) -> str:
    """'1222' → '1222*', '12' → '12  *' (re-pad to width 4 + star)."""
    return clean.ljust(4) + "*"


def _url(lang: str) -> str:
    return _ROOTS.get(lang, _ROOTS["EN"])


def _fetch_starf(lang: str, tries: int = 6) -> dict[str, str]:
    """{clean_code: name} for every numeric ISCO code in the given language."""
    last = None
    for _ in range(tries):
        r = requests.get(_url(lang), timeout=120)
        if r.status_code == 200:
            starf = next(v for v in r.json()["variables"] if v["code"] == "Starf")
            out = {}
            for code, text in zip(starf["values"], starf["valueTexts"]):
                cc = clean_code(code)
                if not (cc.isdigit() and 1 <= len(cc) <= 4):
                    continue
                # texts are prefixed with the code ("1120  Senior…") — strip it
                name = text.strip()
                if name.startswith(cc):
                    name = name[len(cc):].strip()
                out[cc] = name or cc
            return out
        last = f"HTTP {r.status_code}"
        time.sleep(4)
    raise RuntimeError(f"Hagstofa metadata ({lang}) unavailable: {last}")


def build(out_path: str = OUT, log=print) -> dict:
    log("fetching ISCO labels (EN) from Hagstofa …")
    en = _fetch_starf("EN")
    try:
        log("fetching ISCO labels (IS) from Hagstofa …")
        isl = _fetch_starf("IS")
    except Exception as e:                    # native labels best-effort
        log(f"IS labels unavailable ({e}) — falling back to EN")
        isl = dict(en)
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": _url("EN"),
        "classification": "ÍSTARF95 / ISCO-08 aligned; all levels 1–4 digit",
        "codes": {"EN": en, "IS": isl},
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)
    leaves = sum(1 for c in en if len(c) == 4)
    log(f"wrote {len(en)} EN + {len(isl)} IS codes ({leaves} leaf)")
    return {"built_at": payload["built_at"], "codes": len(en), "leaves": leaves}
