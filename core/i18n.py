"""Tiny i18n layer for the shared framework UI.

`UI` holds the generic left-menu / tab / panel strings a language needs (English
plus any language a country wants to offer). A country only overrides the strings
that are truly country-specific — e.g. its sector names — in ``cfg.i18n``.

Resolution order for ``t(cfg, key, lang)``:
    1. cfg.i18n[lang][key]          country override, exact language
    2. cfg.i18n["EN"][key]          country override, English fallback
    3. UI[lang][key]                framework default, exact language
    4. UI["EN"][key]                framework default, English fallback
    5. default (or the key itself)
"""
from __future__ import annotations

# Framework-generic UI strings. Add a language here once and every country that
# offers it inherits a fully translated shell.
UI: dict[str, dict[str, str]] = {
    "EN": {
        "brand": "Salary Explorer",
        "sector": "Sector",
        "sex": "Sex",
        "total": "Total", "women": "Women", "men": "Men",
        "year_range": "Year range",
        "major_group": "Occupation field",
        "all_groups": "All fields",
        "occupations": "Occupation(s)",
        "occ_placeholder": "Choose options",
        "search": "Search", "clear": "Clear",
        "language": "Language",
        "user_guide": "User guide",
        "code_browser": "Code browser",
        "back": "← Back",
        "overview": "Overview",
        "occupation_overview": "Occupation overview",
        "avg_salary": "Average salary",
        "median_salary": "Median salary",
        "col_code": "Code", "col_occupation": "Occupation", "col_name": "Name",
        "col_mean": "Mean", "col_median": "Median", "col_count": "Count",
        "prompt_select": "Select at least one occupation in the sidebar to get started.",
        "no_data_combo": ("No figures are published for this combination of "
                          "occupation, sector, sex and year. Try “All sectors” or "
                          "adjust the selection."),
        "browser_search": "Search a code or name",
        "browser_intro": "Browse the occupation classification. Click a group to expand it.",
        "browser_results": "results",
    },
    "NO": {
        "brand": "Salary Explorer",
        "sector": "Sektor",
        "sex": "Kjønn",
        "total": "Totalt", "women": "Kvinner", "men": "Menn",
        "year_range": "Årsintervall",
        "major_group": "Yrkesfelt",
        "all_groups": "Alle felt",
        "occupations": "Yrke(r)",
        "occ_placeholder": "Velg",
        "search": "Søk", "clear": "Tøm",
        "language": "Språk",
        "user_guide": "Brukerveiledning",
        "code_browser": "Kodeoversikt",
        "back": "← Tilbake",
        "overview": "Oversikt",
        "occupation_overview": "Yrkesoversikt",
        "avg_salary": "Gjennomsnittslønn",
        "median_salary": "Medianlønn",
        "col_code": "Kode", "col_occupation": "Yrke", "col_name": "Navn",
        "col_mean": "Gjennomsnitt", "col_median": "Median", "col_count": "Antall",
        "prompt_select": "Velg minst ett yrke i menyen for å komme i gang.",
        "no_data_combo": ("Ingen tall er publisert for denne kombinasjonen av "
                          "yrke, sektor, kjønn og år. Prøv «Alle sektorer» eller "
                          "juster utvalget."),
        "browser_search": "Søk kode eller navn",
        "browser_intro": "Bla gjennom yrkesklassifiseringen. Klikk en gruppe for å utvide.",
        "browser_results": "treff",
    },
}


def t(cfg, key: str, lang: str = "EN", default: str | None = None) -> str:
    """Resolve a UI string for ``key`` in ``lang`` (see module docstring)."""
    ci = getattr(cfg, "i18n", None) or {}
    for src in (ci.get(lang), ci.get("EN"), UI.get(lang), UI.get("EN")):
        if src and key in src:
            return src[key]
    return default if default is not None else key
