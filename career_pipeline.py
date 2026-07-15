"""Career Paths v1 — refresh orchestrator + aggregation (offline / admin-triggered).

Two modes, same aggregation:
  • FULL (default)       — fetch up to max_ads_per_ssyk ads, (re)classify all,
    aggregate + overwrite that SSYK's evidence. Rebuilds from scratch.
  • INCREMENTAL          — fetch only ads published AFTER the last run
    (JobTech published-after), classify only those NEW ads, upsert them into the
    rolling per-ad store (cp_ad_class), prune expired/stale rows, and re-aggregate
    evidence from the rolling window. Each refresh only touches the delta → fast +
    cheap for ongoing monthly updates.

Writes only AGGREGATE facts + public ad references (no ad body text, no PII).
Gated by cp_v1_config.enabled; never raises; logs the run. Attribution:
Arbetsförmedlingen / JobTech (CC BY-SA).
"""
from __future__ import annotations

import datetime as _dt
from collections import Counter

import careerpaths as cp
import careerpaths_v1 as v1
import career_ai
import career_jobtech as jt

# canonical level_index / track → the ad-seniority bucket(s) that map to it
_LEVEL_BUCKET = {1: {"junior"}, 2: {"mid"}, 3: {"senior"}, 4: {"lead"}, 5: {"principal"}}


def _bucket(title: dict) -> set:
    if title.get("track") == "management":
        return {"manager"}
    return _LEVEL_BUCKET.get(int(title.get("level_index") or 2), {"mid"})


def _strength(n: int) -> str:
    return "strong" if n >= 20 else "moderate" if n >= 8 else "limited"


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _open(deadline, today: str) -> bool:
    """An ad is still 'live' if it has no application deadline or the deadline
    hasn't passed. Expired ads are retained in the store (history) but drop out
    of the live market signal so users never see a dead Platsbanken link."""
    return not deadline or str(deadline)[:10] >= today


def _record(c: dict, s: dict | None) -> dict:
    """Flatten one classified ad (c) + its scrubbed source (s) into a single
    aggregate-ready record — also the exact shape of a cp_ad_class row."""
    s = s or {}
    return {
        "ad_id": c.get("id"), "ssyk": str(c.get("ssyk") or s.get("ssyk") or ""),
        "seniority": c.get("seniority"), "mgmt": bool(c.get("mgmt")),
        "years": c.get("years") if isinstance(c.get("years"), int) else None,
        "norm_title": c.get("norm_title"),
        "skills": list(c.get("skills") or []), "education": c.get("education"),
        "certs": list(c.get("certs") or []), "languages": list(s.get("languages") or []),
        "employment_type": s.get("employment_type"), "region": s.get("region"),
        "employer": s.get("employer"), "deadline": s.get("deadline"), "url": s.get("url"),
        "headline": c.get("headline") or s.get("headline"),
        "publication_date": s.get("publication_date"),
    }


