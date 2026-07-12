"""US config — BLS OEWS. Percentiles + mean + employment; SOC 4-level hierarchy;
a per-state Location filter (the framework's sector slot). No sex/trend/age in
OEWS. access='registered' → LIVE for every signed-in user (free account);
signed-out visitors don't see the US at all (landing tile + switcher hide it)."""
from __future__ import annotations

from core.model import CountryConfig, Capabilities
from .provider import UsProvider

_prov = UsProvider()
_regions = _prov.regions()                      # {code: name} — US national, states, then industries
_YEAR = _prov.year()                            # from the data file meta — never hardcode the vintage
_VINTAGE = f"May {_YEAR}"                       # OEWS reference period is May of the reference year
_TOP_CODE = _prov.top_code()                    # annual top-code (percentiles at/above it are blank)
_CAPTION = f"BLS Occupational Employment & Wage Statistics · {_VINTAGE} · annual USD"


def _scope_label(code: str, name: str) -> str:
    return "All industries" if code == "US" else name


# Sidebar selector = INDUSTRY only (national baseline + nationwide NAICS
# industries). States moved to the By-region tab (real OEWS per-state data);
# OEWS has no industry × state, so the two are separate lenses, never combined.
_scopes = {c: n for c, n in _regions.items() if c == "US" or c.startswith("IND")}
_region_labels = {f"sector_{code}": _scope_label(code, name) for code, name in _scopes.items()}

# Structured guide (the approved User-Guide design; rendered by core/panels.py)
_GUIDE_EN = {
    "title": "How to use the US Salary Explorer",
    "source": f"U.S. Bureau of Labor Statistics · OEWS (SOC-2018) · {_VINTAGE} · annual USD",
    "intro": "Look up US wages by occupation — official data from the Bureau of "
             "Labor Statistics OEWS program, no technical knowledge needed. This "
             "guide covers the three-step flow, finding occupations, and how to "
             "read the charts.",
    "steps_title": "Getting started — three steps",
    "steps": [
        ("Pick an industry",
         "All industries (national) or a single nationwide industry (e.g. "
         "Hospitals). For geography, use the By-region tab instead — BLS does "
         "not publish wages by industry × state, so they are separate cuts."),
        ("Search",
         "Pick one or more occupations, then press the blue Search button at the "
         "bottom of the sidebar."),
        ("Read the results",
         "Explore the tabs on the right. Change any filter and search again to "
         "update the charts."),
    ],
    "find_title": "Finding the right occupation",
    "find": [
        ("Search box", "Type in the “Search occupations…” box — it matches both "
                       "job titles and SOC codes."),
        ("Drill down", "Or narrow step by step with Major → Minor → Broad group "
                       "(the SOC hierarchy)."),
        ("Code browser", "Open the Code browser to explore the whole SOC-2018 "
                         "classification tree."),
        ("Aggregate", "Picked several occupations? Toggle Aggregate selection above "
                      "the tabs to merge them into one employment-weighted series."),
    ],
    "charts_title": "Reading the wage charts",
    "charts_intro": "Wages are shown as percentiles — a wide gap between P10 and "
                    "P90 means pay varies a lot in that job (the average is a "
                    "separate ♦ marker):",
    "pcts": [("P10", 22, "10% earn less"),
             ("P25", 36, "a quarter earn less"),
             ("MED", 52, "half earn less"),
             ("P75", 68, "a quarter earn more"),
             ("P90", 84, "only 10% earn more")],
    "notes_title": "Good to know",
    "notes": [
        "Figures are annual wages (USD) plus employment counts.",
        f"Very high wages are top-coded by BLS — a percentile at or above the top "
        f"code (${_TOP_CODE:,}/yr in {_YEAR}) is shown blank.",
        "OEWS has no gender, age or education breakdown and is a single annual "
        "snapshot, so those tabs and the trend view don't appear.",
        "Industry cuts (NAICS) are national only — BLS does not publish "
        "state × industry.",
    ],
    "tabs_title": "The tabs",
    "tabs": [
        ("Overview", "The key figures at a glance, plus employment."),
        ("Salary distribution", "The percentile chart, plus raw data + CSV export."),
        ("Where do I stand?", "Enter an annual wage and see which percentile it "
                              "falls in."),
        ("Leaderboard", "Ranks all ~830 occupations by pay within a SOC group."),
        ("By region", "Compare a state's actual OEWS wages for the occupation "
                      "against the national figure — real data, not an estimate."),
    ],
    "footer": f"All figures are from the BLS OEWS {_VINTAGE} release, updated annually.",
}

CONFIG = CountryConfig(
    slug="us",
    name="United States",
    native="United States",
    iso="us",
    eyebrow="OFFICIAL STATISTICS · UNITED STATES",
    source_name="U.S. Bureau of Labor Statistics (OEWS)",
    source_url="https://www.bls.gov/oes/",
    caption=_CAPTION,
    currency="USD", currency_suffix="$", money_prefix=True, period="annual",
    capabilities=Capabilities(
        has_occupation_percentiles=True,        # full P10..P90 (richer than Norway)
        has_occupation_hierarchy=True,          # SOC nests via significant-prefix keys
        has_mean=True, has_median=True,
        has_leaderboard=True, leaderboard_scope=4,   # SOC minor group (4-char key)
        has_region_data=True,                   # real per-state OEWS → By-region tab
        sectors=tuple(_scopes),                 # sidebar = national + industries only
        year_range=(_YEAR, _YEAR),              # single OEWS snapshot
    ),
    tabs=("overview", "distribution", "where", "leaderboard", "region_sim",
          "import_overlay"),
    access="registered",                    # LIVE — any signed-in user
    fetch_mode="search",
    landing=True,
    classification="SOC-2018",
    labels={"badge": "Live", "source_short": "BLS OEWS · official"},
    languages=(("EN", "English"),),
    i18n={"EN": {
        "title": "US Salary Explorer",
        "caption": _CAPTION,
        "sector": "Industry",
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
