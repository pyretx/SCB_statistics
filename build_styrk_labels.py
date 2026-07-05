"""Build styrk_labels.json — STYRK-08 4-digit occupation codes → English names.

Source: the SSB Statbank table 11418 'Yrke' variable metadata (582 codes across
levels; we keep the 4-digit detailed occupations, mirroring Sweden's 4-digit
SSYK and France's 4-char PCS). Run once; the app then reads the JSON (fast) and
never hits SSB just to build the occupation menu.

    python build_styrk_labels.py
"""
import json
import os
import datetime

import requests

META_URL = "https://data.ssb.no/api/v0/en/table/11418"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styrk_labels.json")


def main():
    r = requests.get(META_URL, timeout=180)
    r.raise_for_status()
    meta = r.json()
    yrke = next(v for v in meta["variables"] if v["code"] == "Yrke")
    labels = {code: txt for code, txt in zip(yrke["values"], yrke["valueTexts"])
              if len(code) == 4 and code.isdigit()}
    payload = {
        "built_at": datetime.date.today().isoformat(),
        "source": META_URL,
        "classification": "STYRK-08 (ISCO-08 aligned), 4-digit detailed occupations",
        "labels": labels,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"wrote {len(labels)} STYRK-08 codes -> {OUT}")


if __name__ == "__main__":
    main()
