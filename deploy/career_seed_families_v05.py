"""Curated Career Paths families — v0.5 additions (Finance & Accounting, Sales &
Marketing). Reproducible record of the direct-write seed (see docs/career-paths.md).

Idempotent (upsert). All SSYK-2012 codes verified against SCB. Bands are indicative
Qvistin estimates within each role's own SSYK distribution (wide + overlapping);
salaries are computed live on the tab, never stored here.

Run from the repo root:  python deploy/career_seed_families_v05.py
(Requires the Supabase service key in secrets; writes to cp_family/cp_title/cp_relationship.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth

sb = auth._client(service=True)

families = [
    {"family_id": "finance", "name_en": "Finance & Accounting", "name_sv": "Ekonomi och redovisning",
     "level_labels": ["Entry / Associate", "Professional", "Senior Professional", "Specialist", "Management"],
     "published": True},
    {"family_id": "sales_marketing", "name_en": "Sales & Marketing", "name_sv": "Försäljning och marknad",
     "level_labels": ["Entry / Associate", "Professional", "Senior Professional", "Specialist", "Management"],
     "published": True},
]

# (id, family, en, sv, ssyk, track, level_index, level_label, lo, mid, hi, conf, variants, skills)
T = [
    ("fin_assistant", "finance", "Accounting Associate", "Redovisningsekonom", "3313", "ic", 1, "Entry / Associate",
     10, 28, 45, "moderate", ["Redovisningsekonom", "Accounting Assistant", "Ekonomiassistent"], ["bookkeeping", "ledgers", "reconciliation"]),
    ("fin_accountant", "finance", "Accountant", "Revisor / Redovisningsansvarig", "2411", "ic", 2, "Professional",
     25, 45, 60, "moderate", ["Accountant", "Revisor", "Redovisningsansvarig"], ["accounting", "reporting", "closing"]),
    ("fin_senior_accountant", "finance", "Senior Accountant", "Senior redovisningsansvarig", "2411", "ic", 3, "Senior Professional",
     50, 64, 78, "moderate", ["Senior Accountant", "Group Accountant"], ["group reporting", "IFRS", "audit liaison"]),
    ("fin_controller", "finance", "Financial Controller", "Controller", "2412", "specialist", 3, "Specialist",
     50, 66, 80, "moderate", ["Controller", "Business Controller", "Financial Controller"], ["controlling", "budgeting", "analysis"]),
    ("fin_analyst", "finance", "Financial Analyst", "Finansanalytiker", "2413", "specialist", 3, "Specialist",
     50, 66, 82, "moderate", ["Financial Analyst", "Finansanalytiker", "Investment Adviser"], ["valuation", "modelling", "forecasting"]),
    ("fin_manager_l2", "finance", "Finance Manager (level 2)", "Ekonomichef, nivå 2", "1212", "management", 1, "Management",
     30, 52, 70, "limited", ["Ekonomichef", "Finance Manager"], ["team leadership", "budget ownership", "finance strategy"]),
    ("fin_manager_l1", "finance", "Head of Finance / CFO (level 1)", "Ekonomi- och finanschef, nivå 1", "1211", "management", 2, "Management",
     45, 66, 85, "limited", ["CFO", "Head of Finance", "Finanschef"], ["financial strategy", "exec stakeholder", "org leadership"]),
    ("sm_assistant", "sales_marketing", "Market & Sales Assistant", "Marknads- och försäljningsassistent", "4114", "ic", 1, "Entry / Associate",
     10, 28, 45, "moderate", ["Sales Assistant", "Marknadsassistent"], ["coordination", "CRM", "campaign support"]),
    ("sm_sales_rep", "sales_marketing", "Sales Representative", "Företagssäljare", "3322", "ic", 2, "Professional",
     25, 45, 62, "moderate", ["Företagssäljare", "Account Manager", "Sales Rep"], ["b2b sales", "negotiation", "pipeline"]),
    ("sm_marketer", "sales_marketing", "Marketing Specialist", "Marknadsförare", "2431", "ic", 2, "Professional",
     30, 50, 65, "moderate", ["Marknadsförare", "Marketing Specialist", "Digital Marketer"], ["marketing", "campaigns", "analytics"]),
    ("sm_senior_marketer", "sales_marketing", "Senior Marketing Specialist", "Senior marknadsförare", "2431", "ic", 3, "Senior Professional",
     52, 66, 80, "limited", ["Senior Marketing Specialist", "Marketing Lead"], ["strategy", "brand", "budget"]),
    ("sm_pr", "sales_marketing", "Communications / PR Specialist", "Kommunikatör / PR-specialist", "2432", "specialist", 3, "Specialist",
     45, 62, 78, "moderate", ["Kommunikatör", "PR Specialist", "Informatör"], ["communications", "PR", "content"]),
    ("sm_manager_l2", "sales_marketing", "Sales & Marketing Manager (level 2)", "Försäljnings- och marknadschef, nivå 2", "1252", "management", 1, "Management",
     30, 52, 70, "limited", ["Marketing Manager", "Sales Manager", "Marknadschef"], ["team leadership", "budget", "go-to-market"]),
    ("sm_manager_l1", "sales_marketing", "Sales & Marketing Manager (level 1)", "Försäljnings- och marknadschef, nivå 1", "1251", "management", 2, "Management",
     45, 66, 85, "limited", ["CMO", "Head of Sales", "Marknadsdirektör"], ["commercial strategy", "exec stakeholder", "org leadership"]),
]
ssyk = {t[0]: t[4] for t in T}

# (id, family, from, to, type, transferable, gaps, conf, explanation)
R = [
    ("fin_assistant__accountant", "finance", "fin_assistant", "fin_accountant", "progression", ["bookkeeping"], ["reporting", "closing"], "moderate", "Move from accounting support into a qualified accountant role (SSYK 3313→2411)."),
    ("fin_accountant__senior", "finance", "fin_accountant", "fin_senior_accountant", "progression", ["accounting", "reporting"], ["group reporting", "IFRS"], "moderate", "Seniority progression within the same SSYK (2411)."),
    ("fin_accountant__controller", "finance", "fin_accountant", "fin_controller", "specialist", ["reporting", "analysis"], ["controlling", "budgeting"], "moderate", "Move into controlling (SSYK 2411→2412)."),
    ("fin_accountant__analyst", "finance", "fin_accountant", "fin_analyst", "specialist", ["analysis"], ["valuation", "modelling"], "limited", "Move into financial analysis (SSYK 2411→2413)."),
    ("fin_controller__manager_l2", "finance", "fin_controller", "fin_manager_l2", "leadership", ["controlling", "analysis"], ["people leadership", "budget ownership"], "limited", "Move into finance management (SSYK 2412→1212)."),
    ("fin_manager_l2__l1", "finance", "fin_manager_l2", "fin_manager_l1", "leadership", ["finance strategy"], ["exec stakeholder", "org leadership"], "limited", "Progress to a more senior management level (1212→1211; level 1 is senior)."),
    ("sm_assistant__sales_rep", "sales_marketing", "sm_assistant", "sm_sales_rep", "progression", ["CRM"], ["b2b sales", "negotiation"], "moderate", "Move into a sales role (SSYK 4114→3322)."),
    ("sm_assistant__marketer", "sales_marketing", "sm_assistant", "sm_marketer", "progression", ["campaign support"], ["marketing", "analytics"], "moderate", "Move into a marketing role (SSYK 4114→2431)."),
    ("sm_marketer__senior", "sales_marketing", "sm_marketer", "sm_senior_marketer", "progression", ["marketing", "campaigns"], ["strategy", "brand"], "moderate", "Seniority progression within the same SSYK (2431)."),
    ("sm_marketer__pr", "sales_marketing", "sm_marketer", "sm_pr", "specialist", ["content"], ["communications", "PR"], "limited", "Move into communications/PR (SSYK 2431→2432)."),
    ("sm_sales_rep__manager_l2", "sales_marketing", "sm_sales_rep", "sm_manager_l2", "leadership", ["b2b sales"], ["people leadership", "budget"], "limited", "Move into sales/marketing management (SSYK 3322→1252)."),
    ("sm_senior__manager_l2", "sales_marketing", "sm_senior_marketer", "sm_manager_l2", "leadership", ["strategy"], ["people leadership"], "limited", "Move into sales/marketing management (SSYK 2431→1252)."),
    ("sm_manager_l2__l1", "sales_marketing", "sm_manager_l2", "sm_manager_l1", "leadership", ["go-to-market"], ["commercial strategy", "org leadership"], "limited", "Progress to a more senior management level (1252→1251; level 1 is senior)."),
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
    print(f"Seeded 2 families, {len(T)} titles, {len(R)} relationships.")
