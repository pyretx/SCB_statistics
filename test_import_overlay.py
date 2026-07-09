"""TEST / THROWAWAY PAGE — import-overlay prototype.

Standalone Streamlit app (does NOT touch the real app). Run it on its own port:

    python -m streamlit run test_import_overlay.py --server.port=8503

What it does
------------
1. Pulls the live SCB percentile curve for ONE occupation — SSYK 2143
   (electrical / electronics / telecom engineers), all sectors, both sexes,
   latest year — and plots P10/P25/P50/P75/P90 (+ average).
2. Lets you upload a file (.xlsx / .csv / .tsv / .txt) or paste numbers,
   pick the salary column, set the unit, then computes percentiles from YOUR
   data and overlays them on the same chart for an apples-to-apples compare.

Design goals baked in: map-&-confirm before it hits the chart, same percentile
method + units as the reference, robust EU/Swedish number parsing, in-session
only (nothing is persisted), and small-n warnings.

Delete this file (and test_sample_salaries*.csv) to remove the prototype.
"""
from __future__ import annotations

import io
import re
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ── Fixed target: SSYK 2143, all sectors, both sexes, latest year ──────────────
SSYK_CODE = "2143"
SSYK_NAME = "Engineering professionals in electrical, electronics & telecom (SSYK 2143)"
SECTOR = "0"        # all sectors
SEX = "1+2"         # both sexes
TABLE = "LoneSpridSektYrk4AN"   # current-generation percentile table (2023→)
BASE = "https://api.scb.se/OV0104/v1/doris/en/ssd/AM/AM0110/AM0110A"

REF_YEARS = ["2023", "2024", "2025"]   # years available in the current-gen table
DEFAULT_YEAR = "2025"                   # latest published
CURRENT_YEAR = date.today().year        # "today" — drives how many aging sliders

# ContentsCodes for the current-generation table, canonical order.
# (mirrors PCT_TABLES in scb_salaries.py — kept local so this page is standalone)
MEASURES = [
    ("Average", "000007CD", None),   # separate marker, no percentile level
    ("P10", "000007CF", 10),
    ("P25", "000007CG", 25),
    ("P50", "000007CE", 50),
    ("P75", "000007CH", 75),
    ("P90", "000007CI", 90),
]

# Percentile levels we compute from imported data (must match the reference points)
PCT_LEVELS = [10, 25, 50, 75, 90]

REF_COLOR = "#2563eb"    # SCB reference (blue)
YOU_COLOR = "#dc2626"    # your imported data (red)
AGE_COLOR = "#16a34a"    # aged / projected reference (green)


# ── SCB fetch ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def fetch_scb_curve(year: str) -> dict[str, float]:
    """Return {measure_label: monthly SEK} for the fixed occupation and a year."""
    codes = [c for _, c, _ in MEASURES]
    query = [
        {"code": "Sektor", "selection": {"filter": "item", "values": [SECTOR]}},
        {"code": "Yrke2012", "selection": {"filter": "item", "values": [SSYK_CODE]}},
        {"code": "Kon", "selection": {"filter": "item", "values": [SEX]}},
        {"code": "ContentsCode", "selection": {"filter": "item", "values": codes}},
        {"code": "Tid", "selection": {"filter": "item", "values": [year]}},
    ]
    r = requests.post(f"{BASE}/{TABLE}",
                      json={"query": query, "response": {"format": "json"}}, timeout=30)
    r.raise_for_status()
    raw = r.json()
    # PxWebApi returns measure columns in the TABLE's own ContentsCode order, not
    # the order we requested — so map each value by its column code, never by
    # position. Content columns carry type "c" and code == the ContentsCode value.
    col_codes = [c["code"] for c in raw["columns"] if c.get("type") == "c"]
    values = raw["data"][0]["values"]
    label_by_code = {code: lab for lab, code, _ in MEASURES}
    return {label_by_code[code]: float(v)
            for code, v in zip(col_codes, values) if code in label_by_code}


