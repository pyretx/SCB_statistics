"""Compliance register — read/query layer for Salary Explorer.

Reads the Supabase compliance register defined in
deploy/sql/2026-07-14_compliance_register.sql (framework: docs/compliance-framework.md).

Two audiences:
  • PUBLIC  — the Data Sources & Methodology page reads the curated view
    ``v_compliance_public`` (publishable rows/columns only; the release gate is
    baked into the view, framework §6).
  • ADMIN   — the register admin section reads the base tables via auth's existing
    service client (server-side only) and edits clearance/assessments.

Defensive by design: every call is guarded, so BEFORE the migration is applied
(tables absent) it returns empty results + a safe error rather than raising — this
module is import-safe and wiring it into a page cannot break the running app.

Nothing here is wired into a page yet; that is Phase 1–3 in the framework.
"""
from __future__ import annotations

import datetime as _dt

import streamlit as st

import auth

_PUBLIC_VIEW = "v_compliance_public"
_T_PROVIDER = "compliance_provider"
_T_DATASET = "compliance_dataset"
_T_ACCESS = "compliance_access_method"
_T_IMPL = "compliance_country_impl"
_T_ASSESS = "compliance_assessment"
_T_TRANSFORM = "compliance_transformation"

# The five clearance states (framework §4), worst → best for rollups.
CLEARANCE_STATES = ["restricted", "owner_review", "provider_confirm",
                    "likely_verify", "confirmed"]
DIMENSIONS = ["access", "commercial", "redistribute", "derive", "store_cache",
              "attribution", "api_terms", "microdata_confidentiality"]


def _safe(fn, what: str):
    """Run a Supabase read, returning (data, None) or ([], safe_error). Never
    raises — a missing table (pre-migration) or transport error is logged
    server-side and surfaced as a friendly message."""
    try:
        return fn(), None
    except Exception as e:  # noqa: BLE001
        print(f"[compliance] {what} failed: {e}")   # server log only
        return [], f"Could not load {what}."


# ── Public projection (Data Sources & Methodology page) ──────────────────────
def public_all() -> tuple[list[dict], str | None]:
    """Every publishable country record (release gate applied inside the view)."""
    return _safe(lambda: list(
        (auth._client().table(_PUBLIC_VIEW)
         .select("*").order("country_slug").execute()).data or []),
        "public sources")


def public_country(country_slug: str) -> dict | None:
    """The publishable record for one country, or None if not published."""
    rows, _ = _safe(lambda: list(
        (auth._client().table(_PUBLIC_VIEW)
         .select("*").eq("country_slug", country_slug).limit(1).execute()).data or []),
        "public source")
    return rows[0] if rows else None


@st.cache_data(show_spinner=False, ttl=3600)
def country_notes(country_slug: str) -> dict | None:
    """Cached per-country public record for the in-page 'Sources & methods' panel
    (Phase 4 derived-data labelling). Cached for an hour so a country page render
    never pays a DB round-trip on every rerun; returns None if not published or on
    any error (the panel then simply doesn't show)."""
    return public_country(country_slug)


# ── Admin register reads (service client — server-side only) ─────────────────
def _admin_read(table: str, what: str, order: str = "created_at",
                desc: bool = False) -> tuple[list[dict], str | None]:
    return _safe(lambda: list(
        (auth._client(service=True).table(table)
         .select("*").order(order, desc=desc).execute()).data or []),
        what)


def providers():        return _admin_read(_T_PROVIDER, "providers", order="provider_id")
def datasets():         return _admin_read(_T_DATASET, "datasets", order="dataset_id")
def access_methods():   return _admin_read(_T_ACCESS, "access methods", order="access_id")
def country_impls():    return _admin_read(_T_IMPL, "country implementations", order="country_slug")
def assessments():      return _admin_read(_T_ASSESS, "assessments", order="subject_id")
def transformations():  return _admin_read(_T_TRANSFORM, "transformations", order="impl_id")


