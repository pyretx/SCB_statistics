"""Public page — Data sources & methodology.

Generated from the compliance register's public view (v_compliance_public via
compliance.public_all()); see docs/compliance-framework.md §8. Shows, per country,
the official provider/dataset, licence, required attribution, the original values
displayed, and each calculation Salary Explorer applies — with an Official vs.
Salary-Explorer-calculation legend. Text lives in content/about.toml.
"""
from __future__ import annotations

import html

import streamlit as st

import compliance
import content
import pubpage

M = content.load("about")["methodology"]
_TF_NAMES = M["transform_names"]
_LIMITS = M["limitations"]

pubpage.inject_base()
pubpage.top(active="methodology")


def _esc(x) -> str:
    return html.escape(str(x)) if x is not None else ""


def _display_name(slug: str) -> str:
    try:
        from core import registry
        c = registry.get(slug)
        if c:
            return c.name
    except Exception:
        pass
    return slug.replace("_", " ").title()


# ── Heading ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="pp-eyebrow">{M["eyebrow"]}</div>'
            f'<div class="pp-h1">{M["title"]}</div>'
            f'<div class="pp-intro">{M["intro"]}</div>'
            f'<div class="pp-principle">{M["principle"]}</div>',
            unsafe_allow_html=True)
st.write("")

rows, err = compliance.public_all()
if err:
    st.info(M["empty"])
    st.stop()
if not rows:
    st.info(M["empty"])
    st.stop()

# Country picker (by display name)
by_name = {}
for r in rows:
    by_name[_display_name(r["country_slug"])] = r
choice = st.selectbox(M["pick"], sorted(by_name), placeholder=M["pick_ph"], index=0)
rec = by_name.get(choice)
if not rec:
    st.info(M["one_empty"])
    st.stop()


def _row(label: str, value_html: str):
    return f'<div class="pp-row"><div class="pp-lbl">{label}</div><div class="pp-val">{value_html}</div></div>'


# ── Source card ──────────────────────────────────────────────────────────────
parts = []

# Provider
prov = _esc(rec.get("provider_name"))
if rec.get("provider_url"):
    prov = f'<a href="{_esc(rec["provider_url"])}" target="_blank" rel="noopener">{prov}</a>'
parts.append(_row(M["f_provider"], prov))

# Dataset (+ official table id) with official link
ds = _esc(rec.get("dataset_title"))
if rec.get("official_table_id"):
    ds += f' <span class="pp-mono" style="color:#98A0AC;">· {_esc(rec["official_table_id"])}</span>'
parts.append(_row(M["f_dataset"], ds))
if rec.get("dataset_url"):
    parts.append(_row(M["f_link"],
                      f'<a href="{_esc(rec["dataset_url"])}" target="_blank" rel="noopener">{M["open_link"]}</a>'))

# Reference period
period = _esc(rec.get("reference_period") or rec.get("reference_period_note"))
if period:
    parts.append(_row(M["f_period"], period))

# Licence: plain-language summary + link (verbatim only if required)
lic = _esc(rec.get("licence_summary_plain") or rec.get("licence_name"))
if rec.get("licence_name") and rec.get("licence_url"):
    lic += f' <a href="{_esc(rec["licence_url"])}" target="_blank" rel="noopener">({_esc(rec["licence_name"])} ↗)</a>'
if lic:
    parts.append(_row(M["f_licence"], lic))

# Required attribution
if rec.get("required_attribution_text"):
    parts.append(_row(M["f_attribution"],
                      f'<span class="pp-mono">{_esc(rec["required_attribution_text"])}</span>'))

# Original values shown
if rec.get("displayed_original_values"):
    parts.append(_row(M["f_original"],
                      f'<span class="pp-badge pp-badge-off">{M["badge_official"]}</span> '
                      f'{_esc(rec["displayed_original_values"])}'))

st.markdown(f'<div class="pp-card">{"".join(parts)}</div>', unsafe_allow_html=True)

# ── Salary Explorer calculations ─────────────────────────────────────────────
transforms = rec.get("transformations") or []
st.markdown(f'<div class="pp-lbl" style="width:auto;margin-bottom:8px;">{M["f_transforms"]}</div>',
            unsafe_allow_html=True)
if not transforms:
    st.markdown(f'<div class="pp-card"><div class="pp-sec-b">{M["f_none_transf"]}</div></div>',
                unsafe_allow_html=True)
else:
    tf_rows = []
    for t in transforms:
        name = _TF_NAMES.get(t.get("transform_type"), _esc(t.get("transform_type")))
        is_off = t.get("origin") == "source_provided"
        badge = (f'<span class="pp-badge pp-badge-off">{M["badge_official"]}</span>' if is_off
                 else f'<span class="pp-badge pp-badge-der">{M["badge_derived"]}</span>')
        note = _esc(t.get("method_note"))
        if t.get("inputs"):
            note += f' <span class="pp-mono" style="color:#98A0AC;">· {_esc(t["inputs"])}</span>'
        tf_rows.append(f'<div class="pp-tf"><div class="pp-tf-h">{badge}'
                       f'<span class="pp-tf-name">{name}</span></div>'
                       f'<div class="pp-tf-note">{note}</div></div>')
    st.markdown(f'<div class="pp-card">{"".join(tf_rows)}</div>', unsafe_allow_html=True)

# ── Limitations & comparability ──────────────────────────────────────────────
st.markdown(f'<div class="pp-lbl" style="width:auto;margin-bottom:8px;">{M["f_limitations"]}</div>'
            f'<div class="pp-card"><div class="pp-sec-b">{_esc(_LIMITS["default"])}'
            + (f' {_esc(rec["revision_policy"])}' if rec.get("revision_policy") else "")
            + '</div></div>', unsafe_allow_html=True)

# ── Legend ───────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="pp-card" style="background:#FAFBFC;">'
    f'<div class="pp-sec-h" style="font-size:15px;">{M["legend_title"]}</div>'
    f'<div class="pp-tf"><div class="pp-tf-h">'
    f'<span class="pp-badge pp-badge-off">{M["badge_official"]}</span></div>'
    f'<div class="pp-tf-note">{M["legend_official"]}</div></div>'
    f'<div class="pp-tf"><div class="pp-tf-h">'
    f'<span class="pp-badge pp-badge-der">{M["badge_derived"]}</span></div>'
    f'<div class="pp-tf-note">{M["legend_derived"]}</div></div></div>',
    unsafe_allow_html=True)