def _title_evidence(t: dict, records: list[dict], today: str) -> dict | None:
    """Aggregate the records that match a canonical title's seniority bucket."""
    bucket = _bucket(t)
    matched = [r for r in records
               if r.get("seniority") in bucket and _open(r.get("deadline"), today)]
    if not matched:
        return None
    skills = Counter(x for r in matched for x in (r.get("skills") or []))
    yrs = [r["years"] for r in matched if isinstance(r.get("years"), int)]
    edu = Counter(r.get("education") for r in matched if r.get("education"))
    certs = Counter(x for r in matched for x in (r.get("certs") or []))
    langs = Counter(l for r in matched for l in (r.get("languages") or []))
    emp = Counter(r.get("employer") for r in matched if r.get("employer"))
    emptype = Counter(r.get("employment_type") for r in matched if r.get("employment_type"))
    variants = Counter(r["norm_title"] for r in matched if r.get("norm_title"))
    ex = sorted([r for r in matched if r.get("ad_id")],
                key=lambda r: (r.get("publication_date") or ""), reverse=True)[:12]
    return {
        "title_id": t["title_id"], "ad_count": len(matched),
        "common_skills": [{"skill": s, "freq": n} for s, n in skills.most_common(10)],
        "common_experience": ([{"years_min": min(yrs), "years_median": sorted(yrs)[len(yrs) // 2]}]
                              if yrs else []),
        "common_education": [{"label": l, "freq": n} for l, n in edu.most_common(6)],
        "common_certs": [{"label": l, "freq": n} for l, n in certs.most_common(6)],
        "common_languages": [{"label": l, "freq": n} for l, n in langs.most_common(6)],
        "employment_mix": dict(emptype.most_common(6)),
        "top_employers": [{"name": e, "freq": n} for e, n in emp.most_common(6)],
        "example_ads": [{"id": r.get("ad_id"), "headline": (r.get("headline") or "")[:120],
                         "employer": r.get("employer"), "deadline": r.get("deadline"),
                         "region": r.get("region"), "url": r.get("url")} for r in ex],
        "mgmt_freq": round(sum(1 for r in matched if r.get("mgmt")) / len(matched), 2),
        "top_variants": [{"title": v, "freq": n} for v, n in variants.most_common(6)],
        "observed_to": today, "evidence_strength": _strength(len(matched)),
        "updated_at": _dt.datetime.utcnow().isoformat(),
    }


def run(families: list[str] | None = None, actor: str = "admin", max_ads: int | None = None,
        classify_fn=None, model_label: str | None = None, incremental: bool = False) -> dict:
    """Run a refresh over the given families (default: all). Returns a summary.

    Backends (hybrid): default classification uses the paid Anthropic API on the
    configured model; pass `classify_fn(scrubbed_ads) -> list` for a MAX-powered
    pass at no API cost. `incremental=True` only fetches/classifies ads published
    since the last run and re-aggregates from the rolling cp_ad_class store."""
    conf = v1.config()
    api_model = conf.get("model") or "claude-haiku-4-5-20251001"
    model = (model_label or api_model) + ("+inc" if incremental else "")
    classify = classify_fn or (lambda ads: career_ai.classify(ads, model=api_model))
    cap = int(max_ads or conf.get("max_ads_per_ssyk") or 60)
    min_ads = int(conf.get("min_ads_suggestion") or 5)
    last_run = conf.get("last_run") if incremental else None

    titles = cp.titles()[0] or []
    if families:
        titles = [t for t in titles if t.get("family_id") in set(families)]
    fam_list = sorted({t["family_id"] for t in titles})
    run_id = v1.start_run(actor, fam_list, model)

    by_ssyk: dict[str, list] = {}
    for t in titles:
        by_ssyk.setdefault(str(t["primary_ssyk"]), []).append(t)

    ads_fetched = ads_proc = 0
    evidence_rows: list[dict] = []
    raw_rows: list[dict] = []
    suggestions: list[dict] = []
    today = _dt.date.today().isoformat()
    now = _dt.datetime.utcnow().isoformat()

    try:
        for ssyk, ssyk_titles in by_ssyk.items():
            scrubbed = jt.fetch_scrubbed(ssyk, limit=cap, published_after=last_run)
            ads_fetched += len(scrubbed)
            scrub_by_id = {a.get("id"): a for a in scrubbed}
            classified = classify(scrubbed) if scrubbed else []
            ads_proc += len(classified)
            new_records = [_record(c, scrub_by_id.get(c.get("id"))) for c in classified if c.get("id")]

            if incremental:
                if new_records:
                    v1.upsert_ad_class([dict(r, classified_at=now) for r in new_records])
                records = v1.ad_class_for_ssyk(ssyk)          # rolling window (all)
            else:
                records = new_records
            if not records:
                continue

            fam = ssyk_titles[0]["family_id"]
            existing = {_norm(x["name_en"]) for x in ssyk_titles}
            for x in ssyk_titles:
                for v in (x.get("raw_variants") or []):
                    existing.add(_norm(v))

            for t in ssyk_titles:
                ev = _title_evidence(t, records, today)
                if ev:
                    evidence_rows.append(ev)

            variant_counts = Counter(r["norm_title"] for r in records if r.get("norm_title"))
            for variant, n in variant_counts.items():
                raw_rows.append({"family_id": fam, "raw_title": variant[:200], "ssyk": ssyk,
                                 "ad_count": n, "last_seen": today, "status": "auto", "updated_at": now})
            for variant, n in variant_counts.items():
                if n >= min_ads and _norm(variant) not in existing \
                        and not any(_norm(variant) in e or e in _norm(variant) for e in existing):
                    suggestions.append({
                        "family_id": fam, "kind": "new_title",
                        "summary": f"Frequent job title '{variant}' (SSYK {ssyk}) not yet a canonical role",
                        "payload": {"norm_title": variant, "ssyk": ssyk, "ad_count": n},
                        "confidence": "moderate" if n >= 10 else "limited",
                        "ad_support": n, "model": model})

        if incremental:
            v1.prune_ad_class(120)
        v1.upsert_evidence(evidence_rows)
        v1.upsert_raw_titles(raw_rows)
        seen = {(_norm(s["payload"]["norm_title"]), s["payload"]["ssyk"])
                for s in v1.suggestions("pending")}
        fresh = [s for s in suggestions
                 if (_norm(s["payload"]["norm_title"]), s["payload"]["ssyk"]) not in seen]
        v1.add_suggestions(fresh)

        v1.finish_run(run_id, status="done", ads_fetched=ads_fetched,
                      ads_processed=ads_proc, suggestions=len(fresh))
        return {"ok": True, "mode": "incremental" if incremental else "full",
                "ads_fetched": ads_fetched, "ads_processed": ads_proc,
                "titles_with_evidence": len(evidence_rows), "suggestions": len(fresh)}
    except Exception as e:  # noqa: BLE001
        v1.finish_run(run_id, status="failed", ads_fetched=ads_fetched,
                      ads_processed=ads_proc, error=str(e))
        print(f"[career_pipeline] run failed: {e}")
        return {"ok": False, "error": str(e)}
