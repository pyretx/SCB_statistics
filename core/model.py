"""Normalized data model + country config (see docs/architecture.md).

Charts and tables consume ONLY these shapes — never a raw API response. Each
country's provider is responsible for turning its API into an ``OccupationStat``
frame (and, where available, population-distribution / trend frames).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

# ── Normalized tidy tables ───────────────────────────────────────────────────
# One row per occupation × year × dimension-slice. Percentile columns are
# nullable — a country fills only what its source publishes (see Capabilities).
OCC_STAT_COLS = [
    "country", "year", "occ_code", "occ_name", "occ_group",
    "dimension", "dim_value",          # "total" | "sex" | "region" | "age" | "education"
    "currency", "period",              # "monthly" | "annual" | "hourly"
    "mean", "median", "p10", "p25", "p75", "p90",
    "count", "source_name", "source_url", "notes",
]
POP_PCT_COLS = ["country", "year", "sector", "sex", "worktime", "percentile", "value"]
TREND_COLS = ["country", "year", "series", "sex", "value_nominal", "value_real"]


def empty_occ_stats() -> pd.DataFrame:
    return pd.DataFrame(columns=OCC_STAT_COLS)


def empty_pop_pct() -> pd.DataFrame:
    return pd.DataFrame(columns=POP_PCT_COLS)


def empty_trend() -> pd.DataFrame:
    return pd.DataFrame(columns=TREND_COLS)


# ── Capabilities: THE driver of what renders ─────────────────────────────────
@dataclass(frozen=True)
class Capabilities:
    """What a country's data can actually answer. The shared sidebar and tabs
    switch on these, so a country never implies data it doesn't have."""
    has_occupation_percentiles: bool = False   # real P10..P90 per occupation (Sweden)
    has_population_distribution: bool = False   # whole-population curve (France)
    has_mean: bool = True
    has_median: bool = False
    has_sex: bool = False
    has_region: bool = False
    has_age: bool = False
    has_education: bool = False
    has_trend: bool = False
    sectors: tuple[str, ...] = ()               # e.g. ("private", "public"); () = none
    year_range: tuple[int, int] | None = None   # (first, last) available year


# ── Country config: metadata + labels + capabilities + wiring ────────────────
@dataclass
class CountryConfig:
    slug: str                       # url path + widget-key namespace, e.g. "norway"
    name: str                       # English display name, e.g. "Norway"
    native: str                     # native name, e.g. "Norge"
    iso: str                        # flag file code in assets/flags/<iso>.svg, e.g. "no"
    eyebrow: str                    # header eyebrow, e.g. "OFFICIAL STATISTICS · NORWAY"
    source_name: str                # e.g. "Statistics Norway (SSB)"
    source_url: str
    caption: str                    # sub-line under the H1
    currency: str = "SEK"           # ISO code, e.g. "NOK"
    currency_suffix: str = "kr"     # shown after values, e.g. "kr", "€"
    period: str = "monthly"         # "monthly" | "annual" | "hourly"
    capabilities: Capabilities = field(default_factory=Capabilities)
    tabs: tuple[str, ...] = ()       # standard tab ids to enable (see core.tabs)
    access: str = "internal"         # "public" | "registered" | "internal" | "restricted"
    fetch_mode: str = "reactive"     # "search" (commit button) | "reactive"
    labels: dict = field(default_factory=dict)   # i18n / display strings
    provider: object = None          # a core.provider.CountryProvider instance
    landing: bool = False            # show a (gated) tile on the landing page?
    bullets: tuple[str, ...] = ()    # landing-tile feature bullets

    def L(self, key: str, default: str = "") -> str:
        """Look up a display label, falling back to a sane default."""
        return self.labels.get(key, default)
