"""France — Salary Explorer page (INSEE Melodi).

v1: occupation explorer — mean net FTE monthly salary for ~361 detailed
PCS-ESE professions × sex × age (private sector; public mirror, 74 professions).

Session-state rule: this page shares one Streamlit session with the Swedish
app, so EVERY widget/session key here is prefixed "fr_".

Unlike Sweden (one SCB query per search → explicit Search button), the whole
French detail table arrives in a single cached Melodi pull, so all filters are
fully reactive — no search-commit pattern needed.
"""
import pandas as pd
import os
import re

import plotly.graph_objects as go
import streamlit as st

import france_data as fd
import theme
import auth

_FR_LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "logo_france.png")   # blue-white-red bars

# ── Translations ───────────────────────────────────────────────────────────────
T = {
    "FR": {
        "title": "Explorateur de salaires — France",
        "caption": "Salaire net mensuel moyen en équivalent temps plein (EQTP) · Source : INSEE (DADS/DSN via l'API Melodi)",
        "lang": "Language / Langue",
        "sector": "Secteur",
        "sectors": {"private": "Secteur privé", "public": "Fonction publique"},
        "group": "1. Groupe socioprofessionnel",
        "all_groups": "— Tous les groupes —",
        "category": "2. Catégorie",
        "all_cats": "— Toutes les catégories —",
        "occ": "3. Profession(s)",
        "search_ph": "Rechercher une profession…",
        "search_label": "🔍 Rechercher une profession",
        "found_n": "{n} profession(s) trouvée(s)",
        "no_match": "Aucune profession ne correspond.",
        "clear": "✕ Tout effacer",
        "btn_search": "🔍 Rechercher",
        "year_range": "Plage d'années",
        "year_range_note": "Détermine les années affichées dans la distribution et l'évolution des salaires. Le salaire moyen par profession n'est publié que pour {year}.",
        "select_prompt": "Sélectionnez une ou plusieurs professions puis appuyez sur 🔍 Rechercher — ou explorez les codes PCS ci-dessous.",
        "explorer_title": "Professions ({n})",
        "explorer_hint": "Sélectionnez une ou plusieurs professions à gauche pour le détail par âge et par sexe — ou explorez le tableau.",
        "col_code": "Code",
        "col_name": "Profession",
        "col_mean": "Salaire moyen (€/mois)",
        "col_count": "Effectifs (EQTP)",
        "col_gap": "Écart F/H (%)",
        "detail_year": "Données {year}",
        "m_mean": "Salaire moyen",
        "m_count": "Effectifs (EQTP)",
        "m_women": "Femmes",
        "m_men": "Hommes",
        "m_gap": "Écart F/H",
        "age_title": "Salaire moyen par âge",
        "age_axis": "Tranche d'âge",
        "sal_axis": "Salaire net mensuel moyen (€ EQTP)",
        "cmp_title": "Comparaison des professions sélectionnées",
        "sex_total": "Ensemble", "sex_f": "Femmes", "sex_m": "Hommes",
        "all_ages": "Tous âges",
        "raw": "Tableau de données",
        "no_data": "Pas de données pour cette sélection.",
        "err_api": "L'API INSEE Melodi est injoignable pour le moment — réessayez dans un instant.",
        "note_v1": "",
        "tab_explorer": "🔎 Explorateur",
        "tab_dist": "📊 Distribution des salaires",
        "tab_trend": "📈 Évolution",
        "tab_pct": "📊 Distribution par centile",
        "tab_calc": "💰 Où je me situe ?",
        "tab_lead": "🏆 Classement",
        "tab_age": "👤 Par âge",
        "show_high_pct": "Afficher P95 / P99",
        "trend_title": "Évolution des salaires dans le temps",
        "lead_title": "Classement — salaire moyen",
        "lead_hint": "Toutes les professions du secteur, classées par salaire moyen.",
        "age_select_prompt": "Sélectionnez une profession (menu de gauche ou 📖 Codes PCS) pour voir le détail par âge et par sexe.",
        "dist_title": "Distribution des salaires par percentile",
        "dist_caption": "Salaire net mensuel EQTP en euros constants {base} · {sector}",
        "dist_scope_note": "Cette courbe montre la distribution pour **l'ensemble des salariés** ({sector}) — l'INSEE ne publie pas de percentiles de salaire par profession détaillée. Les ★ indiquent où se situe le salaire **moyen** de chaque profession sélectionnée dans cette distribution.",
        "measures_shown": "Percentiles affichés",
        "dist_year": "Année",
        "sex_label": "Sexe",
        "wktime_label": "Temps de travail",
        "wk_all": "Tous", "wk_ft": "Temps complet",
        "x_pct": "Percentile",
        "y_const": "Salaire net mensuel (€ constants {base})",
        "dist_curve": "Distribution",
        "occ_marker": "Moyenne · {name}",
        "whereami": "💰 Où je me situe ?",
        "my_salary": "Votre salaire net mensuel (EQTP, €)",
        "whereami_result": "Vous gagnez plus qu'environ **{p} %** des salariés ({scope}).",
        "whereami_low": "Votre salaire est sous le 1er décile (moins de 10 % des salariés).",
        "whereami_high": "Votre salaire dépasse le dernier centile publié (top 1 %).",
        "whereami_note": "Position estimée par interpolation entre les centiles publiés — année {year}.",
        "marker_note": "★ = salaire moyen des professions sélectionnées (année {year}).",
        "show_own_dist": "Afficher la distribution propre de la profession (estimation, micro-données {year})",
        "own_dist_name": "{name} (estimation {year})",
        "own_dist_help": (
            "Estimation à partir des micro-données anonymisées de l'INSEE ({year}), en tranches de "
            "rémunération annuelle interpolées linéairement (technique standard pour des données "
            "groupées). Limitée au temps complet, quasi-année pleine. Les tranches supérieures les "
            "plus hautes sont plafonnées par la source (« 50 000 € et plus ») : au-delà de ce seuil, "
            "aucune valeur fiable ne peut être calculée et le point n'est pas affiché."
        ),
        "own_dist_censored": "ℹ️ {n} percentile(s) au-delà du seuil de tranche ouverte (~4 170 €/mois) ne peuvent pas être estimés pour cette profession et ne sont pas affichés.",
        "own_dist_none": "Aucune estimation disponible pour cette profession (échantillon trop restreint dans les micro-données).",
        "trend_mode": "Séries",
        "trend_dist": "Distribution (ensemble)",
        "trend_groups": "Groupes socioprofessionnels (moyennes)",
        "trend_caption": "Euros constants — l'inflation est déjà déduite (une courbe qui monte = gain de pouvoir d'achat).",
        "trend_range": "Période",
        "no_dist": "Distribution indisponible pour cette sélection.",
        "groups_private_only": "Les séries par groupe ne sont publiées que pour le secteur privé.",
        "measure_label": "Mesure",
        "unit_growth": "Croissance vs inflation",
        "unit_view_help": (
            "**Nominal (€ courants)** — le salaire tel qu'il était exprimé chaque année, "
            "sans correction de l'inflation.\n\n"
            "**Croissance vs inflation** — croissance du salaire et inflation (IPC), toutes deux "
            "indexées sur la première année affichée (0 %). Si la ligne du salaire reste au-dessus "
            "de celle de l'inflation, le pouvoir d'achat a progressé.\n\n"
            "**Réel (€ constants)** — le salaire corrigé de l'inflation, en euros constants."
        ),
        "sal_growth_label": "Croissance du salaire",
        "cpi_label": "Inflation (IPC)",
        "growth_axis": "Évolution depuis {base} (%)",
        "fr_trend_summary": "**{base}→{last}:** salaire {sal:+.0f}% · inflation {infl:+.0f}% → **réel {real:+.0f}%**",
        "own_group_note": "Évolution du groupe socioprofessionnel **{name}** — la profession sélectionnée en fait partie. L'INSEE ne publie pas d'historique de salaire par profession détaillée.",
        "ensemble": "Ensemble",
        "unit_label": "Unité",
        "unit_real": "Réel (€ constants)",
        "unit_nominal": "Nominal (€ courants)",
        "y_nominal": "Salaire net mensuel (€ courants)",
        "trend_caption_nom": "Euros courants — valeurs de l'époque, non corrigées de l'inflation (IPC INSEE).",
        "no_cpi": "ℹ️ IPC indisponible — affichage en euros constants.",
        "tab_regions": "🗺️ Régions",
        "reg_title": "Salaire moyen par région",
        "reg_caption": "Secteur privé uniquement (données locales BTS) · Année {year}",
        "reg_group": "Groupe socioprofessionnel",
        "reg_france": "France entière",
        "grp_1t3": "Cadres et indépendants salariés (groupes 1–3)",
        "reg_axis": "Salaire net mensuel moyen (€ EQTP)",
        "browse_btn": "📖 Codes PCS",
        "browse_title": "Parcourir les codes PCS (professions)",
        "browse_intro": "Descendez la hiérarchie PCS pour trouver un code. Les libellés proviennent de la nomenclature officielle INSEE PCS-ESE 2017.",
        "browse_search": "🔍 Rechercher un code, une profession…",
        "browse_results": "{n} résultat(s)",
        "browse_l1": "Groupe socioprofessionnel (1 chiffre)",
        "browse_l2": "Catégorie (2 chiffres)",
        "browse_l4": "Profession (4 chiffres)",
        "browse_blank": "—",
        "browse_pick_prompt": "Choisissez un niveau à gauche (ou cherchez ci-dessus) pour voir le détail.",
        "browse_back": "← Retour à l'application",
        "browse_use": "Utiliser cette profession →",
        "browse_hierarchy": "Position dans la hiérarchie",
        "browse_snapshot": "Salaire moyen · {year}",
        "browse_no_salary": "Niveau d'agrégation — pas de salaire détaillé (voir les professions à 4 chiffres).",
        "browse_en_note": "⚠️ Traduit automatiquement du français — la nomenclature officielle est en français.",
    },
    "EN": {
        "title": "Salary Explorer — France",
        "caption": "Mean net monthly salary, full-time equivalent (FTE) · Source: INSEE (DADS/DSN via the Melodi API)",
        "lang": "Language / Langue",
        "sector": "Sector",
        "sectors": {"private": "Private sector", "public": "Public service"},
        "group": "1. Socio-professional group",
        "all_groups": "— All groups —",
        "category": "2. Category",
        "all_cats": "— All categories —",
        "occ": "3. Occupation(s)",
        "search_ph": "Search occupations…",
        "search_label": "🔍 Search occupation",
        "found_n": "{n} occupation(s) found",
        "no_match": "No occupation matches.",
        "clear": "✕ Clear all",
        "btn_search": "🔍 Search",
        "year_range": "Year range",
        "year_range_note": "Sets the years shown in the distribution and salary trend. Mean salary per occupation is only published for {year}.",
        "select_prompt": "Select one or more occupations then press 🔍 Search — or explore the PCS codes below.",
        "explorer_title": "Occupations ({n})",
        "explorer_hint": "Pick one or more occupations on the left for the age/sex detail — or explore the table.",
        "col_code": "Code",
        "col_name": "Occupation",
        "col_mean": "Mean salary (€/month)",
        "col_count": "Headcount (FTE)",
        "col_gap": "F/M gap (%)",
        "detail_year": "Data {year}",
        "m_mean": "Mean salary",
        "m_count": "Headcount (FTE)",
        "m_women": "Women",
        "m_men": "Men",
        "m_gap": "F/M gap",
        "age_title": "Mean salary by age",
        "age_axis": "Age band",
        "sal_axis": "Mean net monthly salary (€ FTE)",
        "cmp_title": "Selected occupations compared",
        "sex_total": "Total", "sex_f": "Women", "sex_m": "Men",
        "all_ages": "All ages",
        "raw": "Raw data table",
        "no_data": "No data for this selection.",
        "err_api": "The INSEE Melodi API is unreachable right now — try again in a moment.",
        "note_v1": "",
        "tab_explorer": "🔎 Explorer",
        "tab_dist": "📊 Wage distribution",
        "tab_trend": "📈 Trend",
        "tab_pct": "📊 Percentile distribution",
        "tab_calc": "💰 Where do I stand?",
        "tab_lead": "🏆 Leaderboard",
        "tab_age": "👤 By age",
        "show_high_pct": "Show P95 / P99",
        "trend_title": "Salary trend over time",
        "lead_title": "Leaderboard — mean salary",
        "lead_hint": "All occupations in the sector, ranked by mean salary.",
        "age_select_prompt": "Select an occupation (left menu or 📖 PCS guide) to see the age and sex breakdown.",
        "dist_title": "Salary distribution by percentile",
        "dist_caption": "Net monthly FTE salary in constant {base} euros · {sector}",
        "dist_scope_note": "This curve shows the distribution for **all employees** ({sector}) — INSEE does not publish salary percentiles per detailed occupation. The ★ marks show where each selected occupation's **mean** salary falls within that distribution.",
        "measures_shown": "Percentiles shown",
        "dist_year": "Year",
        "sex_label": "Sex",
        "wktime_label": "Working time",
        "wk_all": "All", "wk_ft": "Full-time",
        "x_pct": "Percentile",
        "y_const": "Net monthly salary (constant {base} €)",
        "dist_curve": "Distribution",
        "occ_marker": "Mean · {name}",
        "whereami": "💰 Where do I stand?",
        "my_salary": "Your net monthly salary (FTE, €)",
        "whereami_result": "You earn more than about **{p}%** of employees ({scope}).",
        "whereami_low": "Your salary is below the 1st decile (bottom 10% of employees).",
        "whereami_high": "Your salary is above the highest published centile (top 1%).",
        "whereami_note": "Position estimated by interpolating between published centiles — year {year}.",
        "marker_note": "★ = mean salary of the selected occupations (year {year}).",
        "show_own_dist": "Show the occupation's own distribution (estimate, {year} microdata)",
        "own_dist_name": "{name} ({year} estimate)",
        "own_dist_help": (
            "Estimated from INSEE's anonymized microdata ({year}), linearly interpolated within "
            "annual pay bands (a standard technique for grouped data). Limited to full-time, "
            "near-full-year workers. The highest pay bands are capped by the source itself "
            "(\"€50,000 and above\") — beyond that threshold no reliable value can be computed, "
            "so the point is simply not shown."
        ),
        "own_dist_censored": "ℹ️ {n} percentile(s) above the open-band threshold (~€4,170/month) cannot be estimated for this occupation and are not shown.",
        "own_dist_none": "No estimate available for this occupation (sample too small in the microdata).",
        "trend_mode": "Series",
        "trend_dist": "Distribution (all employees)",
        "trend_groups": "Socio-professional groups (means)",
        "trend_caption": "Constant euros — inflation is already removed (a rising line = real purchasing-power gain).",
        "trend_range": "Period",
        "no_dist": "No distribution available for this selection.",
        "groups_private_only": "Group series are only published for the private sector.",
        "measure_label": "Measure",
        "unit_growth": "Growth vs inflation",
        "unit_view_help": (
            "**Nominal (current €)** — the salary as it was reported each year, "
            "not adjusted for inflation.\n\n"
            "**Growth vs inflation** — salary growth and consumer-price inflation (IPC), both "
            "indexed to the first year shown (0 %). If the salary line stays above the inflation "
            "line, pay has outpaced rising prices.\n\n"
            "**Real (constant €)** — the salary adjusted for inflation, in constant euros."
        ),
        "sal_growth_label": "Salary growth",
        "cpi_label": "Inflation (CPI)",
        "growth_axis": "Change from {base} (%)",
        "fr_trend_summary": "**{base}→{last}:** salary {sal:+.0f}% · inflation {infl:+.0f}% → **real {real:+.0f}%**",
        "own_group_note": "Trend for the **{name}** socio-professional group — the selected occupation belongs to it. INSEE does not publish salary history per detailed occupation.",
        "ensemble": "All employees",
        "unit_label": "Unit",
        "unit_real": "Real (constant €)",
        "unit_nominal": "Nominal (current €)",
        "y_nominal": "Net monthly salary (current €)",
        "trend_caption_nom": "Current euros — values of the day, not inflation-adjusted (INSEE CPI).",
        "no_cpi": "ℹ️ CPI unavailable — showing constant euros.",
        "tab_regions": "🗺️ Regions",
        "reg_title": "Mean salary by région",
        "reg_caption": "Private sector only (BTS local data) · Year {year}",
        "reg_group": "Socio-professional group",
        "reg_france": "Whole of France",
        "grp_1t3": "Managers, professionals & self-employed (groups 1–3)",
        "reg_axis": "Mean net monthly salary (€ FTE)",
        "browse_btn": "📖 PCS guide",
        "browse_title": "Browse PCS occupation codes",
        "browse_intro": "Drill down the PCS hierarchy to find a code. Labels are the official INSEE PCS-ESE 2017 nomenclature.",
        "browse_search": "🔍 Search codes, occupations…",
        "browse_results": "{n} result(s)",
        "browse_l1": "Socio-professional group (1-digit)",
        "browse_l2": "Category (2-digit)",
        "browse_l4": "Occupation (4-digit)",
        "browse_blank": "—",
        "browse_pick_prompt": "Pick a level on the left (or search above) to see the detail.",
        "browse_back": "← Back to app",
        "browse_use": "Use this occupation →",
        "browse_hierarchy": "Position in the hierarchy",
        "browse_snapshot": "Mean salary · {year}",
        "browse_no_salary": "Aggregation level — no detailed salary (see the 4-digit occupations).",
        "browse_en_note": "⚠️ Auto-translated from French — the official nomenclature is in French.",
    },
}

