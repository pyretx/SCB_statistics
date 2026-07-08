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
  AGE BANDS          the same annual detail dataset (Y_LT30 … Y_GE60) → the
                     shared "By age" breakdown tab.
  RÉGIONS            DS_BTS_SAL_EQTP_SEX_PCS (mean by région × PCS GROUP —
                     occupation-level régional data does not exist, so the
                     "By region" tab shows the occupation's broad group).
  TREND              the long series (1951→) per broad PCS group in CONSTANT
                     euros → trend_is_real (single real view, no CPI overlay).
  POPULATION         the all-employee centile curve from the same long series
                     → the distribution tab's grey backdrop.
"""
from __future__ import annotations

import pandas as pd

import france_data as fd
from core import model
from core.provider import CountryProvider

SEX_CODE = {"total": "_T", "women": "F", "men": "M"}
_NOTE = "P10–P90: estimate from INSEE microdata (FD_SALAAN), both sexes."

# Detail-dataset age bands, in display order.
AGE_BANDS = ["Y_LT30", "Y30T39", "Y40T49", "Y50T59", "Y_GE60"]
AGE_LABELS = {
    "EN": {"Y_LT30": "Under 30", "Y30T39": "30–39", "Y40T49": "40–49",
           "Y50T59": "50–59", "Y_GE60": "60 and over"},
    "FR": {"Y_LT30": "Moins de 30 ans", "Y30T39": "30–39 ans", "Y40T49": "40–49 ans",
           "Y50T59": "50–59 ans", "Y_GE60": "60 ans et plus"},
}

# Broad PCS groups with a long series / regional coverage. The regional dataset
# groups 1–3 together ("1T3").
GROUP_LABELS = {
    "EN": {"3": "Managers & higher intellectual professions",
           "4": "Intermediate professions", "5": "Employees", "6": "Manual workers",
           "1T3": "Groups 1–3 (farmers, artisans, managers)"},
    "FR": {"3": "Cadres et professions intellectuelles supérieures",
           "4": "Professions intermédiaires", "5": "Employés", "6": "Ouvriers",
           "1T3": "Groupes 1–3 (agriculteurs, artisans, cadres)"},
}
_REGIONAL_GROUP = {"1": "1T3", "2": "1T3", "3": "1T3", "4": "4", "5": "5", "6": "6"}
_GROUP_SUFFIX = {"EN": "group", "FR": "groupe"}


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
        if dimension == "age":
            return self._age_rows(sector, occ_codes, sex, lang)
        if dimension == "region":
            return self._region_rows(occ_codes, sex, lang)
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

    # ── dimension slices ─────────────────────────────────────────────────────
    def _age_rows(self, sector, occ_codes, sex, lang) -> pd.DataFrame:
        """Mean + headcount per age band from the same annual detail dataset."""
        df = fd.fetch_detail_salaries(sector if sector in ("private", "public") else "private")
        if df.empty:
            return model.empty_occ_stats()
        df = df[df["year"] == df["year"].max()]
        sx = SEX_CODE.get(sex, "_T")
        labels = _leaves(lang)
        age_lbl = AGE_LABELS.get(lang, AGE_LABELS["EN"])
        yr = int(df["year"].max())
        rows = []
        for occ in occ_codes:
            sl = df[(df["pcs"] == occ) & (df["sex"] == sx)].set_index("age")
            for band in AGE_BANDS:
                r = sl.loc[band] if band in sl.index else None
                if isinstance(r, pd.DataFrame):
                    r = r.iloc[0]
                rows.append(self._dim_row(occ, labels.get(occ, occ), "age",
                                          age_lbl.get(band, band), yr,
                                          r.get("mean_salary") if r is not None else None,
                                          r.get("headcount") if r is not None else None))
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    def _region_rows(self, occ_codes, sex, lang) -> pd.DataFrame:
        """Mean per région at PCS-GROUP level (occupation-level régional data
        does not exist) — the series is named after the group, not the occupation,
        so the chart never implies more precision than the source has."""
        reg = fd.fetch_regional_salaries()
        if reg.empty:
            return model.empty_occ_stats()
        reg = reg[reg["year"] == reg["year"].max()]
        sx = SEX_CODE.get(sex, "_T")
        glabels = GROUP_LABELS.get(lang, GROUP_LABELS["EN"])
        suffix = _GROUP_SUFFIX.get(lang, "group")
        yr = int(reg["year"].max())
        rows, seen = [], set()
        for occ in occ_codes:
            grp = _REGIONAL_GROUP.get(occ[:1])
            if not grp or grp in seen:          # one series per distinct group
                continue
            seen.add(grp)
            name = f"{glabels.get(grp, grp)} · {suffix}"
            sl = reg[(reg["pcs_group"] == grp) & (reg["sex"] == sx)].set_index("region")
            for code, rname in fd.REGIONS_FR.items():
                r = sl.loc[code] if code in sl.index else None
                if isinstance(r, pd.DataFrame):
                    r = r.iloc[0]
                rows.append(self._dim_row(grp, name, "region", rname, yr,
                                          r.get("mean_salary") if r is not None else None,
                                          None))
        return pd.DataFrame(rows, columns=model.OCC_STAT_COLS)

    @staticmethod
    def _dim_row(code, name, dim, dv, yr, mean, cnt):
        return {"country": "fr2", "year": yr, "occ_code": code, "occ_name": name,
                "occ_group": str(code)[:1], "dimension": dim, "dim_value": dv,
                "currency": "EUR", "period": "monthly",
                "mean": mean, "median": None, "p10": None, "p25": None,
                "p75": None, "p90": None, "count": cnt,
                "source_name": "INSEE (Melodi)",
                "source_url": "https://api.insee.fr/melodi/", "notes": ""}

    # ── long series (1951→, constant euros) + population curve ──────────────
    def trend(self, *, sector="private", occ_codes=(), sex="total", years=(),
              lang="EN", measure="mean") -> pd.DataFrame:
        """Constant-euro mean per broad PCS group (the occupation's group) —
        the framework renders it as a real-only trend (trend_is_real)."""
        sl = fd.fetch_series_longues(sector if sector in ("private", "public") else "private")
        if sl.empty:
            return model.empty_trend()
        sx = SEX_CODE.get(sex, "_T")
        glabels = GROUP_LABELS.get(lang, GROUP_LABELS["EN"])
        suffix = _GROUP_SUFFIX.get(lang, "group")
        rows, seen = [], set()
        for occ in occ_codes:
            grp = occ[:1]
            if grp not in ("3", "4", "5", "6") or grp in seen:
                continue                        # groups 1–2 have no salaried series
            seen.add(grp)
            name = f"{glabels.get(grp, grp)} · {suffix}"
            g = sl[(sl["pcs"] == grp) & (sl["sex"] == sx)
                   & (sl["wktime"] == "_T") & (sl["centile"] == "_T")]
            for _, r in g.iterrows():
                if str(r["year"]).isdigit():
                    rows.append({"country": "fr2", "year": int(r["year"]), "series": name,
                                 "sex": sex, "value_nominal": r["salary_const_eur"],
                                 "value_real": r["salary_const_eur"]})
        return pd.DataFrame(rows, columns=model.TREND_COLS)

    def population_distribution(self, *, sector="private", sex="total",
                                year=None) -> pd.DataFrame:
        """All-employee centile curve (latest year of the long series) — the
        distribution tab's grey backdrop."""
        sl = fd.fetch_series_longues(sector if sector in ("private", "public") else "private")
        if sl.empty:
            return model.empty_pop_pct()
        sx = SEX_CODE.get(sex, "_T")
        d = sl[(sl["pcs"] == "_T") & (sl["sex"] == sx)
               & (sl["wktime"] == "_T") & (sl["centile"] != "_T")]
        if d.empty:
            return model.empty_pop_pct()
        ly = d["year"].max()
        rows = []
        for _, r in d[d["year"] == ly].iterrows():
            p = fd.centile_pct(r["centile"])
            if p and pd.notna(r["salary_const_eur"]):
                rows.append({"country": "fr2", "year": int(ly), "sector": sector,
                             "sex": sex, "worktime": "_T", "percentile": int(p),
                             "value": float(r["salary_const_eur"])})
        return pd.DataFrame(rows, columns=model.POP_PCT_COLS)
