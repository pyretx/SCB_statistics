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


def server_container() -> str:
    """This environment's docker container name (scb-dev / scb-test / scb-prod),
    derived from the [app] url secret; scb-dev when unknown (local dev)."""
    try:
        import re
        import tomllib
        with open(os.path.join(_ROOT, ".streamlit", "secrets.toml"), "rb") as f:
            url = tomllib.load(f).get("app", {}).get("url", "")
        m = re.match(r"https?://(scb(?:-\w+)?)\.", url)
        if m:
            return "scb-prod" if m.group(1) == "scb" else m.group(1)
    except Exception:
        pass
    return "scb-dev"


def restart_command() -> str:
    """The final-step command shown after data-year updates."""
    return f"docker restart {server_container()}"


def _restart_note() -> str:
    return _notes().get("restart_step", "Final step on the server: run `{cmd}` "
                        "(~10 s, no rebuild).").format(cmd=restart_command())


def _commit_note(file: str) -> str:
    return _notes().get("commit_step", "Runtime update — commit {file} to keep "
                        "it after the next redeploy.").format(file=file)


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
        s.note = _restart_note()
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
                        f"{target} · {_restart_note()}")


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
    return UpdateResult("sweden_labels", OUT_UPDATED,
                        f"{ts} · {n} codes · {_commit_note('occupations_cache.json')}")


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


def _fd_salaan_published(year: int):
    """insee.fr publication id of 'Description des emplois salariés en <year> —
    Fichier détail', or None when that vintage isn't published yet. Uses the
    site's Solr search API (the query needs the full body, not just ?q=)."""
    q = f"Description des emplois salariés en {year}"
    r = requests.post("https://www.insee.fr/fr/solr/consultation",
                      params={"q": q},
                      json={"q": q, "start": 0, "rows": 20, "facets": [],
                            "filters": [], "sortFields": []},
                      headers={"User-Agent": "Mozilla/5.0 (salary-explorer; research)"},
                      timeout=30)
    r.raise_for_status()
    for d in r.json().get("documents", []):
        if (d.get("titre") == q
                and (d.get("famille") or {}).get("libelleFr") == "Fichier détail"):
            return d.get("id")
    return None


def _check_france_micro() -> SourceStatus:
    my = _micro_year()
    if not my:
        raise RuntimeError("bundled pcs_microdata_percentiles.json missing/unreadable")
    s = SourceStatus("france_micro", "France", "INSEE · microdata",
                     current=str(my), can_auto=False)
    # "Latest available" = the newest PUBLISHED fichier détail (the file our
    # percentiles come from) — NOT Melodi's means year, which runs ~1 year
    # ahead by design and used to make this row misleading.
    latest, pub = my, None
    try:
        for y in (my + 1, my + 2):
            pid = _fd_salaan_published(y)
            if pid:
                latest, pub = y, pid
    except Exception:
        pass          # search degraded — stay at current, no false alarms
    s.latest = str(latest)
    s.latest_raw = latest
    s.update_available = latest > my
    if s.update_available:
        s.note = _notes().get("france_found", "").format(
            year=latest, url=f"https://www.insee.fr/fr/statistiques/{pub}")
    else:
        s.note = _notes().get("france_lag", "")
    return s


def _update_france_micro(status, log) -> UpdateResult:
    return UpdateResult("france_micro", OUT_MANUAL,
                        _notes().get("france", "Manual microdata download required."))


# ── Norway · SSB data year — same pattern as Sweden: salaries are fetched
#    live, but the app pins the displayed year range (app_settings.json,
#    "norway_latest_year"), so a new SSB year needs this explicit bump. ────────
_SSB_TABLE_URL = "https://data.ssb.no/api/v0/en/table/11418"


def _ssb_meta() -> dict:
    """One plain GET on the 11418 table metadata (no long retries — checks)."""
    r = requests.get(_SSB_TABLE_URL, timeout=30)
    r.raise_for_status()
    return r.json()


def _ssb_latest_year() -> int | None:
    tid = next(v for v in _ssb_meta()["variables"] if v["code"] == "Tid")
    yrs = [int(v) for v in tid["values"] if str(v).isdigit()]
    return max(yrs) if yrs else None


