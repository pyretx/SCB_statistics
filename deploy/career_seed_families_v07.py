"""Curated Career Paths families — v0.7: Education & Teaching, Construction &
Skilled Trades, Hospitality & Restaurant. Reproducible direct-write seed.

Idempotent (upsert). SSYK-2012 codes verified against SCB. Bilingual (name_sv).
Bands are indicative Qvistin estimates within each role's own SSYK distribution.

Run from the repo root:  python deploy/career_seed_families_v07.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth

sb = auth._client(service=True)

_LL = ["Entry / Associate", "Professional", "Specialist", "Management"]
families = [
    {"family_id": "education", "name_en": "Education & Teaching", "name_sv": "Utbildning och skola",
     "level_labels": _LL, "published": True},
    {"family_id": "construction", "name_en": "Construction & Skilled Trades", "name_sv": "Bygg och hantverk",
     "level_labels": _LL, "published": True},
    {"family_id": "hospitality", "name_en": "Hospitality & Restaurant", "name_sv": "Restaurang och besöksnäring",
     "level_labels": _LL, "published": True},
]

# (id, family, en, sv, ssyk, track, level_index, level_label, lo, mid, hi, conf, variants, skills)
T = [
    # Education
    ("edu_aide", "education", "Teacher's Aide", "Elevassistent", "5312", "ic", 1, "Entry / Associate",
     10, 32, 50, "moderate", ["Elevassistent", "Teaching Aide"], ["support", "supervision"]),
    ("edu_preschool", "education", "Preschool Teacher", "Förskollärare", "2343", "ic", 2, "Professional",
     25, 45, 60, "moderate", ["Förskollärare", "Preschool Teacher"], ["pedagogy", "child development"]),
    ("edu_primary", "education", "Primary School Teacher", "Grundskollärare", "2341", "ic", 2, "Professional",
     30, 50, 64, "moderate", ["Grundskollärare", "Lärare"], ["teaching", "curriculum", "assessment"]),
    ("edu_secondary", "education", "Secondary School Teacher", "Gymnasielärare", "2330", "ic", 2, "Professional",
     35, 54, 68, "moderate", ["Gymnasielärare", "Ämneslärare"], ["subject teaching", "assessment"]),
    ("edu_special", "education", "Special Needs Teacher", "Speciallärare", "2351", "specialist", 3, "Specialist",
     40, 58, 74, "limited", ["Speciallärare", "Specialpedagog"], ["special education", "IEPs"]),
    ("edu_lecturer", "education", "University Lecturer", "Universitetslektor", "2312", "specialist", 3, "Specialist",
     45, 64, 82, "limited", ["Universitetslektor", "Lecturer"], ["higher education", "research", "supervision"]),
    ("edu_principal", "education", "School Principal", "Rektor", "1411", "management", 1, "Management",
     45, 66, 85, "limited", ["Rektor", "Principal"], ["school leadership", "budget", "staff"]),
    # Construction & Skilled Trades
    ("con_labourer", "construction", "Construction Labourer", "Byggnadsarbetare", "9310", "ic", 1, "Entry / Associate",
     10, 35, 55, "moderate", ["Byggnadsarbetare", "Construction Worker"], ["site work", "safety"]),
    ("con_carpenter", "construction", "Carpenter", "Snickare", "7111", "ic", 2, "Professional",
     25, 48, 64, "moderate", ["Snickare", "Träarbetare", "Carpenter"], ["carpentry", "blueprints"]),
    ("con_electrician", "construction", "Electrician", "Elektriker", "7411", "ic", 2, "Professional",
     30, 50, 66, "moderate", ["Elektriker", "Installationselektriker"], ["installation", "regulations"]),
    ("con_plumber", "construction", "Plumber / Heating Fitter", "VVS-montör", "7125", "ic", 2, "Professional",
     30, 50, 66, "moderate", ["VVS-montör", "Rörmokare", "Plumber"], ["plumbing", "heating", "regulations"]),
    ("con_supervisor", "construction", "Construction Supervisor", "Arbetsledare bygg", "3121", "specialist", 3, "Specialist",
     45, 62, 78, "limited", ["Arbetsledare", "Site Supervisor"], ["scheduling", "quality", "coordination"]),
    ("con_manager_l2", "construction", "Production Manager, Construction (level 2)", "Produktionschef bygg, nivå 2", "1362", "management", 1, "Management",
     35, 56, 74, "limited", ["Produktionschef", "Platschef"], ["project delivery", "budget", "safety"]),
    ("con_manager_l1", "construction", "Production Manager, Construction (level 1)", "Produktionschef bygg, nivå 1", "1361", "management", 2, "Management",
     50, 68, 85, "limited", ["Produktionschef", "Projektchef bygg"], ["programme delivery", "org leadership"]),
    # Hospitality & Restaurant
    ("hos_kitchen_help", "hospitality", "Kitchen Helper", "Köksbiträde", "9412", "ic", 1, "Entry / Associate",
     10, 35, 55, "moderate", ["Köksbiträde", "Kitchen Assistant"], ["prep", "hygiene"]),
    ("hos_cook", "hospitality", "Cook", "Kock", "5120", "ic", 2, "Professional",
     20, 42, 58, "moderate", ["Kock", "Cook"], ["cooking", "food safety"]),
    ("hos_waiter", "hospitality", "Waiter", "Servitör", "5131", "ic", 2, "Professional",
     15, 38, 55, "moderate", ["Servitör", "Servitris", "Waiter"], ["service", "POS", "upselling"]),
    ("hos_chef", "hospitality", "Chef / Sous-chef", "Kock / Souschef", "3451", "specialist", 3, "Specialist",
     30, 50, 68, "moderate", ["Souschef", "Chef", "Kökschef"], ["menu", "kitchen leadership", "costing"]),
    ("hos_rest_manager_l2", "hospitality", "Restaurant Manager (level 2)", "Restaurangchef, nivå 2", "1722", "management", 1, "Management",
     25, 48, 68, "limited", ["Restaurangchef", "Restaurant Manager"], ["operations", "staffing", "budget"]),
    ("hos_rest_manager_l1", "hospitality", "Restaurant Manager (level 1)", "Restaurangchef, nivå 1", "1721", "management", 2, "Management",
     40, 60, 80, "limited", ["Restaurangchef", "Krögare"], ["P&L", "multi-site", "strategy"]),
    ("hos_hotel_manager_l2", "hospitality", "Hotel Manager (level 2)", "Hotellchef, nivå 2", "1712", "management", 1, "Management",
     30, 52, 72, "limited", ["Hotellchef", "Hotel Manager"], ["hotel operations", "guest experience"]),
]
ssyk = {t[0]: t[4] for t in T}

# (id, family, from, to, type, transferable, gaps, conf, explanation)
R = [
    ("edu_aide__preschool", "education", "edu_aide", "edu_preschool", "progression", ["support"], ["pedagogy"], "moderate", "Qualify as a preschool teacher (SSYK 5312→2343)."),
    ("edu_primary__special", "education", "edu_primary", "edu_special", "specialist", ["teaching"], ["special education"], "limited", "Specialise in special-needs teaching (SSYK 2341→2351)."),
    ("edu_primary__principal", "education", "edu_primary", "edu_principal", "leadership", ["teaching"], ["school leadership", "budget"], "limited", "Move into school leadership (SSYK 2341→1411)."),
    ("edu_secondary__principal", "education", "edu_secondary", "edu_principal", "leadership", ["subject teaching"], ["school leadership"], "limited", "Move into school leadership (SSYK 2330→1411)."),
    ("edu_secondary__lecturer", "education", "edu_secondary", "edu_lecturer", "specialist", ["subject teaching"], ["research", "higher education"], "limited", "Move into higher education (SSYK 2330→2312)."),
    ("con_labourer__carpenter", "construction", "con_labourer", "con_carpenter", "progression", ["site work"], ["carpentry"], "moderate", "Train into a skilled trade (SSYK 9310→7111)."),
    ("con_carpenter__supervisor", "construction", "con_carpenter", "con_supervisor", "leadership", ["carpentry"], ["scheduling", "coordination"], "limited", "Move into site supervision (SSYK 7111→3121)."),
    ("con_electrician__supervisor", "construction", "con_electrician", "con_supervisor", "leadership", ["installation"], ["scheduling", "coordination"], "limited", "Move into site supervision (SSYK 7411→3121)."),
    ("con_supervisor__mgr_l2", "construction", "con_supervisor", "con_manager_l2", "leadership", ["coordination"], ["project delivery", "budget"], "limited", "Move into construction management (SSYK 3121→1362)."),
    ("con_mgr_l2__l1", "construction", "con_manager_l2", "con_manager_l1", "leadership", ["project delivery"], ["programme delivery", "org leadership"], "limited", "Progress to a more senior management level (1362→1361; level 1 is senior)."),
    ("hos_help__cook", "hospitality", "hos_kitchen_help", "hos_cook", "progression", ["prep"], ["cooking", "food safety"], "moderate", "Train as a cook (SSYK 9412→5120)."),
    ("hos_cook__chef", "hospitality", "hos_cook", "hos_chef", "progression", ["cooking"], ["menu", "kitchen leadership"], "moderate", "Progress toward chef roles (SSYK 5120→3451)."),
    ("hos_waiter__rest_l2", "hospitality", "hos_waiter", "hos_rest_manager_l2", "leadership", ["service"], ["operations", "budget"], "limited", "Move into restaurant management (SSYK 5131→1722)."),
    ("hos_chef__rest_l2", "hospitality", "hos_chef", "hos_rest_manager_l2", "leadership", ["kitchen leadership"], ["operations", "staffing"], "limited", "Move into restaurant management (SSYK 3451→1722)."),
    ("hos_rest_l2__l1", "hospitality", "hos_rest_manager_l2", "hos_rest_manager_l1", "leadership", ["operations"], ["P&L", "multi-site"], "limited", "Progress to a more senior management level (1722→1721; level 1 is senior)."),
    ("hos_rest_l1__hotel", "hospitality", "hos_rest_manager_l1", "hos_hotel_manager_l2", "lateral", ["operations", "P&L"], ["hotel operations"], "limited", "Move across into hotel management (SSYK 1721→1712)."),
]

if __name__ == "__main__":
    sb.table("cp_family").upsert(families, on_conflict="family_id").execute()
    sb.table("cp_title").upsert([{
        "title_id": t[0], "family_id": t[1], "name_en": t[2], "name_sv": t[3], "primary_ssyk": t[4],
        "track": t[5], "level_index": t[6], "level_label": t[7], "lo_pct": t[8], "mid_pct": t[9],
        "hi_pct": t[10], "confidence": t[11], "evidence": "curated", "review_status": "draft",
        "published": True, "raw_variants": t[12], "skills": t[13]} for t in T],
        on_conflict="title_id").execute()
    sb.table("cp_relationship").upsert([{
        "rel_id": r[0], "family_id": r[1], "from_title": r[2], "to_title": r[3], "rel_type": r[4],
        "same_ssyk": ssyk[r[2]] == ssyk[r[3]], "transferable_skills": r[5], "skill_gaps": r[6],
        "confidence": r[7], "review_status": "draft", "published": True, "explanation": r[8]} for r in R],
        on_conflict="rel_id").execute()
    print(f"Seeded {len(families)} families, {len(T)} titles, {len(R)} relationships.")