# ── Review cadence (framework §10 — admin Overview reminder tile) ─────────────
def overdue_reviews(within_days: int = 0) -> tuple[list[dict], str | None]:
    """Assessments whose next_review_date is on/before (today + within_days).
    within_days=0 → strictly overdue; e.g. 30 → 'due within a month' too."""
    cutoff = (_dt.date.today() + _dt.timedelta(days=within_days)).isoformat()
    return _safe(lambda: list(
        (auth._client(service=True).table(_T_ASSESS)
         .select("*").lte("next_review_date", cutoff)
         .order("next_review_date").execute()).data or []),
        "overdue reviews")


def review_counts() -> dict:
    """Small summary for the admin Overview tile: {overdue, due_soon}. Silent on
    error (returns zeros) so the tile never breaks the Overview."""
    overdue, err = overdue_reviews(0)
    if err:
        return {"overdue": 0, "due_soon": 0}
    soon, _ = overdue_reviews(30)
    return {"overdue": len(overdue), "due_soon": max(0, len(soon) - len(overdue))}


# ── Clearance rollup helper (worst dimension wins) ───────────────────────────
def rollup(statuses) -> str:
    """The overall clearance = the WORST dimension state present (framework §4).
    Empty → 'likely_verify' (nothing assessed yet, not a hard fail)."""
    present = [s for s in statuses if s in CLEARANCE_STATES]
    if not present:
        return "likely_verify"
    return min(present, key=CLEARANCE_STATES.index)


# ── Admin writes (service client — server-side only) ─────────────────────────
def set_assessment(assessment_id: str, *, status=None, next_review_date=None,
                   evidence_url=None, evidence_note=None,
                   reviewed_by=None, reviewed_date=None) -> str | None:
    """Update one assessment (a dimension verdict). None on success, else a safe
    error string. Only whitelisted fields are written."""
    changes: dict = {}
    if status is not None:
        if status not in CLEARANCE_STATES:
            return "Invalid status."
        changes["status"] = status
    for k, v in (("next_review_date", next_review_date), ("evidence_url", evidence_url),
                 ("evidence_note", evidence_note), ("reviewed_by", reviewed_by),
                 ("reviewed_date", reviewed_date)):
        if v is not None:
            changes[k] = v or None      # "" → NULL
    if not changes:
        return None
    try:
        (auth._client(service=True).table(_T_ASSESS)
         .update(changes).eq("assessment_id", assessment_id).execute())
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[compliance] set_assessment failed: {e}")
        return "Could not save assessment."


def set_impl(impl_id: str, **changes) -> str | None:
    """Update a country implementation's gate fields (release_status,
    public_publishable, grandfathered, clearance_overall). Ignores other keys."""
    allowed = {"release_status", "public_publishable", "grandfathered", "clearance_overall"}
    changes = {k: v for k, v in changes.items() if k in allowed}
    if not changes:
        return None
    try:
        (auth._client(service=True).table(_T_IMPL)
         .update(changes).eq("impl_id", impl_id).execute())
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[compliance] set_impl failed: {e}")
        return "Could not save implementation."


def recompute_for_dataset(dataset_id: str) -> int:
    """After dataset-dimension edits, recompute clearance_overall (worst of the
    dataset's dimensions + each impl's access-method dimensions) for every impl on
    that dataset. Returns how many impls changed."""
    ass, _ = assessments()
    impls, _ = country_impls()
    ds_status = [a["status"] for a in ass
                 if a["subject_type"] == "dataset" and a["subject_id"] == dataset_id]
    changed = 0
    for im in impls:
        if im.get("dataset_id") != dataset_id:
            continue
        acc_status = [a["status"] for a in ass
                      if a["subject_type"] == "access" and a["subject_id"] == im.get("access_id")]
        overall = rollup(ds_status + acc_status)
        if overall != im.get("clearance_overall"):
            if not set_impl(im["impl_id"], clearance_overall=overall):
                changed += 1
    return changed
