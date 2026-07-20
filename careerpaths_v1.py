"""Career Paths v1 — job-ad evidence data layer (admin/offline only).

Reads/writes the cp_v1_* tables (deploy/sql/2026-07-14_career_v1.sql). Everything
here is admin/master-gated and server-side (service key). No public exposure.
Guarded: before the migration exists (tables absent) every call returns empty /
False, so the admin UI + importer stay import-safe.

The AI batch + JobTech importer live in separate modules (added next); this is just
the storage interface + the master on/off toggle + the review queue.
"""
from __future__ import annotations

import datetime as _dt

import auth

_T_CONFIG = "cp_v1_config"
_T_RUN = "cp_run_log"
_T_RTM = "cp_raw_title_map"
_T_EVID = "cp_title_evidence"
_T_SUG = "cp_suggestion"
_T_ADCLASS = "cp_ad_class"


def _safe(fn, what, default=None):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        print(f"[careerpaths_v1] {what} failed: {e}")
        return default


# ── Master config / toggle ───────────────────────────────────────────────────
def config() -> dict:
    rows = _safe(lambda: list(
        (auth._client(service=True).table(_T_CONFIG).select("*").limit(1).execute()).data or []),
        "config", [])
    return rows[0] if rows else {"enabled": False, "model": "claude-haiku-4-5",
                                 "max_ads_per_ssyk": 60, "min_ads_suggestion": 5,
                                 "review_level": "light", "last_run": None}


def set_config(**changes) -> str | None:
    allowed = {"enabled", "model", "max_ads_per_ssyk", "min_ads_suggestion", "review_level", "last_run"}
    changes = {k: v for k, v in changes.items() if k in allowed}
    if not changes:
        return None
    return _safe(lambda: (auth._client(service=True).table(_T_CONFIG)
                          .update(changes).eq("id", 1).execute()) and None,
                 "set_config", "Could not save config.")


def enabled() -> bool:
    return bool(config().get("enabled"))


# ── Run log ──────────────────────────────────────────────────────────────────
def start_run(actor: str, families: list, model: str) -> str | None:
    row = _safe(lambda: (auth._client(service=True).table(_T_RUN).insert({
        "actor": actor, "families": families, "model": model, "status": "running"}).execute()).data,
        "start_run", None)
    return row[0]["run_id"] if row else None


def finish_run(run_id: str, *, status="done", ads_fetched=0, ads_processed=0,
               suggestions=0, error=None) -> None:
    _safe(lambda: auth._client(service=True).table(_T_RUN).update({
        "finished_at": _dt.datetime.utcnow().isoformat(), "status": status,
        "ads_fetched": ads_fetched, "ads_processed": ads_processed,
        "suggestions": suggestions, "error": error}).eq("run_id", run_id).execute(),
        "finish_run")
    if status == "done":
        set_config(last_run=_dt.datetime.utcnow().isoformat())


def recent_runs(limit=10) -> list[dict]:
    return _safe(lambda: list(
        (auth._client(service=True).table(_T_RUN).select("*")
         .order("started_at", desc=True).limit(limit).execute()).data or []), "runs", []) or []


def due_for_refresh(days=30) -> bool:
    lr = config().get("last_run")
    if not lr:
        return True
    try:
        last = _dt.datetime.fromisoformat(str(lr).replace("Z", "+00:00")).replace(tzinfo=None)
        return (_dt.datetime.utcnow() - last).days >= days
    except Exception:
        return True


# ── Suggestions (review queue) ───────────────────────────────────────────────
def suggestions(status="pending") -> list[dict]:
    def q():
        b = auth._client(service=True).table(_T_SUG).select("*")
        if status:
            b = b.eq("status", status)
        return list((b.order("confidence").order("ad_support", desc=True).execute()).data or [])
    return _safe(q, "suggestions", []) or []


def set_suggestion(sug_id: str, status: str, reviewer: str) -> str | None:
    return _safe(lambda: (auth._client(service=True).table(_T_SUG).update({
        "status": status, "reviewed_by": reviewer,
        "reviewed_at": _dt.datetime.utcnow().isoformat()}).eq("id", sug_id).execute()) and None,
        "set_suggestion", "Could not save.")


