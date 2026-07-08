"""Leaderboard tab — rank ALL occupations by pay, scoped to the drilled-into
sub-group, with the user's own occupations highlighted and CSV export. Metrics
(like Sweden): median / average / gender gap / median growth — each shown only
when the data supports it. Needs provider.leaderboard() + has_leaderboard.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts, i18n, states


def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    slug = cfg.slug
    def k(n):
        return f"{slug}_{n}"
    st.subheader(i18n.t(cfg, "tab_lead", lang, "Leaderboard"))
    caps = cfg.capabilities
    sector, sex = query.get("sector", ""), query.get("sex", "total")
    suf = cfg.currency_suffix

    metric_opts = []
    if caps.has_median:
        metric_opts.append(("median", i18n.t(cfg, "m_median", lang, "Median (P50)")))
    if caps.has_mean:
        metric_opts.append(("mean", i18n.t(cfg, "m_average", lang, "Average")))
    if caps.has_sex:
        metric_opts.append(("gap", i18n.t(cfg, "lead_m_gap", lang, "Gender gap")))
    multiyear = caps.year_range and caps.year_range[1] > caps.year_range[0]
    if caps.has_trend and multiyear:
        metric_opts.append(("growth", i18n.t(cfg, "lead_m_growth", lang, "Median growth")))
    if not metric_opts:
        return
    m_label = dict(metric_opts)
    years = (list(range(caps.year_range[1], caps.year_range[0] - 1, -1))
             if caps.year_range else [int(query.get("years", (None,))[-1] or 0)])

    mkey = st.selectbox(i18n.t(cfg, "lead_metric", lang, "Rank by"),
                        [m for m, _ in metric_opts], format_func=lambda kk: m_label[kk],
                        key=k("lmetric"))
    hi = i18n.t(cfg, "lead_high", lang, "Highest first")
    lo = i18n.t(cfg, "lead_low", lang, "Lowest first")

    # ── Controls + fetch + build a [occ_code, occ_name, val] frame ────────────
    axis, value_fmt = f"{suf}{cfg.per_label}", lambda v: charts.fmt_value(v, cfg)
    if mkey == "growth":
        c1, c2, c3 = st.columns(3)
        yf = c1.selectbox(i18n.t(cfg, "lead_from", lang, "From"), years, index=len(years) - 1, key=k("lfrom"))
        yt = c2.selectbox(i18n.t(cfg, "lead_to", lang, "To"), years, index=0, key=k("lto"))
        asc = c3.selectbox(i18n.t(cfg, "lead_order", lang, "Order"), [hi, lo], key=k("lorder")) == lo
        if yf == yt:
            st.info(i18n.t(cfg, "lead_need_two", lang, "Pick two different years."))
            return
        with states.loading():
            a = cfg.provider.leaderboard(sector=sector, sex=sex, year=yf, lang=lang)
            b = cfg.provider.leaderboard(sector=sector, sex=sex, year=yt, lang=lang)
        g = (a[["occ_code", "occ_name", "median"]]
             .merge(b[["occ_code", "median"]], on="occ_code", suffixes=("_0", "_1")).dropna())
        g = g[g["median_0"] > 0]
        g["val"] = ((g["median_1"] / g["median_0"] - 1) * 100).round(1)
        ranked = g[["occ_code", "occ_name", "val"]]
        axis, value_fmt = "%", lambda v: f"{v:+.1f} %"
    elif mkey == "gap":
        c1, c2 = st.columns(2)
        year = c1.selectbox(i18n.t(cfg, "x_year", lang, "Year"), years, key=k("lyear"))
        asc = c2.selectbox(i18n.t(cfg, "lead_order", lang, "Order"), [hi, lo], key=k("lorder")) == lo
        with states.loading():
            w = cfg.provider.leaderboard(sector=sector, sex="women", year=year, lang=lang)
            m = cfg.provider.leaderboard(sector=sector, sex="men", year=year, lang=lang)
        # rank on medians when the source publishes them per sex; otherwise fall
        # back to means (e.g. France: percentiles exist only for both sexes)
        basis = ("median" if (not w.empty and w["median"].notna().any()
                              and not m.empty and m["median"].notna().any()) else "mean")
        g = (w[["occ_code", "occ_name", basis]]
             .merge(m[["occ_code", basis]], on="occ_code", suffixes=("_w", "_m")).dropna())
        g = g[g[f"{basis}_m"] > 0]
        g["val"] = (g[f"{basis}_w"] / g[f"{basis}_m"] * 100).round(1)
        ranked = g[["occ_code", "occ_name", "val"]]
        axis, value_fmt = i18n.t(cfg, "lead_gap_axis", lang, "Women % of men"), lambda v: f"{v:.1f} %"
        if basis == "mean":
            st.caption(i18n.t(cfg, "lead_gap_mean_note", lang,
                              "Ranked on mean salary (medians aren't published per sex here)."))
    else:                                            # median / mean
        c1, c2 = st.columns(2)
        year = c1.selectbox(i18n.t(cfg, "x_year", lang, "Year"), years, key=k("lyear"))
        asc = c2.selectbox(i18n.t(cfg, "lead_order", lang, "Order"), [hi, lo], key=k("lorder")) == lo
        with states.loading():
            lb = cfg.provider.leaderboard(sector=sector, sex=sex, year=year, lang=lang)
        ranked = lb.dropna(subset=[mkey]).rename(columns={mkey: "val"})[["occ_code", "occ_name", "val"]]

    if ranked is None or ranked.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return

    # scope to the drilled sub-group (STYRK 2-digit, SOC minor 4-char), like Sweden
    scope = query.get("scope", "")[:caps.leaderboard_scope]
    if scope:
        ranked = ranked[ranked["occ_code"].str.startswith(scope)]
    tree = cfg.provider.occupation_tree(lang) if cfg.provider else {}
    scope_disp = (f"{scope} · {tree.get(scope, '')}".strip(" ·") if scope
                  else i18n.t(cfg, "lead_all_occ", lang, "all occupations"))
    st.caption(i18n.t(cfg, "lead_intro", lang,
                      "Ranking {scope} — your picks are highlighted.").format(scope=scope_disp))
    if ranked.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return
    ranked = ranked.sort_values("val", ascending=asc).reset_index(drop=True)
    ranked["rank"] = ranked.index + 1

    topn = st.slider(i18n.t(cfg, "lead_topn", lang, "Show top"), 5, 40, 15, key=k("ltopn"))
    show = ranked.head(topn).iloc[::-1]
    highlight = set(query.get("occ_codes", ()))
    fig = charts.leaderboard_bar(show, cfg, value_col="val", value_fmt=value_fmt,
                                 highlight=highlight, x_title=axis, title=m_label[mkey])
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    for c in query.get("occ_codes", ()):
        r = ranked[ranked["occ_code"] == c]
        if not r.empty:
            row = r.iloc[0]
            st.markdown(i18n.t(cfg, "lead_your", lang,
                               "**{name}** — rank **{rank}** of {total} ({val})").format(
                name=row["occ_name"], rank=int(row["rank"]), total=len(ranked),
                val=value_fmt(row["val"])))

    with st.expander(i18n.t(cfg, "raw_data", lang, "Raw data")):
        col_rank = i18n.t(cfg, "lead_rank", lang, "Rank")
        col_code = i18n.t(cfg, "col_code", lang)
        col_occ = i18n.t(cfg, "col_occupation", lang)
        disp = pd.DataFrame({col_rank: ranked["rank"], col_code: ranked["occ_code"],
                             col_occ: ranked["occ_name"]})
        disp[m_label[mkey]] = ranked["val"].map(value_fmt)
        st.dataframe(disp, use_container_width=True, hide_index=True)
        raw = ranked[["rank", "occ_code", "occ_name", "val"]]
        st.download_button(i18n.t(cfg, "download_csv", lang, "Download CSV"),
                           raw.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{slug}_leaderboard_{mkey}.csv", mime="text/csv",
                           key=k("dl_lead"))
