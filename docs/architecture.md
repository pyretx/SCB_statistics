# Salary Explorer — reusable country-page framework

Status: **adopted** (2026-07). Sweden and France ship today as standalone page
scripts; this document is the agreed plan for turning "add a country" into
"write one config + one data provider, register it in a list".

Guiding principle:

> **Functionality originates from Sweden. Data plumbing follows France.**

The shared tabs, charts, filters and calculators are modelled on Sweden's richer
feature set. Every country feeds them through a France-style **provider** module
(API calls → tidy DataFrames → one normalized model). Sweden defines *what to
show*; France defines *how to fetch and shape data cleanly*.

---

## Locked decisions

1. **Access now:** Sweden/France are `public` (no login). In-development countries
   are `internal` (admin/master only). The model is **built to flip** Sweden/France
   to "login-required-but-free" (`registered`) with a one-line config change.
2. **Order:** Norway first, then the United States when ready.
3. **Validation via SE2:** legacy Sweden (`scb_salaries.py`) is left untouched. A
   second Sweden ("SE2") is built on the framework and run **side by side**, diffed
   against legacy Sweden to find gaps, then cut over. This removes the risk of
   migrating the live Sweden page in one shot.
4. **Cross-country comparison:** later (needs an ISCO-08 occupation crosswalk; own
   project).

---

## Access-tier model

| Tier | Who can open | Used by |
|---|---|---|
| `public` | anyone, no login | SE, FR (now) |
| `registered` | any signed-in user (still free) | SE, FR after the flip |
| `internal` | admin/master only | Norway/US while building |
| `restricted` | explicit `app_metadata.countries` allow-list | fine-grained, optional |

One gate at the top of `render_country(cfg)` reads `cfg.access` + the current user.
The country switcher and the landing cards filter to what the user may see.
Releasing/gating a country is a config change, never a code change.

---

## Architecture

A country = **(config + provider)**. Everything else is shared.

```
core/                      # the framework (shared)
  model.py                 # normalized data types + Capabilities + CountryConfig
  provider.py              # CountryProvider protocol (every country implements it)
  access.py                # access-tier gate (public/registered/internal/restricted)
  registry.py              # COUNTRIES = [...]  ← add a country here
  sidebar.py               # the ONE left menu (logo, switcher, capability-driven filters)
  states.py                # empty / loading / error + the st.empty view-mount shell
  charts.py                # bar / line / distribution / comparison (wrap theme.style_fig)
  tables.py                # ranked table, searchable occupation table
  page.py                  # render_country(cfg): the ONE page skeleton
  tabs/                    # one renderer per standard tab (distribution, where-do-I-stand,
                           #   leaderboard, by-age/region/education, basic-stats, trend)

countries/
  <slug>/config.py         # metadata, labels/i18n, capabilities, enabled tabs, access, fetch_mode
  <slug>/provider.py       # API calls + transform → normalized model (a france_data.py)
  <slug>/...               # optional country modules (Sweden: work_permit; France: own_distribution)
```

`app.py` builds `st.navigation` by looping the registry, so a new country needs
**no new page file** — just an entry in `core/registry.py`.

### Streamlit mechanics baked into the shell (learned from the current code)

- **Widget-key namespacing.** All country pages share one Streamlit session (France
  already prefixes every key `fr_`). The shell auto-prefixes every widget key with
  the country slug so countries can't collide.
- **Fetch mode.** Sweden commits on a **Search** button (SCB cell limits); France is
  **fully reactive** (one cached pull). `cfg.fetch_mode ∈ {"search","reactive"}`.
