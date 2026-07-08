# SE2 / FR2 — legacy pages vs the framework rebuilds

*Written 2026-07-07 when `countries/se2` and `countries/fr2` were built; updated
2026-07-08 when the gaps were closed. Both are `access="internal"` (admin/master
only), `landing=False` (no home tile) — open them from the admin panel's
"Open a country" or at `/se2` and `/fr2`.*

The goal of Phase 5: rebuild **Sweden** (`scb_salaries.py`, ~2 800 lines) and
**France** (`france.py` + `france_data.py`) on the shared framework
(`core/` + `countries/<slug>/`), compare, and close the gaps before the v2
pages replace the legacy ones.

---

## What the framework gained (shared by ALL countries)

| Addition | Where | Who benefits |
|---|---|---|
| Generic **By age / By education / By region** tabs (one implementation, three ids, capability-gated) | `core/tabs/breakdown.py`, `charts.category_bar` | SE2 + FR2 today; any future country |
| **Swedish + French** framework translations | `core/i18n.py` (`UI["SV"]`, `UI["FR"]`) | SE2/FR2 language toggles; future reuse |
| Page-registration hardening: per-country guard + logged errors (a broken country can no longer silently unregister the ones after it) | `app.py` | everyone |
| Convention made explicit: **country module dir == slug** (`countries/se2` ↔ slug `se2`) | `core/registry.py` note | future countries |
| **`extra_tabs` hook** — country-specific tabs appended after the standard ones | `core/model.py`, `core/tabs/__init__.py` | SE2's work-permit check; any country extension |
| **`occupation_details` / `occupation_synonyms` provider hooks** — descriptions in the code browser, synonyms in the sidebar search | `core/provider.py`, `core/panels.py`, `core/sidebar.py` | SE2 (SSYK); any classification with metadata |
| **Aggregate-selection toggle** — collapse several picks into one headcount-weighted series, across all tabs | `core/agg.py`, `core/page.py`, tab wiring | every country with counts |
| **Split-by-sex toggle** in the breakdown tabs | `core/tabs/breakdown.py` | every `has_sex` country |
| **Population backdrop** in the distribution chart (`has_population_distribution`) | `core/tabs/distribution.py`, `charts.distribution_chart` | FR2; any source with an all-employee curve |
| **`trend_is_real`** — real-only trend sources render one constant-price view, mean-only measure, no CPI overlay | `core/model.py`, `core/tabs/trend.py` | FR2's long-run series (1996→ per group) |
| **Leaderboard gap fallback** — gap ranks on means when per-sex medians don't exist (with caption) | `core/tabs/leaderboard.py` | FR2; any mean-only-by-sex source |

Every country-specific addition (the non-standard extras) is listed on that
country's tile in **Admin panel → Data sources** (`content/admin.toml` →
`[data.<country>].extras`), so the catalogue of beyond-standard features is
always visible where the data connections are managed.

---

## SE2 — Sweden v2 vs legacy `scb_salaries.py`

**Ported at full parity** (same SCB tables, codes and merge logic — values match
the legacy page):

| Feature | Notes |
|---|---|
| Percentiles P10–P90 + mean + median | both table generations merged (4A 2014–22, 4AN 2023→); `2512` median 53 500 matches legacy |
| Sectors (8), sex, years 2014→latest | latest year read from `app_settings.json` — the legacy admin data-year check rolls BOTH pages forward |
| Trend: measure selector + nominal / growth-vs-inflation / real | CPI = same KPI2020M shadow index |
| Leaderboard: median / mean / gender gap / median growth, scoped to SSYK 2-digit | |
| By gender (+ women-as-%-of-men), Where-do-I-stand calculator | |
| **By age / By education / By region** | via the new shared breakdown tabs; education aggregates men+women (headcount-weighted) when the table lacks a "total" sex |
| Bilingual EN/SV, code browser, occupation drill-down, guide | labels shared with legacy (`occupations_cache.json`, `ssyk_descriptions.json`) |
| Headcount | pulled from the region table's national row (the percentile table has none) — same trick as legacy |

**Differences → resolution** (2026-07-08: #1–4 BUILT; their *mechanisms* were
promoted to the framework standard so any country can use them):

| # | Gap in SE2 | Resolution | Status |
|---|---|---|---|
| 1 | **Work-permit checker** (Migrationsverket rules, floors, banned lists) | STANDARD: `cfg.extra_tabs={"id": render_fn}` hook appends country-specific tabs. SE2: `countries/se2/workpermit.py` ports the full checker (eligibility / floor / market / docs, reads the same `wp_rules.json` the legacy editor writes) | ✅ built |
| 2 | **SSYK descriptions & synonyms** in browser + search | STANDARD: provider hooks `occupation_details(code)` + `occupation_synonyms()` consumed by the code browser and the sidebar search. SE2 serves them from `ssyk_descriptions.json` | ✅ built |
| 3 | **Aggregate-selection toggle** (collapse picks into one weighted series) | STANDARD: page-level toggle + `core/agg.py` (headcount-weighted; weighted percentiles are an approximation, same as legacy) — applied across overview / distribution / sex / breakdowns / trend | ✅ built |
| 4 | Breakdown tabs charted the selected sex only | STANDARD: "Split by sex" toggle in the breakdown tabs (when `has_sex` and the query is total) | ✅ built |
| 5 | Legacy admin extras (guide editor, work-permit rules editor, app settings, SSYK label overrides) live on the legacy page | Migrate into the common admin panel as part of retiring the legacy page | ⏳ retirement phase |
| 6 | Landing "live preview" carousel + `fetch_live_median` still call legacy code paths | Point them at shared helpers when legacy retires | ⏳ retirement phase |

