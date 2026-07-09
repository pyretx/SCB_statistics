"""US config — BLS OEWS. Percentiles + mean + employment; SOC 4-level hierarchy;
a per-state Location filter (the framework's sector slot). No sex/trend/age in
OEWS. access='restricted' → admin/master or granted users only (beta)."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .provider import UsProvider

_prov = UsProvider()
_regions = _prov.regions()                      # {code: name} — US national, states, then industries


def _scope_label(code: str, name: str) -> str:
    # Industry scopes (key "IND"+NAICS) are national-only and mutually exclusive
    # with a state — mark them so they read distinctly in the combined selector.
    return f"Industry · {name}" if code.startswith("IND") else name


_region_labels = {f"sector_{code}": _scope_label(code, name) for code, name in _regions.items()}

_GUIDE_EN = """
# 👋 Welcome to the US Salary Explorer

Look up **US wages** by occupation — official data from the U.S. Bureau of
Labor Statistics **OEWS** program (May 2024). No technical knowledge needed.

## 🚀 Getting started — 3 steps
1. Pick a **Location / industry** — United States (national), a state, or a
   nationwide **industry** (`Industry · …`, e.g. *Hospitals*). Location and
   industry are separate cuts, so you choose one or the other, not both.
2. Narrow by **occupation field** (SOC major → minor → broad), pick one or
   more **occupations**, and click **🔍 Search**.
3. **Read the results** in the tabs. Change a filter and search again.

## 🔎 Finding the right occupation
- Type in the **"Search occupations…"** box — it matches job titles and codes.
- Or drill down the SOC hierarchy level by level.
- Open the **Code browser** to explore the whole SOC-2018 classification.
- Picked several occupations? Toggle **Aggregate selection** above the tabs to
  merge them into one employment-weighted series.

## 📈 Reading the wage charts
Wages are shown as **percentiles**:
- **P10** — 10% earn less than this (the lower end).
- **Median (P50)** — the middle wage; half earn more, half less.
- **P90** — only 10% earn more (the top end).
- **Average** — shown as a separate ♦ marker.

## 🗂 The tabs
- **Overview** — the key figures at a glance, plus employment.
- **Salary distribution** — the percentile chart, raw data + CSV export.
- **Where do I stand?** — enter an annual wage and see which percentile it
  falls in.
- **Leaderboard** — ranks all ~830 occupations by pay within a SOC group.

## ❓ Good to know
- Figures are **annual** wages (USD) plus **employment** counts.
- Very high wages are **top-coded** by BLS (shown blank when a percentile is
  at or above the top code, $239,200/yr in 2024).
- OEWS has **no gender, age or education** breakdown and is a single annual
  snapshot, so those tabs and the trend view don't appear.
"""

CONFIG = CountryConfig(
    slug="us",
    name="United States",
    native="United States",
    iso="us",
    eyebrow="OFFICIAL STATISTICS · UNITED STATES",
    source_name="U.S. Bureau of Labor Statistics (OEWS)",
    source_url="https://www.bls.gov/oes/",
    caption="BLS Occupational Employment & Wage Statistics · May 2024 · annual USD",
    currency="USD", currency_suffix="$", money_prefix=True, period="annual",
    capabilities=Capabilities(
        has_occupation_percentiles=True,        # full P10..P90 (richer than Norway)
        has_occupation_hierarchy=True,          # SOC nests via significant-prefix keys
        has_mean=True, has_median=True,
        has_leaderboard=True, leaderboard_scope=4,   # SOC minor group (4-char key)
        sectors=tuple(_regions),                # the sector slot holds the Location/state
        year_range=(2024, 2024),                # single OEWS snapshot
    ),
    tabs=("overview", "distribution", "where", "leaderboard", "import_overlay"),
    access="restricted",
    fetch_mode="search",
    landing=True,
    classification="SOC-2018",
    labels={"badge": "Beta", "source_short": "BLS OEWS · official"},
    languages=(("EN", "English"),),
    i18n={"EN": {
        "title": "US Salary Explorer",
        "caption": "BLS Occupational Employment & Wage Statistics · May 2024 · annual USD",
        "sector": "Location / industry",
        **_region_labels,
        # SOC drill-down (sidebar, by depth) and code browser (by key length 2/4/6/7)
        "grp_1": "Major group", "grp_2": "Minor group", "grp_3": "Broad occupation",
        "all_grp_1": "— All major groups —", "all_grp_2": "— All minor groups —",
        "all_grp_3": "— All broad groups —",
        "brlvl_2": "Major group", "brlvl_4": "Minor group",
        "brlvl_6": "Broad occupation", "brlvl_7": "Detailed occupation",
    }},
    guide={"EN": _GUIDE_EN},
    provider=_prov,
)
