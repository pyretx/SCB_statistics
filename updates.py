"""Shared data-source update service (admin panel).

ONE implementation per source of: probe the newest available release → compare
with what the app currently stores → download/validate/process a new release
and swap it in only on success. The admin panel's global "Check for updates"
table (Overview) and the per-source buttons (Data sources) both call these
functions — never their own copies.

Safety rules (both flows):
  · ``check*`` never mutates anything — pure probes;
  · updates run only after an explicit admin confirmation in the UI;
  · every updater validates before swapping (the US build writes a temp file
    and atomically replaces the bundle only on success; Sweden's year update
    is sanity-checked first), so the existing dataset survives any failure;
  · ``update_many`` isolates errors per source — one failure never stops the
    other selected sources.

Plain module (no Streamlit) so it can be tested and reused anywhere; the UI
layer owns session state, confirmations and st.cache_data clearing.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

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
    key: str                      # "us" | "sweden" | "france" | "norway"
    country: str
    source: str
    current: str = "—"            # stored version / release, display string
    latest: str = ""              # probed latest, display string ("" = unknown)
    latest_raw: object = None     # machine value (e.g. int year) for the updater
    update_available: bool | None = None   # None = n/a (live source / probe failed)
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


# ── United States — BLS OEWS (bundled us_oews.json.gz, full auto pipeline) ───
def _check_us() -> SourceStatus:
    from countries.us import build as usbuild
    info = usbuild.bundled_info()
    s = SourceStatus("us", "United States", "BLS OEWS",
                     current=f"May {info.get('year', '—')}")
    latest = usbuild.latest_available_year()
    if latest is None:
        raise RuntimeError("BLS probe returned no release year")
    s.latest = f"May {latest}"
    s.latest_raw = int(latest)
    s.update_available = bool(info.get("year") and latest > info["year"])
    return s


def _update_us(status: SourceStatus | None, log) -> UpdateResult:
    from countries.us import build as usbuild
    target = status.latest_raw if status and status.latest_raw else \
        usbuild.latest_available_year()
    info = usbuild.bundled_info()
    if not target:
        return UpdateResult("us", OUT_UNAVAILABLE, "BLS probe returned no release year")
    if info.get("year") and int(target) <= int(info["year"]):
        return UpdateResult("us", OUT_UP_TO_DATE, f"May {info['year']}")
    # build() downloads + parses + writes a temp file and atomically swaps the
    # bundle only on success — any exception leaves the current data untouched.
    res = usbuild.build(year=int(target), log=log)
    if not (res.get("occupations") and res.get("scopes")):
        return UpdateResult("us", OUT_VALIDATION,
                            f"build produced empty counts: {res}")
    try:
        from countries.us import provider as usprov
        usprov._load.clear()                      # serve the new data immediately
    except Exception:
        pass
    return UpdateResult("us", OUT_UPDATED,
                        f"May {res['year']} · {res['occupations']} occupations · "
                        f"{res['scopes']} scopes")


# ── Sweden — SCB (live API; stored artifact = latest_data_year) ──────────────
def _check_sweden() -> SourceStatus:
    import sweden_codes
    cur = int(sweden_codes.load_app_settings().get("latest_data_year", 2025))
    s = SourceStatus("sweden", "Sweden", "SCB", current=str(cur))
    latest = sweden_codes.fetch_available_year()
    if latest is None:
        raise RuntimeError("SCB metadata probe failed")
    s.latest = str(latest)
    s.latest_raw = int(latest)
    s.update_available = latest > cur
    if s.update_available:
        s.note = _notes().get("sweden_restart", "")
    return s


def _update_sweden(status: SourceStatus | None, log) -> UpdateResult:
    import sweden_codes
    target = status.latest_raw if status and status.latest_raw else \
        sweden_codes.fetch_available_year()
    if target is None:
        return UpdateResult("sweden", OUT_UNAVAILABLE, "SCB metadata probe failed")
    if not (2000 < int(target) < 2100):
        return UpdateResult("sweden", OUT_VALIDATION,
                            f"implausible year from SCB: {target!r}")
    cur = int(sweden_codes.load_app_settings().get("latest_data_year", 2025))
    if int(target) <= cur:
        return UpdateResult("sweden", OUT_UP_TO_DATE, str(cur))
    log(f"latest_data_year {cur} → {target}")
    s = sweden_codes.load_app_settings()
    sweden_codes.save_app_settings({**s, "latest_data_year": int(target)})
    return UpdateResult("sweden", OUT_UPDATED,
                        f"{target} · {_notes().get('sweden_restart', '')}".strip(" ·"))


# ── France — INSEE (means live via Melodi; percentiles = bundled microdata
#    from a MANUAL download, so no automated update is possible) ──────────────
def _micro_year() -> int:
    try:
        with open(os.path.join(_ROOT, "pcs_microdata_percentiles.json"),
                  encoding="utf-8") as f:
            return int(str(json.load(f).get("year", 0))[:4])
    except Exception:
        return 0


def _check_france() -> SourceStatus:
    import france_data as fd
    my = _micro_year()
    s = SourceStatus("france", "France", "INSEE",
                     current=str(my or "—"), can_auto=False,
                     note=_notes().get("france", ""))
    latest = fd.fetch_available_year("private")
    if latest is None:
        raise RuntimeError("INSEE Melodi probe failed")
    s.latest = str(latest)
    s.latest_raw = int(latest)
    s.update_available = bool(my and int(latest) > my)
    return s


def _update_france(status: SourceStatus | None, log) -> UpdateResult:
    return UpdateResult("france", OUT_MANUAL,
                        _notes().get("france", "Manual microdata download required."))


# ── Norway — SSB (fully live API; nothing stored can lag) ────────────────────
def _check_norway() -> SourceStatus:
    built = "—"
    try:
        with open(os.path.join(_ROOT, "styrk_labels.json"), encoding="utf-8") as f:
            built = json.load(f).get("built_at", "—")
    except Exception:
        pass
    return SourceStatus("norway", "Norway", "SSB",
                        current=f"labels {built}", latest="live",
                        update_available=False, can_auto=False,
                        note=_notes().get("norway", ""))


def _update_norway(status: SourceStatus | None, log) -> UpdateResult:
    return UpdateResult("norway", OUT_UP_TO_DATE,
                        _notes().get("norway", "Live API — always current."))


# ── Service API ───────────────────────────────────────────────────────────────
_CHECKERS = {"us": _check_us, "sweden": _check_sweden,
             "france": _check_france, "norway": _check_norway}
_UPDATERS = {"us": _update_us, "sweden": _update_sweden,
             "france": _update_france, "norway": _update_norway}
_BASE = {"us": ("United States", "BLS OEWS"), "sweden": ("Sweden", "SCB"),
         "france": ("France", "INSEE"), "norway": ("Norway", "SSB")}
SOURCE_ORDER = ["sweden", "france", "norway", "us"]


def check(key: str) -> SourceStatus:
    """Probe one source (never mutates). A failed probe returns a status with
    ``error`` set and ``update_available=None`` — the 'source unavailable' row."""
    try:
        return _CHECKERS[key]()
    except Exception as e:  # noqa: BLE001
        c, src = _BASE.get(key, (key, "—"))
        return SourceStatus(key, c, src, error=str(e), update_available=None)


def check_all() -> list[SourceStatus]:
    """Probe every configured source, each guarded independently."""
    return [check(k) for k in SOURCE_ORDER]


def update(key: str, status: SourceStatus | None = None,
           log=lambda m: None) -> UpdateResult:
    """Run one source's update pipeline (download → validate → process → swap).
    Never raises — failures come back as OUT_FAILED/OUT_VALIDATION/etc., and
    the stored dataset is left untouched on any failure."""
    try:
        return _UPDATERS[key](status, log)
    except Exception as e:  # noqa: BLE001
        return UpdateResult(key, OUT_FAILED, str(e))


def update_many(keys, statuses: dict | None = None,
                log=lambda m: None) -> list[UpdateResult]:
    """Update several sources; each isolated — one failure never stops the rest."""
    statuses = statuses or {}
    return [update(k, statuses.get(k), log) for k in keys]
