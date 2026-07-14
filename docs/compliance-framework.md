# Salary Explorer — Data-source, Licensing, Attribution & Methodology Framework

Status: **proposal** (2026-07). This document defines how every data source used by
Salary Explorer is reviewed, recorded, attributed, and released — and how original
source values are kept visibly separate from Salary Explorer calculations.

It is a *design proposal*, not yet implemented. No code or repository behaviour is
changed by this document.

---

## 0. Goal

For **every** source we use — APIs, downloadable files, official tables, reports,
PDFs and microdata — we must be able to demonstrate:

1. Whether we are permitted to **access and use** the data.
2. Whether **commercial use** is permitted.
3. Whether we may **store, cache, transform and redistribute** it.
4. Whether **derived calculations and visualisations** are permitted.
5. What **attribution, disclaimers, links or wording** are required.
6. Whether there are **API-key, rate-limit, automated-download, microdata,
   confidentiality or personal-data** restrictions.
7. What **evidence** supports the assessment, and **when it was last reviewed**.

We never grant approval on assumption. Every permission carries an explicit
**clearance state** (§4) with evidence and dates.

---

## 1. Locked decisions (owner, 2026-07)

1. **Register lives in Supabase** — a controlled set of admin-writable tables in the
   shared Salary Explorer project, with a public read-only view feeding the public
   pages. (Not version-controlled files.)
2. **Owner sign-off is the approval ceiling.** No external legal review is engaged at
   this stage; where an assessment would otherwise say "legal review required", it is
   escalated to the **owner** for an accept/hold decision and that decision is recorded.
3. **Commercial posture: pre-commercialization.** Salary Explorer is in **beta**,
   **free**, and **not yet commercialized**. It is commercial in spirit (a Qvistin
   product) but nothing is being sold; the aim is to test whether a market exists.
   Therefore:
   - `commercial_use` is still recorded per dataset.
   - Current operation relies on each source's **free / research / general-reuse**
     terms; the owner accepts current risk under those terms.
   - **Before any commercialization**, the commercial-use gate is re-run for every
     source (see §9 and the commercialization checklist in §12).
4. **No downgrades.** All currently published countries stay published. The release
   gate (§6) is **forward-looking**: it governs *new* sources and *re-reviews*.
   Existing countries are **grandfathered** — clearance is still recorded for them,
   but a non-`Confirmed` result does not pull a live country. Grandfathering is an
   explicit owner decision, logged per country.
5. **Licence display: plain-language summary + link.** Show a short, human summary
   and a link to the official terms. Use **verbatim** licence/attribution text **only
   where the licence requires it**. Keep it unobtrusive — it must not distract from
   the data.
6. **Currency and CPI conversion sources are datasets.** Exchange-rate and
   inflation-index providers (e.g. ECB reference rates, national CPI series) are
   registered as their own datasets with their own attribution.
7. **Public methodology shows per-transformation detail.** The public page exposes,
   per country, each transformation Salary Explorer applies and how.
8. **Review cadence: 12 months, admin-owned.** Every clearance carries a
   `next_review_date` (default +12 months). Overdue reviews surface as a **reminder
   tile in the admin Overview**.

---

## 2. Principles

- **Terms attach to the dataset, not the provider.** One provider may publish several
  datasets under different terms; one country may use several sources. Provider-level
  records hold only defaults and contacts.
- **Access clearance ≠ user access tier.** The app's existing `access` field
  (`public`/`registered`/`restricted`/`internal`) gates *which users* see a page. It
  says nothing about whether a source is *legally cleared*. Clearance and release are
  tracked separately (`release_status`).
- **Preserve-and-label, don't claim "unchanged".** We do **not** say "Salary Explorer
  does not change the underlying data." Instead:

  > **Salary Explorer preserves original source values and identifies them separately
  > from calculations, conversions, classifications, projections and other derived
  > outputs created by Salary Explorer.**

