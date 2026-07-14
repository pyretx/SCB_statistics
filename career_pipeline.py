"""Career Paths v1 — refresh orchestrator + aggregation (offline / admin-triggered).

Ties the pieces together for a refresh run:
  fetch (career_jobtech) → PII scrub → classify (career_ai) → aggregate → write.

Writes only AGGREGATE facts (no ad text, no PII):
  • cp_title_evidence — per canonical title: ad count, top skills (with counts),
    management frequency, typical experience, top title variants, evidence strength.
    Auto-applied (the "light" review lane).
  • cp_raw_title_map — discovered normalised title variants per SSYK, with counts.
  • cp_suggestion — NEW-TITLE ideas (a frequent normalised title that doesn't match
    any existing canonical title in the family) → the review queue.

Gated by cp_v1_config.enabled; bounded by max_ads_per_ssyk; suppresses evidence /
suggestions below min_ads. Never raises; logs the run. Attribution:
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


def run(families: list[str] | None = None, actor: str = "admin",
        max_ads: int | None = None) -> dict:
    """Run a refresh over the given families (default: all published). Returns a
    summary dict. Safe to call only when enabled; the caller checks the toggle."""
    conf = v1.config()
    model = conf.get("model") or "claude-haiku-4-5-20251001"
    cap = int(max_ads or conf.get("max_ads_per_ssyk") or 60)
    min_ads = int(conf.get("min_ads_suggestion") or 5)

    titles = cp.titles()[0] or []
    if families:
        titles = [t for t in titles if t.get("family_id") in set(families)]
    fam_list = sorted({t["family_id"] for t in titles})
    run_id = v1.start_run(actor, fam_list, model)

    # SSYK → the canonical titles that live in it (with their families)
    by_ssyk: dict[str, list] = {}
    for t in titles:
        by_ssyk.setdefault(str(t["primary_ssyk"]), []).append(t)

    ads_fetched = ads_proc = 0
    evidence_rows: list[dict] = []
    raw_rows: list[dict] = []
    suggestions: list[dict] = []
    today = _dt.date.today().isoformat()

    try:
        for ssyk, ssyk_titles in by_ssyk.items():
            scrubbed = jt.fetch_scrubbed(ssyk, limit=cap)
            ads_fetched += len(scrubbed)
            classified = career_ai.classify(scrubbed, model=model) if scrubbed else []
            ads_proc += len(classified)
            if not classified:
                continue

            # discovered title variants (per ssyk)
            variant_counts = Counter(c["norm_title"] for c in classified if c.get("norm_title"))
            fam = ssyk_titles[0]["family_id"]
            existing = {_norm(x["name_en"]) for x in ssyk_titles}
            for x in ssyk_titles:
                for v in (x.get("raw_variants") or []):
                    existing.add(_norm(v))

            # per canonical title: aggregate matching ads (by seniority bucket)
            for t in ssyk_titles:
                bucket = _bucket(t)
                matched = [c for c in classified if c.get("seniority") in bucket]
                if len(matched) < 1:
                    continue
                skills = Counter(s for c in matched for s in (c.get("skills") or []))
                yrs = [c["years"] for c in matched if isinstance(c.get("years"), int)]
                variants = Counter(c["norm_title"] for c in matched if c.get("norm_title"))
                evidence_rows.append({
                    "title_id": t["title_id"], "ad_count": len(matched),
                    "common_skills": [{"skill": s, "freq": n} for s, n in skills.most_common(10)],
                    "common_experience": ([{"years_min": min(yrs), "years_median": sorted(yrs)[len(yrs) // 2]}]
                                          if yrs else []),
                    "common_education": [], "common_certs": [],
                    "mgmt_freq": round(sum(1 for c in matched if c.get("mgmt")) / len(matched), 2),
                    "top_variants": [{"title": v, "freq": n} for v, n in variants.most_common(6)],
                    "observed_to": today, "evidence_strength": _strength(len(matched)),
                    "updated_at": _dt.datetime.utcnow().isoformat(),
                })

            # raw-title map rows (discovered variants → best-guess canonical)
            for variant, n in variant_counts.items():
                raw_rows.append({
                    "family_id": fam, "raw_title": variant[:200], "ssyk": ssyk,
                    "ad_count": n, "last_seen": today, "status": "auto",
                    "updated_at": _dt.datetime.utcnow().isoformat(),
                })

            # NEW-TITLE suggestions: frequent variant not matching any canonical name
            for variant, n in variant_counts.items():
                if n >= min_ads and _norm(variant) not in existing \
                        and not any(_norm(variant) in e or e in _norm(variant) for e in existing):
                    suggestions.append({
                        "family_id": fam, "kind": "new_title",
                        "summary": f"Frequent job title '{variant}' (SSYK {ssyk}) not yet a canonical role",
                        "payload": {"norm_title": variant, "ssyk": ssyk, "ad_count": n},
                        "confidence": "moderate" if n >= 10 else "limited",
                        "ad_support": n, "model": model,
                    })

        v1.upsert_evidence(evidence_rows)
        v1.upsert_raw_titles(raw_rows)
        # de-dup suggestions by (norm_title, ssyk) and skip ones already pending
        seen = {(_norm(s["payload"]["norm_title"]), s["payload"]["ssyk"])
                for s in v1.suggestions("pending")}
        fresh = [s for s in suggestions
                 if (_norm(s["payload"]["norm_title"]), s["payload"]["ssyk"]) not in seen]
        v1.add_suggestions(fresh)

        v1.finish_run(run_id, status="done", ads_fetched=ads_fetched,
                      ads_processed=ads_proc, suggestions=len(fresh))
        return {"ok": True, "ads_fetched": ads_fetched, "ads_processed": ads_proc,
                "titles_with_evidence": len(evidence_rows), "suggestions": len(fresh)}
    except Exception as e:  # noqa: BLE001
        v1.finish_run(run_id, status="failed", ads_fetched=ads_fetched,
                      ads_processed=ads_proc, error=str(e))
        print(f"[career_pipeline] run failed: {e}")
        return {"ok": False, "error": str(e)}
