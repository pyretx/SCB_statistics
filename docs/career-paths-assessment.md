# Career Paths (Sweden beta) — evaluation & proposed method

Status: **assessment / proposal** (2026-07). Written before implementation, per the
brief's Phase 1. It inspects the existing app, challenges the concept's weak
assumptions, and proposes a defensible, tightly-scoped Swedish beta. Nothing is built
by this document.

---

## 1. What the codebase gives us (inspected)

| Area | Finding | Consequence for Career Paths |
|---|---|---|
| **Sweden data** (`countries/se2/provider.py`) | SCB AM0110: per **4-digit SSYK-2012** occupation × sex × year × sector, values = **mean, median (=P50), P10, P25, P75, P90** (monthly SEK, full-time-equivalent). Plus mean-only breakdowns by age / region / education. | We have **exactly 5 distribution points** per occupation. Any finer curve is interpolation. Managers ARE separate SSYK occupations (major group 1), incl. level-1/level-2 splits. |
| **Percentile rendering** (`core/tabs/distribution.py`, `core/charts.py`) | The distribution tab plots the 5 discrete points as a value-vs-percentile chart. **No interpolation exists today.** | Career overlays need a new, documented, tested interpolation utility that preserves the 5 official points. |
| **Beta gating** (`core/tabs/__init__.py`) | `_BETA_TABS` + `access.is_beta_or_admin(cfg)` already hide tabs from non-beta users. `import_overlay` is a live example. | A "Career Paths — Beta" tab drops straight into this — **no new feature-flag system needed**. |
| **Country tabs** (`cfg.extra_tabs`) | `{id: render_fn(cfg, stats, query)}`, appended per country (Germany's skill-levels uses it). | Career Paths = a Sweden-only `extra_tab`, reusing the existing chart + i18n + disclaimer patterns. |
| **AI** | **None.** Grep for openai/anthropic/llm hits only comments and offline build scripts. Occupation translations were produced offline, not at runtime. | AI is **net-new infrastructure**. It must be **offline/batch**, never per-request. The runtime stays deterministic (reads pre-computed tables). |
| **Compliance register** (`compliance.py`, Supabase) | We just built a Provider→Dataset→Access→Impl register with clearance + attribution + the public methodology page. | JobTech is registered as a new dataset; its CC-BY-SA terms + attribution live there and surface on the public methodology page. |
| **Persistence** | Supabase (register/feedback/messages) + bundled JSON/gzip snapshots + disk cache for live SCB fetches. | Career Paths data (canonical titles, level estimates, relationships) fits the Supabase pattern; the runtime reads approved rows only. |

---

## 2. The core epistemic problem (and challenged assumptions)

**SCB percentiles describe the pay distribution of the *employed population* in an SSYK
(FTE). Job ads describe *employer demand for vacancies*. Neither dataset links a job
title or seniority level to a percentile of the SCB curve.** There is **no ground truth**
for "Senior Developer = P60–P80". Every level→percentile statement is an *inference*.

The brief already acknowledges this (its §2). The method must therefore be conservative,
wide, overlapping, and labelled a Qvistin estimate. Concrete challenges to the brief:

1. **Job-ad salary evidence (Approach B's salary part) is near-useless in Sweden.** Most
   Swedish ads say "lön enligt överenskommelse" — salary is rarely stated. So we cannot
   calibrate levels from ad salaries. We calibrate **seniority ordering** from ads and
   place it on the SCB curve. → *Drop ad-salary calibration for the Sweden beta.*
2. **Distribution mixture model (Approach C) is not identifiable** from 5 percentile
   points with no per-title microdata. It would manufacture false precision. → *Reject C
   for the beta.*
3. **Career-transition probabilities cannot come from ads.** Ads show role *similarity*,
   not how often people move. → *Only ever show "possible directions", never "% move".*
   (The brief agrees in §6.6 — reinforced here.)
4. **Seven levels is too many to force.** HR and Software realistically support ~4–6.
   Management is a **separate track**, not a higher IC rung. → *Configurable level count
   per family; IC and management as parallel tracks that fork.*
5. **The beta does not need a live ad-import + AI pipeline to test the concept.** The most
   defensible first step is a **human-curated scaffold** (below). This is the single
   biggest change I recommend to the plan.

---

## 3. Biggest recommended change — build the *curated scaffold* first

The brief assumes the beta = ad importer + AI normalisation + AI level/percentile
estimation + relationships. That is a multi-month build with real cost, CC-BY-SA
share-alike exposure, GDPR questions (ads contain contact persons), and AI spend —
**before we know the UX/methodology is even useful.**

**Recommendation — two stages:**

- **Beta v0 (this scope): curated, deterministic, cheap, legally clean.**
  - A **hand-built, owner-reviewed** mapping for **2 occupation families** (HR + Software/ICT):
    canonical titles → estimated level/track → **indicative, wide, overlapping percentile
    band** → salary band read off the *real* SCB curve via the new interpolation utility.
  - Stored in Supabase; runtime reads approved rows. **No AI at runtime, no ad import yet.**
  - Full UI: SCB curve + career-level overlays, typical titles, a simple 3-branch career
    map (advance / specialist / leadership), role compare, all disclaimers + confidence.
  - Behind the existing beta flag, Sweden-only.
  - This validates the entire concept, wording, and chart UX with zero external-data risk.

- **Beta v1 (fast-follow, after v0 is validated + JobTech cleared in the register):**
  - JobTech importer (aggregate evidence only) → offline batch AI (Claude) proposes
    canonical-title mappings, seniority signals, skills, and *draft* level/percentile
    estimates → **admin review queue** → approved rows replace/augment the curated seed.
  - AI is a *calibration aid feeding human review*, never a runtime call, never auto-published.

Everything in the brief's data model, pipeline, and admin design is still built — but v0
proves the surface first and de-risks the expensive parts.

---

## 4. Methodology

### 4.1 Salary-curve interpolation (mandatory, testable, reusable)
- Fit a **monotone cubic (PCHIP) interpolation on log-salary** through the 5 official
  points (P10, P25, P50, P75, P90). Log-space keeps it realistic for right-skewed pay.
- **Preserve the 5 published points exactly**; guarantee monotonicity; no oscillation.
- **No extrapolation below P10 / above P90** without an explicit "beyond published range"
  warning (tails are where SCB is least informative).
- Every value is tagged **published | interpolated | model-estimated**. The UI shows
  published points as solid markers and interpolation as a lighter line.
- Lives in a shared `core/` utility with unit tests (monotonicity, exact-point recovery,
  boundary behaviour) so other countries can reuse it later.

### 4.2 Level → percentile (Approach D, conservative)
Rule-based ordering from ad/curated evidence, mapped to the curve with **wide, overlapping
bands** and low stated confidence:
- Signals (per canonical title): seniority words in title, requested years of experience,
  people-management (yes/no), budget responsibility, strategic vs operational language,
  education/certification, skill rarity, and which SSYK it sits in.
- These produce a **relative seniority score → an indicative percentile band** (lower /
  central / upper) — *not* a point. Bands **overlap by design** (a top Professional out-earns
  a new Senior). We never publish "level = Pxx" as fact.
- Central salary from the interpolation at the central percentile; band edges from the
  band's percentile edges. All flagged Qvistin-estimated.

### 4.3 Confidence (published label)
Composite of: supporting sample size, title-mapping consistency, seniority-signal
consistency, SSYK-mapping strength, official-data width/suppression, and human-review
status → public label **Strong / Moderate / Limited / Experimental**. Below a threshold,
a level is not shown (or only in an explicitly-enabled experimental view).

---

## 5. Product design & placement

- A **"Career Paths — Beta"** entry on the **Swedish occupation page**, as a Sweden-only
  `extra_tab` behind the beta flag. It is *connected to the existing percentile chart*,
  not a separate page.
- **§9.1 Curve with career overlays** — the real SCB curve + estimated level bands
  (overlapping, hover/select, published-vs-interpolated distinguished, accessible list
  fallback). Never alters the official data.
- **§9.2 Typical titles**, **§9.3 development paths** (advance / specialist / leadership /
  lateral), **§9.5 role compare** — all reading approved rows.
- **§10 Career map** — a *simple fixed layout* (centre = selected role; vertical =
  same-SSYK progression; branches = specialist / leadership / lateral), not a free graph.
  Nodes badge: same-vs-different SSYK, official-vs-Qvistin, evidence strength.

## 6. Architecture

- **Runtime: fully deterministic.** The tab reads approved Supabase rows + the SCB curve;
  computes bands via the interpolation utility. No AI, no ad fetch at request time.
- **Offline pipeline (v1): batch/admin-triggered**, with prompt/model/data versioning,
  idempotency, audit logs, retry, min-sample thresholds, and an **admin review queue**
  before anything publishes.
- **Supabase tables** (refined from the brief; admin-write, runtime read-approved-only):
  `cp_canonical_title`, `cp_raw_title_map`, `cp_title_evidence`, `cp_level_estimate`
  (with per-value source: official/interpolated/ai/rule/human), `cp_relationship`,
  `cp_family` (config: level count + labels + tracks per family), and (v1)
  `cp_source_ad_agg` (**aggregates only** — counts/frequencies, never full ad text or
  personal data). Feature flag + published flags on families.

## 7. JobTech / Platsbanken (verified, primary sources)

- **APIs:** JobSearch (current/recent ads), **Historical job ads** (bulk/analytics),
  **Taxonomy** (occupation concepts ↔ **SSYK-2012** mapping + skills), JobAd Links. Some
  need a free API key (apirequest.jobtechdev.se).
- **Licence: CC-BY-SA** on the ad-data content (Taxonomy *software* is EPL-2.0). Two hard
  consequences: (1) **attribution to Arbetsförmedlingen/JobTech is mandatory**; (2)
  **share-alike** attaches to *derivative works of the content* — so we **store only
  aggregate facts** (counts, skill frequencies — facts aren't copyrightable) and **never
  redistribute ad text**, which keeps us clear of the share-alike obligation and of GDPR
  (ads name contact persons). This is exactly why v0 avoids ad text entirely.
- **Compliance:** register JobTech as a Dataset in our compliance register with
  `commercial` + `redistribute` flagged for owner review (share-alike is the sharp edge),
  attribution confirmed, retention = aggregates only. It then shows on the public
  methodology page automatically.
- **SSYK-2012 codes** for the two families **must be verified** against SCB's official
  SSYK-2012 index during build (don't hardcode from this brief) — e.g. software developers,
  system analysts/architects, testers, ICT security, sysadmins, ICT managers L1/L2; HR
  specialists, payroll/personnel clerks, M&O analysts, HR managers L1/L2.

## 8. Performance overlay (Phase 5/11)

Build the **data model + admin config + feature flag + a disabled internal preview only**.
**Do not publish** the 5-point overlay in the beta — there is no evidence linking a salary
position to measured individual performance, and doing so risks exactly the misuse the
brief warns against. Document the evidence bar for later public release (individual-level,
consented compensation data we do not have and should not infer).

## 9. Main risks

- **False precision / authority** — mitigated by wide overlapping bands, confidence
  labels, published-vs-estimated tagging, and blunt wording.
- **CC-BY-SA share-alike + GDPR** — mitigated by aggregates-only, attribution, no ad text.
- **AI cost/drift** — mitigated by offline batch + versioning + human review; none at runtime.
- **Scope creep** — mitigated by v0 (2 families, curated) before v1 (pipeline).
- **Destabilising Sweden's live page** — mitigated by extra_tab isolation + beta gate.

## 10. Postpone / change from the concept

- Postpone: live ad import + runtime/near-real-time AI, mixture models, transition
  probabilities, public performance overlay, all-occupation coverage.
- Change: fewer configurable levels (not forced 7); IC vs management as parallel tracks;
  ad-salary calibration dropped for Sweden; **curated scaffold before the AI pipeline**.

## 11. Proposed build sequence (after sign-off)

1. Interpolation utility + tests (reusable, no feature coupling).
2. Supabase `cp_*` schema + feature flag + a curated seed for HR + Software/ICT (owner-reviewed).
3. Sweden `extra_tab` "Career Paths — Beta": curve overlays, titles, simple career map,
   compare, disclaimers, confidence — reading approved rows.
4. Admin: review/edit/publish canonical titles, level bands, relationships (audit-logged).
5. Register JobTech in the compliance register.
6. (v1) JobTech aggregate importer → offline batch AI → admin review queue.
7. Performance overlay data model + disabled preview.
8. Tests per the brief's Phase 15; docs (setup/refresh/calibration/rollback).

---

## 12. Decisions needed before I build

1. **v0 curated-scaffold first (recommended) vs. build the ad+AI pipeline immediately?**
2. **AI provider/budget** for v1 — Anthropic Claude, offline batch, owner-set spend cap?
3. **Commercial/CC-BY-SA posture** — accept aggregates-only + attribution now, and gate
   any ad-text storage out entirely? (Recommended.)
4. **Performance overlay** — internal-preview-only in the beta (recommended), or attempt a
   labelled experimental public view?
5. **Family scope for v0** — HR + Software/ICT (recommended), or one first?
6. **Percentile-band width policy** — how conservative (e.g. central ±1 quartile minimum)?

*This is a proposal for review. On sign-off I'll start with the interpolation utility +
tests and the curated scaffold, in small reviewable commits.*
