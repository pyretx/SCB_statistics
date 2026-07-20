"""Career Paths v1 — JobTech / Platsbanken importer + PII scrubber.

Fetches Swedish job ads for a given SSYK-2012 occupation from the open JobSearch
API (no key), and returns a PII-scrubbed, evidence-only view. Attribution:
Arbetsförmedlingen / JobTech (CC BY-SA). We never store ad text or personal data —
only aggregate facts downstream.

The API filters directly by SSYK via ``occupation-group`` (the legacy AMS taxonomy
id == SSYK-2012 4-digit). Skills / education / experience come pre-structured in
``must_have`` / ``nice_to_have`` (JobTech taxonomy), so no AI is needed to extract
them — the AI step only normalises the job title and infers seniority.

PII removed before anything leaves this module: contact-person names, emails,
phone numbers, application URLs, and street addresses. Municipality + region are
kept (aggregate geography). The scrubbed ``description`` is only ever passed to the
offline AI step — it is not persisted.
"""
from __future__ import annotations

import re

import net_fix  # noqa: F401 — force IPv4 before HTTP
import requests

_BASE = "https://jobsearch.api.jobtechdev.se/search"
# JobTech rejects offset > ~2000 with a 400, and `limit` > 100 likewise. Stop
# cleanly at the ceiling instead of walking into an error response.
_MAX_OFFSET = 2000
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_URL = re.compile(r"https?://\S+")
# Swedish phone numbers: start +46 or 0, then 7+ phone chars. Won't match salaries.
_PHONE = re.compile(r"(?:\+46|0)[\d\s\-()]{7,}\d")


def fetch_ads(ssyk: str, limit: int = 60, published_after: str | None = None) -> list[dict]:
    """Raw ads for one SSYK-2012 occupation (paginated up to ``limit``).
    ``published_after`` (ISO datetime) → only ads published since then, for the
    incremental refresh (JobTech ``published-after``)."""
    out: list[dict] = []
    offset = 0
    while len(out) < limit and offset < _MAX_OFFSET:
        n = min(100, limit - len(out), _MAX_OFFSET - offset)
        params = {"occupation-group": str(ssyk), "limit": n, "offset": offset}
        if published_after:
            params["published-after"] = str(published_after)[:19]
        try:
            r = requests.get(_BASE, params=params,
                             timeout=30, headers={"accept": "application/json"})
        except Exception as e:  # noqa: BLE001
            print(f"[career_jobtech] fetch {ssyk} failed: {e}")
            break
        if r.status_code != 200:
            break
        hits = r.json().get("hits", [])
        if not hits:
            break
        out += hits
        offset += n
        if len(hits) < n:
            break
    return out[:limit]


def _labels(section: dict | None, key: str) -> list[str]:
    return [s.get("label") for s in ((section or {}).get(key) or []) if s.get("label")]


def scrub(ad: dict) -> dict:
    """PII-scrubbed, evidence-only view of one ad. The scrubbed ``description`` is
    for the AI step only (never stored)."""
    contacts = ad.get("application_contacts") or []
    names = [c.get("name", "").strip() for c in contacts if c.get("name")]
    desc = (ad.get("description") or {}).get("text") or ""
    for nm in names:                       # drop known contact-person names
        if nm:
            desc = desc.replace(nm, " ")
    desc = _EMAIL.sub(" ", desc)
    desc = _URL.sub(" ", desc)
    desc = _PHONE.sub(" ", desc)
    desc = re.sub(r"[ \t]{2,}", " ", desc).strip()

    wa = ad.get("workplace_address") or {}
    mh, nh = ad.get("must_have") or {}, ad.get("nice_to_have") or {}
    return {
        "id": ad.get("id"),
        "headline": ad.get("headline"),
        "ssyk": (ad.get("occupation_group") or {}).get("legacy_ams_taxonomy_id"),
        "occupation": (ad.get("occupation") or {}).get("label"),
        "employer": (ad.get("employer") or {}).get("name"),      # company — not PII
        "municipality": wa.get("municipality"), "region": wa.get("region"),
        "employment_type": (ad.get("employment_type") or {}).get("label"),
        "experience_required": ad.get("experience_required"),
        "salary_type": (ad.get("salary_type") or {}).get("label"),
        "publication_date": ad.get("publication_date"),
        # Public ad reference — the id IS the Platsbanken reference number, and
        # webpage_url the direct link. Not PII (points at a public ad; links expire
        # at the application deadline). Used for "see the ads" references.
        "deadline": (ad.get("application_deadline") or "")[:10] or None,
        "url": ad.get("webpage_url") or (
            f"https://arbetsformedlingen.se/platsbanken/annonser/{ad.get('id')}" if ad.get("id") else None),
        "skills": _labels(mh, "skills") + _labels(nh, "skills"),
        "education": _labels(mh, "education") + _labels(nh, "education"),
        "languages": _labels(mh, "languages") + _labels(nh, "languages"),
        "experiences": _labels(mh, "work_experiences") + _labels(nh, "work_experiences"),
        "description": desc,               # scrubbed; passed to AI only, never stored
    }


def fetch_scrubbed(ssyk: str, limit: int = 60, published_after: str | None = None) -> list[dict]:
    return [scrub(a) for a in fetch_ads(ssyk, limit, published_after=published_after)]