- **Evidence or it didn't happen.** Every permission verdict links to the specific
  terms/page that supports it, with a reviewer and date.

---

## 3. Information architecture

A single controlled register with a layered entity model and a generated public
projection:

```
Provider ──1:N──> Dataset ──1:N──> AccessMethod
                     │                  │
                     └────────┬─────────┘
                              ▼
                   CountryImplementation ──1:N──> TransformationApplied
                              │
                              ├── ClearanceAssessment  (per permission dimension)
                              └── ReviewLog            (append-only)
```

- **Provider** — the organisation; defaults + contacts only.
- **Dataset** — a specific table / report / microdata product. **Licence and
  permissions live here.**
- **AccessMethod** — *how we ingest a dataset* (API / Excel / CSV / PDF / microdata).
  API-key, rate-limit, automated-download and confidentiality constraints live here.
- **CountryImplementation** — one country's use of one dataset via one access method;
  holds what we display, the transformations applied, and the release gate.
- **ClearanceAssessment** — the reviewed verdict, recorded **per permission
  dimension**, each with a five-state status + evidence + dates.
- **TransformationApplied** — links a country to entries in a shared transformation
  catalogue (§7).
- **ReviewLog** — append-only history (who/when/what).

**Why layered:** `countries/eurostat_ses.py` is a single dataset (`earn_ses_21`)
powering ~22 countries. The licence is reviewed **once** on the dataset and
*referenced* by 22 country implementations — each of which still carries its own
reference period, transformations, and release decision.

**Relationship to existing app metadata:** the register does **not** absorb the
operational freshness data (`built_at`, file size, update-available) that already
lives in `admin_ui.py` and the `*_earnings.json.gz` snapshots. The register
references datasets by a stable `dataset_id`; ops data stays where it is.

---

## 4. Clearance model

**Five states** (recorded **per permission dimension**, so a source can be *Confirmed*
to access but *Legal/owner review required* to redistribute):

| State | Meaning |
|---|---|
| `confirmed` | Explicit licence or terms permit it. |
| `likely_verify` | Likely permitted, still needs verification. |
| `provider_confirm` | Requires provider confirmation (email/ticket). |
| `owner_review` | Escalated to owner for accept/hold (replaces "legal review" per §1.2). |
| `restricted` | Restricted or not permitted. |

**Permission dimensions** (each dataset/access/impl carries an assessment per relevant
dimension):

`access` · `commercial` · `redistribute` · `derive` · `store_cache` · `attribution`
· (access-method only) `api_terms` · `microdata_confidentiality`

**Overall rollup** for a country = the **worst** dimension state.

---

## 5. Data model — Supabase schema

Admin-writable tables (RLS: write restricted to admin/master; see §5.1). Names are
proposals; adjust to house conventions on implementation.

### `compliance_provider`
| Column | Type | Notes |
|---|---|---|
| `provider_id` | text PK | slug, e.g. `eurostat`, `ssb`, `estat` |
| `name` | text | |
| `country_or_org` | text | |
| `homepage_url` | text | |
| `default_licence_ref` | text | default only — overridable per dataset |
| `contact_email` | text | for provider-confirmation actions |
| `reuse_policy_url` | text | |
| `notes` | text | |

### `compliance_dataset`  *(terms live here)*
| Column | Type | Notes |
|---|---|---|
| `dataset_id` | text PK | e.g. `eurostat_earn_ses_21`, `ssb_11418`, `estat_0003426315`, `ecb_fx`, `cpi_xx` |
| `provider_id` | text FK | |
| `title` | text | |
| `official_table_id` | text | |
| `dataset_url` | text | |
| `data_type` | text | `official_table` \| `report_pdf` \| `microdata` \| `derived_bundle` \| `fx_rates` \| `cpi_index` |
| `licence_name` | text | e.g. "CC BY 4.0", "Eurostat reuse policy" |
| `licence_url` | text | |
| `licence_version` | text | |
| `licence_summary_plain` | text | the plain-language summary shown publicly (§1.5) |
| `licence_verbatim_required` | bool | true → render exact notice |
| `required_attribution_text` | text | verbatim string the UI must render |
| `required_disclaimer_text` | text | verbatim, if mandated |
| `required_link_url` | text | compulsory back-link, if any |
| `personal_data` | text | `none` \| `pseudonymised` \| … (aggregates = `none`, still recorded) |
| `reference_period_note` | text | |
| `revision_policy` | text | |