SEX_ORDER  = ["_T", "F", "M"]
SEX_COLORS = {"_T": theme.ACCENT, "F": "#8B5FA6", "M": "#4E93C6"}

# Years the long-series (distribution/trend) datasets are known to cover.
# Static like Sweden's own year bound — building the sidebar slider must not
# fetch anything (nothing loads before Search), so this can't be data-derived.
FR_YEARS = [str(y) for y in range(1996, 2025)]


def _age_label(code: str, t: dict) -> str:
    """Human label for Melodi AGE band codes (Y30T39, Y_LT30, Y_GE60, _T)."""
    if code == "_T":
        return t["all_ages"]
    c = code.replace("_", "")          # Y_LT30 → YLT30, Y_GE60 → YGE60
    if c.startswith("YLT"):
        return f"< {c[3:]}"
    if c.startswith("YGE"):
        return f"≥ {c[3:]}"
    if c.startswith("Y") and "T" in c[1:]:
        lo, hi = c[1:].split("T", 1)
        return f"{lo}–{hi}"
    return code


def _age_sort_key(code: str) -> int:
    c = code.replace("_", "")
    digits = "".join(ch for ch in c if ch.isdigit())
    if not digits:
        return 999
    n = int(digits[:2])
    return n - 1 if c.startswith("YLT") else n   # "< 30" sorts before "30–39"


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Same sidebar treatment as the Swedish page. The logo is the only sidebar
    # page-link and doubles as the Home link (no separate nav items).
    st.markdown(theme.SIDEBAR_CSS, unsafe_allow_html=True)
    st.page_link("landing.py", label="Salary Explorer", icon=":material/language:")
    auth.sidebar_identity()   # show who's signed in (avatar + name + role) + Log out
    st.markdown('<div style="height:1px;background:#EEF0F3;margin:12px 0 4px;"></div>',
                unsafe_allow_html=True)

    _fr_lang_prev = st.session_state.get("_fr_lang_val", "English")
    _lang_sel = st.segmented_control(T["EN"]["lang"], ["English", "Français"],
                                     default=_fr_lang_prev, key="fr_lang_seg") or _fr_lang_prev
    st.session_state["_fr_lang_val"] = _lang_sel
    lang = "EN" if _lang_sel == "English" else "FR"
    t = T[lang]

    # Browse-codes guide button, at the top like Sweden's SSYK guide.
    if st.button(t["browse_btn"], use_container_width=True, key="fr_browse_open"):
        for k in ("fr_group", "fr_cat", "fr_search"):
            st.session_state.pop(k, None)
        st.session_state["fr_show_browser"] = True
        st.rerun()

    # Store the sector KEY (not its localized label) so switching language never
    # leaves a stale value that isn't in the options.
    sector = st.selectbox(t["sector"], list(t["sectors"].keys()),
                          format_func=lambda k: t["sectors"][k], key="fr_sector")
    sector_label = t["sectors"][sector]

    # Year range — defines what data to pull for the distribution/trend charts,
    # like Sweden's slider. Default: last 3 years (matches Sweden's default).
    yr_from, yr_to = st.select_slider(t["year_range"], options=FR_YEARS,
                                      value=(FR_YEARS[-3], FR_YEARS[-1]),
                                      key="fr_year_range")
    selected_years_fr = tuple(y for y in FR_YEARS if yr_from <= y <= yr_to)
    st.caption(t["year_range_note"].format(year=FR_YEARS[-1]))

    labels = fd.load_pcs_labels()

    # Drill-down: group (1) → category (2) → professions (4). Options are CODES;
    # format_func renders the localized name (labels follow the language and the
    # stored value stays valid across a switch).
    group_codes = sorted(c for c in labels if len(c) == 1)
    g_code = st.selectbox(
        t["group"], [None] + group_codes, key="fr_group",
        format_func=lambda c: t["all_groups"] if c is None
        else f"{c} – {fd.pcs_name(c, lang)}")

    c_code = None
    if g_code:
        cat_codes = sorted(c for c in labels if len(c) == 2 and c.startswith(g_code))
        c_code = st.selectbox(
            t["category"], [None] + cat_codes, key="fr_cat",
            format_func=lambda c: t["all_cats"] if c is None
            else f"{c} – {fd.pcs_name(c, lang)}")

    # Occupation pool comes from the LABELS file (not the salary data) — like
    # Sweden's cached occupations list — so nothing is fetched to build the menu.
    prefix = c_code or g_code or ""
    pool_codes = sorted(c for c in labels if len(c) == 4 and c.startswith(prefix))
    search = st.text_input(re.sub(r"^\W+", "", t["search_label"]).strip(),
                           placeholder=t["search_ph"], key="fr_search")
    if search.strip():
        s = search.strip().lower()
        pool_codes = [c for c in pool_codes
                      if s in fd.pcs_name(c, lang).lower() or s in c.lower()]
        st.caption(t["found_n"].format(n=len(pool_codes)) if pool_codes
                   else t["no_match"])

    occ_opts = [f"{fd.pcs_name(c, lang)}  ({c})" for c in pool_codes]
    sel_labels = st.multiselect(t["occ"], occ_opts, max_selections=6, key="fr_occ")
    sel_codes = [l.rsplit("(", 1)[-1].rstrip(")") for l in sel_labels]

    def _fr_clear():
        for k in ("fr_group", "fr_cat", "fr_search", "fr_occ", "fr_query"):
            st.session_state.pop(k, None)
        st.session_state["fr_show_browser"] = True

    c_search, c_clear = st.columns(2)
    with c_search:
        search_clicked = st.button(t["btn_search"], type="primary",
                                   use_container_width=True, key="fr_do_search")
    with c_clear:
        st.button(t["clear"], use_container_width=True, on_click=_fr_clear)

