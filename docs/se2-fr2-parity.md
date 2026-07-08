# SE2 / FR2 — legacy pages vs the framework rebuilds

*Written 2026-07-07, when `countries/se2` and `countries/fr2` were built. Both are
`access="internal"` (admin/master only), `landing=False` (no home tile) — open
them from the admin panel's "Open a country" or at `/se2` and `/fr2`.*

The goal of Phase 5: rebuild **Sweden** (`scb_salaries.py`, ~2 800 lines) and
**France** (`france.py` + `france_data.py`) on the shared framework
(`core/` + `countries/<slug>/`), compare, and decide how to close the gaps
before the v2 pages replace the legacy ones.

---

## What the framework gained in this round (shared by ALL countries)

| Addition | Where | Who benefits |
|---|---|---|
| Generic **By age / By education / By region** tabs (one implementation, three ids, capability-gated) | `core/tabs/breakdown.py`, `charts.category_bar` | SE2 today; FR2 age is an easy follow-up; any future country |
| **Swedish + French** framework translations | `core/i18n.py` (`UI["SV"]`, `UI["FR"]`) | SE2/FR2 language toggles; future reuse |
| Page-registration hardening: per-country guard + logged errors (a broken country can no longer silently unregister the ones after it) | `app.py` | everyone |
| Convention made explicit: **country module dir == slug** (`countries/se2` ↔ slug `se2`) | `core/registry.py` note | future countries |

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

**Differences → proposed mitigations** (ordered by importance):

| # | Gap in SE2 | Mitigation proposal | Effort |
|---|---|---|---|
| 1 | **Work-permit checker** (Migrationsverket rules, floors, banned lists, admin-editable) is Sweden-specific and has no framework slot | Add a config hook `extra_tabs={"id": render_fn}` so a country can append custom tabs after the standard ones; port the checker (rules stay in `wp_rules.json`, editable from the admin panel) | Medium — the hook is ~10 lines; the port is the work |
| 2 | **SSYK descriptions & synonyms**: legacy browser shows per-code descriptions, and its occupation search also matches ~60 synonyms per code; v2 browser shows names only and searches names/codes | Provider hook `occupation_details(code)` (+ synonym index) consumed by `core/panels.py`; Sweden serves it from `ssyk_descriptions.json` | Medium |
| 3 | **Aggregate-selection toggle**: legacy can collapse several picked occupations into ONE headcount-weighted series (`collapse_df`) | Framework toggle "Aggregate selection" that weight-averages the stats frame (weights from `count`) before the tabs render | Medium |
| 4 | Breakdown tabs chart the **selected sex only**; legacy by-age drew men + women side by side | Optional sex-split traces in `breakdown.py` when `sex == "total"` and the country `has_sex` | Small |
| 5 | Legacy admin extras (guide editor, work-permit rules editor, app settings, SSYK label overrides) live on the legacy page | Migrate into the common admin panel (a "Country settings" section) as part of retiring the legacy page | Medium |
| 6 | Landing "live preview" carousel + `fetch_live_median` still call legacy code paths | Point them at `sweden_codes.py`-style shared helpers when legacy retires | Small |

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

**Differences → proposed mitigations:**

| # | Gap in FR2 | Mitigation proposal | Effort |
|---|---|---|---|
| 1 | **Long-run series (1951→)**: legacy shows constant-euro trends per broad PCS group; the framework trend tab assumes nominal values + CPI | Framework: support `value_real`-only trend sources (a `trend_is_real` capability that relabels the views); FR2 maps each occupation to its broad group's series, labelled "group trend" | Medium |
| 2 | **Population distribution backdrop**: legacy draws the all-employee centile curve with the occupation estimate overlaid | The provider base already has `population_distribution()` — add an optional backdrop to `core/tabs/distribution.py` when `has_population_distribution` | Small–medium |
| 3 | **By age** exists in the Melodi detail data (age bands fetched already) but v2 doesn't expose it | Enable the shared `age` breakdown tab for FR2 — provider maps the AGE dimension | Small (quick win) |
| 4 | **Régional view** (BTS dataset: mean by région × PCS group) | Enable the shared `region` tab at PCS-GROUP granularity, clearly labelled (occupation-level régional data does not exist) | Small–medium |
| 5 | Leaderboard **gender-gap metric is empty** (medians exist only for both-sexes microdata; the gap ranks on median) | Framework: let the gap metric fall back to mean when a country has per-sex means but not per-sex medians (label follows) | Small |
| 6 | Working-time filter (FT / all) in the legacy series view | Only meaningful with the long series (see #1); fold into that work | — |

---

## Verification (all against live APIs, 2026-07-07)

- **Providers**: SE2 — 431 occupations, tree 10/40/149/431; totals (P10–P90+mean+median+count),
  age (6 bands), education (7 levels, weighted total), region (8 régions), trend
  (2015/2020/2024 medians), CPI (10 yrs), leaderboard (431 rows, top = Financial &
  insurance managers 126 500). FR2 — 429 occupations, tree 6/29/429; means+headcount
  (2024), women/men means, percentiles incl. honest censored-tail blanks,
  leaderboard (361 rows, top = Large-enterprise managers €16 853).
- **Tabs**: every SE2 tab (9) and FR2 tab (5) rendered via AppTest harness with real
  fetches — one chart each, zero exceptions.
- **Live**: `/se2` and `/fr2` route and render (header, prompt, code browser);
  `/norway`, `/us`, landing and admin unaffected.

## Suggested path to replacing the legacy pages

1. Admins beta-test SE2/FR2 (now). Widen later by flipping `access` to
   `restricted` + granting users — a config change.
2. Close SE gaps #1–2 and FR gaps #1–3 (the visible feature deltas).
3. Point the landing tiles at the v2 pages, keep legacy reachable at
   `/sweden-classic` for one release, then delete `scb_salaries.py` / `france.py`
   and move their remaining admin tools into the admin panel.
