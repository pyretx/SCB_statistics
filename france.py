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
import plotly.graph_objects as go
import streamlit as st

import france_data as fd

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
        "found_n": "{n} profession(s) trouvée(s)",
        "no_match": "Aucune profession ne correspond.",
        "clear": "✕ Tout effacer",
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
        "dist_title": "Distribution des salaires — ensemble des salariés",
        "dist_caption": "Salaire net mensuel EQTP en euros constants {base} · {sector}",
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
        "trend_mode": "Séries",
        "trend_dist": "Distribution (ensemble)",
        "trend_groups": "Groupes socioprofessionnels (moyennes)",
        "trend_caption": "Euros constants — l'inflation est déjà déduite (une courbe qui monte = gain de pouvoir d'achat).",
        "trend_range": "Période",
        "no_dist": "Distribution indisponible pour cette sélection.",
        "groups_private_only": "Les séries par groupe ne sont publiées que pour le secteur privé.",
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
        "browse_btn": "🗂️ Parcourir les codes PCS",
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
        "found_n": "{n} occupation(s) found",
        "no_match": "No occupation matches.",
        "clear": "✕ Clear all",
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
        "dist_title": "Wage distribution — all employees",
        "dist_caption": "Net monthly FTE salary in constant {base} euros · {sector}",
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
        "trend_mode": "Series",
        "trend_dist": "Distribution (all employees)",
        "trend_groups": "Socio-professional groups (means)",
        "trend_caption": "Constant euros — inflation is already removed (a rising line = real purchasing-power gain).",
        "trend_range": "Period",
        "no_dist": "No distribution available for this selection.",
        "groups_private_only": "Group series are only published for the private sector.",
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
        "browse_btn": "🗂️ Browse PCS codes",
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
        "browse_hierarchy": "Position in the hierarchy",
        "browse_snapshot": "Mean salary · {year}",
        "browse_no_salary": "Aggregation level — no detailed salary (see the 4-digit occupations).",
        "browse_en_note": "⚠️ Auto-translated from French — the official nomenclature is in French.",
    },
}

SEX_ORDER  = ["_T", "F", "M"]
SEX_COLORS = {"_T": "#4e79a7", "F": "#e15759", "M": "#76b7b2"}


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
    lang = st.radio(T["EN"]["lang"], ["English", "Français"], horizontal=True,
                    key="fr_lang")
    lang = "EN" if lang == "English" else "FR"
    t = T[lang]

    sector_label = st.selectbox(
        t["sector"], list(t["sectors"].values()), key="fr_sector")
    sector = [k for k, v in t["sectors"].items() if v == sector_label][0]

    labels = fd.load_pcs_labels()

    # Drill-down: group (1 char) → category (2 chars) → professions (4 chars)
    groups = {c: v["fr"] for c, v in labels.items() if len(c) == 1}
    g_opts = [t["all_groups"]] + [f"{c} – {n}" for c, n in sorted(groups.items())]
    g_sel  = st.selectbox(t["group"], g_opts, key="fr_group")
    g_code = None if g_sel == t["all_groups"] else g_sel.split(" – ")[0]

    c_code = None
    if g_code:
        cats = {c: v["fr"] for c, v in labels.items()
                if len(c) == 2 and c.startswith(g_code)}
        c_opts = [t["all_cats"]] + [f"{c} – {n}" for c, n in sorted(cats.items())]
        c_sel  = st.selectbox(t["category"], c_opts, key="fr_cat")
        c_code = None if c_sel == t["all_cats"] else c_sel.split(" – ")[0]

    search = st.text_input("🔍", placeholder=t["search_ph"],
                           label_visibility="collapsed", key="fr_search")

# ── Data (one cached pull per sector) ─────────────────────────────────────────
st.title(f"🇫🇷 {t['title']}")
st.caption(t["caption"])

try:
    with st.spinner("INSEE…"):
        df = fd.fetch_detail_salaries(sector)
except Exception:
    st.error(t["err_api"])
    st.stop()

year = df["year"].max()
det  = df[df["pcs"].str.len() == 4]

# Occupation pool after drill-down + search
prefix = c_code or g_code or ""
pool_codes = sorted({c for c in det["pcs"].unique() if c.startswith(prefix)})
if search.strip():
    s = search.strip().lower()
    pool_codes = [c for c in pool_codes
                  if s in fd.pcs_name(c, lang).lower() or s in c.lower()]
    st.sidebar.caption(t["found_n"].format(n=len(pool_codes)) if pool_codes
                       else t["no_match"])

