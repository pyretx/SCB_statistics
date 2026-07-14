# Career Paths (Sweden beta) — runbook

Operational guide for the Career Paths v0 beta. Design rationale + methodology live in
[career-paths-assessment.md](career-paths-assessment.md); this is setup / calibration /
rollback.

**What v0 is:** a curated, deterministic interpretation layer on the official SCB
statistics for two occupation families (HR, Software & ICT). No AI and no job-ad import
at runtime; salaries are computed live from the SCB curve. Beta-gated + Sweden-only.

---

## 1. Architecture

| Piece | File / table |
|---|---|
| Curve engine (monotone, preserves published points) | `core/interp.py` (+ `tests/test_interp.py`) |
| Data layer (public reads, admin writes, audit log) | `careerpaths.py` |
| Register tables | Supabase `cp_family`, `cp_title`, `cp_relationship` (published-only views `v_cp_title_public` / `v_cp_rel_public`) |
| Performance overlay (internal) | Supabase `cp_perf_band`, `cp_perf_config` |
| Public UI (beta tab) | `countries/se2/career.py` (registered in `countries/se2/config.py` `extra_tabs`; beta-gated in `core/tabs/__init__.py` `_BETA_TABS`) |
| Admin calibration | `admin_ui.py` `career_section` (+ `content/admin.toml` `[career]`) |
| Job-ad source (v1, registered only) | compliance register `jobtech_*` |

## 2. Setup (run once, in the Supabase SQL editor)

1. `deploy/sql/2026-07-14_career_paths.sql` — register + curated seed.
2. `deploy/sql/2026-07-14_career_perf_overlay.sql` — performance overlay (internal).

JobTech is registered in the compliance register via a **direct-write script** (per the
register-writes convention), not a SQL file. No app secrets beyond the existing Supabase
keys are needed; the runtime uses no AI and no JobTech calls.

## 3. Methodology (summary)

- **Interpolation:** monotone cubic (Fritsch–Carlson) on log-salary through the published
  points (P10/P25/P50/P75/P90). Published points exact; monotone; **no invented tails**
  (clamped + tagged `extrapolated`). Values tagged published / interpolated / extrapolated.
- **Level → percentile:** each canonical title carries an **indicative band**
  (`lo_pct/mid_pct/hi_pct`) interpreted **within its own SSYK's SCB distribution**. Bands
  overlap by design. Salaries are computed live at those percentiles — never stored.
- **Confidence:** `strong / moderate / limited / experimental`, shown publicly.
- Everything is labelled a Qvistin estimate; official SCB data is never restated or altered.

## 4. Calibration workflow (Admin → Career Paths)

1. Search / expand a family. Edit the **Titles** grid: track, level label/order, the
   `lo/mid/hi` percentile band (DB enforces `0 ≤ lo ≤ mid ≤ hi ≤ 100`), confidence,
   review status, published. Editing a band re-positions the role on the public tab.
2. Edit the **Relationships** grid: type, confidence, review, published, explanation.
3. Set **review status → approved** and **published** on rows you've verified; toggle the
   **family published** switch to show/hide the whole family.
4. Every save is audit-logged (`compliance_review_log`, subject `cp_title` / `cp_relationship`).
   Public reads are cached ~1h; saves clear the cache.

## 5. Feature flag / gating

- The tab id `career` is in `core/tabs._BETA_TABS`, so only **beta users + admins** see it;
  it is registered only on Sweden (`countries/se2/config.py`).
- A family also needs `cp_family.published = true` to appear.
- **Nothing shows on the public Sweden page** for normal users until you both (a) publish
  the family and (b) promote the beta tab out of `_BETA_TABS` (a deliberate later step).

## 6. Performance overlay (internal only)

- `cp_perf_config.enabled_public` **stays false**. While false, the 5-point overlay is an
  **admin-only preview** in the beta tab and an editor in Admin → Career Paths.
- **Do not enable publicly.** It is illustrative positioning within a level range, not a
  measure of individual performance. Public release requires individual-level, consented
  compensation evidence we do not hold.

## 7. Adding a family / title (curated)

Per the register-writes convention, add rows via a direct Supabase service-key script (or
extend the seed SQL) — provider of the numbers stays SCB. Keep bands wide + overlapping,
set `confidence` honestly, `review_status = draft` until reviewed. Verify SSYK-2012 codes
against SCB before use. Re-run `tests/test_career_seed.py` after seeding.

## 8. Rollback / disable

- **Hide one family:** toggle its **family published** off (instant).
- **Hide one role/path:** untick **published** on the row.
- **Disable the whole tab:** remove `"career"` from `countries/se2` `extra_tabs` (or from
  `_BETA_TABS` semantics) and redeploy — the register data is untouched.
- **Remove entirely:** drop the `cp_*` tables (SQL) — the rest of the app is unaffected
  (the tab + admin section are guarded and simply go empty).

## 9. Tests

- `python tests/test_interp.py` — 9 checks (exactness, monotonicity, no tails, inverse,
  degenerate inputs, HR + ICT shapes).
- `python tests/test_career_seed.py` — seed integrity (band order, referential integrity,
  `same_ssyk` correctness, valid tracks/confidence/SSYK, published coverage). Skips if the
  register is unreachable.

## 10. v1 (fast-follow — not built)

JobTech aggregate importer (aggregates only, attribution, no ad text — CC-BY-SA + GDPR) →
offline batch Claude (title normalisation + draft estimates) → **admin review queue** →
approved rows augment the curated seed. The compliance entry + share-alike/GDPR gates are
already recorded; ad-text storage needs explicit owner sign-off + a legal check first.
