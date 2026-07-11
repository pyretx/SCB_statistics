"""Shared data-source update service (admin panel).

ONE implementation per source of: probe the newest available release → compare
with what the app currently stores → download/validate/process a new release
and swap it in only on success. The admin panel's global "Check for updates"
table (Data sources) and the per-card buttons both call these functions —
never their own copies.

A country can have SEVERAL rows (sub-sources): e.g. Sweden = the SCB data year
(the app pins its displayed year in app_settings.json even though salaries are
fetched live) + the SSYK occupation labels; Norway = the live API (reachability
only — nothing stored can lag) + the STYRK labels; France = the live Melodi API
+ the bundled microdata percentiles (manual download).

Safety rules (both flows):
  · ``check*`` never mutates anything — pure probes;
  · updates run only after an explicit admin confirmation in the UI;
  · every updater validates before swapping (atomic temp-file swaps where a
    file is replaced), so the existing dataset survives any failure;
  · ``update_many`` isolates errors per source — one failure never stops the
    other selected sources.

Plain module (no Streamlit) so it can be tested and reused anywhere; the UI
layer owns session state, confirmations and st.cache_data clearing.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests

_ROOT = os.path.dirname(os.path.abspath(__file__))

# Outcome codes (display labels live in content/admin.toml [updates]).
OUT_UPDATED = "updated"
OUT_UP_TO_DATE = "up_to_date"
OUT_MANUAL = "manual"
OUT_FAILED = "failed"
OUT_VALIDATION = "validation_failed"
OUT_UNAVAILABLE = "unavailable"


@dataclass
class SourceStatus:
    key: str                      # e.g. "sweden_data", "norway_labels", "us_data"
    country: str
    source: str                   # shown in the table's Data source column
    current: str = "—"            # stored version / release, display string
    latest: str = ""              # probed latest, display string ("" = unknown)
    latest_raw: object = None     # machine value (e.g. int year) for the updater
    update_available: bool | None = None   # None = probe failed (unavailable row)
    can_auto: bool = True         # False → needs a manual step (FR microdata)
    note: str = ""
    error: str = ""


@dataclass
class UpdateResult:
    key: str
    outcome: str                  # one of the OUT_* codes
    message: str = ""


def _notes() -> dict:
    """Per-source note texts from content/admin.toml [updates.notes] (editable)."""
    try:
        import content
        return content.load("admin").get("updates", {}).get("notes", {})
    except Exception:
        return {}


# ── Sweden · SCB data year — salaries are fetched live, but the app pins the
#    displayed year (sliders/pills/leaderboard/work-permit bench) in
#    app_settings.json, so a new SCB year needs this explicit bump. ───────────
def _check_sweden_data() -> SourceStatus:
    import sweden_codes
    cur = int(sweden_codes.load_app_settings().get("latest_data_year", 2025))
    s = SourceStatus("sweden_data", "Sweden", "SCB · data year", current=str(cur))
    latest = sweden_codes.fetch_available_year()
    if latest is None:
        raise RuntimeError("SCB metadata probe failed")
    s.latest = str(latest)
    s.latest_raw = int(latest)
    s.update_available = latest > cur
    if s.update_available:
        s.note = _notes().get("sweden_restart", "")
    return s


def _update_sweden_data(status, log) -> UpdateResult:
    import sweden_codes
    target = status.latest_raw if status and status.latest_raw else \
        sweden_codes.fetch_available_year()
    if target is None:
        return UpdateResult("sweden_data", OUT_UNAVAILABLE, "SCB metadata probe failed")
    if not (2000 < int(target) < 2100):
        return UpdateResult("sweden_data", OUT_VALIDATION,
                            f"implausible year from SCB: {target!r}")
    cur = int(sweden_codes.load_app_settings().get("latest_data_year", 2025))
    if int(target) <= cur:
        return UpdateResult("sweden_data", OUT_UP_TO_DATE, str(cur))
    log(f"latest_data_year {cur} → {target}")
    s = sweden_codes.load_app_settings()
    sweden_codes.save_app_settings({**s, "latest_data_year": int(target)})
    return UpdateResult("sweden_data", OUT_UPDATED,
                        f"{target} · {_notes().get('sweden_restart', '')}".strip(" ·"))


# ── Sweden · SSYK occupation labels — diff the live SCB list vs the cache ─────
def _label_diff(live: dict, cached: dict) -> str:
    added = sum(1 for c in live if c not in cached)
    removed = sum(1 for c in cached if c not in live)
    renamed = sum(1 for c, n in live.items() if c in cached and cached[c] != n)
    parts = [f"+{added} new" if added else "", f"−{removed} removed" if removed else "",
             f"{renamed} renamed" if renamed else ""]
    return " · ".join(p for p in parts if p)


def _check_sweden_labels() -> SourceStatus:
    import sweden_codes
    try:
        with open(sweden_codes.CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
    except Exception:
        cache = {}
    cached = cache.get("EN", {})
    s = SourceStatus("sweden_labels", "Sweden", "SCB · SSYK labels",
                     current=f"{len(cached)} codes · {(cache.get('cached_at') or '—')[:10]}")
    live = sweden_codes.fetch_occupations("EN")
    if not live:
        raise RuntimeError("SCB returned no occupation metadata")
    s.latest = f"{len(live)} codes"
    diff = _label_diff(live, cached)
    s.update_available = bool(diff)
    s.note = diff
    return s


def _update_sweden_labels(status, log) -> UpdateResult:
    import sweden_codes
    log("re-fetching SSYK labels (EN + SV) from SCB …")
    ts = sweden_codes.refresh()          # validates counts BEFORE the atomic swap
    n = len(sweden_codes.occupation_names("EN"))
    return UpdateResult("sweden_labels", OUT_UPDATED, f"{ts} · {n} codes")


# ── France · Melodi API — fully live (reachability check only) ────────────────
def _check_france_api() -> SourceStatus:
    import france_data as fd
    s = SourceStatus("france_api", "France", "INSEE Melodi · API",
                     current="live", can_auto=False,
                     note=_notes().get("france_api", ""))
    latest = fd.fetch_available_year("private")
    if latest is None:
        raise RuntimeError("INSEE Melodi probe failed")
    s.latest = str(latest)
    s.update_available = False
    return s


def _update_france_api(status, log) -> UpdateResult:
    return UpdateResult("france_api", OUT_UP_TO_DATE,
                        _notes().get("france_api", "Live API — always current."))


# ── France · microdata percentiles — bundled FD_SALAAN build (manual download)
def _micro_year() -> int:
    try:
        with open(os.path.join(_ROOT, "pcs_microdata_percentiles.json"),
                  encoding="utf-8") as f:
            return int(str(json.load(f).get("year", 0))[:4])
    except Exception:
        return 0


def _check_france_micro() -> SourceStatus:
    import france_data as fd
    my = _micro_year()
    s = SourceStatus("france_micro", "France", "INSEE · microdata",
                     current=str(my or "—"), can_auto=False,
                     note=_notes().get("france", ""))
    latest = fd.fetch_available_year("private")
    if latest is None:
        raise RuntimeError("INSEE Melodi probe failed")
    s.latest = str(latest)
    s.latest_raw = int(latest)
    s.update_available = bool(my and int(latest) > my)
    return s


def _update_france_micro(status, log) -> UpdateResult:
    return UpdateResult("france_micro", OUT_MANUAL,
                        _notes().get("france", "Manual microdata download required."))


# ── Norway · SSB API — fully live (reachability check only) ───────────────────
_SSB_TABLE_URL = "https://data.ssb.no/api/v0/en/table/11418"


def _check_norway_data() -> SourceStatus:
    s = SourceStatus("norway_data", "Norway", "SSB · API",
                     current="live", latest="live", update_available=False,
                     can_auto=False, note=_notes().get("norway_data", ""))
    r = requests.get(_SSB_TABLE_URL, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"SSB API answered HTTP {r.status_code}")
    return s


def _update_norway_data(status, log) -> UpdateResult:
    return UpdateResult("norway_data", OUT_UP_TO_DATE,
                        _notes().get("norway_data", "Live API — always current."))


# ── Norway · STYRK labels — diff the live SSB list vs styrk_labels.json ───────
def _fetch_styrk_light() -> dict[str, str]:
    """One plain GET (no long retries — this is a check, not a build)."""
    r = requests.get(_SSB_TABLE_URL, timeout=30)
    r.raise_for_status()
    yrke = next(v for v in r.json()["variables"] if v["code"] == "Yrke")
    return {c: t for c, t in zip(yrke["values"], yrke["valueTexts"])
            if c.isdigit() and 1 <= len(c) <= 4}


def _check_norway_labels() -> SourceStatus:
    from countries.norway.build import MAJORS
    try:
        with open(os.path.join(_ROOT, "styrk_labels.json"), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    cached = (data.get("codes") or {}).get("EN", {})
    s = SourceStatus("norway_labels", "Norway", "SSB · STYRK labels",
                     current=f"{len(cached)} codes · {data.get('built_at', '—')}")
    live = _fetch_styrk_light()
    for one, name in MAJORS["EN"].items():   # the build fills these — mirror it
        live.setdefault(one, name)
    s.latest = f"{len(live)} codes"
    diff = _label_diff(live, cached)
    s.update_available = bool(diff)
    s.note = diff
    return s


def _update_norway_labels(status, log) -> UpdateResult:
    from countries.norway import build as nobuild
    res = nobuild.build(log=log)             # atomic swap inside
    if res.get("codes", 0) < 300:
        return UpdateResult("norway_labels", OUT_VALIDATION,
                            f"implausibly few codes from SSB: {res}")
    try:
        from countries.norway import provider as noprov
        noprov._codes.clear()                 # serve the new labels immediately
    except Exception:
        pass
    return UpdateResult("norway_labels", OUT_UPDATED,
                        f"{res['built_at']} · {res['codes']} codes ({res['leaves']} occupations)")


# ── United States · BLS OEWS — bundled build, full auto pipeline ──────────────
def _check_us_data() -> SourceStatus:
    from countries.us import build as usbuild
    info = usbuild.bundled_info()
    s = SourceStatus("us_data", "United States", "BLS OEWS",
                     current=f"May {info.get('year', '—')}")
    latest = usbuild.latest_available_year()
    if latest is None:
        raise RuntimeError("BLS probe returned no release year")
    s.latest = f"May {latest}"
    s.latest_raw = int(latest)
    s.update_available = bool(info.get("year") and latest > info["year"])
    return s


def _update_us_data(status, log) -> UpdateResult:
    from countries.us import build as usbuild
    target = status.latest_raw if status and status.latest_raw else \
        usbuild.latest_available_year()
    info = usbuild.bundled_info()
    if not target:
        return UpdateResult("us_data", OUT_UNAVAILABLE,
                            "BLS probe returned no release year")
    if info.get("year") and int(target) <= int(info["year"]):
        return UpdateResult("us_data", OUT_UP_TO_DATE, f"May {info['year']}")
    # build() downloads + parses + writes a temp file and atomically swaps the
    # bundle only on success — any exception leaves the current data untouched.
    res = usbuild.build(year=int(target), log=log)
    if not (res.get("occupations") and res.get("scopes")):
        return UpdateResult("us_data", OUT_VALIDATION,
                            f"build produced empty counts: {res}")
    try:
        from countries.us import provider as usprov
        usprov._load.clear()                  # serve the new data immediately
    except Exception:
        pass
    return UpdateResult("us_data", OUT_UPDATED,
                        f"May {res['year']} · {res['occupations']} occupations · "
                        f"{res['scopes']} scopes")


# ── Service API ───────────────────────────────────────────────────────────────
_CHECKERS = {"sweden_data": _check_sweden_data, "sweden_labels": _check_sweden_labels,
             "france_api": _check_france_api, "france_micro": _check_france_micro,
             "norway_data": _check_norway_data, "norway_labels": _check_norway_labels,
             "us_data": _check_us_data}
_UPDATERS = {"sweden_data": _update_sweden_data, "sweden_labels": _update_sweden_labels,
             "france_api": _update_france_api, "france_micro": _update_france_micro,
             "norway_data": _update_norway_data, "norway_labels": _update_norway_labels,
             "us_data": _update_us_data}
_BASE = {"sweden_data": ("Sweden", "SCB · data year"),
         "sweden_labels": ("Sweden", "SCB · SSYK labels"),
         "france_api": ("France", "INSEE Melodi · API"),
         "france_micro": ("France", "INSEE · microdata"),
         "norway_data": ("Norway", "SSB · API"),
         "norway_labels": ("Norway", "SSB · STYRK labels"),
         "us_data": ("United States", "BLS OEWS")}
SOURCE_ORDER = ["sweden_data", "sweden_labels", "france_api", "france_micro",
                "norway_data", "norway_labels", "us_data"]


def check(key: str) -> SourceStatus:
    """Probe one sub-source (never mutates). A failed probe returns a status
    with ``error`` set and ``update_available=None`` — the 'unavailable' row."""
    try:
        return _CHECKERS[key]()
    except Exception as e:  # noqa: BLE001
        c, src = _BASE.get(key, (key, "—"))
        return SourceStatus(key, c, src, error=str(e), update_available=None)


def check_all() -> list[SourceStatus]:
    """Probe every configured sub-source, each guarded independently."""
    return [check(k) for k in SOURCE_ORDER]


def update(key: str, status: SourceStatus | None = None,
           log=lambda m: None) -> UpdateResult:
    """Run one sub-source's update pipeline (download → validate → process →
    swap). Never raises — failures come back as OUT_FAILED/OUT_VALIDATION/etc.,
    and the stored dataset is left untouched on any failure."""
    try:
        return _UPDATERS[key](status, log)
    except Exception as e:  # noqa: BLE001
        return UpdateResult(key, OUT_FAILED, str(e))


def update_many(keys, statuses: dict | None = None,
                log=lambda m: None) -> list[UpdateResult]:
    """Update several sub-sources; each isolated — one failure never stops the rest."""
    statuses = statuses or {}
    return [update(k, statuses.get(k), log) for k in keys]


# ── Check log (update_checks.json, git-ignored) — survives restarts so the
# admin Overview can show when the last full check ran and what it found. ─────
CHECK_LOG = os.path.join(_ROOT, "update_checks.json")


def record_check(results: list) -> dict:
    """Persist a full-check result (called by the global check, not the
    per-source card buttons — those are partial views)."""
    import datetime
    data = {
        "checked_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updates_available": [s.key for s in results if s.update_available],
        "sources": {s.key: {"current": s.current, "latest": s.latest,
                            "update_available": s.update_available,
                            "error": s.error} for s in results},
    }
    try:
        with open(CHECK_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return data


def last_check() -> dict | None:
    """The most recent recorded full check, or None if none has run yet."""
    try:
        with open(CHECK_LOG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