# ── Commit the query on Search — the right side renders ONLY from this ───────
# Exactly like Sweden: nothing on the right loads until Search commits a query.
if search_clicked and sel_codes:
    st.session_state["fr_query"] = {"sector": sector, "codes": tuple(sel_codes)}
    st.session_state["fr_show_browser"] = False

_q = st.session_state.get("fr_query", {})
query_codes  = _q.get("codes", ())
query_sector = _q.get("sector", sector)
query_sector_label = t["sectors"].get(query_sector, sector_label)

# ── Header (design-system.md §4: eyebrow + H1 + source). The signed-in identity
# lives in the sidebar (auth.sidebar_identity), so there's no header avatar.
st.markdown(f"""
<div style="margin-bottom:6px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
              letter-spacing:.16em;color:#0A63A6;margin-bottom:10px;">OFFICIAL STATISTICS · FRANCE</div>
  <h1 style="margin:0;font-size:34px;font-weight:800;letter-spacing:-.025em;color:#0C1119;line-height:1.05;">{t['title']}</h1>
  <p style="margin:8px 0 0;font-size:14px;color:#7A828F;">{t['caption']}</p>
</div>
""", unsafe_allow_html=True)

# ── Landing: the code browser (no data loaded) until a query is committed ────
# Mirrors Sweden's SSYK guide/landing: cascading dropdowns + global search + a
# detail panel — built purely from the labels file, so nothing is fetched. Pick
# an occupation and "Use this occupation" commits the query (like Sweden).
_fr_view = st.empty()  # single mount point so the code browser clears on chart runs
if st.session_state.get("fr_show_browser") or not query_codes:
    with _fr_view.container():
        st.subheader(t["browse_title"])
        st.caption(t["browse_intro"])

        def _br_fmt(code):
            return f"{code} · {fd.pcs_name(code, lang)}"

        def _br_panel(code):
            if not code:
                st.info(t["browse_pick_prompt"])
                return
            st.markdown(f"#### {code} · {fd.pcs_name(code, lang)}")
            if lang == "EN":
                st.caption(t["browse_en_note"])
            crumbs = [c for c in (code[:1], code[:2]) if c in labels and c != code]
            if crumbs:
                st.caption(f"**{t['browse_hierarchy']}:** "
                           + " › ".join(fd.pcs_name(c, lang) for c in crumbs))
            if len(code) < 4:
                st.caption(t["browse_no_salary"])

        def _fr_use_occupation(code, sctr, language):
            # on_click callback (runs before widgets are instantiated): commit the
            # query and reflect the pick in the sidebar multiselect.
            st.session_state["fr_query"] = {"sector": sctr, "codes": (code,)}
            st.session_state["fr_show_browser"] = False
            for k in ("fr_group", "fr_cat", "fr_search"):
                st.session_state.pop(k, None)
            st.session_state["fr_occ"] = [f"{fd.pcs_name(code, language)}  ({code})"]

        q = st.text_input(t["browse_search"], key="fr_br_search",
                          placeholder=t["browse_search"], label_visibility="collapsed")
        use_code = None
        if q.strip():
            qs = q.strip().lower()
            matches = [c for c, v in labels.items()
                       if qs in c.lower() or qs in v.get("fr", "").lower()
                       or qs in (v.get("en") or "").lower()]
            matches.sort(key=lambda c: (len(c), c))
            if matches:
                sel = st.selectbox(t["browse_results"].format(n=len(matches)),
                                   matches[:300], format_func=_br_fmt, key="fr_br_res")
                _br_panel(sel)
                use_code = sel if len(sel) == 4 else None
            else:
                st.info(t["no_match"])
        else:
            BLANK = "__none__"

            def _br_pick(label, opts, key):
                v = st.selectbox(label, [BLANK] + opts, key=key,
                                 format_func=lambda c: t["browse_blank"] if c == BLANK
                                 else _br_fmt(c))
                return None if v == BLANK else v

            nav, panel = st.columns([1, 1.3])
            with nav:
                l1 = sorted(c for c in labels if len(c) == 1)
                s1 = _br_pick(t["browse_l1"], l1, "fr_br_l1")
                l2 = sorted(c for c in labels if len(c) == 2 and c.startswith(s1)) if s1 else []
                s2 = _br_pick(t["browse_l2"], l2, "fr_br_l2") if s1 else None
                l4 = sorted(c for c in labels if len(c) == 4 and c.startswith(s2)) if s2 else []
                s4 = _br_pick(t["browse_l4"], l4, "fr_br_l4") if s2 else None
                current = s4 or s2 or s1
            with panel:
                _br_panel(current)
            use_code = s4

        st.divider()
        st.button(t["browse_use"], key="fr_br_use", type="primary",
                  use_container_width=True, disabled=use_code is None,
                  on_click=_fr_use_occupation, args=(use_code, sector, lang))
    st.stop()

