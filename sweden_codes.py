"""Sweden SCB occupation-code cache — the fetch + disk-cache shared by the
Sweden page (scb_salaries.py) and the admin panel's "Re-fetch codes".

Plain module (no Streamlit) so the admin panel can refresh the cache without
importing the Sweden page script.
"""
from __future__ import annotations

import datetime
import json
import os

import requests

TABLE_BASE = "AM/AM0110/AM0110A"                    # same table family as the page
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "occupations_cache.json")


def fetch_occupations(lang: str) -> dict[str, str]:
    """{ssyk_code: name} from the SCB PxWeb table metadata ('EN' | 'SV')."""
    base = f"https://api.scb.se/OV0104/v1/doris/{lang.lower()}/ssd"
    url = f"{base}/{TABLE_BASE}/LoneSpridSektorYrk4A"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    for var in r.json()["variables"]:
        if var["code"] == "Yrke2012":
            return dict(zip(var["values"], var["valueTexts"]))
    return {}


def refresh() -> str:
    """Fetch EN + SV occupations and atomically rewrite the disk cache.
    Returns the new timestamp string (same shape scb_salaries.py reads)."""
    data = {
        "EN": fetch_occupations("EN"),
        "SV": fetch_occupations("SV"),
        "cached_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CACHE_FILE)                     # atomic swap on success
    return data["cached_at"]