with st.sidebar:
    occ_opts = [f"{fd.pcs_name(c, lang)}  ({c})" for c in pool_codes]
    sel_labels = st.multiselect(t["occ"], occ_opts, max_selections=6,
                                key="fr_occ")
    sel_codes = [l.rsplit("(", 1)[-1].rstrip(")") for l in sel_labels]

    def _fr_clear():
        for k in ("fr_group", "fr_cat", "fr_search", "fr_occ"):
            st.session_state.pop(k, None)
    st.button(t["clear"], use_container_width=True, on_click=_fr_clear)

    st.divider()
    if st.button(t["browse_btn"], use_container_width=True, key="fr_browse_open"):
        st.session_state["fr_show_browser"] = True
        st.rerun()

st.caption(t["detail_year"].format(year=year) + f" · {sector_label}")

# Convenience frames
tot = det[(det["sex"] == "_T") & (det["age"] == "_T")].set_index("pcs")


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


# ── Browse PCS codes — full-page drill-down reference (opened from sidebar) ────
# Mirrors Sweden's SSYK guide: cascading dropdowns + global search + a detail
# panel. PCS has no descriptions, so the panel shows the occupation's own wage
# snapshot instead. Full-page (st.stop) so it replaces the tabs while open.
if st.session_state.get("fr_show_browser"):
    labels = fd.load_pcs_labels()
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
        if len(code) == 4 and code in tot.index and pd.notna(tot.loc[code, "mean_salary"]):
            rows_t = det[(det["pcs"] == code) & (det["age"] == "_T")]
            mf = rows_t[rows_t["sex"] == "F"]["mean_salary"]
            mm = rows_t[rows_t["sex"] == "M"]["mean_salary"]
            gap = _gap_pct(code)
            st.markdown(f"**{t['browse_snapshot'].format(year=year)}**")
            c1, c2, c3 = st.columns(3)
            c1.metric(t["m_mean"] + " (€)",  _num(tot.loc[code, "mean_salary"]))
            c2.metric(t["m_women"] + " (€)", _num(mf.iloc[0] if len(mf) else None))
            c3.metric(t["m_men"] + " (€)",   _num(mm.iloc[0] if len(mm) else None))
            c4, c5, _ = st.columns(3)
            c4.metric(t["m_gap"],   f"{gap:+.1f} %" if gap is not None else "–")
            c5.metric(t["m_count"], _num(tot.loc[code, "headcount"]))
        elif len(code) < 4:
            st.caption(t["browse_no_salary"])

    q = st.text_input(t["browse_search"], key="fr_br_search",
                      placeholder=t["browse_search"], label_visibility="collapsed")
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

    st.divider()
    if st.button(t["browse_back"], key="fr_br_back"):
        st.session_state["fr_show_browser"] = False
        st.rerun()
    st.stop()


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


# Distribution + trend share the long-series pull (lazy, cached, may fail alone)
try:
    sl = fd.fetch_series_longues(sector)
    sl_error = False
except Exception:
    sl, sl_error = None, True

tab_exp, tab_dist, tab_trend, tab_reg = st.tabs(
    [t["tab_explorer"], t["tab_dist"], t["tab_trend"], t["tab_regions"]])

# ── Tab 1: occupation explorer ────────────────────────────────────────────────
with tab_exp:
    if not sel_codes:
        st.subheader(t["explorer_title"].format(n=len(pool_codes)))
        st.caption(t["explorer_hint"])
        rows = []
        for c in pool_codes:
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
        tbl = pd.DataFrame(rows).sort_values(t["col_mean"], ascending=False,
                                             na_position="last")
        st.dataframe(tbl, use_container_width=True, hide_index=True, height=560)
    else:
        for code in sel_codes:
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

            # Mean salary by age band × sex
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
                st.plotly_chart(fig, use_container_width=True,
                                key=f"fr_age_chart_{code}")

        # Comparison chart when several occupations are selected
        if len(sel_codes) > 1:
            st.subheader(t["cmp_title"])
            cmp_rows = [(fd.pcs_name(c, lang), tot.loc[c, "mean_salary"])
                        for c in sel_codes if c in tot.index]
            cmp_rows.sort(key=lambda r: (pd.isna(r[1]), r[1]))
            fig = go.Figure(go.Bar(
                x=[v for _, v in cmp_rows], y=[n for n, _ in cmp_rows],
                orientation="h", marker_color="#4e79a7"))
            fig.update_layout(height=90 + 45 * len(cmp_rows),
                              xaxis_title=t["sal_axis"], margin=dict(t=20, b=40))
            st.plotly_chart(fig, use_container_width=True, key="fr_cmp_chart")

        with st.expander(t["raw"]):
            show = det[det["pcs"].isin(sel_codes)].copy()
            show.insert(1, t["col_name"], show["pcs"].map(lambda c: fd.pcs_name(c, lang)))
            show["age"] = show["age"].map(lambda a: _age_label(a, t))
            show["sex"] = show["sex"].map(
                {"_T": t["sex_total"], "F": t["sex_f"], "M": t["sex_m"]})
            st.dataframe(show, use_container_width=True, hide_index=True)

