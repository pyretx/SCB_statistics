"""Demo provider — hardcoded normalized data, so the framework shell can be
verified without any real API. A real provider (e.g. countries/norway) does the
same thing but from an API, exactly like france_data.py."""
from __future__ import annotations

import pandas as pd

from core import model
from core.provider import CountryProvider

_OCCS = {
    "1001": "Software developers", "1002": "Mechanical engineers",
    "1003": "Registered nurses", "1004": "Primary school teachers",
    "1005": "Economists", "1006": "Electricians",
}
_MEAN = {"1001": 55500, "1002": 54300, "1003": 41000,
         "1004": 39000, "1005": 58000, "1006": 43500}


class DemoProvider(CountryProvider):
    def occupations(self, lang: str = "EN") -> dict[str, str]:
        return dict(_OCCS)

    def occupation_stats(self, *, sector="", occ_codes=(), sex="total",
                         years=(), dimension="total", year=None) -> pd.DataFrame:
        yr = years[-1] if years else 2025
        rows = []
        for c in occ_codes:
            if c not in _OCCS:
                continue
            m = _MEAN[c]
            rows.append({
                "country": "demo", "year": yr, "occ_code": c, "occ_name": _OCCS[c],
                "occ_group": "", "dimension": "total", "dim_value": "total",
                "currency": "SEK", "period": "monthly",
                "mean": m, "median": round(m * 0.95),
                "p10": round(m * 0.70), "p25": round(m * 0.85),
                "p75": round(m * 1.18), "p90": round(m * 1.40),
                "count": 1000, "source_name": "Demo", "source_url": "", "notes": "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)
