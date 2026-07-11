"""Sweden SCB shared helpers — occupation-code cache, app settings and the
data-year availability check, shared by the legacy Sweden page
(scb_salaries.py), the framework Sweden page (countries/se2) and the admin
panel.

Plain module (no Streamlit) so the admin panel can act without importing the
Sweden page script.
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


def occupation_names(lang: str = "EN") -> dict[str, str]:
    """{ssyk_code: name} from the disk cache (empty dict if missing)."""
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f).get(lang, {})
    except Exception:
        return {}


# ── App settings (app_settings.json — the data year the whole app uses).
# Same file + defaults as scb_salaries.py's load/save_app_settings; the
# framework Sweden page (countries/se2) reads latest_data_year from it too. ───
APP_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "app_settings.json")
APP_DEFAULTS = {"ssyk_show_3digit": True, "latest_data_year": 2025}


def load_app_settings() -> dict:
    s = dict(APP_DEFAULTS)
    if os.path.exists(APP_SETTINGS_FILE):
        try:
            with open(APP_SETTINGS_FILE, encoding="utf-8") as f:
                s.update(json.load(f))
        except Exception:
            pass
    return s


def save_app_settings(s: dict):
    with open(APP_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


def fetch_available_year():
    """Newest year SCB actually publishes for the current wage table (reads the
    table's 'Tid' metadata, a plain GET). int, or None on failure. Deliberately
    uncached — only called when an admin forces a check."""
    url = f"https://api.scb.se/OV0104/v1/doris/en/ssd/{TABLE_BASE}/LoneSpridSektYrk4AN"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        for var in r.json().get("variables", []):
            if var.get("code") == "Tid":
                yrs = [int(v) for v in var.get("values", []) if str(v).isdigit()]
                return max(yrs) if yrs else None
    except Exception:
        return None
    return None
