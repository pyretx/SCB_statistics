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
        # occupation drill-down levels (numbered in code by cascade depth)
        "grp_1": "Major group", "grp_2": "Sub-group", "grp_3": "Minor group",
        "group_generic": "Group",
        "all_grp_1": "— All major groups —", "all_grp_2": "— All sub-groups —",
        "all_grp_3": "— All minor groups —", "all_generic": "— All —",
        "occ_search": "Search occupations…",
        "occupations": "Occupation(s)",
        "use_occupation": "Use this occupation →",
        "occ_placeholder": "Choose options",
        "found_n": "{n} match",
        "no_match": "No match.",
        "browse_title": "Browse occupation codes",
        "search": "Search", "clear": "Clear all",
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
        "browser_intro": "Drill down the classification — pick a level and the next appears.",
        "browser_results": "results",
        "browser_blank": "— select —",
        "browser_pick": "Pick a level on the left to drill down.",
        "browser_hierarchy": "Hierarchy",
        "browser_leaf": "Detailed occupation — no sub-levels.",
        "brlvl_1": "Major group (1-digit)",
        "brlvl_2": "Sub-major group (2-digit)",
        "brlvl_3": "Minor group (3-digit)",
        "brlvl_4": "Unit group / occupation (4-digit)",
    },
    "NO": {
        "brand": "Salary Explorer",
        "sector": "Sektor",
        "sex": "Kjønn",
        "total": "Totalt", "women": "Kvinner", "men": "Menn",
        "year_range": "Årsintervall",
        "grp_1": "Yrkesfelt", "grp_2": "Yrkesområde", "grp_3": "Yrkesgruppe",
        "group_generic": "Gruppe",
        "all_grp_1": "— Alle yrkesfelt —", "all_grp_2": "— Alle yrkesområder —",
        "all_grp_3": "— Alle yrkesgrupper —", "all_generic": "— Alle —",
        "occ_search": "Søk yrker…",
        "occupations": "Yrke(r)",
        "use_occupation": "Bruk dette yrket →",
        "occ_placeholder": "Velg",
        "found_n": "{n} treff",
        "no_match": "Ingen treff.",
        "browse_title": "Bla gjennom yrkeskoder",
        "search": "Søk", "clear": "Tøm alt",
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
        "browser_intro": "Bor deg ned i klassifiseringen — velg et nivå, så vises det neste.",
        "browser_results": "treff",
        "browser_blank": "— velg —",
        "browser_pick": "Velg et nivå til venstre for å bore ned.",
        "browser_hierarchy": "Hierarki",
        "browser_leaf": "Detaljert yrke — ingen undernivåer.",
        "brlvl_1": "Yrkesfelt (1-siffer)",
        "brlvl_2": "Yrkesområde (2-siffer)",
        "brlvl_3": "Yrkesgruppe (3-siffer)",
        "brlvl_4": "Yrke (4-siffer)",
    },
}


def t(cfg, key: str, lang: str = "EN", default: str | None = None) -> str:
    """Resolve a UI string for ``key`` in ``lang`` (see module docstring)."""
    ci = getattr(cfg, "i18n", None) or {}
    for src in (ci.get(lang), ci.get("EN"), UI.get(lang), UI.get("EN")):
        if src and key in src:
            return src[key]
    return default if default is not None else key
