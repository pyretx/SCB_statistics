"""Build styrk_labels.json — STYRK-08 occupation codes → names, bilingual + all
levels.

Source: the SSB Statbank table 11418 'Yrke' variable metadata, fetched in both
English (/en/) and Norwegian (/no/). We keep EVERY numeric level:
  1-digit  major group      (e.g. 2  "Academic occupations")
  2-digit  sub-major group
  3-digit  minor group
  4-digit  unit group        (the detailed occupation, the menu leaf)

This one file then feeds three shared framework features without touching SSB at
runtime: the occupation menu (leaf), the major-group drill-down (leveling), the
language toggle (EN/NO) and the code browser (the whole tree).

    python build_styrk_labels.py
"""
import json
import os
import datetime
import time

import requests

BASE = "https://data.ssb.no/api/v0/{lang}/table/11418"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styrk_labels.json")

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
    for attempt in range(6):
        r = requests.get(url, timeout=180)
        if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
            yrke = next(v for v in r.json()["variables"] if v["code"] == "Yrke")
            return {c: t for c, t in zip(yrke["values"], yrke["valueTexts"])
                    if c.isdigit() and 1 <= len(c) <= 4}
        last = f"HTTP {r.status_code}"
        time.sleep(4)
    raise RuntimeError(f"SSB metadata ({lang}) unavailable: {last}")


def main():
    en = _fetch_yrke("en")
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
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    n4 = sum(1 for c in en if len(c) == 4)
    print(f"wrote {len(en)} EN + {len(no)} NO codes ({n4} leaf) -> {OUT}")


if __name__ == "__main__":
    main()