# ── Data — fetched ONLY now, after Search committed a query ──────────────────
try:
    with st.spinner("INSEE…"):
        df = fd.fetch_detail_salaries(query_sector)
except Exception:
    st.error(t["err_api"])
    st.stop()
year = df["year"].max()
det  = df[df["pcs"].str.len() == 4]
tot  = det[(det["sex"] == "_T") & (det["age"] == "_T")].set_index("pcs")
st.caption(t["detail_year"].format(year=year) + f" · {query_sector_label}")


def _gap_pct(code: str):
    """Women vs men mean-salary gap in % for one occupation (all ages)."""
    rows = det[(det["pcs"] == code) & (det["age"] == "_T")]
    f = rows[rows["sex"] == "F"]["mean_salary"]
    m = rows[rows["sex"] == "M"]["mean_salary"]
    if len(f) and len(m) and pd.notna(f.iloc[0]) and pd.notna(m.iloc[0]) and m.iloc[0]:
        return (f.iloc[0] / m.iloc[0] - 1) * 100
    return None


def _num(v):
    return f"{v:,.0f}".replace(",", " ") if v is not None and pd.notna(v) else "–"


def _ranked_table(codes) -> pd.DataFrame:
    """Ranked occupation table (mean salary desc) for a list of 4-digit PCS codes."""
    rows = []
    for c in codes:
        if c not in tot.index:
            continue
        r = tot.loc[c]
        gap = _gap_pct(c)
        rows.append({
            t["col_code"]:  c,
            t["col_name"]:  fd.pcs_name(c, lang),
            t["col_mean"]:  round(r["mean_salary"]) if pd.notna(r["mean_salary"]) else None,
            t["col_count"]: round(r["headcount"]) if pd.notna(r["headcount"]) else None,
            t["col_gap"]:   round(gap, 1) if gap is not None else None,
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(t["col_mean"], ascending=False,
                                          na_position="last")


def _sex_radio(label_key: str, widget_key: str) -> str:
    """Sex picker returning the Melodi code (_T/F/M)."""
    names = {t["sex_total"]: "_T", t["sex_f"]: "F", t["sex_m"]: "M"}
    return names[st.radio(t[label_key], list(names), horizontal=True, key=widget_key)]


def _wk_radio(widget_key: str) -> str:
    """Working-time picker returning the Melodi code (_T/FT)."""
    names = {t["wk_all"]: "_T", t["wk_ft"]: "FT"}
    return names[st.radio(t["wktime_label"], list(names), horizontal=True, key=widget_key)]


def _pos_on_curve(salary: float, pts: list[tuple[int, float]]):
    """Percentile position of a salary on a centile curve [(pct, value)…].
    Returns float pct, or 'low'/'high' when outside the published range."""
    if salary < pts[0][1]:
        return "low"
    if salary > pts[-1][1]:
        return "high"
    for (p1, v1), (p2, v2) in zip(pts, pts[1:]):
        if v1 <= salary <= v2:
            return p1 + (p2 - p1) * (salary - v1) / ((v2 - v1) or 1)
    return "high"


# The distribution, calculator and trend all use the long-series pull; the
# derived centile frame is computed once here. The sidebar Year range is a
# hard filter for the Trend and "Where do I stand?" tabs — exactly like Sweden.
# The Percentile Distribution SNAPSHOT (with the occupation ★ marker) is
# pinned to its own latest year instead: it must match the occupation's mean
# (single-year data), so it stays fixed regardless of the slicer.
try:
    sl_full = fd.fetch_series_longues(sector)
    sl = sl_full[sl_full["year"].isin(selected_years_fr)]
    sl_error = False
except Exception:
    sl_full, sl, sl_error = None, None, True
if not sl_error:
    dist_all = sl_full[sl_full["centile"].map(fd.centile_pct).notna()].copy()
    dist_all["pct"] = dist_all["centile"].map(fd.centile_pct)
    snapshot_years = sorted(dist_all["year"].unique(), reverse=True)
    snapshot_year = snapshot_years[0] if snapshot_years else year

    dist = sl[sl["centile"].map(fd.centile_pct).notna()].copy()
    dist["pct"] = dist["centile"].map(fd.centile_pct)
    dist_years = sorted(dist["year"].unique(), reverse=True)
    dist_base = dist_years[0] if dist_years else year

# Tabs mirror the Swedish page as closely as the French data allows. The code
# browser is reached from the sidebar (📖 PCS guide), so there is no explorer tab.
_notab = lambda s: re.sub(r"^\W+", "", s).strip()   # strip the leading emoji
tab_pct, tab_calc, tab_lead, tab_age, tab_reg = st.tabs(
    [_notab(x) for x in
     (t["tab_pct"], t["tab_calc"], t["tab_lead"], t["tab_age"], t["tab_regions"])])

# Canonical percentile order — P95/P99 available but NOT shown by default,
# and re-adding a removed chip always snaps back to this order (Sweden's fix).
PCT_ORDER = [10, 25, 50, 75, 90, 95, 99]


def _pct_label(p: int, lang: str) -> str:
    if p == 50:
        return "Médiane (P50)" if lang == "FR" else "Median (P50)"
    return f"P{p}"


# ── Tab 1: percentile distribution + salary trend (mirrors Sweden's tab 1) ────
with tab_pct:
    if sl_error:
        st.error(t["err_api"])
    else:
        st.subheader(t["dist_title"])
        st.caption(t["dist_caption"].format(base=snapshot_year, sector=query_sector_label))
        # No Year selector here: this snapshot must match the occupation's mean
        # (which INSEE only publishes for one year), so it's pinned to that year
        # regardless of the sidebar Year range — unlike the Trend section below.
        c2, c3 = st.columns(2)
        with c2:
            d_sex = _sex_radio("sex_label", "fr_dist_sex")
        with c3:
            d_wk = _wk_radio("fr_dist_wk")

        # Chip multiselect, canonical order enforced on every change — mirrors
        # Sweden's "Measures shown" fix so re-adding a chip restores its slot.
        pct_opts = [_pct_label(p, lang) for p in PCT_ORDER]
        pct_default = [_pct_label(p, lang) for p in PCT_ORDER if p <= 90]

        def _sort_pct_chips():
            cur = st.session_state.get("fr_pct_measures", [])
            order = {lbl: i for i, lbl in enumerate(pct_opts)}
            st.session_state["fr_pct_measures"] = sorted(cur, key=lambda m: order.get(m, 99))

        shown = st.multiselect(t["measures_shown"], options=pct_opts,
                               default=pct_default, key="fr_pct_measures",
                               on_change=_sort_pct_chips)
        shown = [lbl for lbl in pct_opts if lbl in (shown or pct_opts)]
        shown_pcts = [PCT_ORDER[pct_opts.index(lbl)] for lbl in shown]

        micro_pcts = fd.load_microdata_percentiles()
        micro_occs = micro_pcts.get("occupations", {})
        micro_year = micro_pcts.get("year", "2023")
        show_own = st.checkbox(t["show_own_dist"].format(year=micro_year),
                               value=True, key="fr_show_own_dist",
                               help=t["own_dist_help"].format(year=micro_year))

        sub = dist_all[(dist_all["year"] == snapshot_year) & (dist_all["sex"] == d_sex)
                       & (dist_all["wktime"] == d_wk)].sort_values("pct")
        pts = [(int(p), float(v)) for p, v in
               zip(sub["pct"], sub["salary_const_eur"]) if pd.notna(v)]
        pts = [pv for pv in pts if pv[0] in shown_pcts]
        if not pts:
            st.info(t["no_dist"])
        else:
            fig = go.Figure(go.Scatter(
                x=[p for p, _ in pts], y=[v for _, v in pts],
                mode="lines+markers", name=t["dist_curve"],
                line=dict(color=theme.ACCENT, width=2.5),
                marker=theme.series_marker(theme.ACCENT)))
            # Selected occupations' means: a red star + a dashed horizontal
            # reference line spanning the chart, so the level is easy to read
            # against the curve even when it falls outside the P10–P90 range.
            markers_added = False
            n_censored = 0
            any_own_dist = False
            for code in query_codes:
                if code in tot.index and pd.notna(tot.loc[code, "mean_salary"]):
                    mv  = float(tot.loc[code, "mean_salary"])
                    pos = _pos_on_curve(mv, pts)
                    px  = {"low": pts[0][0], "high": pts[-1][0]}.get(pos, pos)
                    fig.add_hline(y=mv, line=dict(color=theme.MEAN, width=1.5, dash="dot"))
                    fig.add_trace(go.Scatter(
                        x=[px], y=[mv], mode="markers",
                        name=t["occ_marker"].format(name=fd.pcs_name(code, lang)[:40]),
                        marker=dict(symbol="star", size=16, color=theme.MEAN,
                                   line=dict(width=1, color="#9a2f33"))))
                    markers_added = True

                # Toggleable layer: the occupation's OWN estimated distribution
                # (band-interpolated microdata) — real per-occupation points,
                # not the all-employee curve. Only uncensored percentiles plot.
                if show_own:
                    entry = micro_occs.get(code)
                    if entry:
                        any_own_dist = True
                        own_pts = [(p, v) for p, v in
                                   ((int(k), val) for k, val in entry["pct"].items())
                                   if v is not None and p in shown_pcts]
                        n_censored += sum(1 for p in shown_pcts
                                          if entry["pct"].get(str(p)) is None)
                        if own_pts:
                            own_pts.sort()
                            fig.add_trace(go.Scatter(
                                x=[p for p, _ in own_pts], y=[v for _, v in own_pts],
                                mode="lines+markers",
                                name=t["own_dist_name"].format(
                                    name=fd.pcs_name(code, lang)[:35], year=micro_year),
                                line=dict(color="#5B8A72", width=2, dash="dash"),
                                marker=dict(size=7, symbol="diamond")))
            if show_own and query_codes and not any_own_dist:
                st.caption(t["own_dist_none"])
            elif show_own and n_censored:
                st.caption(t["own_dist_censored"].format(n=n_censored))
            fig.update_layout(
                height=380, xaxis_title=t["x_pct"],
                yaxis_title=t["y_const"].format(base=snapshot_year),
                xaxis=dict(tickmode="array", tickvals=[p for p, _ in pts]),
                margin=dict(t=30, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
            theme.style_fig(fig)
            st.plotly_chart(fig, use_container_width=True, key="fr_dist_chart")
            if markers_added:
                st.caption(t["marker_note"].format(year=snapshot_year))
        st.caption(t["dist_scope_note"].format(sector=query_sector_label.lower()))

        # ── Salary trend over time (below the distribution, like Sweden) ──────
        st.divider()
        st.subheader(t["trend_title"])
        has_groups = (sl["pcs"] != "_T").any()
        series_opts = [t["trend_dist"]] + ([t["trend_groups"]] if has_groups else [])

        occ_group = query_codes[0][:1] if query_codes else None

        tc1, tc2 = st.columns([2, 3])
        with tc1:
            tr_series = st.radio(t["trend_mode"], series_opts, key="fr_tr_series")
        with tc2:
            tr_view = st.radio(t["unit_label"],
                               [t["unit_nominal"], t["unit_growth"], t["unit_real"]],
                               horizontal=True, key="fr_tr_view",
                               help=t["unit_view_help"])
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            if tr_series == t["trend_dist"]:
                tr_measure = st.selectbox(
                    t["measure_label"], PCT_ORDER, index=PCT_ORDER.index(50),
                    format_func=lambda p: _pct_label(p, lang), key="fr_tr_pct")
            else:
                grp_opts = [p for p in ("3", "4", "5", "6") if p in set(sl["pcs"])]
                grp_default = occ_group if occ_group in grp_opts else None
                tr_group = st.selectbox(
                    t["measure_label"], ["_T"] + grp_opts,
                    index=(["_T"] + grp_opts).index(grp_default) if grp_default else 0,
                    format_func=lambda p: t["ensemble"] if p == "_T"
                    else fd.pcs_name(p, lang), key="fr_tr_grp")
                if tr_group != "_T" and tr_group == occ_group:
                    st.caption(t["own_group_note"].format(name=fd.pcs_name(tr_group, lang)))
        with c2:
            tr_sex = _sex_radio("sex_label", "fr_tr_sex")
        with c3:
            tr_wk = _wk_radio("fr_tr_wk")
        if not has_groups:
            st.caption(t["groups_private_only"])

        if tr_series == t["trend_dist"]:
            sdf = sl[(sl["centile"] != "_T") & (sl["sex"] == tr_sex)
                     & (sl["wktime"] == tr_wk)].copy()
            sdf["pct"] = sdf["centile"].map(fd.centile_pct)
            sdf = sdf[sdf["pct"] == tr_measure]
        else:
            sdf = sl[(sl["centile"] == "_T") & (sl["sex"] == tr_sex)
                     & (sl["wktime"] == tr_wk) & (sl["pcs"] == tr_group)]
        sdf = sdf.dropna(subset=["salary_const_eur"]).sort_values("year")

        yrs_all = sorted(sdf["year"].unique())
        if not yrs_all:
            st.info(t["no_dist"])
        else:
            y0, y1 = st.select_slider(t["trend_range"], options=yrs_all,
                                      value=(yrs_all[0], yrs_all[-1]),
                                      key="fr_tr_range")
            tbase_yr = yrs_all[-1]   # year the "constant euros" series is priced in
            pairs = [(y, v) for y, v in zip(sdf["year"], sdf["salary_const_eur"])
                     if y0 <= y <= y1]

            cpi = {}
            if tr_view in (t["unit_nominal"], t["unit_growth"]):
                try:
                    cpi = fd.fetch_cpi_annual()
                except Exception:
                    cpi = {}
            cpi_ref = cpi.get(tbase_yr)

            fig = go.Figure()
            if tr_view == t["unit_growth"] and cpi_ref and len(pairs) > 1:
                base_y, base_const = pairs[0]
                base_nominal = base_const * cpi.get(base_y, cpi_ref) / cpi_ref
                years  = [y for y, _ in pairs]
                salary_growth = []
                infl_growth = []
                for y, c in pairs:
                    if cpi.get(y):
                        nom = c * cpi[y] / cpi_ref
                        salary_growth.append((nom / base_nominal - 1) * 100)
                        infl_growth.append((cpi[y] / cpi.get(base_y, cpi_ref) - 1) * 100)
                    else:
                        salary_growth.append(None)
                        infl_growth.append(None)
                fig.add_trace(go.Scatter(
                    x=years, y=salary_growth, mode="lines+markers",
                    name=t["sal_growth_label"],
                    line=dict(color=theme.ACCENT, width=2.5), marker=dict(size=6)))
                fig.add_trace(go.Scatter(
                    x=years, y=infl_growth, mode="lines+markers",
                    name=t["cpi_label"],
                    line=dict(color=theme.MEAN, width=2, dash="dash"), marker=dict(size=6)))
                yaxis = t["growth_axis"].format(base=base_y)
                last_y, last_c = pairs[-1]
                if cpi.get(last_y):
                    sal_chg  = salary_growth[-1]
                    infl_chg = infl_growth[-1]
                    real_chg = ((1 + sal_chg / 100) / (1 + infl_chg / 100) - 1) * 100
                    summary = t["fr_trend_summary"].format(
                        base=base_y, last=last_y, sal=sal_chg, infl=infl_chg, real=real_chg)
                else:
                    summary = None
            else:
                if tr_view == t["unit_nominal"] and not cpi_ref:
                    st.caption(t["no_cpi"])
                    tr_view = t["unit_real"]
                if tr_view == t["unit_nominal"]:
                    years = [y for y, _ in pairs if cpi.get(y)]
                    ys    = [c * cpi[y] / cpi_ref for y, c in pairs if cpi.get(y)]
                    yaxis = t["y_nominal"]
                else:
                    years = [y for y, _ in pairs]
                    ys    = [c for _, c in pairs]
                    yaxis = t["y_const"].format(base=tbase_yr)
                fig.add_trace(go.Scatter(
                    x=years, y=ys, mode="lines+markers",
                    name=(tr_measure if tr_series == t["trend_dist"] else
                          (t["ensemble"] if tr_group == "_T" else fd.pcs_name(tr_group, lang))),
                    line=dict(color=theme.ACCENT, width=2.5), marker=dict(size=6)))
                summary = None

            fig.update_layout(
                height=380, xaxis_title="", yaxis_title=yaxis,
                margin=dict(t=30, b=40), hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
            theme.style_fig(fig)
            st.plotly_chart(fig, use_container_width=True, key="fr_tr_chart")
            if summary:
                st.caption(summary)

# ── Tab 2: where do I stand? (mirrors Sweden's calculator) ────────────────────
with tab_calc:
    if sl_error:
        st.error(t["err_api"])
    else:
        st.subheader(t["whereami"])
        st.caption(t["dist_caption"].format(base=dist_base, sector=query_sector_label))
        c1, c2, c3 = st.columns([1, 2, 2])
        with c1:
            w_year = st.selectbox(t["dist_year"], dist_years, key="fr_w_year")
        with c2:
            w_sex = _sex_radio("sex_label", "fr_w_sex")
        with c3:
            w_wk = _wk_radio("fr_w_wk")
        wsub = dist[(dist["year"] == w_year) & (dist["sex"] == w_sex)
                    & (dist["wktime"] == w_wk)].sort_values("pct")
        wpts = [(int(p), float(v)) for p, v in
                zip(wsub["pct"], wsub["salary_const_eur"]) if pd.notna(v)]
        if not wpts:
            st.info(t["no_dist"])
        else:
            my = st.number_input(t["my_salary"], min_value=0, step=50,
                                 key="fr_my_salary")
            if my:
                pos = _pos_on_curve(float(my), wpts)
                if pos == "low":
                    st.info(t["whereami_low"])
                elif pos == "high":
                    st.success(t["whereami_high"])
                else:
                    st.success(t["whereami_result"].format(
                        p=f"{pos:.0f}", scope=query_sector_label.lower()))
                st.caption(t["whereami_note"].format(year=w_year))

# ── Tab 3: leaderboard (ranked mean salary — mirrors Sweden's leaderboard) ────
with tab_lead:
    st.subheader(t["lead_title"])
    st.caption(t["lead_hint"])
    st.dataframe(_ranked_table(sorted(det["pcs"].unique())),
                 use_container_width=True, hide_index=True, height=560)

# ── Tab 4: by age (occupation detail — mirrors Sweden's "By age") ─────────────
with tab_age:
    if not query_codes:
        st.info(t["age_select_prompt"])
    else:
        for code in query_codes:
            st.subheader(f"{fd.pcs_name(code, lang)}  ({code})")
            rows_t = det[(det["pcs"] == code) & (det["age"] == "_T")]
            mean_t  = rows_t[rows_t["sex"] == "_T"]["mean_salary"]
            count_t = rows_t[rows_t["sex"] == "_T"]["headcount"]
            mean_f  = rows_t[rows_t["sex"] == "F"]["mean_salary"]
            mean_m  = rows_t[rows_t["sex"] == "M"]["mean_salary"]
            gap = _gap_pct(code)

            c1, c2, c3 = st.columns(3)
            c1.metric(t["m_mean"] + " (€)",  _num(mean_t.iloc[0] if len(mean_t) else None))
            c2.metric(t["m_women"] + " (€)", _num(mean_f.iloc[0] if len(mean_f) else None))
            c3.metric(t["m_men"] + " (€)",   _num(mean_m.iloc[0] if len(mean_m) else None))
            c4, c5, _ = st.columns(3)
            c4.metric(t["m_gap"],   f"{gap:+.1f} %" if gap is not None else "–")
            c5.metric(t["m_count"], _num(count_t.iloc[0] if len(count_t) else None))

            by_age = det[(det["pcs"] == code) & (det["age"] != "_T")]
            if not by_age.empty:
                bands = sorted(by_age["age"].unique(), key=_age_sort_key)
                fig = go.Figure()
                for sex in SEX_ORDER:
                    sub = by_age[by_age["sex"] == sex].set_index("age")
                    ys = [sub["mean_salary"].get(b) for b in bands]
                    if all(pd.isna(y) for y in ys):
                        continue
                    fig.add_trace(go.Bar(
                        x=[_age_label(b, t) for b in bands], y=ys,
                        name={"_T": t["sex_total"], "F": t["sex_f"], "M": t["sex_m"]}[sex],
                        marker_color=SEX_COLORS[sex]))
                fig.update_layout(
                    title=t["age_title"], barmode="group", height=320,
                    xaxis_title=t["age_axis"], yaxis_title=t["sal_axis"],
                    margin=dict(t=50, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
                theme.style_fig(fig)
                st.plotly_chart(fig, use_container_width=True,
                                key=f"fr_age_chart_{code}")

        if len(query_codes) > 1:
            st.subheader(t["cmp_title"])
            cmp_rows = [(fd.pcs_name(c, lang), tot.loc[c, "mean_salary"])
                        for c in query_codes if c in tot.index]
            cmp_rows.sort(key=lambda r: (pd.isna(r[1]), r[1]))
            fig = go.Figure(go.Bar(
                x=[v for _, v in cmp_rows], y=[n for n, _ in cmp_rows],
                orientation="h", marker_color=theme.ACCENT))
            fig.update_layout(height=90 + 45 * len(cmp_rows),
                              xaxis_title=t["sal_axis"], margin=dict(t=20, b=40))
            theme.style_fig(fig, horizontal=True)
            st.plotly_chart(fig, use_container_width=True, key="fr_cmp_chart")

        with st.expander(t["raw"]):
            show = det[det["pcs"].isin(query_codes)].copy()
            show.insert(1, t["col_name"], show["pcs"].map(lambda c: fd.pcs_name(c, lang)))
            show["age"] = show["age"].map(lambda a: _age_label(a, t))
            show["sex"] = show["sex"].map(
                {"_T": t["sex_total"], "F": t["sex_f"], "M": t["sex_m"]})
            st.dataframe(show, use_container_width=True, hide_index=True)

# ── Tab 4: mean salary by région (private sector, BTS local data) ─────────────
with tab_reg:
    try:
        reg = fd.fetch_regional_salaries()
        reg_error = False
    except Exception:
        reg_error = True
    if reg_error:
        st.error(t["err_api"])
    else:
        r_year = reg["year"].max()
        st.subheader(t["reg_title"])
        st.caption(t["reg_caption"].format(year=r_year))

        grp_labels = {
            "_T":  t["sex_total"] if lang == "EN" else "Ensemble",
            "1T3": t["grp_1t3"],
            "4":   fd.pcs_name("4", lang),
            "5":   fd.pcs_name("5", lang),
            "6":   fd.pcs_name("6", lang),
        }
        c1, c2 = st.columns([2, 2])
        with c1:
            g_label = st.selectbox(t["reg_group"], list(grp_labels.values()),
                                   key="fr_reg_pcs")
            g_code_r = [k for k, v in grp_labels.items() if v == g_label][0]
        with c2:
            r_sex = _sex_radio("sex_label", "fr_reg_sex")

        sub = reg[(reg["year"] == r_year) & (reg["sex"] == r_sex)
                  & (reg["pcs_group"] == g_code_r)]
        sub = sub.dropna(subset=["mean_salary"])
        if sub.empty:
            st.info(t["no_data"])
        else:
            rows = [(t["reg_france"] if r == "FR"
                     else fd.REGIONS_FR.get(r, r), v, r == "FR")
                    for r, v in zip(sub["region"], sub["mean_salary"])]
            rows.sort(key=lambda x: x[1])
            fig = go.Figure(go.Bar(
                x=[v for _, v, _ in rows], y=[n for n, _, _ in rows],
                orientation="h",
                marker_color=[theme.MEAN if fr else theme.ACCENT
                              for _, _, fr in rows]))
            fig.update_layout(height=110 + 30 * len(rows),
                              xaxis_title=t["reg_axis"],
                              margin=dict(t=20, b=40))
            theme.style_fig(fig, horizontal=True)
            st.plotly_chart(fig, use_container_width=True, key="fr_reg_chart")
            with st.expander(t["raw"]):
                tbl = pd.DataFrame(
                    [{t["col_name"]: n, t["col_mean"]: round(v)}
                     for n, v, _ in reversed(rows)])
                st.dataframe(tbl, use_container_width=True, hide_index=True)

if t["note_v1"]:
    st.caption(t["note_v1"])
