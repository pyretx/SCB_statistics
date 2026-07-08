"""CountryProvider — the data interface every country implements.

A provider turns one country's API into the normalized model (core.model). It
subclasses this base and overrides only the methods its source supports; the
config's Capabilities declare which of those are meaningful, so the shared tabs
know what to render. This mirrors France's clean data-layer split (france_data.py),
generalized behind one interface.
"""
from __future__ import annotations

import pandas as pd

from . import model


class CountryProvider:
    """Base provider: every method returns an empty normalized frame by default.
    Countries override what they can serve.

    Query kwargs are a superset; a provider ignores dimensions it doesn't support:
        sector: str            selected market sector (or "" if the country has none)
        occ_codes: tuple[str]  selected occupation codes
        sex: str               "total" | "women" | "men"
        years: tuple[int]      selected year range
        year: int              single year for one-year breakdowns
    """

    # occupation code -> display name (leaf occupations only), for the language
    def occupations(self, lang: str = "EN") -> dict[str, str]:
        return {}

    # code -> name for EVERY classification level (groups + leaves), so the
    # framework can build the major-group drill-down and the code browser.
    # Default: no groups, just the leaves (a flat classification).
    def occupation_tree(self, lang: str = "EN") -> dict[str, str]:
        return self.occupations(lang)

    # long/tidy OccupationStat rows (dimension="total" unless a breakdown is asked)
    def occupation_stats(self, *, sector: str = "", occ_codes: tuple[str, ...] = (),
                         sex: str = "total", years: tuple[int, ...] = (),
                         dimension: str = "total", year: int | None = None,
                         lang: str = "EN") -> pd.DataFrame:
        return model.empty_occ_stats()

    # whole-population percentile curve (France-style backdrop)
    def population_distribution(self, *, sector: str = "", sex: str = "total",
                               year: int | None = None) -> pd.DataFrame:
        return model.empty_pop_pct()

    # trend series over years (normalized TREND_COLS: year, series, value_nominal…)
    def trend(self, *, sector: str = "", occ_codes: tuple[str, ...] = (),
              sex: str = "total", years: tuple[int, ...] = (),
              lang: str = "EN", measure: str = "mean") -> pd.DataFrame:
        return model.empty_trend()

    # annual-average national CPI index → {year: index} (any base). Powers the
    # trend tab's inflation / real-salary views. Empty when the country has no CPI.
    def cpi_annual(self, years: tuple[int, ...] = ()) -> dict:
        return {}

    # ALL occupations' pay for one year → DataFrame[occ_code, occ_name, mean,
    # median, count] (powers the Leaderboard). Empty by default.
    def leaderboard(self, *, sector: str = "", sex: str = "total",
                    year: int | None = None, lang: str = "EN") -> pd.DataFrame:
        return pd.DataFrame(columns=["occ_code", "occ_name", "mean", "median", "count"])

    # Rich per-code metadata for the code browser: {"description": str|None,
    # "synonyms": [str, …]}. Empty when the classification has none (Sweden's
    # SSYK descriptions/synonyms are the first source).
    def occupation_details(self, code: str, lang: str = "EN") -> dict:
        return {}

    # {leaf_code: "joined synonym text, lowercased"} — extends the sidebar's
    # occupation search beyond names/codes. Empty by default.
    def occupation_synonyms(self, lang: str = "EN") -> dict:
        return {}