---

## FR2 — France v2 vs legacy `france.py`

**Ported** (reusing `france_data.py` directly — the fetches and caches are
literally shared, so the two pages can never disagree):

| Feature | Notes |
|---|---|
| Mean + headcount per occupation (live Melodi, private/public, sex _T/F/M) | latest published year per sector (means can be a year newer than percentiles — flagged in caption + guide) |
| **P10–P90 + median percentiles** per occupation | from the bundled FD_SALAAN microdata estimates (2023, both sexes) — attached to sex="total" only, flagged in `notes`; censored upper tail stays blank (same as legacy; the planned simulation toggle addresses it) |
| Overview KPIs incl. women/men/F-M gap, comparison bar | |
| Salary distribution chart, Where-do-I-stand calculator | powered by the microdata percentiles |
| Leaderboard by mean (361 occupations, scoped to PCS group) | median metric ranks on the microdata P50 (total only) |
| Bilingual EN/FR, PCS drill-down (1 → 2 → 4 chars), code browser, guide | |

**Differences → resolution** (2026-07-08: #1–5 BUILT; #1/#2/#5's mechanisms
promoted to the framework standard):

| # | Gap in FR2 | Resolution | Status |
|---|---|---|---|
| 1 | **Long-run series (1996→)** in constant euros per broad PCS group | STANDARD: `Capabilities.trend_is_real` — the trend tab shows a single "Real (constant prices)" view, no CPI overlay, mean-only measure. FR2 maps each occupation to its broad group's series, labelled "… · group" (groups 1–2 have no salaried series) | ✅ built |
| 2 | **Population distribution backdrop** | STANDARD: `has_population_distribution` + the provider's `population_distribution()` draw a grey dashed all-employee centile curve behind the distribution chart | ✅ built |
| 3 | **By age** (Melodi age bands Y_LT30…Y_GE60) | Shared `age` breakdown tab enabled; mean + headcount per band | ✅ built |
| 4 | **Régional view** (BTS dataset, PCS-group level) | Shared `region` tab enabled at GROUP granularity — the series is named after the group ("Employees · group"), never the occupation, so the chart can't imply unpublished precision | ✅ built |
| 5 | Leaderboard **gender-gap metric was empty** (no per-sex medians) | STANDARD: the gap metric falls back to means when per-sex medians don't exist, with an explanatory caption | ✅ built |
| 6 | Working-time filter (FT / all) in the legacy series view | Not ported — the long series defaults to all working times; revisit if requested | ⏳ open |

---

## Verification

**2026-07-07 (initial build), all against live APIs:**
- **Providers**: SE2 — 431 occupations, tree 10/40/149/431; totals (P10–P90 + mean +
  median + count), age (6 bands), education (7 levels, weighted total), region
  (8 régions), trend (2015/2020/2024 medians), CPI (10 yrs), leaderboard (431
  rows, top = Financial & insurance managers 126 500). FR2 — 429 occupations,
  tree 6/29/429; means + headcount (2024), women/men means, percentiles incl.
  honest censored-tail blanks, leaderboard (361 rows, top = Large-enterprise
  managers €16 853).
- **Tabs**: every SE2 tab (9) and FR2 tab (5) rendered via AppTest harness with
  real fetches — one chart each, zero exceptions.
- **Live**: `/se2` and `/fr2` route and render; `/norway`, `/us`, landing and
  admin unaffected.

**2026-07-08 (gap build), all against live APIs:**
- FR2 trend: 58 rows, two group series, 1996–2024 constant euros. Population
  curve: P10 1 492 → P99 10 261 (2024). Age bands with honest suppression
  (50–59/60+ NaN for the probed occupation). Régions: 36 rows at group level.
  Gap-fallback inputs confirmed (per-sex means only).
- SE2 work-permit tab, aggregate toggle, sex-split, synonyms search and
  browser descriptions verified via the AppTest harness (see commit).

## Remaining path to replacing the legacy pages

1. Admins beta-test SE2/FR2 (now). Widen later by flipping `access` to
   `restricted` + granting users — a config change.
2. Retirement phase: migrate the legacy admin editors (guide, work-permit
   rules, app settings, SSYK overrides) into the common admin panel; point the
   landing "live preview" + `fetch_live_median` at shared helpers.
3. Point the landing tiles at the v2 pages, keep legacy reachable for one
   release, then delete `scb_salaries.py` / `france.py`.
