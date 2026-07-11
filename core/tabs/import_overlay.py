"""Import-overlay tab (beta) — compare an uploaded/pasted salary list against
the selected occupation's official distribution.

Promoted from a standalone prototype (since deleted). Standard
framework tab, but BETA-GATED: core.tabs.render_tabs only lists it for
admin/master users and beta testers (users with the country in their
app_metadata.countries grant) — see core.access.is_beta_or_admin.

Flow: reference curve for the user's selected occupation (re-fetched per chart
year, like the Distribution tab) → optional forward-projection ("aging") with
one compounded %-increase slider per year up to today → upload/paste import
with map-&-confirm (column pick, unit, preview of computed percentiles) before
anything is drawn. Percentile levels adapt to what the source publishes
(Sweden P10–P90, Norway quartiles) so the comparison stays like-for-like.
The imported data lives in session state only — never persisted or logged.
"""
from __future__ import annotations

import io
import re
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import theme

from .. import agg, charts, i18n, states
from . import projection

# canonical percentile columns of the normalized model ↔ percentile levels
_PCT_LEVELS = [("p10", 10), ("p25", 25), ("median", 50), ("p75", 75), ("p90", 90)]

AGE_COLOR = "#16A34A"   # aged / projected reference (green)
YOU_COLOR = "#DC2626"   # imported data (red)


