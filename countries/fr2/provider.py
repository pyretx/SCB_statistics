"""France v2 data provider — INSEE Melodi + bundled microdata, the framework
port of the legacy france.py data layer (it reuses france_data.py directly, so
the two share every fetch and cache).

Shape of the source:
  MEAN + HEADCOUNT   live from Melodi DS_DERA_*_ANNUEL, per detailed PCS-ESE
                     occupation × sector (private/public) × sex (_T/F/M),
                     national, latest published year per sector.
  PERCENTILES        the bundled microdata estimates (FD_SALAAN,
                     pcs_microdata_percentiles.json): P10/P25/P50/P75/P90 per
                     occupation, both sexes together — attached only to
                     sex='total' rows, flagged in `notes`.
  LABELS             bundled pcs_labels.json (FR + EN, levels 1/2/4 — a prefix
                     hierarchy the framework drill-down handles natively).

No trend here: INSEE's long series exist only per broad PCS group in constant
euros — see docs/se2-fr2-parity.md for the mitigation proposal.
"""
from __future__ import annotations

import pandas as pd

import france_data as fd
from core import model
from core.provider import CountryProvider

SEX_CODE = {"total": "_T", "women": "F", "men": "M"}
_NOTE = "P10–P90: estimate from INSEE microdata (FD_SALAAN), both sexes."


def _labels(lang: str = "EN") -> dict[str, str]:
    """{code: name} for every PCS level, in the asked language (EN falls back to
    the French title when no translation exists)."""
    out = {}
    for code, entry in fd.load_pcs_labels().items():
        name = (entry.get("en") or entry.get("fr")) if lang == "EN" else \
               (entry.get("fr") or entry.get("en"))
        if name:
            out[code] = name
    return out


def _leaves(lang: str = "EN") -> dict[str, str]:
    return {c: n for c, n in _labels(lang).items() if len(c) == 4}


def _micro() -> dict:
    return fd.load_microdata_percentiles().get("occupations", {})


def micro_year() -> int:
    try:
        occs = fd.load_microdata_percentiles().get("occupations", {})
        return int(next(iter(occs.values()))["year"])
    except Exception:
        return 2023


def _detail(sector: str) -> pd.DataFrame:
    """Latest-year national totals slice (age _T) of the annual detail dataset."""
    df = fd.fetch_detail_salaries(sector if sector in ("private", "public") else "private")
    if df.empty:
        return df
    df = df[df["age"] == "_T"]
    return df[df["year"] == df["year"].max()]


class France2Provider(CountryProvider):
    def occupations(self, lang: str = "EN") -> dict[str, str]:
        return _leaves(lang)

    def occupation_tree(self, lang: str = "EN") -> dict[str, str]:
        return _labels(lang)

    def occupation_stats(self, *, sector="private", occ_codes=(), sex="total",
                         years=(), dimension="total", year=None,
                         lang="EN") -> pd.DataFrame:
        occ_codes = tuple(occ_codes)
        if not occ_codes:
            return model.empty_occ_stats()
        det = _detail(sector)
        sx = SEX_CODE.get(sex, "_T")
        sl = det[det["sex"] == sx].set_index("pcs") if not det.empty else pd.DataFrame()
        micro = _micro()
        labels = _leaves(lang)
        yr = int(det["year"].max()) if not det.empty else micro_year()

        rows = []
        for occ in occ_codes:
            mean = cnt = None
            if not sl.empty and occ in sl.index:
                r = sl.loc[occ]
                r = r.iloc[0] if isinstance(r, pd.DataFrame) else r
                mean, cnt = r.get("mean_salary"), r.get("headcount")
            pct = (micro.get(occ, {}).get("pct", {}) if sex == "total" else {})
            rows.append({
                "country": "fr2", "year": yr, "occ_code": occ,
                "occ_name": labels.get(occ, occ), "occ_group": occ[:1],
                "dimension": "total", "dim_value": "total",
                "currency": "EUR", "period": "monthly",
                "mean": mean, "median": pct.get("50"),
                "p10": pct.get("10"), "p25": pct.get("25"),
                "p75": pct.get("75"), "p90": pct.get("90"),
                "count": cnt,
                "source_name": "INSEE (Melodi + FD_SALAAN microdata)",
                "source_url": "https://api.insee.fr/melodi/",
                "notes": _NOTE if pct else "",
            })
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def leaderboard(self, *, sector="private", sex="total", year=None,
                    lang="EN") -> pd.DataFrame:
        det = _detail(sector)
        sx = SEX_CODE.get(sex, "_T")
        micro = _micro()
        labels = _leaves(lang)
        rows = []
        if not det.empty:
            for _, r in det[det["sex"] == sx].iterrows():
                occ = r["pcs"]
                if occ not in labels:
                    continue
                # median exists only as the microdata estimate (both sexes) —
                # attach it to 'total' only, so a per-sex gap never silently
                # compares mislabelled figures.
                med = micro.get(occ, {}).get("pct", {}).get("50") if sex == "total" else None
                rows.append({"occ_code": occ, "occ_name": labels[occ],
                             "mean": r.get("mean_salary"), "median": med,
                             "count": r.get("headcount")})
        return pd.DataFrame(rows, columns=["occ_code", "occ_name", "mean", "median", "count"])
