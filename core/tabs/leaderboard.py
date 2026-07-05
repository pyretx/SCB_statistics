"""Leaderboard tab — rank ALL occupations by pay (median/mean) for a year, with
the user's own occupations highlighted, a top-N slider, "where you land"
call-outs, and an exportable table. Mirrors the Swedish Leaderboard; needs
provider.leaderboard() (gated by capabilities.has_leaderboard).
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

    metric_opts = []
    if caps.has_median:
        metric_opts.append(("median", i18n.t(cfg, "m_median", lang, "Median (P50)")))
    if caps.has_mean:
        metric_opts.append(("mean", i18n.t(cfg, "m_average", lang, "Average")))
    if not metric_opts:
        return
    m_label = dict(metric_opts)

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        mkey = st.selectbox(i18n.t(cfg, "lead_metric", lang, "Rank by"),
                            [m for m, _ in metric_opts],
                            format_func=lambda kk: m_label[kk], key=k("lmetric"))
    with c2:
        if caps.year_range:
            y0, y1 = caps.year_range
            year = st.selectbox(i18n.t(cfg, "x_year", lang, "Year"),
                                list(range(y1, y0 - 1, -1)), key=k("lyear"))
        else:
            yy = query.get("years", ())
            year = int(yy[-1]) if yy else None
    with c3:
        hi = i18n.t(cfg, "lead_high", lang, "Highest first")
        lo = i18n.t(cfg, "lead_low", lang, "Lowest first")
        asc = st.selectbox(i18n.t(cfg, "lead_order", lang, "Order"), [hi, lo], key=k("lorder")) == lo

    with states.loading():
        lb = cfg.provider.leaderboard(sector=query.get("sector", ""),
                                      sex=query.get("sex", "total"), year=year, lang=lang)
    lb = lb.dropna(subset=[mkey]) if lb is not None and not lb.empty else lb
    if lb is None or lb.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return
    # Scope the ranking to the group drilled into in the sidebar (like Sweden),
    # but capped at the SUB-GROUP (2-digit) so a deep drill-down still ranks a
    # useful set — e.g. drilling to 231 ranks all of sub-group 23, not just 231.
    scope = query.get("scope", "")[:2]
    if scope:
        lb = lb[lb["occ_code"].str.startswith(scope)]
    tree = cfg.provider.occupation_tree(lang) if cfg.provider else {}
    scope_disp = (f"{scope} · {tree.get(scope, '')}".strip(" ·") if scope
                  else i18n.t(cfg, "lead_all_occ", lang, "all occupations"))
    st.caption(i18n.t(cfg, "lead_intro", lang,
                      "Ranking {scope} — your picks are highlighted.").format(scope=scope_disp))
    if lb.empty:
        st.caption(i18n.t(cfg, "no_data_combo", lang))
        return
    lb = lb.sort_values(mkey, ascending=asc).reset_index(drop=True)
    lb["rank"] = lb.index + 1

    suf = cfg.currency_suffix
    def fmt(v):
        return f"{int(round(v)):,}".replace(",", " ") + f" {suf}"

    topn = st.slider(i18n.t(cfg, "lead_topn", lang, "Show top"), 5, 40, 15, key=k("ltopn"))
    show = lb.head(topn).iloc[::-1]                 # reversed so #1 sits on top
    highlight = set(query.get("occ_codes", ()))
    fig = charts.leaderboard_bar(show, cfg, value_col=mkey, value_fmt=fmt, highlight=highlight,
                                 x_title=f"{suf}/mo", title=f"{m_label[mkey]} · {year}")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    for c in query.get("occ_codes", ()):            # where do the user's picks land?
        r = lb[lb["occ_code"] == c]
        if not r.empty:
            row = r.iloc[0]
            st.markdown(i18n.t(cfg, "lead_your", lang,
                               "**{name}** — rank **{rank}** of {total} ({val})").format(
                name=row["occ_name"], rank=int(row["rank"]), total=len(lb), val=fmt(row[mkey])))

    with st.expander(i18n.t(cfg, "raw_data", lang, "Raw data")):
        col_rank = i18n.t(cfg, "lead_rank", lang, "Rank")
        col_code = i18n.t(cfg, "col_code", lang)
        col_occ = i18n.t(cfg, "col_occupation", lang)
        disp = pd.DataFrame({col_rank: lb["rank"], col_code: lb["occ_code"],
                             col_occ: lb["occ_name"]})
        disp[m_label[mkey]] = lb[mkey].map(fmt)
        st.dataframe(disp, use_container_width=True, hide_index=True)
        raw = lb[["rank", "occ_code", "occ_name", mkey]]
        st.download_button(i18n.t(cfg, "download_csv", lang, "Download CSV"),
                           raw.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"{slug}_leaderboard_{mkey}_{year}.csv", mime="text/csv",
                           key=k("dl_lead"))