# ── Number / file parsing (ported from the prototype) ─────────────────────────
def clean_number(raw) -> float | None:
    """'45 000,50 kr' / '45.000,50' / '$45,000.50' / '55k' → float, else None."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw) if np.isfinite(raw) else None
    s = str(raw).strip().lower()
    if not s:
        return None
    mult = 1.0
    if s.endswith("k"):
        mult, s = 1000.0, s[:-1]
    s = re.sub(r"[^0-9,.\-]", "", s)      # strip currency, letters, spaces
    if not re.search(r"\d", s):
        return None
    has_comma, has_dot = "," in s, "." in s
    if has_comma and has_dot:
        # the LAST separator is the decimal mark; the other is thousands
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        thou = "." if dec == "," else ","
        s = s.replace(thou, "").replace(dec, ".")
    elif has_comma:
        # comma alone: decimal if it looks like ,dd — else thousands separator
        s = s.replace(",", ".") if re.search(r",\d{1,2}$", s) else s.replace(",", "")
    try:
        return float(s) * mult
    except ValueError:
        return None


def parse_upload(name: str, data: bytes) -> pd.DataFrame:
    """Bytes → DataFrame. Only STRONG delimiters (, ; tab |) split columns —
    never plain spaces (a space is a thousands separator: '41 000 kr'). Header
    inferred from whether the first cell parses as a number."""
    low = name.lower()
    if low.endswith((".xlsx", ".xlsm", ".xls")):
        return pd.read_excel(io.BytesIO(data))
    text = data.decode("utf-8-sig", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return pd.DataFrame()
    first = lines[0]
    strong = [d for d in [";", "\t", "|", ","] if d in text]
    if strong:
        sep = max(strong, key=text.count)
        header = 0 if clean_number(first.split(sep)[0]) is None else None
        df = pd.read_csv(io.StringIO(text), sep=sep, engine="python", header=header)
        if header is None:
            df.columns = [f"col{i + 1}" for i in range(df.shape[1])]
        return df
    if clean_number(first) is None:          # one value per line, first row = header
        return pd.DataFrame({first: lines[1:]})
    return pd.DataFrame({"value": lines})


def weighted_percentiles(values: np.ndarray, weights: np.ndarray | None,
                         levels: list[int]) -> dict[int, float]:
    """Percentiles matching numpy's 'linear' (type-7) method; weighted when
    weights are given — the standard estimator, so overlay points sit on a
    like-for-like basis with the official curve."""
    if weights is None:
        return {lv: float(np.percentile(values, lv)) for lv in levels}
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    pos = (cw - 0.5 * w) / w.sum()            # 0..1 plotting positions
    return {lv: float(np.interp(lv / 100.0, pos, v)) for lv in levels}


def _unit_options(cfg, T):
    """(label, to-page-period conversion) choices, adapted to cfg.period."""
    cur = cfg.currency
    if cfg.period == "annual":
        return [(T("io_unit_annual", f"Annual {cur} (as reported)"), lambda v: v),
                (T("io_unit_monthly_x12", f"Monthly {cur} (×12 → annual)"), lambda v: v * 12.0),
                (T("io_unit_thousands", f"Thousands of {cur} (×1000)"), lambda v: v * 1000.0)]
    if cfg.period == "hourly":
        return [(T("io_unit_hourly", f"Hourly {cur} (as reported)"), lambda v: v),
                (T("io_unit_thousands", f"Thousands of {cur} (×1000)"), lambda v: v * 1000.0)]
    return [(T("io_unit_monthly", f"Monthly {cur} (as reported)"), lambda v: v),
            (T("io_unit_annual_d12", f"Annual {cur} (÷12 → monthly)"), lambda v: v / 12.0),
            (T("io_unit_thousands", f"Thousands of {cur} (×1000)"), lambda v: v * 1000.0)]


# ── Tab entry point ────────────────────────────────────────────────────────────
def render(cfg, stats, query):
    lang = query.get("lang", "EN")
    slug = cfg.slug
    caps = cfg.capabilities

    def k(n):
        return f"{slug}_io_{n}"

    def T(key, default=""):
        return i18n.t(cfg, key, lang, default)

    st.subheader(T("io_header", "Import & compare your own salary data"))
    st.caption(T("io_privacy",
                 "🔒 Imported data is processed in this session only — it is never "
                 "uploaded to a server, saved to disk, or logged."))

    occ = tuple(query.get("occ_codes", ()))
    sector, sex = query.get("sector", ""), query.get("sex", "total")

    # ── Reference: selected occupation × chart year (Distribution-tab pattern) ─
    c1, c2 = st.columns([1, 2])
    with c1:
        yy = query.get("years", ())
        years = sorted({int(y) for y in yy}, reverse=True) if yy else (
            list(range(caps.year_range[1], caps.year_range[0] - 1, -1))
            if caps.year_range else [])
        ref_year = st.selectbox(T("io_ref_year", "Reference data year"),
                                years, key=k("year")) if years else None

    with states.loading():
        d = cfg.provider.occupation_stats(sector=sector, occ_codes=occ, sex=sex,
                                          year=ref_year, lang=lang)
    tot = d[d["dimension"] == "total"]
    if query.get("aggregate") and not tot.empty:
        tot = agg.collapse_stats(tot, agg.agg_name(cfg, lang, len(occ)))
    tot = tot.dropna(subset=["occ_name"])
    if tot.empty:
        st.caption(T("no_data_combo", "No data for this combination."))
        return

    # several occupations, not aggregated → the user picks ONE reference
    names = list(dict.fromkeys(tot["occ_name"].astype(str)))
    with c2:
        ref_name = (st.selectbox(T("io_ref_occ", "Compare against occupation"),
                                 names, key=k("occ"))
                    if len(names) > 1 else names[0])
        if len(names) == 1:
            st.markdown(f"**{ref_name}**")
    row = tot[tot["occ_name"].astype(str) == ref_name].iloc[0]

    # percentile points the source actually publishes for this row
    pct = [(col, lv) for col, lv in _PCT_LEVELS
           if col in row and pd.notna(row[col])]
    levels = [lv for _, lv in pct] or [lv for _, lv in _PCT_LEVELS]
    mean_val = float(row["mean"]) if caps.has_mean and pd.notna(row.get("mean")) else None
    if not pct:
        st.info(T("io_no_ref_pct",
                  "This source publishes no percentiles for the selection — the "
                  "reference shows the average only; your import still plots the "
                  "standard percentile curve."))

    def xlab(col, lv):
        return {"median": i18n.t(cfg, "m_median", lang, "Median (P50)")}.get(col, f"P{lv}")

    cats = [xlab(c, lv) for c, lv in pct] or [f"P{lv}" for lv in levels]
    mean_label = i18n.t(cfg, "m_average", lang, "Average")
    all_cats = cats + ([mean_label] if mean_val is not None else [])
    ref_by_level = {lv: float(row[c]) for c, lv in pct}
    cat_by_level = dict(zip(levels, cats))

    # ── Visibility toggles + forward projection (shared block, see projection.py)
    this_year = date.today().year
    proj_years = projection.years_to_project(ref_year)

    st.markdown(f"**{T('io_show_on_chart', 'Show on chart')}**")
    tc = st.columns(2)
    show_ref = tc[0].toggle(T("io_show_ref", "Reference curve"), value=True,
                            key=k("show_ref"))
    show_aged = (projection.toggle(cfg, lang, k("show_aged"), container=tc[1])
                 if proj_years else False)
    factor = projection.slider_block(cfg, lang, k, ref_year, expanded=show_aged)

    # ── Import wizard (map & confirm before anything hits the chart) ──────────
    st.divider()
    st.markdown(f"##### {T('io_import_header', 'Import your data')}")
    src = st.radio("io_src", [T("io_upload", "Upload a file"), T("io_paste", "Paste numbers")],
                   horizontal=True, label_visibility="collapsed", key=k("src"))

    with st.expander(T("io_structure_title", "ℹ️ How should the file be structured?")):
        st.markdown(T("io_structure_body",
                      "One salary **per row**, in a **single column** (extra columns are "
                      "fine — you choose which one). Any number format works: `55 600 kr`, "
                      "`45 000,50`, `45,000.50`, `55k`. Header row optional.\n\n"
                      "**Avoid:** totals/average/summary rows (they get counted as "
                      "salaries), wide layouts (one person per column), and title rows "
                      "above the header in Excel. You always see the parsed count and "
                      "computed percentiles below **before** anything is drawn."))

    df: pd.DataFrame | None = None
    if src == T("io_upload", "Upload a file"):
        up = st.file_uploader(T("io_file", "File (.xlsx, .csv, .tsv, .txt)"),
                              type=["xlsx", "xlsm", "xls", "csv", "tsv", "txt"],
                              key=k("file"))
        if up is not None:
            try:
                df = parse_upload(up.name, up.getvalue())
            except Exception as e:  # noqa: BLE001
                st.error(T("io_parse_fail", "Couldn't parse that file: {err}")
                         .format(err=e))
    else:
        txt = st.text_area(T("io_paste_label", "Paste one salary per line"),
                           height=140, key=k("paste"),
                           placeholder="52000\n48 500 kr\n61 250\n…")
        if txt.strip():
            # one value per line — a comma here is part of a number, never a delimiter
            df = pd.DataFrame({T("io_pasted", "Pasted salary"):
                               [ln for ln in txt.splitlines() if ln.strip()]})

    ov_key = k("overlay")
    if df is not None and not df.empty:
        st.markdown(f"**{T('io_map_header', '1 · Map & configure')}**")
        st.dataframe(df.head(8), use_container_width=True, height=200)

        cols = list(df.columns.astype(str))
        numeric_score = {c: df[c].map(clean_number).notna().mean() for c in cols}
        default_col = max(numeric_score, key=numeric_score.get)
        none_lbl = T("io_none", "— none —")
        units = _unit_options(cfg, T)

        m1, m2, m3 = st.columns(3)
        sal_col = m1.selectbox(T("io_salary_col", "Salary column"), cols,
                               index=cols.index(default_col), key=k("salcol"))
        weight_col = m2.selectbox(T("io_weight_col", "Weight / headcount column (optional)"),
                                  [none_lbl] + cols, key=k("wcol"))
        unit_lbl = m3.selectbox(T("io_unit", "Unit of the values"),
                                [u[0] for u in units], key=k("unit"))
        convert = dict(units)[unit_lbl]

        vals = df[sal_col].map(clean_number)
        n_raw = len(vals)
        vals = vals.dropna().map(convert)
        vals = vals[vals > 0]
        dropped = n_raw - len(vals)
        values = vals.to_numpy(dtype=float)

        weights = None
        if weight_col != none_lbl:
            w = df.loc[vals.index, weight_col].map(clean_number)
            if w.notna().all() and (w > 0).all():
                weights = w.to_numpy(dtype=float)
            else:
                st.warning(T("io_bad_weights",
                             "Weight column has missing/invalid values — ignoring weights."))

        if len(values) == 0:
            st.error(T("io_no_values", "No usable numeric salaries found in that column."))
        else:
            if dropped:
                st.info(T("io_skipped", "Skipped {n} row(s) that weren't valid numbers.")
                        .format(n=dropped))
            if len(values) < 20:
                st.warning(T("io_small_n",
                             "Only {n} values — percentiles (especially the extremes) "
                             "are unreliable at this sample size.").format(n=len(values)))
            comp = weighted_percentiles(values, weights, levels)
            your_avg = float(np.average(values, weights=weights))

            st.markdown(f"**{T('io_preview_header', '2 · Preview computed percentiles')}**")
            prev = pd.DataFrame({
                T("io_col_measure", "Measure"):
                    [cat_by_level.get(lv, f"P{lv}") for lv in levels]
                    + [mean_label, "n"],
                T("io_col_yours", "Your data"):
                    [charts.fmt_value(comp[lv], cfg) for lv in levels]
                    + [charts.fmt_value(your_avg, cfg), f"{len(values)}"],
                T("io_col_ref", "Reference ({year})").format(year=ref_year):
                    [charts.fmt_value(ref_by_level.get(lv), cfg) for lv in levels]
                    + [charts.fmt_value(mean_val, cfg), "–"],
            })
            st.dataframe(prev, use_container_width=True, hide_index=True)

            b1, b2 = st.columns([1, 1])
            if b1.button(T("io_add_overlay", "➕ Add overlay to chart"),
                         type="primary", key=k("add")):
                st.session_state[ov_key] = {"pct": comp, "avg": your_avg,
                                            "n": len(values)}
            if ov_key in st.session_state and b2.button(
                    T("io_remove_overlay", "✕ Remove overlay"), key=k("rm")):
                del st.session_state[ov_key]

    # ── Chart: reference · aged projection · imported overlay ─────────────────
    fig = go.Figure()
    accent = theme.SERIES[0] if getattr(theme, "SERIES", None) else theme.ACCENT

    if show_ref and pct:
        fig.add_trace(go.Scatter(
            x=cats, y=[ref_by_level[lv] for _, lv in pct],
            mode="lines+markers",
            name=T("io_trace_ref", "Official ({year})").format(year=ref_year),
            line=dict(color=accent, width=2.5), marker=dict(size=9),
            hovertemplate="%{x}: %{y:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
    if show_ref and mean_val is not None:
        fig.add_trace(go.Scatter(
            x=[mean_label], y=[mean_val], mode="markers", showlegend=False,
            marker=dict(size=12, symbol="diamond", color=accent,
                        line=dict(width=1, color="white")),
            hovertemplate=mean_label + " %{y:,.0f} " + cfg.currency_suffix + "<extra></extra>"))

    if show_aged and factor > 1.0:
        aged_name = T("io_trace_aged", "Projected to {year}").format(year=this_year)
        if pct:
            fig.add_trace(go.Scatter(
                x=cats, y=[ref_by_level[lv] * factor for _, lv in pct],
                mode="lines+markers", name=aged_name,
                line=dict(color=AGE_COLOR, width=2.5, dash="dot"),
                marker=dict(size=9, symbol="triangle-up"),
                hovertemplate="%{x}: %{y:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
        if mean_val is not None:
            fig.add_trace(go.Scatter(
                x=[mean_label], y=[mean_val * factor], mode="markers", showlegend=False,
                marker=dict(size=12, symbol="diamond", color=AGE_COLOR,
                            line=dict(width=1, color="white")),
                hovertemplate=aged_name + " %{y:,.0f} " + cfg.currency_suffix + "<extra></extra>"))

    ov = st.session_state.get(ov_key)
    if ov:
        fig.add_trace(go.Scatter(
            x=[cat_by_level.get(lv, f"P{lv}") for lv in ov["pct"]],
            y=list(ov["pct"].values()), mode="lines+markers",
            name=T("io_trace_yours", "Your data (n={n})").format(n=ov["n"]),
            line=dict(color=YOU_COLOR, width=2.5, dash="dash"),
            marker=dict(size=10, symbol="diamond"),
            hovertemplate="%{x}: %{y:,.0f} " + cfg.currency_suffix + "<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=[mean_label], y=[ov["avg"]], mode="markers", showlegend=False,
            marker=dict(size=12, symbol="diamond", color=YOU_COLOR,
                        line=dict(width=1, color="white")),
            hovertemplate=mean_label + " %{y:,.0f} " + cfg.currency_suffix + "<extra></extra>"))

    if fig.data:
        fig.update_layout(
            xaxis=dict(categoryorder="array", categoryarray=all_cats,
                       title=i18n.t(cfg, "x_percentile", lang, "Percentile")),
            yaxis_title=f"{cfg.currency_suffix}{cfg.per_label}",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            height=440, margin=dict(t=60, b=40), hovermode="x unified")
        st.plotly_chart(theme.style_fig(fig), use_container_width=True,
                        key=k("chart"))
