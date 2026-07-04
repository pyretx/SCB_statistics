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
        "lang": "Langue / Language",
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
        "note_v1": "v1 : moyennes par profession. À venir : distribution des salaires, séries longues, inflation.",
    },
    "EN": {
        "title": "Salary Explorer — France",
        "caption": "Mean net monthly salary, full-time equivalent (FTE) · Source: INSEE (DADS/DSN via the Melodi API)",
        "lang": "Langue / Language",
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
        "note_v1": "v1: means per occupation. Coming next: wage distribution, long series, inflation.",
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
    lang = st.radio(T["FR"]["lang"], ["Français", "English"], horizontal=True,
                    key="fr_lang")
    lang = "FR" if lang == "Français" else "EN"
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


# ── No selection → ranked explorer table ─────────────────────────────────────
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
    st.caption(t["note_v1"])
    st.stop()

# ── Selection → detail view ───────────────────────────────────────────────────
for code in sel_codes:
    st.subheader(f"{fd.pcs_name(code, lang)}  ({code})")
    rows_t = det[(det["pcs"] == code) & (det["age"] == "_T")]
    mean_t  = rows_t[rows_t["sex"] == "_T"]["mean_salary"]
    count_t = rows_t[rows_t["sex"] == "_T"]["headcount"]
    mean_f  = rows_t[rows_t["sex"] == "F"]["mean_salary"]
    mean_m  = rows_t[rows_t["sex"] == "M"]["mean_salary"]
    gap = _gap_pct(code)

    def _num(v):
        return f"{v:,.0f}".replace(",", " ") if v is not None and pd.notna(v) else "–"

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

# Raw data expander
with st.expander(t["raw"]):
    show = det[det["pcs"].isin(sel_codes)].copy()
    show.insert(1, t["col_name"], show["pcs"].map(lambda c: fd.pcs_name(c, lang)))
    show["age"] = show["age"].map(lambda a: _age_label(a, t))
    show["sex"] = show["sex"].map(
        {"_T": t["sex_total"], "F": t["sex_f"], "M": t["sex_m"]})
    st.dataframe(show, use_container_width=True, hide_index=True)

st.caption(t["note_v1"])
