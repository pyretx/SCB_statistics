"""Career Paths (Sweden beta) — data layer.

Reads the curated cp_* register (deploy/sql/2026-07-14_career_paths.sql); see
docs/career-paths-assessment.md. Two audiences, same pattern as compliance.py:

  • PUBLIC  — the Sweden "Career Paths — Beta" tab reads the published views
    (v_cp_title_public / v_cp_rel_public), cached.
  • ADMIN   — the register admin section reads/edits the base tables via auth's
    service client (server-side only).

Defensive: every call is guarded, so BEFORE the migration is applied (tables
absent) it returns empty results — the tab then simply shows an empty/disabled
state and nothing crashes. No AI, no job-ad access here: v0 is fully curated and
deterministic. Salaries are NEVER stored here; they are computed live from the
official SCB curve via core.interp using each title's percentile band.
"""
from __future__ import annotations

import streamlit as st

import auth

_V_TITLE = "v_cp_title_public"
_V_REL = "v_cp_rel_public"
_T_FAMILY = "cp_family"
_T_TITLE = "cp_title"
_T_REL = "cp_relationship"

TRACKS = ["ic", "specialist", "management"]
CONFIDENCE = ["strong", "moderate", "limited", "experimental"]
REVIEW = ["draft", "reviewed", "approved"]
REL_TYPES = ["progression", "leadership", "specialist", "lateral", "entry", "related"]


def _safe(fn, what: str):
    try:
        return fn(), None
    except Exception as e:  # noqa: BLE001
        print(f"[careerpaths] {what} failed: {e}")
        return [], f"Could not load {what}."


# ── Public (cached) ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def public_titles() -> list[dict]:
    rows, _ = _safe(lambda: list(
        (auth._client().table(_V_TITLE).select("*")
         .order("family_id").order("level_index").execute()).data or []), "career titles")
    return rows


@st.cache_data(show_spinner=False, ttl=3600)
def public_relationships() -> list[dict]:
    rows, _ = _safe(lambda: list(
        (auth._client().table(_V_REL).select("*").execute()).data or []), "career relationships")
    return rows


def family_for_ssyk(ssyk: str) -> str | None:
    """Which published family a given occupation (4-digit SSYK) belongs to — the
    tab shows a family's map on the pages of any occupation that family covers.
    Matches a title's primary_ssyk or alt_ssyk."""
    ssyk = str(ssyk)
    for t in public_titles():
        if str(t.get("primary_ssyk")) == ssyk or ssyk in (t.get("alt_ssyk") or []):
            return t.get("family_id")
    return None


def titles_for_family(family_id: str) -> list[dict]:
    return [t for t in public_titles() if t.get("family_id") == family_id]


def relationships_for_family(family_id: str) -> list[dict]:
    return [r for r in public_relationships() if r.get("family_id") == family_id]


# ── Admin reads (service client) ─────────────────────────────────────────────
def _admin(table, what, order="created_at"):
    return _safe(lambda: list(
        (auth._client(service=True).table(table).select("*").order(order).execute()).data or []), what)


def families():      return _admin(_T_FAMILY, "families", order="family_id")
def titles():        return _admin(_T_TITLE, "titles", order="title_id")
def relationships(): return _admin(_T_REL, "relationships", order="rel_id")


# ── Admin writes ─────────────────────────────────────────────────────────────
def set_title(title_id: str, **changes) -> str | None:
    allowed = {"name_en", "name_sv", "primary_ssyk", "track", "level_index", "level_label",
               "lo_pct", "mid_pct", "hi_pct", "confidence", "review_status", "published", "notes"}
    changes = {k: v for k, v in changes.items() if k in allowed}
    if not changes:
        return None
    try:
        auth._client(service=True).table(_T_TITLE).update(changes).eq("title_id", title_id).execute()
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[careerpaths] set_title failed: {e}")
        return "Could not save title."


def set_relationship(rel_id: str, **changes) -> str | None:
    allowed = {"rel_type", "confidence", "review_status", "published", "explanation", "same_ssyk"}
    changes = {k: v for k, v in changes.items() if k in allowed}
    if not changes:
        return None
    try:
        auth._client(service=True).table(_T_REL).update(changes).eq("rel_id", rel_id).execute()
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[careerpaths] set_relationship failed: {e}")
        return "Could not save relationship."


def set_family_published(family_id: str, published: bool) -> str | None:
    try:
        auth._client(service=True).table(_T_FAMILY).update(
            {"published": bool(published)}).eq("family_id", family_id).execute()
        _clear_cache()
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[careerpaths] set_family_published failed: {e}")
        return "Could not save."


def _clear_cache():
    for fn in (public_titles, public_relationships):
        try:
            fn.clear()
        except Exception:
            pass


# ── Performance overlay (internal preview; never public unless enabled) ──────
def perf_bands() -> list[dict]:
    rows, _ = _safe(lambda: list(
        (auth._client(service=True).table("cp_perf_band").select("*")
         .order("position").execute()).data or []), "performance bands")
    return rows


def perf_config() -> dict:
    rows, _ = _safe(lambda: list(
        (auth._client(service=True).table("cp_perf_config").select("*").limit(1).execute()).data or []),
        "performance config")
    return rows[0] if rows else {"enabled_public": False, "disclaimer": ""}


def set_perf_band(band_id: str, **changes) -> str | None:
    allowed = {"label", "position", "rel_lo", "rel_hi", "description"}
    changes = {k: v for k, v in changes.items() if k in allowed}
    if not changes:
        return None
    try:
        auth._client(service=True).table("cp_perf_band").update(changes).eq("band_id", band_id).execute()
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[careerpaths] set_perf_band failed: {e}")
        return "Could not save band."


def set_perf_config(**changes) -> str | None:
    allowed = {"enabled_public", "disclaimer"}
    changes = {k: v for k, v in changes.items() if k in allowed}
    if not changes:
        return None
    try:
        auth._client(service=True).table("cp_perf_config").update(changes).eq("id", 1).execute()
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[careerpaths] set_perf_config failed: {e}")
        return "Could not save config."


def log_change(subject_type: str, subject_id: str, action: str, actor: str,
               before_after: dict | None = None) -> None:
    """Append an audit entry (reuses the compliance_review_log table — generic
    subject_type/subject_id). Never raises."""
    try:
        (auth._client(service=True).table("compliance_review_log").insert({
            "subject_type": subject_type, "subject_id": subject_id,
            "action": action, "actor": actor, "before_after": before_after or {}}).execute())
    except Exception as e:  # noqa: BLE001
        print(f"[careerpaths] log_change failed: {e}")
