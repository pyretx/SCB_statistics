"""Manual browser harness for the career-map component — no login needed.

    python -m streamlit run tests/career_map_harness.py --server.port=8503

(or via .claude/launch.json, name "cp-map-harness"). Renders the component with
a small fake payload and prints the value each click posts back to Python, so
the click -> setComponentValue -> rerun round trip can be verified without the
beta+auth gate in front of the real Career Paths tab."""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

import net_fix  # noqa: F401 — force IPv4 first
import streamlit as st
import streamlit.components.v1 as components

comp = components.declare_component(
    "se2_career_map", path=os.path.join(_REPO, "countries", "se2", "career_map"))

_LBL = {"eyebrow": "CAREER PATHS - HARNESS", "title": "Paths from {r}", "subtitle": "component test",
        "you_here": "YOU ARE HERE", "levels_lbl": "Steps to show:", "ads": "ads",
        "sub_roles": "roles", "specialisations": "specialisations", "range": "Estimated range",
        "vs": "vs occupation median", "gaps": "Typical gaps", "same_ssyk": "same SSYK",
        "ads_header": "FROM JOB ADS", "experience": "Typical experience",
        "education": "Top education req.", "skills": "Skills", "no_ads": "No ad signal.",
        "hint": "harness hint", "pick": "Click a role to see its detail."}

payload = {
    "occupation": {"name": "Test occupation", "ssyk": "2423", "base_mid": 40000,
                   "lo": 35000, "hi": 50000},
    "roles": {
        "role_a": {"name": "Role A", "subcode": "", "level": "Senior", "conf": "estimate",
                   "ssyk": "2423", "lo": 42000, "mid": 46000, "hi": 52000, "ad_count": 7,
                   "skills": ["Skill X"], "education": None, "experience": None},
        "role_b": {"name": "Role B", "subcode": "", "level": "Lead", "conf": "estimate",
                   "ssyk": "2423", "lo": 48000, "mid": 55000, "hi": 62000, "ad_count": 3,
                   "skills": [], "education": None, "experience": None},
    },
    "edges": [{"from": "entry", "to": "role_a", "rel": "progression", "same_ssyk": True,
               "gaps": [], "color": "#0A63A6"},
              {"from": "role_a", "to": "role_b", "rel": "leadership", "same_ssyk": False,
               "gaps": [], "color": "#B26A00"}],
    "legend": [{"color": "#0A63A6", "label": "Advance", "dashed": False}],
    "rellabels": {"progression": "Advance", "leadership": "Leadership"},
    "layer": {"role_a": 1, "role_b": 2},
    "parent": {"role_a": "entry", "role_b": "role_a"},
    "center_ids": ["entry"], "max_layer": 2,
    "subgroups": [{"label": "Test cluster", "anchor": "center", "count": 2, "ad_count": 9,
                   "members": [
                       {"title_id": "2423-6", "name": "Exec Search", "subcode": "2423-6",
                        "level": "Professional", "conf": "estimate", "ssyk": "2423",
                        "same_ssyk": True, "lo": 40000, "mid": 45000, "hi": 51000,
                        "diff": 5000, "ad_count": 5, "skills": ["Search"],
                        "education": None, "experience": None},
                       {"title_id": "2423-7", "name": "Recruiter", "subcode": "2423-7",
                        "level": "Professional", "conf": "estimate", "ssyk": "2423",
                        "same_ssyk": True, "lo": 38000, "mid": 42000, "hi": 48000,
                        "diff": 2000, "ad_count": 4, "skills": [],
                        "education": None, "experience": None}]}],
    "labels": _LBL,
}

st.set_page_config(page_title="career map harness", layout="wide")
val = comp(data=payload, key="cp_map_harness", default=None)
st.write("RETURNED:", val)