def _check_norway_data() -> SourceStatus:
    from countries.norway.build import latest_year
    cur = latest_year()
    s = SourceStatus("norway_data", "Norway", "SSB · data year", current=str(cur))
    latest = _ssb_latest_year()
    if latest is None:
        raise RuntimeError("SSB metadata probe returned no years")
    s.latest = str(latest)
    s.latest_raw = int(latest)
    s.update_available = latest > cur
    if s.update_available:
        s.note = _restart_note()
    return s


def _update_norway_data(status, log) -> UpdateResult:
    from countries.norway.build import latest_year, save_latest_year
    target = status.latest_raw if status and status.latest_raw else _ssb_latest_year()
    if target is None:
        return UpdateResult("norway_data", OUT_UNAVAILABLE,
                            "SSB metadata probe returned no years")
    if not (2000 < int(target) < 2100):
        return UpdateResult("norway_data", OUT_VALIDATION,
                            f"implausible year from SSB: {target!r}")
    cur = latest_year()
    if int(target) <= cur:
        return UpdateResult("norway_data", OUT_UP_TO_DATE, str(cur))
    log(f"norway_latest_year {cur} → {target}")
    save_latest_year(int(target))
    return UpdateResult("norway_data", OUT_UPDATED,
                        f"{target} · {_restart_note()}")


# ── Norway · STYRK labels — diff the live SSB list vs styrk_labels.json ───────
def _fetch_styrk_light() -> dict[str, str]:
    """One plain GET (no long retries — this is a check, not a build)."""
    yrke = next(v for v in _ssb_meta()["variables"] if v["code"] == "Yrke")
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
                        f"{res['built_at']} · {res['codes']} codes ({res['leaves']} "
                        f"occupations) · {_commit_note('styrk_labels.json')}")


# ── Denmark · DST data year — same pattern as Sweden/Norway: salaries are
#    fetched live from LONS20, but the app pins the displayed year range
#    (app_settings.json, "denmark_latest_year"), so a new DST year needs this
#    explicit bump. ───────────────────────────────────────────────────────────
def _dst_tableinfo() -> dict:
    """One plain POST on the LONS20 table metadata (no long retries — checks)."""
    r = requests.post("https://api.statbank.dk/v1/tableinfo",
                      json={"lang": "en", "table": "LONS20"}, timeout=30)
    r.raise_for_status()
    return r.json()


def _dst_latest_year() -> int | None:
    tid = next(v for v in _dst_tableinfo()["variables"] if v["id"] == "Tid")
    yrs = [int(x["id"]) for x in tid["values"] if str(x["id"]).isdigit()]
    return max(yrs) if yrs else None


def _check_denmark_data() -> SourceStatus:
    from countries.denmark.build import latest_year
    cur = latest_year()
    s = SourceStatus("denmark_data", "Denmark", "DST · data year", current=str(cur))
    latest = _dst_latest_year()
    if latest is None:
        raise RuntimeError("DST metadata probe returned no years")
    s.latest = str(latest)
    s.latest_raw = int(latest)
    s.update_available = latest > cur
    if s.update_available:
        s.note = _restart_note()
    return s


def _update_denmark_data(status, log) -> UpdateResult:
    from countries.denmark.build import latest_year, save_latest_year
    target = status.latest_raw if status and status.latest_raw else _dst_latest_year()
    if target is None:
        return UpdateResult("denmark_data", OUT_UNAVAILABLE,
                            "DST metadata probe returned no years")
    if not (2000 < int(target) < 2100):
        return UpdateResult("denmark_data", OUT_VALIDATION,
                            f"implausible year from DST: {target!r}")
    cur = latest_year()
    if int(target) <= cur:
        return UpdateResult("denmark_data", OUT_UP_TO_DATE, str(cur))
    log(f"denmark_latest_year {cur} → {target}")
    save_latest_year(int(target))
    return UpdateResult("denmark_data", OUT_UPDATED,
                        f"{target} · {_restart_note()}")


