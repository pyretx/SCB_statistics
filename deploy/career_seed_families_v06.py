"""Curated Career Paths families — v0.6 additions: Healthcare & Nursing, Legal,
Logistics & Procurement, Engineering. Reproducible record of the direct-write seed.

Idempotent (upsert). All SSYK-2012 codes verified against SCB. Bands are indicative
Qvistin estimates within each role's own SSYK distribution; salaries computed live.
Engineering is anchored on mechanical/industrial codes (illustrative).

Run from the repo root:  python deploy/career_seed_families_v06.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth

sb = auth._client(service=True)

families = [
    {"family_id": "nursing", "name_en": "Healthcare & Nursing", "name_sv": "Vård och omvårdnad",
     "level_labels": ["Entry / Associate", "Professional", "Specialist", "Management"], "published": True},
    {"family_id": "legal", "name_en": "Legal", "name_sv": "Juridik",
     "level_labels": ["Entry / Associate", "Professional", "Senior / Specialist"], "published": True},
    {"family_id": "logistics", "name_en": "Logistics & Procurement", "name_sv": "Logistik och inköp",
     "level_labels": ["Entry / Associate", "Professional", "Specialist", "Management"], "published": True},
    {"family_id": "engineering", "name_en": "Engineering (mechanical & industrial)", "name_sv": "Ingenjör (maskin/industri)",
     "level_labels": ["Entry / Associate", "Professional", "Senior Professional", "Lead / Specialist", "Management"], "published": True},
]

# (id, family, en, sv, ssyk, track, level_index, level_label, lo, mid, hi, conf, variants, skills)
T = [
    # Nursing
    ("nur_assistant", "nursing", "Assistant Nurse", "Undersköterska", "5323", "ic", 1, "Entry / Associate",
     10, 32, 50, "moderate", ["Undersköterska", "Assistant Nurse"], ["patient care", "hygiene", "documentation"]),
    ("nur_nurse", "nursing", "Registered Nurse", "Sjuksköterska", "2221", "ic", 2, "Professional",
     25, 48, 62, "strong", ["Sjuksköterska", "Registered Nurse", "RN"], ["clinical care", "medication", "assessment"]),
    ("nur_specialist", "nursing", "Specialist Nurse", "Specialistsjuksköterska", "2239", "specialist", 3, "Specialist",
     50, 64, 78, "moderate", ["Specialistsjuksköterska", "Specialist Nurse"], ["specialist care", "clinical leadership"]),
    ("nur_unit_manager", "nursing", "Unit Manager, Health care (level 2)", "Enhetschef vård, nivå 2", "1512", "management", 1, "Management",
     40, 58, 75, "limited", ["Enhetschef", "Unit Manager", "Vårdenhetschef"], ["team leadership", "budget", "operations"]),
    ("nur_clinical_manager", "nursing", "Clinical / Operations Manager (level 1)", "Verksamhetschef vård, nivå 1", "1511", "management", 2, "Management",
     50, 68, 85, "limited", ["Verksamhetschef", "Clinical Manager"], ["operations leadership", "strategy", "exec stakeholder"]),
    # Legal
    ("leg_secretary", "legal", "Legal Secretary", "Paralegal / Juristsekreterare", "3342", "ic", 1, "Entry / Associate",
     10, 30, 48, "moderate", ["Paralegal", "Juristsekreterare", "Legal Assistant"], ["case admin", "drafting support", "research"]),
    ("leg_lawyer", "legal", "Lawyer", "Jurist / Advokat", "2611", "ic", 2, "Professional",
     30, 52, 68, "moderate", ["Jurist", "Advokat", "Associate"], ["legal analysis", "drafting", "advisory"]),
    ("leg_business_lawyer", "legal", "Corporate / Business Lawyer", "Affärsjurist / Bolagsjurist", "2614", "specialist", 3, "Senior / Specialist",
     55, 70, 85, "moderate", ["Bolagsjurist", "Affärsjurist", "Corporate Counsel"], ["contracts", "M&A", "compliance"]),
    ("leg_org_lawyer", "legal", "Legal Counsel (public administration)", "Förvaltnings- / organisationsjurist", "2615", "specialist", 3, "Senior / Specialist",
     50, 66, 80, "limited", ["Förvaltningsjurist", "Legal Counsel"], ["administrative law", "governance", "policy"]),
    # Logistics & Procurement
    ("log_assistant", "logistics", "Purchasing / Order Assistant", "Inköps- och orderassistent", "4115", "ic", 1, "Entry / Associate",
     10, 30, 48, "moderate", ["Inköpsassistent", "Order Administrator"], ["order handling", "supplier admin", "ERP"]),
    ("log_buyer", "logistics", "Buyer / Purchaser", "Inköpare / Upphandlare", "3323", "ic", 2, "Professional",
     25, 45, 62, "moderate", ["Inköpare", "Upphandlare", "Buyer"], ["sourcing", "negotiation", "contracts"]),
    ("log_warehouse_super", "logistics", "Warehouse & Terminal Supervisor", "Lager- och terminalchef", "4321", "specialist", 2, "Professional",
     25, 45, 62, "limited", ["Lagerchef", "Warehouse Supervisor"], ["warehouse ops", "scheduling", "safety"]),
    ("log_planner", "logistics", "Logistics / Production Engineer", "Logistik- och produktionsingenjör", "2141", "specialist", 3, "Specialist",
     45, 62, 78, "limited", ["Logistikingenjör", "Supply Planner"], ["supply planning", "optimisation", "S&OP"]),
    ("log_manager_l2", "logistics", "Supply & Logistics Manager (level 2)", "Inköps- och logistikchef, nivå 2", "1322", "management", 1, "Management",
     30, 52, 70, "limited", ["Logistikchef", "Supply Chain Manager"], ["team leadership", "budget", "supply strategy"]),
    ("log_manager_l1", "logistics", "Supply & Logistics Manager (level 1)", "Inköps- och logistikchef, nivå 1", "1321", "management", 2, "Management",
     45, 66, 85, "limited", ["Head of Supply Chain", "Inköpsdirektör"], ["supply strategy", "exec stakeholder", "org leadership"]),
    # Engineering (mechanical/industrial, illustrative)
    ("eng_technician", "engineering", "Engineering Technician", "Ingenjör / tekniker", "3114", "ic", 1, "Entry / Associate",
     10, 32, 50, "moderate", ["Maskintekniker", "Engineering Technician"], ["CAD", "testing", "documentation"]),
    ("eng_engineer", "engineering", "Engineer", "Civilingenjör (maskin)", "2144", "ic", 2, "Professional",
     25, 48, 62, "moderate", ["Civilingenjör", "Mechanical Engineer", "Konstruktör"], ["design", "analysis", "project work"]),
    ("eng_senior", "engineering", "Senior Engineer", "Senior ingenjör", "2144", "ic", 3, "Senior Professional",
     50, 64, 80, "moderate", ["Senior Engineer", "Senior Konstruktör"], ["complex design", "mentoring", "verification"]),
    ("eng_specialist", "engineering", "Specialist / Lead Engineer", "Specialist / ledande ingenjör", "2144", "specialist", 4, "Lead / Specialist",
     60, 74, 88, "limited", ["Lead Engineer", "Teknisk specialist"], ["technical authority", "standards", "cross-team"]),
    ("eng_manager_l2", "engineering", "Engineering Manager (level 2)", "Chef ingenjörsverksamhet, nivå 2", "1342", "management", 1, "Management",
     30, 54, 72, "limited", ["Engineering Manager", "Teknikchef"], ["people leadership", "delivery", "budget"]),
    ("eng_manager_l1", "engineering", "Engineering Manager (level 1)", "Chef ingenjörsverksamhet, nivå 1", "1341", "management", 2, "Management",
     45, 66, 85, "limited", ["Head of Engineering", "Teknisk direktör"], ["org leadership", "tech strategy", "exec stakeholder"]),
    ("eng_rd_manager", "engineering", "R&D Manager (level 2)", "Forsknings- och utvecklingschef, nivå 2", "1332", "management", 1, "Management",
     35, 56, 74, "limited", ["R&D Manager", "Utvecklingschef"], ["R&D leadership", "roadmap", "innovation"]),
]
ssyk = {t[0]: t[4] for t in T}

# (id, family, from, to, type, transferable, gaps, conf, explanation)
R = [
    ("nur_assistant__nurse", "nursing", "nur_assistant", "nur_nurse", "progression", ["patient care"], ["clinical care", "medication"], "moderate", "Qualify as a registered nurse (SSYK 5323→2221)."),
    ("nur_nurse__specialist", "nursing", "nur_nurse", "nur_specialist", "specialist", ["clinical care"], ["specialist care"], "moderate", "Specialise (SSYK 2221→2239)."),
    ("nur_nurse__unit_mgr", "nursing", "nur_nurse", "nur_unit_manager", "leadership", ["clinical care"], ["people leadership", "budget"], "limited", "Move into unit management (SSYK 2221→1512)."),
    ("nur_specialist__unit_mgr", "nursing", "nur_specialist", "nur_unit_manager", "leadership", ["clinical leadership"], ["operations", "budget"], "limited", "Move into unit management (SSYK 2239→1512)."),
    ("nur_unit__clinical", "nursing", "nur_unit_manager", "nur_clinical_manager", "leadership", ["operations"], ["strategy", "exec stakeholder"], "limited", "Progress to a more senior management level (1512→1511; level 1 is senior)."),
    ("leg_sec__lawyer", "legal", "leg_secretary", "leg_lawyer", "progression", ["research"], ["legal analysis", "advisory"], "moderate", "Qualify as a lawyer (SSYK 3342→2611)."),
    ("leg_lawyer__business", "legal", "leg_lawyer", "leg_business_lawyer", "specialist", ["legal analysis"], ["contracts", "M&A"], "moderate", "Specialise in corporate/business law (SSYK 2611→2614)."),
    ("leg_lawyer__org", "legal", "leg_lawyer", "leg_org_lawyer", "specialist", ["legal analysis"], ["administrative law", "governance"], "limited", "Move into public-administration legal work (SSYK 2611→2615)."),
    ("log_assistant__buyer", "logistics", "log_assistant", "log_buyer", "progression", ["order handling"], ["sourcing", "negotiation"], "moderate", "Move into a buyer role (SSYK 4115→3323)."),
    ("log_buyer__planner", "logistics", "log_buyer", "log_planner", "specialist", ["sourcing"], ["supply planning", "optimisation"], "limited", "Move into supply/logistics planning (SSYK 3323→2141)."),
    ("log_buyer__mgr_l2", "logistics", "log_buyer", "log_manager_l2", "leadership", ["negotiation"], ["people leadership", "budget"], "limited", "Move into supply management (SSYK 3323→1322)."),
    ("log_wh__mgr_l2", "logistics", "log_warehouse_super", "log_manager_l2", "leadership", ["warehouse ops"], ["supply strategy", "budget"], "limited", "Move into supply management (SSYK 4321→1322)."),
    ("log_mgr_l2__l1", "logistics", "log_manager_l2", "log_manager_l1", "leadership", ["supply strategy"], ["exec stakeholder", "org leadership"], "limited", "Progress to a more senior management level (1322→1321; level 1 is senior)."),
    ("eng_tech__engineer", "engineering", "eng_technician", "eng_engineer", "progression", ["CAD"], ["design", "analysis"], "moderate", "Move into a professional engineer role (SSYK 3114→2144)."),
    ("eng_engineer__senior", "engineering", "eng_engineer", "eng_senior", "progression", ["design"], ["complex design", "mentoring"], "moderate", "Seniority progression within the same SSYK (2144)."),
    ("eng_senior__specialist", "engineering", "eng_senior", "eng_specialist", "progression", ["complex design"], ["technical authority"], "limited", "Advanced specialist track within the same SSYK (2144)."),
    ("eng_senior__mgr_l2", "engineering", "eng_senior", "eng_manager_l2", "leadership", ["mentoring"], ["people leadership", "budget"], "limited", "Move into engineering management (SSYK 2144→1342)."),
    ("eng_mgr_l2__l1", "engineering", "eng_manager_l2", "eng_manager_l1", "leadership", ["delivery"], ["org leadership", "tech strategy"], "limited", "Progress to a more senior management level (1342→1341; level 1 is senior)."),
    ("eng_senior__rd", "engineering", "eng_senior", "eng_rd_manager", "leadership", ["verification"], ["R&D leadership", "roadmap"], "limited", "Move into R&D management (SSYK 2144→1332)."),
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