- **View mount.** The `st.empty()` container that mutually-exclusive full-page views
  render into (so panels/browsers don't ghost behind charts) is standard in the shell.

---

## Normalized data model

Not one flat table — the data has three shapes, so three tidy tables + a
capabilities object. Charts/tables consume **only** these, never a raw API response.

```python
# 1) Occupation-level stats (long/tidy) — both countries have some of this
OccupationStat: country, year, occ_code, occ_name, occ_group,
                dimension ("total"|"sex"|"region"|"age"|"education"),
                dim_value, currency, period ("monthly"|"annual"|"hourly"),
                mean, median, p10, p25, p75, p90,   # nullable per capability
                count, source_name, source_url, notes

# 2) Population distribution (France-style backdrop) — long/tidy
PopulationPercentile: country, year, sector, sex, worktime, percentile, value

# 3) Trend series — long/tidy
TrendPoint: country, year, series ("population"|occ_code), sex, value_nominal, value_real

# 4) Capabilities — THE driver of what renders
Capabilities: has_occupation_percentiles, has_population_distribution,
              has_mean, has_median, has_sex, has_region, has_age,
              has_education, has_trend, currency, period, sectors, year_range
```

### Capability-driven "distribution" tab (the key reconciliation)

Same tab, same styling, honest to each country's data:

- `has_occupation_percentiles = True` (Sweden; likely Norway/US) → per-occupation
  percentile curve (P10–P90), Sweden-style.
- `has_occupation_percentiles = False` (France) → population distribution curve with
  occupation means as ★ markers (+ optional microdata estimate).

Every filter/tab is gated the same way, so a country never implies data it lacks.

---

## Roadmap

| Phase | Deliverable | Risk | Legacy SE & FR |
|---|---|---|---|
| **1** | `core/` skeleton: model + Capabilities + CountryConfig, `CountryProvider`, access gate (`public`/`internal`), registry-driven pages, sidebar, states, charts/tables helpers, the standard reusable tabs (extracted from Sweden's logic), and a **demo country** proving the shell. | Med | **Untouched** |
| **2** | **Norway** — config + provider (SSB Statbank → normalized). `/norway`, `internal`. | Med | Untouched |
| **3** | **SE2** — Sweden on the framework at `/sweden2`; introduces optional country modules (work-permit first). Diff SE vs SE2, close gaps. | Med | Untouched, compared |
| **4** | Full auth-by-country: `registered` tier, switcher/landing filtering. | Med | Additive |
| **5** | Cutover SE2 → SE (retire legacy); migrate **France** (own-distribution + population-distribution mode). | Med | SE cutover; FR migrated |
| **Later** | US; then more countries. Cross-country comparison as its own project. | — | — |

**Why safe:** always build new pages next to the working ones. Norway proves the
framework on fresh data; SE2 proves it reproduces the best page before anything is
retired; the Sweden cutover becomes a validated swap, not a rewrite.

---

## Adding a country (the payoff)

1. `countries/<slug>/provider.py` — API calls + transform to the normalized model.
2. `countries/<slug>/config.py` — flag, currency/period, occupation labels,
   capabilities, enabled tabs, `access`.
3. One line in `core/registry.py`.

→ Identical menu, tabs, switcher entry, landing card and auth gate, automatically.
No UI, chart or styling work.

---

## Risks / open items

- **Sweden's depth is the real work** (percentiles, aggregation/weighting, CPI,
  work-permit). SE2 de-risks it by validating before cutover.
- **Classification differs** per country (SSYK/PCS/STYRK/SOC); stays inside each
  provider. Cross-country mapping deferred.
- Occupation aggregation/weighting (`collapse_df`, `fetch_occ_weights`) becomes a
  shared, capability-gated feature.

## Standard tabs (the single naming standard — 2026-07)

Every country page uses the same canonical tabs; each appears only if the
country's Capabilities support it (so a country never implies data it lacks).
Names live in core/i18n.py (`tab_<id>`); the registry is core/tabs/__init__.py.

| id            | Label (EN)          | Contents                                                                                   | Shown when |
|---------------|---------------------|--------------------------------------------------------------------------------------------|------------|
| overview      | Overview            | Per-occupation KPI cards (mean · median · P25/P75 · women · men · F/M gap · headcount) + comparison bar | always |
| distribution  | Salary distribution | Percentile/quartile chart + year & measures pickers + raw-data table/export + embedded Salary-trend-over-time (nominal/growth/real) | has_occupation_percentiles OR has_quartiles |
| where         | Where do I stand?   | Salary → percentile-position calculator                                                    | has_occupation_percentiles OR has_quartiles |
| leaderboard   | Leaderboard         | Rank occupations by pay, scoped to the 2-digit sub-group drilled into                       | has_leaderboard |
| age/region/education/sex | By age / By region / By education / By gender | One breakdown tab per dimension the source actually has                       | has_age / has_region / has_education / has_sex |
| stats         | Basic statistics    | Per-occupation summary table + headcount + CSV export                                       | always |

Standard order: overview · distribution · where · leaderboard · (breakdowns) · stats.
The Trend view is embedded inside Salary distribution (a "Salary trend over time"
section with a Measure selector), not a separate tab — mirrors the Swedish page.

Note: the legacy Sweden (scb_salaries.py) and France (france.py) pages predate
this standard and still say "Percentile distribution"; they are separate pages,
untouched. New framework countries follow the table above.