### `compliance_access_method`  *(channel constraints)*
| Column | Type | Notes |
|---|---|---|
| `access_id` | text PK | e.g. `estat_0003426315_api` |
| `dataset_id` | text FK | |
| `method` | text | `api` \| `excel` \| `csv` \| `pdf` \| `microdata_download` |
| `endpoint_or_file` | text | |
| `requires_api_key` | bool | |
| `key_terms_url` | text | |
| `rate_limit` | text | |
| `automated_download_allowed` | text | five-state or note |
| `microdata_confidentiality_terms` | text | small-cell suppression, no re-identification |
| `caching_allowed_note` | text | |

### `compliance_country_impl`  *(join + release gate)*
| Column | Type | Notes |
|---|---|---|
| `impl_id` | text PK | |
| `country_slug` | text | FK to the app registry slug |
| `dataset_id` | text FK | |
| `access_id` | text FK | |
| `displayed_original_values` | text | what we show unchanged |
| `reference_period` | text | mirrors snapshot `year`/`years` |
| `clearance_overall` | text | five-state rollup |
| `release_status` | text | `blocked` \| `internal_only` \| `beta_ok` \| `public_ok` |
| `grandfathered` | bool | true = pre-existing, kept live by owner decision (§1.4) |
| `public_publishable` | bool | the public view reads this |

### `compliance_assessment`  *(one row per dimension)*
| Column | Type | Notes |
|---|---|---|
| `assessment_id` | uuid PK | |
| `subject_type` | text | `dataset` \| `access` \| `impl` |
| `subject_id` | text | |
| `dimension` | text | access \| commercial \| redistribute \| derive \| store_cache \| attribution \| api_terms \| microdata_confidentiality |
| `status` | text | the five states (§4) |
| `evidence_url` | text | |
| `evidence_note` | text | |
| `reviewed_by` | text | |
| `reviewed_date` | date | |
| `next_review_date` | date | default +12 months |
| `outstanding_action` | text | |

### `compliance_transformation`  *(country → catalogue)*
| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `impl_id` | text FK | |
| `transform_type` | text | `currency_conversion` \| `period_conversion` \| `inflation_adjustment` \| `aggregation` \| `ranking` \| `projection` \| `reclassification` \| `cross_country_standardisation` |
| `origin` | text | `source_provided` vs `salary_explorer` — drives the badge (§7) |
| `method_note` | text | e.g. "×160.33 monthly hours" |
| `inputs` | text | e.g. "ECB reference rate, {date}" |

### `compliance_review_log`  *(append-only)*
`log_id uuid PK, subject_type, subject_id, action, actor, timestamp, before_after jsonb`

### 5.1 RLS & the public view
- **Write:** admin/master only (mirror the existing auth-role pattern).
- **Public read:** a single view `v_compliance_public` exposing **only** publishable
  fields, filtered to `public_publishable = true` (see §6). The public pages read this
  view; they never touch the raw tables.

---

## 6. Release gate

The public projection filters on:

```
public_publishable = true
AND (clearance_overall = 'confirmed' OR grandfathered = true)
```

Rules:
- **New sources** must reach `clearance_overall = confirmed` on every relevant
  dimension **and** carry attribution text before `release_status = public_ok`.
- Any dimension = `restricted` → `release_status = blocked`, forced `internal_only`
  (this applies even to grandfathered countries: a hard "not permitted" is never
  published).