# ── Tab 2: wage distribution (all employees) ──────────────────────────────────
with tab_dist:
    if sl_error:
        st.error(t["err_api"])
    else:
        dist = sl[sl["centile"].map(fd.centile_pct).notna()].copy()
        dist["pct"] = dist["centile"].map(fd.centile_pct)
        d_years = sorted(dist["year"].unique(), reverse=True)
        base_yr = d_years[0] if d_years else year

        st.subheader(t["dist_title"])
        st.caption(t["dist_caption"].format(base=base_yr, sector=sector_label))
        c1, c2, c3 = st.columns([1, 2, 2])
        with c1:
            d_year = st.selectbox(t["dist_year"], d_years, key="fr_dist_year")
        with c2:
            d_sex = _sex_radio("sex_label", "fr_dist_sex")
        with c3:
            d_wk = _wk_radio("fr_dist_wk")

        sub = dist[(dist["year"] == d_year) & (dist["sex"] == d_sex)
                   & (dist["wktime"] == d_wk)].sort_values("pct")
        pts = [(int(p), float(v)) for p, v in
               zip(sub["pct"], sub["salary_const_eur"]) if pd.notna(v)]
        if not pts:
            st.info(t["no_dist"])
        else:
            fig = go.Figure(go.Scatter(
                x=[p for p, _ in pts], y=[v for _, v in pts],
                mode="lines+markers", name=t["dist_curve"],
                line=dict(color="#4e79a7", width=2), marker=dict(size=7)))
            # Selected occupations' means as ★ markers (comparable on the
            # latest year only — detail means are current-euro latest-year).
            if d_year == base_yr:
                for code in sel_codes:
                    if code not in tot.index or pd.isna(tot.loc[code, "mean_salary"]):
                        continue
                    mv  = float(tot.loc[code, "mean_salary"])
                    pos = _pos_on_curve(mv, pts)
                    px  = {"low": pts[0][0], "high": pts[-1][0]}.get(pos, pos)
                    fig.add_trace(go.Scatter(
                        x=[px], y=[mv], mode="markers+text",
                        name=t["occ_marker"].format(name=fd.pcs_name(code, lang)[:40]),
                        text=["★"], textfont=dict(size=16, color="#e15759"),
                        textposition="middle center",
                        marker=dict(size=1, color="#e15759")))
            fig.update_layout(
                height=380, xaxis_title=t["x_pct"],
                yaxis_title=t["y_const"].format(base=base_yr),
                xaxis=dict(tickmode="array", tickvals=[p for p, _ in pts]),
                margin=dict(t=30, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
            st.plotly_chart(fig, use_container_width=True, key="fr_dist_chart")
            if d_year == base_yr and sel_codes:
                st.caption(t["marker_note"].format(year=base_yr))

            # Where do I stand?
            st.subheader(t["whereami"])
            my = st.number_input(t["my_salary"], min_value=0, step=50,
                                 key="fr_my_salary")
            if my:
                pos = _pos_on_curve(float(my), pts)
                if pos == "low":
                    st.info(t["whereami_low"])
                elif pos == "high":
                    st.success(t["whereami_high"])
                else:
                    st.success(t["whereami_result"].format(
                        p=f"{pos:.0f}", scope=sector_label.lower()))
                st.caption(t["whereami_note"].format(year=d_year))

# ── Tab 3: long-series trend (constant euros) ─────────────────────────────────
with tab_trend:
    if sl_error:
        st.error(t["err_api"])
    else:
        modes = [t["trend_dist"]]
        has_groups = (sl["pcs"] != "_T").any()
        if has_groups:
            modes.append(t["trend_groups"])
        c1, c2, c3, c4 = st.columns([2, 2, 1, 2])
        with c1:
            tr_mode = st.radio(t["trend_mode"], modes, key="fr_tr_mode")
        with c2:
            tr_sex = _sex_radio("sex_label", "fr_tr_sex")
        with c3:
            tr_wk = _wk_radio("fr_tr_wk")
        with c4:
            tr_unit = st.radio(t["unit_label"],
                               [t["unit_real"], t["unit_nominal"]],
                               key="fr_tr_unit")
        if not has_groups:
            st.caption(t["groups_private_only"])

        if tr_mode == t["trend_dist"]:
            base = sl[(sl["centile"] != "_T") & (sl["sex"] == tr_sex)
                      & (sl["wktime"] == tr_wk)].copy()
            base["pct"] = base["centile"].map(fd.centile_pct)
            series = [(f"P{int(p)}", base[base["pct"] == p])
                      for p in sorted(base["pct"].dropna().unique())]
        else:
            base = sl[(sl["centile"] == "_T") & (sl["sex"] == tr_sex)
                      & (sl["wktime"] == tr_wk)]
            order = [p for p in ("_T", "3", "4", "5", "6")
                     if p in set(base["pcs"])]
            ens = t["sex_total"] if lang == "EN" else "Ensemble"
            series = [(ens if p == "_T" else fd.pcs_name(p, lang)[:40],
                       base[base["pcs"] == p]) for p in order]

        yrs_all = sorted(base["year"].unique())
        if not yrs_all:
            st.info(t["no_dist"])
        else:
            y0, y1 = st.select_slider(t["trend_range"], options=yrs_all,
                                      value=(yrs_all[0], yrs_all[-1]),
                                      key="fr_tr_range")
            base_yr = yrs_all[-1]

            # Nominal view: constant euros are expressed in latest-year prices,
            # so nominal(y) = const(y) × CPI(y)/CPI(latest). Needs the IPC.
            nominal, cpi, cpi_base = tr_unit == t["unit_nominal"], {}, None
            if nominal:
                try:
                    cpi = fd.fetch_cpi_annual()
                except Exception:
                    cpi = {}
                cpi_base = cpi.get(base_yr)
                if not cpi_base:
                    nominal = False
                    st.caption(t["no_cpi"])

            BLUES = ["#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5",
                     "#08519c", "#083b7a", "#0a2f63", "#081d58"]
            fig = go.Figure()
            for i, (name, sdf) in enumerate(series):
                sdf = sdf[(sdf["year"] >= y0) & (sdf["year"] <= y1)]
                sdf = sdf.dropna(subset=["salary_const_eur"]).sort_values("year")
                if nominal:
                    sdf = sdf[sdf["year"].isin(cpi)]
                if sdf.empty:
                    continue
                ys = (sdf["salary_const_eur"] if not nominal else
                      [v * cpi[y] / cpi_base
                       for y, v in zip(sdf["year"], sdf["salary_const_eur"])])
                color = ("#e15759" if name in ("P50",)
                         else BLUES[min(i, len(BLUES) - 1)])
                fig.add_trace(go.Scatter(
                    x=sdf["year"], y=ys,
                    mode="lines", name=name, line=dict(color=color, width=2)))
            fig.update_layout(
                height=420, xaxis_title="",
                yaxis_title=(t["y_nominal"] if nominal
                             else t["y_const"].format(base=base_yr)),
                margin=dict(t=30, b=40), hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
            st.plotly_chart(fig, use_container_width=True, key="fr_tr_chart")
            st.caption(t["trend_caption_nom"] if nominal else t["trend_caption"])

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
                marker_color=["#e15759" if fr else "#4e79a7"
                              for _, _, fr in rows]))
            fig.update_layout(height=110 + 30 * len(rows),
                              xaxis_title=t["reg_axis"],
                              margin=dict(t=20, b=40))
            st.plotly_chart(fig, use_container_width=True, key="fr_reg_chart")
            with st.expander(t["raw"]):
                tbl = pd.DataFrame(
                    [{t["col_name"]: n, t["col_mean"]: round(v)}
                     for n, v, _ in reversed(rows)])
                st.dataframe(tbl, use_container_width=True, hide_index=True)

if t["note_v1"]:
    st.caption(t["note_v1"])