# ── Robust number parsing (handles EU / Swedish formatting) ───────────────────
def clean_number(raw) -> float | None:
    """'45 000,50 kr' / '45.000,50' / '45,000.50' / '55k' → float, else None."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw) if np.isfinite(raw) else None
    s = str(raw).strip().lower()
    if not s:
        return None
    mult = 1.0
    if s.endswith("k"):          # 55k → 55000
        mult, s = 1000.0, s[:-1]
    s = re.sub(r"[^0-9,.\-]", "", s)   # strip currency, letters, spaces
    if not re.search(r"\d", s):
        return None
    has_comma, has_dot = "," in s, "." in s
    if has_comma and has_dot:
        # the LAST separator is the decimal point; the other is thousands
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        thou = "." if dec == "," else ","
        s = s.replace(thou, "").replace(dec, ".")
    elif has_comma:
        # comma alone: decimal if it looks like ,dd  else thousands separator
        s = s.replace(",", ".") if re.search(r",\d{1,2}$", s) else s.replace(",", "")
    # dot alone → assume already a decimal point; leave as is
    try:
        return float(s) * mult
    except ValueError:
        return None


def parse_upload(name: str, data: bytes) -> pd.DataFrame:
    """Bytes → DataFrame. Excel via pandas/openpyxl, else delimited text.

    Only STRONG delimiters (, ; tab |) are treated as column separators — never
    plain spaces, because in this domain a space is a thousands separator
    ('41 000 kr'). A header row is inferred by whether the first cell parses as a
    number (headerless files/pastes of raw values are common).
    """
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
    # No column structure → one value per line (header only if first isn't numeric)
    if clean_number(first) is None:
        return pd.DataFrame({first: lines[1:]})
    return pd.DataFrame({"value": lines})


def weighted_percentiles(values: np.ndarray, weights: np.ndarray | None,
                         levels: list[int]) -> dict[int, float]:
    """Percentiles matching numpy's 'linear' method; weighted when weights given.

    numpy.percentile (linear / type-7) is the standard population estimator and
    is the closest match to how the SCB reference curve is derived, so overlay
    points line up on a like-for-like basis.
    """
    if weights is None:
        return {lv: float(np.percentile(values, lv)) for lv in levels}
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    # position of each sorted point on a 0..(n-1)-style scale, weighted
    pos = (cw - 0.5 * w) / w.sum()   # 0..1 plotting positions
    out = {}
    for lv in levels:
        out[lv] = float(np.interp(lv / 100.0, pos, v))
    return out


# ── Page ──────────────────────────────────────────────────────────────────────
# Runs both standalone (own port) and embedded in the main app (linked from the
# Admin panel). When embedded, app.py already called set_page_config once, so a
# second call raises — swallow it.
try:
    st.set_page_config(page_title="Import overlay — TEST", layout="wide")
except Exception:  # noqa: BLE001
    pass

# Soft gate: block signed-in non-admins (the Admin-panel link is the entry point).
# A logged-out session (incl. standalone testing) has no auth_user and passes.
_u = st.session_state.get("auth_user")
if _u is not None and _u.get("role") not in ("admin", "master"):
    st.error("🔒 This test page is for admins only.")
    st.stop()

st.title("🧪 Import-overlay prototype")
st.caption(
    "Throwaway test page. Reference curve = live SCB percentiles for "
    f"**{SSYK_NAME}**, all sectors, both sexes. "
    "Upload your own salaries to overlay computed percentiles, and optionally "
    "project the official curve forward to today."
)

# --- Reference curve -----------------------------------------------------------
ref_year = st.selectbox(
    "Reference data year (SCB)", REF_YEARS, index=REF_YEARS.index(DEFAULT_YEAR),
    help="Official data lags. Pick the published year to compare against; below "
         "you can project it forward to the current year.",
)
try:
    curve = fetch_scb_curve(ref_year)
except Exception as e:  # noqa: BLE001
    st.error(f"Could not fetch SCB data: {e}")
    st.stop()

ref_x = [lv for _, _, lv in MEASURES if lv is not None]
ref_y = [curve[lab] for lab, _, lv in MEASURES if lv is not None]
avg = curve.get("Average")

fig = go.Figure()

st.markdown(f"### 📊 Reference distribution ({ref_year})")
scb_cols = st.columns(len(ref_x) + 1)
for c, (lab, x, y) in zip(scb_cols, [("Average", None, avg)] + list(zip([f"P{v}" for v in ref_x], ref_x, ref_y))):
    if y is not None:
        c.metric(lab, f"{y:,.0f}")

# Grouped chart-curve visibility toggles (imported overlay has its own buttons).
proj_years = list(range(int(ref_year) + 1, CURRENT_YEAR + 1))
st.markdown("**Show on chart**")
tcols = st.columns(2)
show_ref = tcols[0].toggle("Reference curve", value=True)
show_aged = (tcols[1].toggle(f"Projection (aged to {CURRENT_YEAR})", value=True)
             if proj_years else False)

# --- Age the reference curve forward -------------------------------------------
# One slider per year between the (lagging) data year and today; each is an
# assumed % salary increase, COMPOUNDED year-on-year across all percentiles
# (incl. the average): 2024 = base×(1+p24), 2025 = 2024×(1+p25), …
st.divider()
st.markdown("### ⏩ Project the reference forward")
aged: dict[str, float] | None = None
if not proj_years:
    st.info(f"{ref_year} is already the current year — nothing to project.")
else:
    st.caption(
        f"Assumed **% salary increase** for each year from {ref_year} to "
        f"{CURRENT_YEAR}, **compounded** year-on-year (e.g. +3% then +4% "
        "lifts the base by ×1.03×1.04). Applied to every percentile and the average."
    )
    slider_cols = st.columns(len(proj_years))
    factor = 1.0
    for c, y in zip(slider_cols, proj_years):
        pct = c.slider(f"{y} (%)", min_value=0.0, max_value=15.0, value=3.0,
                       step=0.5, key=f"age_{y}")
        factor *= 1 + pct / 100
    st.caption(f"Cumulative uplift {ref_year}→{CURRENT_YEAR}: "
               f"**{(factor - 1) * 100:+.1f}%** (×{factor:.3f})")
    if show_aged:
        aged = {lab: v * factor for lab, v in curve.items()}

# --- Build reference / aged traces now that visibility is known ----------------
if show_ref:
    fig.add_trace(go.Scatter(
        x=ref_x, y=ref_y, mode="lines+markers", name="SCB (reference)",
        line=dict(color=REF_COLOR, width=3), marker=dict(size=9),
        hovertemplate="P%{x}: %{y:,.0f} SEK<extra>SCB</extra>",
    ))
    if avg:
        fig.add_hline(y=avg, line=dict(color=REF_COLOR, width=1, dash="dot"),
                      annotation_text=f"SCB average {avg:,.0f}",
                      annotation_position="top left")

if aged:
    fig.add_trace(go.Scatter(
        x=PCT_LEVELS, y=[aged[f"P{lv}"] for lv in PCT_LEVELS],
        mode="lines+markers", name=f"Reference aged to {CURRENT_YEAR} (proj.)",
        line=dict(color=AGE_COLOR, width=3, dash="dot"),
        marker=dict(size=9, symbol="triangle-up"),
        hovertemplate="P%{x}: %{y:,.0f} SEK<extra>Aged projection</extra>",
    ))
    if aged.get("Average"):
        fig.add_hline(y=aged["Average"], line=dict(color=AGE_COLOR, width=1, dash="dot"),
                      annotation_text=f"Aged average {aged['Average']:,.0f}",
                      annotation_position="top right")

# --- Import wizard -------------------------------------------------------------
st.divider()
st.markdown("### 📥 Import your own data to overlay")
st.caption(
    "🔒 Your file is processed in this session only — it is never uploaded to a "
    "server, saved to disk, or logged."
)

src = st.radio("Input", ["Upload a file", "Paste numbers"], horizontal=True,
               label_visibility="collapsed")

with st.expander("ℹ️ How should the file be structured?"):
    st.markdown(
        "The import is forgiving — you pick the salary column and set the unit "
        "afterwards — but a few things matter:\n\n"
        "**Works automatically**\n"
        "- One salary **per row**, all in a **single column** (extra columns are fine — you choose which).\n"
        "- Any number format: `55 600 kr`, `45 000,50`, `45,000.50`, `55k`.\n"
        "- Header row optional (auto-detected). Column name/position doesn't matter.\n\n"
        "**Please avoid** (these skew results silently)\n"
        "- **Totals / averages / summary rows** — they get counted as salaries.\n"
        "- **Wide layouts** (one person per column) or two numbers in one cell.\n"
        "- Excel: keep data on the **first sheet** with the header on **row 1** "
        "(no title rows above it).\n\n"
        "You'll always see the parsed count and computed percentiles in the "
        "preview below **before** anything is added to the chart."
    )

df: pd.DataFrame | None = None
if src == "Upload a file":
    up = st.file_uploader("File (.xlsx, .csv, .tsv, .txt)",
                          type=["xlsx", "xlsm", "xls", "csv", "tsv", "txt"])
    if up is not None:
        try:
            df = parse_upload(up.name, up.getvalue())
        except Exception as e:  # noqa: BLE001
            st.error(f"Couldn't parse that file: {e}")
else:
    txt = st.text_area("Paste one salary per line",
                       height=140, placeholder="52000\n48 500 kr\n61 250\n…")
    if txt.strip():
        # Paste is always one value per line — a comma here is a decimal/thousands
        # mark inside a number, never a column delimiter.
        df = pd.DataFrame({"Pasted salary": [ln for ln in txt.splitlines() if ln.strip()]})

if df is not None and not df.empty:
    st.markdown("#### 1 · Map & configure")
    st.dataframe(df.head(8), use_container_width=True, height=200)

    cols = list(df.columns.astype(str))
    # auto-pick the most-numeric column as default
    numeric_score = {c: df[c].map(clean_number).notna().mean() for c in cols}
    default_col = max(numeric_score, key=numeric_score.get)

    c1, c2, c3 = st.columns(3)
    sal_col = c1.selectbox("Salary column", cols, index=cols.index(default_col))
    weight_col = c2.selectbox("Weight / headcount column (optional)",
                              ["— none —"] + cols)
    unit = c3.selectbox("Unit of the values",
                        ["Monthly SEK", "Annual SEK (÷12)", "Thousands SEK (×1000)"])

    # Clean + convert to monthly SEK
    vals = df[sal_col].map(clean_number)
    n_raw = len(vals)
    vals = vals.dropna()
    dropped = n_raw - len(vals)
    if unit.startswith("Annual"):
        vals = vals / 12.0
    elif unit.startswith("Thousands"):
        vals = vals * 1000.0
    vals = vals[vals > 0]
    values = vals.to_numpy(dtype=float)

    weights = None
    if weight_col != "— none —":
        w = df.loc[vals.index, weight_col].map(clean_number)
        if w.notna().all() and (w > 0).all():
            weights = w.to_numpy(dtype=float)
        else:
            st.warning("Weight column has missing/invalid values — ignoring weights.")

    # Validation gate
    if len(values) == 0:
        st.error("No usable numeric salaries found in that column.")
    else:
        if dropped:
            st.info(f"Skipped {dropped} row(s) that weren't valid numbers.")
        if len(values) < 20:
            st.warning(
                f"Only {len(values)} values — percentiles (especially P10/P90) "
                "are unreliable at this sample size."
            )
        comp = weighted_percentiles(values, weights, PCT_LEVELS)
        your_avg = float(np.average(values, weights=weights))

        st.markdown("#### 2 · Preview computed percentiles")
        prev = pd.DataFrame({
            "Percentile": [f"P{lv}" for lv in PCT_LEVELS] + ["Average", "n"],
            "Your data (SEK)": [f"{comp[lv]:,.0f}" for lv in PCT_LEVELS]
            + [f"{your_avg:,.0f}", f"{len(values)}"],
            "SCB (SEK)": [f"{curve[f'P{lv}']:,.0f}" for lv in PCT_LEVELS]
            + [f"{avg:,.0f}", "—"],
        })
        st.dataframe(prev, use_container_width=True, hide_index=True)

        st.markdown("#### 3 · Overlay")
        if st.button("➕ Add overlay to chart", type="primary"):
            st.session_state["overlay"] = {"pct": comp, "avg": your_avg, "n": len(values)}
        if "overlay" in st.session_state and st.button("✕ Remove overlay"):
            del st.session_state["overlay"]

# --- Draw overlay if confirmed -------------------------------------------------
ov = st.session_state.get("overlay")
if ov:
    fig.add_trace(go.Scatter(
        x=PCT_LEVELS, y=[ov["pct"][lv] for lv in PCT_LEVELS],
        mode="lines+markers", name=f"Your data (n={ov['n']})",
        line=dict(color=YOU_COLOR, width=3, dash="dash"),
        marker=dict(size=10, symbol="diamond"),
        hovertemplate="P%{x}: %{y:,.0f} SEK<extra>Your data</extra>",
    ))
    fig.add_hline(y=ov["avg"], line=dict(color=YOU_COLOR, width=1, dash="dot"),
                  annotation_text=f"Your average {ov['avg']:,.0f}",
                  annotation_position="bottom right")

fig.update_layout(
    xaxis=dict(title="Percentile", tickvals=PCT_LEVELS,
               ticktext=[f"P{v}" for v in PCT_LEVELS]),
    yaxis=dict(title="Monthly salary (SEK)", tickformat=",.0f"),
    height=460, hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(t=40, r=20, b=40, l=60),
)
st.plotly_chart(fig, use_container_width=True)
