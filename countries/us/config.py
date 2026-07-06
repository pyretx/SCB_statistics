"""US config — BLS OEWS. Percentiles + mean + employment; SOC 4-level hierarchy;
a per-state Location filter (the framework's sector slot). No sex/trend/age in
OEWS. access='restricted' → admin/master or granted users only (beta)."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .provider import UsProvider

_prov = UsProvider()
_regions = _prov.regions()                      # {code: name}, "US" (national) first
_region_labels = {f"sector_{code}": name for code, name in _regions.items()}

_GUIDE_EN = """
**What this shows.** Annual wages for ~830 occupations (SOC-2018) from the U.S.
Bureau of Labor Statistics **OEWS** program (May 2024), nationally and for every
state.

**How to use it**
1. Pick a **Location** — United States (national) or a state.
2. Narrow by **occupation field** (SOC major → minor → broad), then pick one or
   more **occupations**.
3. Press **Search**.

**Good to know**
- Figures are annual **mean**, **median** and **P10 / P25 / P75 / P90** wages, plus
  **employment**.
- Very high wages are **top-coded** by BLS (shown blank when a percentile is at or
  above the top code, $239,200/yr in 2024).
- OEWS has **no gender, age or education** breakdown and is a single annual
  snapshot, so those tabs and the trend view don't appear.
- Use the **Code browser** to explore the SOC classification.
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
    tabs=("overview", "distribution", "where", "leaderboard"),
    access="restricted",
    fetch_mode="search",
    landing=True,
    classification="SOC-2018",
    labels={"badge": "Beta", "source_short": "BLS OEWS · official"},
    languages=(("EN", "English"),),
    i18n={"EN": {
        "title": "US Salary Explorer",
        "caption": "BLS Occupational Employment & Wage Statistics · May 2024 · annual USD",
        "sector": "Location",
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