# ── Denmark · DISCO labels — diff the live DST list vs disco_labels.json ──────
def _check_denmark_labels() -> SourceStatus:
    from countries.denmark.build import _labels
    try:
        with open(os.path.join(_ROOT, "disco_labels.json"), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    cached = (data.get("codes") or {}).get("EN", {})
    s = SourceStatus("denmark_labels", "Denmark", "DST · DISCO labels",
                     current=f"{len(cached)} codes · {data.get('built_at', '—')}")
    live = _labels(_dst_tableinfo())
    if not live:
        raise RuntimeError("DST returned no occupation metadata")
    s.latest = f"{len(live)} codes"
    diff = _label_diff(live, cached)
    s.update_available = bool(diff)
    s.note = diff
    return s


def _update_denmark_labels(status, log) -> UpdateResult:
    from countries.denmark import build as dkbuild
    res = dkbuild.build(log=log)             # atomic swap inside
    if res.get("codes", 0) < 300:
        return UpdateResult("denmark_labels", OUT_VALIDATION,
                            f"implausibly few codes from DST: {res}")
    try:
        from countries.denmark import provider as dkprov
        dkprov._codes.clear()                 # serve the new labels immediately
    except Exception:
        pass
    return UpdateResult("denmark_labels", OUT_UPDATED,
                        f"{res['built_at']} · {res['codes']} codes ({res['leaves']} "
                        f"occupations) · {_commit_note('disco_labels.json')}")


# ── Iceland · Hagstofa data year + ISCO labels ───────────────────────────────
_IS_URL = ("https://px.hagstofa.is/pxen/api/v1/en/Samfelag/launogtekjur/"
           "1_laun/1_laun/VIN02001.px")


def _hagstofa_meta() -> dict:
    r = requests.get(_IS_URL, timeout=30)
    r.raise_for_status()
    return r.json()


def _iceland_latest_year():
    ar = next(v for v in _hagstofa_meta()["variables"] if v["code"] == "Ár")
    yrs = [int(x) for x in ar["values"] if str(x).isdigit()]
    return max(yrs) if yrs else None


def _check_iceland_data() -> SourceStatus:
    from countries.iceland.build import latest_year
    cur = latest_year()
    s = SourceStatus("iceland_data", "Iceland", "Hagstofa · data year", current=str(cur))
    latest = _iceland_latest_year()
    if latest is None:
        raise RuntimeError("Hagstofa metadata probe returned no years")
    s.latest, s.latest_raw = str(latest), int(latest)
    s.update_available = latest > cur
    if s.update_available:
        s.note = _restart_note()
    return s


def _update_iceland_data(status, log) -> UpdateResult:
    from countries.iceland.build import latest_year, save_latest_year
    target = status.latest_raw if status and status.latest_raw else _iceland_latest_year()
    if not target or not (2000 < int(target) < 2100):
        return UpdateResult("iceland_data", OUT_VALIDATION, f"implausible year: {target!r}")
    if int(target) <= latest_year():
        return UpdateResult("iceland_data", OUT_UP_TO_DATE, str(latest_year()))
    save_latest_year(int(target))
    return UpdateResult("iceland_data", OUT_UPDATED, f"{target} · {_restart_note()}")


def _check_iceland_labels() -> SourceStatus:
    from countries.iceland.build import _fetch_starf
    try:
        with open(os.path.join(_ROOT, "iceland_labels.json"), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    cached = (data.get("codes") or {}).get("EN", {})
    s = SourceStatus("iceland_labels", "Iceland", "Hagstofa · ISCO labels",
                     current=f"{len(cached)} codes · {data.get('built_at', '—')}")
    live = _fetch_starf("EN")
    s.latest = f"{len(live)} codes"
    diff = _label_diff(live, cached)
    s.update_available = bool(diff)
    s.note = diff
    return s


def _update_iceland_labels(status, log) -> UpdateResult:
    from countries.iceland import build as isbuild
    res = isbuild.build(log=log)
    if res.get("codes", 0) < 100:
        return UpdateResult("iceland_labels", OUT_VALIDATION, f"too few codes: {res}")
    try:
        from countries.iceland import provider as isprov
        isprov._codes.clear()
    except Exception:
        pass
    return UpdateResult("iceland_labels", OUT_UPDATED,
                        f"{res['built_at']} · {res['codes']} codes · "
                        f"{_commit_note('iceland_labels.json')}")


# ── Finland · StatFin data year (snapshot) + ISCO labels ──────────────────────
_FI_URL = "https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin/pra/15au.px"


def _statfin_meta() -> dict:
    r = requests.get(_FI_URL, timeout=30)
    r.raise_for_status()
    return r.json()


def _finland_latest_year(meta=None):
    meta = meta or _statfin_meta()
    tp = next(v for v in meta["variables"] if v["code"] == "timeperiod_y")
    yrs = [int(x) for x in tp["values"] if str(x).isdigit()]
    return max(yrs) if yrs else None


def _check_finland_data() -> SourceStatus:
    from countries.finland.build import latest_year
    cur = latest_year()
    s = SourceStatus("finland_data", "Finland", "StatFin · data year", current=str(cur))
    latest = _finland_latest_year()
    if latest is None:
        raise RuntimeError("StatFin metadata probe returned no years")
    s.latest, s.latest_raw = str(latest), int(latest)
    s.update_available = latest > cur
    if s.update_available:
        s.note = _restart_note()
    return s


def _update_finland_data(status, log) -> UpdateResult:
    from countries.finland.build import latest_year, save_latest_year
    target = status.latest_raw if status and status.latest_raw else _finland_latest_year()
    if not target or not (2000 < int(target) < 2100):
        return UpdateResult("finland_data", OUT_VALIDATION, f"implausible year: {target!r}")
    if int(target) <= latest_year():
        return UpdateResult("finland_data", OUT_UP_TO_DATE, str(latest_year()))
    save_latest_year(int(target))
    return UpdateResult("finland_data", OUT_UPDATED, f"{target} · {_restart_note()}")


def _check_finland_labels() -> SourceStatus:
    from countries.finland.build import _labels
    try:
        with open(os.path.join(_ROOT, "finland_labels.json"), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    cached = (data.get("codes") or {}).get("EN", {})
    s = SourceStatus("finland_labels", "Finland", "StatFin · ISCO labels",
                     current=f"{len(cached)} codes · {data.get('built_at', '—')}")
    live = _labels(_statfin_meta())
    s.latest = f"{len(live)} codes"
    diff = _label_diff(live, cached)
    s.update_available = bool(diff)
    s.note = diff
    return s


def _update_finland_labels(status, log) -> UpdateResult:
    from countries.finland import build as fibuild
    res = fibuild.build(log=log)
    if res.get("codes", 0) < 200:
        return UpdateResult("finland_labels", OUT_VALIDATION, f"too few codes: {res}")
    try:
        from countries.finland import provider as fiprov
        fiprov._codes.clear()
    except Exception:
        pass
    return UpdateResult("finland_labels", OUT_UPDATED,
                        f"{res['built_at']} · {res['codes']} codes · "
                        f"{_commit_note('finland_labels.json')}")


# ── Estonia · Statistics Estonia PA623 data year (4-yearly SES) + labels ──────
def _estonia_latest_year():
    from countries.estonia.build import available_years
    yrs = available_years()
    return max(yrs) if yrs else None


def _check_estonia_data() -> SourceStatus:
    from countries.estonia.build import latest_year
    cur = latest_year()
    s = SourceStatus("estonia_data", "Estonia", "Stat. Estonia · data year", current=str(cur))
    latest = _estonia_latest_year()
    if latest is None:
        raise RuntimeError("Statistics Estonia metadata probe returned no years")
    s.latest, s.latest_raw = str(latest), int(latest)
    s.update_available = latest > cur
    if s.update_available:
        s.note = _restart_note()
    return s


def _update_estonia_data(status, log) -> UpdateResult:
    from countries.estonia.build import latest_year, save_latest_year
    target = status.latest_raw if status and status.latest_raw else _estonia_latest_year()
    if not target or not (2000 < int(target) < 2100):
        return UpdateResult("estonia_data", OUT_VALIDATION, f"implausible year: {target!r}")
    if int(target) <= latest_year():
        return UpdateResult("estonia_data", OUT_UP_TO_DATE, str(latest_year()))
    save_latest_year(int(target))
    return UpdateResult("estonia_data", OUT_UPDATED, f"{target} · {_restart_note()}")


def _check_estonia_labels() -> SourceStatus:
    from countries.estonia.build import _labels, _meta
    try:
        with open(os.path.join(_ROOT, "estonia_labels.json"), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    cached = (data.get("codes") or {}).get("EN", {})
    s = SourceStatus("estonia_labels", "Estonia", "Stat. Estonia · ISCO labels",
                     current=f"{len(cached)} groups · {data.get('built_at', '—')}")
    live = _labels(_meta("EN"))
    s.latest = f"{len(live)} groups"
    diff = _label_diff(live, cached)
    s.update_available = bool(diff)
    s.note = diff
    return s


def _update_estonia_labels(status, log) -> UpdateResult:
    from countries.estonia import build as eebuild
    res = eebuild.build(log=log)
    if res.get("codes", 0) < 5:
        return UpdateResult("estonia_labels", OUT_VALIDATION, f"too few groups: {res}")
    try:
        from countries.estonia import provider as eeprov
        eeprov._codes.clear()
    except Exception:
        pass
    return UpdateResult("estonia_labels", OUT_UPDATED,
                        f"{res['built_at']} · {res['codes']} groups · "
                        f"{_commit_note('estonia_labels.json')}")


# ── Netherlands · CBS 85517NED data year + BRC labels ────────────────────────
def _netherlands_latest_year():
    from countries.netherlands.build import available_years
    yrs = available_years()
    return max(yrs) if yrs else None


def _check_netherlands_data() -> SourceStatus:
    from countries.netherlands.build import latest_year
    cur = latest_year()
    s = SourceStatus("netherlands_data", "Netherlands", "CBS · data year", current=str(cur))
    latest = _netherlands_latest_year()
    if latest is None:
        raise RuntimeError("CBS metadata probe returned no years")
    s.latest, s.latest_raw = str(latest), int(latest)
    s.update_available = latest > cur
    if s.update_available:
        s.note = _restart_note()
    return s


def _update_netherlands_data(status, log) -> UpdateResult:
    from countries.netherlands.build import latest_year, save_latest_year
    target = status.latest_raw if status and status.latest_raw else _netherlands_latest_year()
    if not target or not (2000 < int(target) < 2100):
        return UpdateResult("netherlands_data", OUT_VALIDATION, f"implausible year: {target!r}")
    if int(target) <= latest_year():
        return UpdateResult("netherlands_data", OUT_UP_TO_DATE, str(latest_year()))
    save_latest_year(int(target))
    return UpdateResult("netherlands_data", OUT_UPDATED, f"{target} · {_restart_note()}")


def _check_netherlands_labels() -> SourceStatus:
    from countries.netherlands.build import _parse
    try:
        with open(os.path.join(_ROOT, "netherlands_labels.json"), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    cached = (data.get("codes") or {}).get("EN", {})
    s = SourceStatus("netherlands_labels", "Netherlands", "CBS · BRC labels",
                     current=f"{len(cached)} codes · {data.get('built_at', '—')}")
    live, _ = _parse()
    s.latest = f"{len(live)} codes"
    diff = _label_diff(live, cached)
    s.update_available = bool(diff)
    s.note = diff
    return s


def _update_netherlands_labels(status, log) -> UpdateResult:
    from countries.netherlands import build as nlbuild
    res = nlbuild.build(log=log)
    if res.get("codes", 0) < 50:
        return UpdateResult("netherlands_labels", OUT_VALIDATION, f"too few codes: {res}")
    try:
        from countries.netherlands import provider as nlprov
        nlprov._bundle.clear()
    except Exception:
        pass
    return UpdateResult("netherlands_labels", OUT_UPDATED,
                        f"{res['built_at']} · {res['codes']} codes · "
                        f"{_commit_note('netherlands_labels.json')}")


# ── United States · BLS OEWS — bundled build, full auto pipeline ──────────────
def _check_us_data() -> SourceStatus:
    from countries.us import build as usbuild
    info = usbuild.bundled_info()
    s = SourceStatus("us_data", "United States", "BLS OEWS",
                     current=f"May {info.get('year', '—')}")
    try:
        latest = usbuild.latest_available_year()
    except RuntimeError as e:
        if "403" in str(e):
            # Known condition, not an outage: BLS (Akamai) blocks datacenter
            # IPs, so a VPS deploy can never run this check. Calm info state
            # instead of a red 'unavailable' row on every check.
            s.update_available = None
            s.can_auto = False
            s.note = (_notes().get("us_blocked", "").format(current=s.current)
                      or str(e))
            return s
        raise
    if latest is None:
        raise RuntimeError("BLS probe returned no release year")
    s.latest = f"May {latest}"
    s.latest_raw = int(latest)
    s.update_available = bool(info.get("year") and latest > info["year"])
    if s.update_available:
        # BLS (Akamai) blocks datacenter IPs — from the server this update
        # fails; the admin must run it from the dev machine and commit.
        s.note = _notes().get("us_backend", "")
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
                        f"{res['scopes']} scopes · {_commit_note('us_oews.json.gz')}")


# ── Service API ───────────────────────────────────────────────────────────────
_CHECKERS = {"sweden_data": _check_sweden_data, "sweden_labels": _check_sweden_labels,
             "france_api": _check_france_api, "france_micro": _check_france_micro,
             "norway_data": _check_norway_data, "norway_labels": _check_norway_labels,
             "us_data": _check_us_data,
             "denmark_data": _check_denmark_data,
             "denmark_labels": _check_denmark_labels,
             "iceland_data": _check_iceland_data,
             "iceland_labels": _check_iceland_labels,
             "finland_data": _check_finland_data,
             "finland_labels": _check_finland_labels,
             "estonia_data": _check_estonia_data,
             "estonia_labels": _check_estonia_labels,
             "netherlands_data": _check_netherlands_data,
             "netherlands_labels": _check_netherlands_labels}
_UPDATERS = {"sweden_data": _update_sweden_data, "sweden_labels": _update_sweden_labels,
             "france_api": _update_france_api, "france_micro": _update_france_micro,
             "norway_data": _update_norway_data, "norway_labels": _update_norway_labels,
             "us_data": _update_us_data,
             "denmark_data": _update_denmark_data,
             "denmark_labels": _update_denmark_labels,
             "iceland_data": _update_iceland_data,
             "iceland_labels": _update_iceland_labels,
             "finland_data": _update_finland_data,
             "finland_labels": _update_finland_labels,
             "estonia_data": _update_estonia_data,
             "estonia_labels": _update_estonia_labels,
             "netherlands_data": _update_netherlands_data,
             "netherlands_labels": _update_netherlands_labels}
_BASE = {"sweden_data": ("Sweden", "SCB · data year"),
         "sweden_labels": ("Sweden", "SCB · SSYK labels"),
         "france_api": ("France", "INSEE Melodi · API"),
         "france_micro": ("France", "INSEE · microdata"),
         "norway_data": ("Norway", "SSB · data year"),
         "norway_labels": ("Norway", "SSB · STYRK labels"),
         "us_data": ("United States", "BLS OEWS"),
         "denmark_data": ("Denmark", "DST · data year"),
         "denmark_labels": ("Denmark", "DST · DISCO labels"),
         "iceland_data": ("Iceland", "Hagstofa · data year"),
         "iceland_labels": ("Iceland", "Hagstofa · ISCO labels"),
         "finland_data": ("Finland", "StatFin · data year"),
         "finland_labels": ("Finland", "StatFin · ISCO labels"),
         "estonia_data": ("Estonia", "Stat. Estonia · data year"),
         "estonia_labels": ("Estonia", "Stat. Estonia · ISCO labels"),
         "netherlands_data": ("Netherlands", "CBS · data year"),
         "netherlands_labels": ("Netherlands", "CBS · BRC labels")}
SOURCE_ORDER = ["sweden_data", "sweden_labels", "france_api", "france_micro",
                "norway_data", "norway_labels", "us_data",
                "denmark_data", "denmark_labels",
                "iceland_data", "iceland_labels",
                "finland_data", "finland_labels",
                "estonia_data", "estonia_labels",
                "netherlands_data", "netherlands_labels"]


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