- **Grandfathered** existing countries publish regardless of a non-`confirmed`
  (but non-`restricted`) rollup, per §1.4 — the owner decision is logged.
- An **overdue** `next_review_date` raises an admin reminder (§10); it does not
  auto-unpublish, but flags the country for re-confirmation.

---

## 7. Original vs. derived data (public + in-app wording)

**Governing statement** (from §2) is shown on the methodology page and in the
country-page "Sources & methods" expander.

**Two badges beside every figure/chart/table:**
- 🟦 **Official** — value as published by the source provider.
- 🟨 **Salary Explorer calculation** — derived; caption states the method.

Each `TransformationApplied.origin` decides the badge: `source_provided` conversions
(e.g. Eurostat's own EUR figures) read **Official**; `salary_explorer` conversions
(e.g. Denmark hourly→monthly, Mexico weighted mean from microdata) read **SE
calculation**.

**Per-transformation captions** (placed beside the relevant element; also listed in
full on the public methodology page per §1.7):

| Transformation | Beside-element caption |
|---|---|
| Currency conversion | "Converted to {CUR} by Salary Explorer using {rate source}, {date}. Source publishes in {orig}." |
| Monthly/annual | "Scaled from {published period} to {shown period} by Salary Explorer ({factor})." |
| Inflation adjustment | "Adjusted to {base-year} prices by Salary Explorer using {CPI source}." |
| Aggregation | "Headcount-weighted combination of {n} occupations — Salary Explorer calculation." |
| Ranking | "Ordering by pay is a Salary Explorer presentation, not a source ranking." |
| Projection | "Forward estimate produced by Salary Explorer — not official data." |
| Reclassification | "Mapped to {target classification} by Salary Explorer from {source classification}." |
| Cross-country standardisation | "Cross-country figures are aligned by Salary Explorer and may not be directly comparable — see methodology." |

Exports/screenshots must carry attribution + the relevant badges baked in, so derived
values never travel out of context.

---

## 8. Public pages & navigation

Add a small **About ▾** dropdown to the app chrome (and mirror on `qvist.in`). Three
pages, all generated from `v_compliance_public` — **no manual duplication**:

1. **Data Sources & Methodology** — country search/select → per country: official
   provider · exact dataset/table · official link · reference period & last update ·
   plain-language licence summary + link · required attribution · original values
   displayed · **each** SE transformation and how (per §1.7) · limitations &
   comparability warnings · an Official-vs-SE-derived legend.
2. **About Salary Explorer** — purpose · use of official statistics · country coverage
   · general methodology · limitations · contact · "a Qvistin product" · link to
   `qvist.in`.
3. **Disclaimers & Terms** — independence from providers · no implied endorsement ·
   official statistics may be revised · derived calculations are Salary Explorer's ·
   cross-country figures may not be directly comparable · no individual salary,
   employment, legal or financial advice.

Plus an in-page **"Sources & methods" expander** on each country page — a compact
projection of the same record, so attribution/methodology sit next to the data too.

---

## 9. Commercial-use handling (pre-commercialization)

Because Salary Explorer is free and not yet commercialized (§1.3):
- `commercial` is assessed and recorded now, but a non-`confirmed` commercial verdict
  **does not** block or downgrade current free/beta use.
- The register makes future commercialization a **checklist, not a rediscovery**: at
  the point of monetising, filter the register for any dataset whose `commercial`
  dimension is not `confirmed` and resolve each (obtain a commercial licence, replace
  the source, or drop the country) before selling.

---

## 10. Review & approval workflow

**State machine** for a `CountryImplementation`:
`Draft → Assessed (dimensions filled) → Reviewed → [owner accept/hold if any dimension
= owner_review] → Approved-for-release → Published`; side states
`Provider-confirmation-pending`, `Restricted/Blocked`.

**Roles:** *Author* fills the register + evidence → *Reviewer* checks evidence (no
self-approval) → *Owner sign-off* on `owner_review` items and on any commercial
uncertainty.

**Cadence:** every assessment carries `next_review_date` (default +12 months). The
**admin Overview** shows a reminder tile: count of overdue / due-soon reviews, linking
into the register. The admin owns re-confirmation.

---

## 11. Risks & edge cases

- **Commercial use is the future sharp edge** — a `CC BY-NC` / non-commercial source is
  fine now but blocks commercialization; flag early.
- **Eurostat one-dataset / ~22 countries** — licence reviewed once, but each country
  keeps its own reference-period + comparability note.
- **Microdata (Mexico ENOE, France PCS)** — confidentiality / no-re-identification /
  small-cell suppression apply to the *derivation*, not just access; highest scrutiny.
- **Redistribution vs. caching** — live-API countries cache to disk (usually allowed);
  *serving* those figures publicly is redistribution — assess separately.
- **Derived-data IP** — ranking/projection/standardisation are ours but built on their
  numbers; attribution still required under most licences.
- **API-key ToS drift & rate limits** — e-Stat, Stats NZ, BLS keys carry terms that can
  change; record `key_terms_url` + review date.
- **Attribution stacking** — ODbL/CC-BY require specific notices; cross-country charts
  need combined attribution.
- **Revisions** — providers restate figures; disclaimer covers "may be revised".
- **Access-tier ≠ clearance** — never read `access="restricted"` (Beta) as "cleared".
- **Exports/translation** — exported charts carry derived values out of context (bake
  in attribution); occupation-label translations are themselves a reclassification.
- **Personal data** — aggregates only; record `personal_data = none` explicitly.

---

## 12. Phased implementation (no code in this document)

- **Phase 0 — Schema + pilot:** create the Supabase tables + `v_compliance_public`;
  fill **Eurostat SES** (unlocks ~22 countries) + Norway (live API) + Mexico
  (microdata) as contrasting pilots.
- **Phase 1 — Backfill:** populate every provider/dataset/access/impl from existing
  `build.py` / `admin.toml` / config metadata; run per-dimension clearance; attach
  evidence; mark existing countries `grandfathered = true`.
- **Phase 2 — Release gate:** wire `public_publishable` + `v_compliance_public`;
  enforce the gate for **new** sources only.
- **Phase 3 — Public pages:** build Data Sources & Methodology + About + Disclaimers
  from the view; add the About ▾ nav.
- **Phase 4 — Derived-data labelling:** add the Official / SE-calculation badges +
  per-transformation captions across tabs and exports.
- **Phase 5 — Cadence:** add the overdue-review reminder tile to the admin Overview.

**Commercialization checklist (when the time comes):** re-run §9 across the whole
register; resolve every non-`confirmed` `commercial` dimension before selling.

---

## 13. Appendix — worked example (Eurostat, illustrative)

```
provider:  eurostat  ("Eurostat", homepage, reuse_policy_url, contact)
dataset:   eurostat_earn_ses_21
           title "Structure of Earnings Survey (earn_ses_21)"
           licence_name "Eurostat reuse policy"
           licence_summary_plain "Free reuse incl. for commercial purposes, with
             attribution to Eurostat; Eurostat not liable."
           required_attribution_text "Source: Eurostat"
access:    eurostat_earn_ses_21_api  (method api, no key, caching allowed)
impls:     belgium, portugal, austria, … (~22)
           each: dataset_id=eurostat_earn_ses_21, own reference_period,
                 transformations=[currency_conversion origin=source_provided (EUR)],
                 grandfathered=true
assessment (dataset level):
           access=confirmed, commercial=confirmed, redistribute=confirmed,
           derive=confirmed, attribution=confirmed
           evidence_url=<Eurostat reuse policy>, reviewed_by=owner,
           reviewed_date=…, next_review_date=+12mo
```

---

*This is a proposal for review. Nothing in the application is changed by adopting this
document; implementation follows the phases in §12.*