def bulk_set_suggestions(ids: list[str], status: str, reviewer: str) -> int:
    n = 0
    for sid in ids:
        if not set_suggestion(sid, status, reviewer):
            n += 1
    return n


# ── Evidence / raw-title map (reads for admin + the tab) ─────────────────────
def evidence() -> dict:
    rows = _safe(lambda: list(
        (auth._client(service=True).table(_T_EVID).select("*").execute()).data or []), "evidence", []) or []
    return {r["title_id"]: r for r in rows}


def raw_title_map(status=None) -> list[dict]:
    def q():
        b = auth._client(service=True).table(_T_RTM).select("*")
        if status:
            b = b.eq("status", status)
        return list((b.order("ad_count", desc=True).execute()).data or [])
    return _safe(q, "raw title map", []) or []


# ── Writes (used by the pipeline orchestrator) ───────────────────────────────
def upsert_evidence(rows: list[dict]) -> None:
    if rows:
        _safe(lambda: auth._client(service=True).table(_T_EVID)
              .upsert(rows, on_conflict="title_id").execute(), "upsert_evidence")


def upsert_raw_titles(rows: list[dict]) -> None:
    if rows:
        _safe(lambda: auth._client(service=True).table(_T_RTM)
              .upsert(rows, on_conflict="raw_title,ssyk").execute(), "upsert_raw_titles")


def add_suggestions(rows: list[dict]) -> None:
    if rows:
        _safe(lambda: auth._client(service=True).table(_T_SUG).insert(rows).execute(),
              "add_suggestions")


# ── Rolling per-ad classification store (incremental refresh) ────────────────
def upsert_ad_class(rows: list[dict]) -> None:
    if rows:
        _safe(lambda: auth._client(service=True).table(_T_ADCLASS)
              .upsert(rows, on_conflict="ad_id").execute(), "upsert_ad_class")


def ad_class_for_ssyk(ssyk: str) -> list[dict]:
    return _safe(lambda: list(
        (auth._client(service=True).table(_T_ADCLASS).select("*")
         .eq("ssyk", str(ssyk)).execute()).data or []), "ad_class", []) or []


def ads_for_titles(pairs) -> dict:
    """The stored ads behind a set of (ssyk, norm_title) suggestions, keyed by
    that pair. One batched query over the indexed `ssyk` column — the review
    queue renders up to 60 suggestions, so a per-card lookup would be 60 round
    trips. Newest ad first. A missing/empty entry is normal: cp_ad_class is
    pruned after the rolling window, so older ads drop out."""
    ssyks = sorted({str(s) for s, _ in pairs if s})
    if not ssyks:
        return {}
    rows = _safe(lambda: list(
        (auth._client(service=True).table(_T_ADCLASS).select("*")
         .in_("ssyk", ssyks).execute()).data or []), "ads_for_titles", []) or []
    want = {(str(s), (t or "").strip().casefold()) for s, t in pairs}
    out: dict = {}
    for r in rows:
        key = (str(r.get("ssyk") or ""), (r.get("norm_title") or "").strip().casefold())
        if key in want:
            out.setdefault(key, []).append(r)
    for v in out.values():
        v.sort(key=lambda r: str(r.get("publication_date") or ""), reverse=True)
    return out


def prune_ad_class(max_days: int = 120) -> None:
    """Drop only STALE classifications (older than the rolling window) so the
    store doesn't grow unbounded. Expired ads (application deadline passed) are
    KEPT — we retain them in the database for history; the live signal simply
    stops counting them (aggregation + UI filter out ads whose deadline passed).
    A stale-by-classified_at prune still clears out ads we haven't re-seen in
    `max_days`, which naturally sweeps long-expired rows."""
    cutoff = (_dt.date.today() - _dt.timedelta(days=max_days)).isoformat()
    _safe(lambda: auth._client(service=True).table(_T_ADCLASS)
          .delete().lt("classified_at", cutoff).execute(), "prune stale")
