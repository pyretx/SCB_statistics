"""Curated Career Paths families — v0.8: Administration & Office, Social Work &
Care, Medicine (Physicians), Science & Research, Media/Design/Creative, Real Estate
& Facilities, Manufacturing & Production, Banking & Insurance.

Reproducible direct-write seed. Idempotent (upsert). SSYK-2012 codes verified
against SCB and checked for cross-family collisions. Bilingual (name_sv). Bands are
indicative Qvistin estimates within each role's own SSYK distribution.

Run from the repo root:  python deploy/career_seed_families_v08.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth

sb = auth._client(service=True)

_L4 = ["Entry / Associate", "Professional", "Specialist", "Management"]
families = [
    {"family_id": "admin_office", "name_en": "Administration & Office", "name_sv": "Administration och kontor", "level_labels": _L4, "published": True},
    {"family_id": "social_care", "name_en": "Social Work & Care", "name_sv": "Socialt arbete och omsorg", "level_labels": _L4, "published": True},
    {"family_id": "medicine", "name_en": "Medicine (Physicians)", "name_sv": "Läkare", "level_labels": ["Professional", "Senior professional"], "published": True},
    {"family_id": "science", "name_en": "Science & Research", "name_sv": "Naturvetenskap och forskning", "level_labels": _L4, "published": True},
    {"family_id": "creative", "name_en": "Media, Design & Creative", "name_sv": "Media, design och kreativt", "level_labels": _L4, "published": True},
    {"family_id": "real_estate", "name_en": "Real Estate & Facilities", "name_sv": "Fastighet och förvaltning", "level_labels": _L4, "published": True},
    {"family_id": "manufacturing", "name_en": "Manufacturing & Production", "name_sv": "Tillverkning och produktion", "level_labels": _L4, "published": True},
    {"family_id": "banking", "name_en": "Banking & Insurance", "name_sv": "Bank och försäkring", "level_labels": _L4, "published": True},
]

# (id, family, en, sv, ssyk, track, level_index, level_label, lo, mid, hi, conf, variants, skills)
T = [
    # Administration & Office
    ("ao_clerk", "admin_office", "Office Clerk", "Kontorsassistent", "4119", "ic", 1, "Entry / Associate", 10, 30, 48, "moderate", ["Kontorsassistent", "Office Clerk"], ["admin", "filing", "scheduling"]),
    ("ao_secretary", "admin_office", "Administrative Secretary", "Administrativ sekreterare", "3359", "ic", 2, "Professional", 20, 42, 58, "moderate", ["Administrativ sekreterare", "Handläggare"], ["administration", "coordination"]),
    ("ao_exec_secretary", "admin_office", "Executive Secretary", "Ledningssekreterare", "3343", "specialist", 3, "Specialist", 30, 50, 66, "moderate", ["Ledningssekreterare", "Executive Assistant"], ["exec support", "governance", "planning"]),
    ("ao_supervisor", "admin_office", "Office Supervisor", "Kontorschef / arbetsledare", "3341", "management", 1, "Management", 35, 55, 72, "limited", ["Kontorschef", "Office Manager"], ["team leadership", "operations"]),
    # Social Work & Care
    ("sc_care_worker", "social_care", "Personal Care Worker", "Vårdbiträde / personlig assistent", "5330", "ic", 1, "Entry / Associate", 10, 32, 50, "moderate", ["Vårdbiträde", "Personlig assistent"], ["personal care", "support"]),
    ("sc_associate", "social_care", "Social Work Associate", "Behandlingsassistent", "3411", "ic", 2, "Professional", 25, 45, 60, "moderate", ["Behandlingsassistent", "Stödpedagog"], ["support work", "documentation"]),
    ("sc_social_worker", "social_care", "Social Worker", "Socialsekreterare", "2661", "ic", 2, "Professional", 35, 54, 68, "moderate", ["Socialsekreterare", "Social Worker"], ["casework", "assessment", "legislation"]),
    ("sc_counsellor", "social_care", "Counsellor", "Kurator", "2662", "specialist", 3, "Specialist", 40, 58, 74, "limited", ["Kurator", "Counsellor"], ["counselling", "psychosocial support"]),
    ("sc_unit_mgr", "social_care", "Unit Manager, Social Care (level 2)", "Enhetschef socialt arbete, nivå 2", "1522", "management", 1, "Management", 40, 58, 75, "limited", ["Enhetschef", "Unit Manager"], ["team leadership", "budget"]),
    ("sc_dept_mgr", "social_care", "Department Manager, Social Care (level 1)", "Avdelningschef socialt arbete, nivå 1", "1521", "management", 2, "Management", 50, 68, 85, "limited", ["Avdelningschef", "Department Manager"], ["operations leadership", "strategy"]),
    # Medicine (Physicians)
    ("med_resident", "medicine", "Resident Physician", "ST-läkare", "2212", "ic", 1, "Professional", 40, 58, 72, "moderate", ["ST-läkare", "Resident"], ["clinical work", "diagnosis"]),
    ("med_gp", "medicine", "General Practitioner", "Allmänläkare", "2219", "ic", 1, "Professional", 45, 62, 78, "moderate", ["Allmänläkare", "Distriktsläkare"], ["primary care", "diagnosis"]),
    ("med_specialist", "medicine", "Specialist Physician", "Specialistläkare", "2211", "ic", 2, "Senior professional", 60, 74, 88, "moderate", ["Specialistläkare", "Överläkare"], ["specialist care", "clinical leadership"]),
    # Science & Research
    ("sci_assistant", "science", "Research Assistant", "Forskningsassistent", "2313", "ic", 1, "Entry / Associate", 15, 38, 55, "moderate", ["Forskningsassistent", "Research Assistant"], ["research support", "data"]),
    ("sci_labtech", "science", "Laboratory Technician", "Laboratorietekniker", "3212", "ic", 1, "Entry / Associate", 20, 42, 58, "moderate", ["Laborant", "Lab Technician"], ["lab work", "analysis"]),
    ("sci_chemist", "science", "Chemist", "Kemist", "2113", "ic", 2, "Professional", 35, 54, 70, "moderate", ["Kemist", "Chemist"], ["chemistry", "analysis", "research"]),
    ("sci_biologist", "science", "Biologist", "Biolog", "2131", "ic", 2, "Professional", 35, 54, 70, "moderate", ["Biolog", "Biologist"], ["biology", "field work", "research"]),
    ("sci_physicist", "science", "Physicist", "Fysiker", "2111", "ic", 2, "Professional", 35, 56, 72, "moderate", ["Fysiker", "Physicist"], ["physics", "modelling", "research"]),
    ("sci_environ", "science", "Environmental Scientist", "Miljövetare", "2183", "specialist", 3, "Specialist", 35, 54, 70, "limited", ["Miljövetare", "Environmental Scientist"], ["environment", "assessment", "compliance"]),
    ("sci_rd_mgr", "science", "R&D Manager", "Forskningschef", "1331", "management", 1, "Management", 50, 68, 85, "limited", ["Forskningschef", "R&D Manager"], ["research leadership", "roadmap"]),
    # Media, Design & Creative
    ("cre_photographer", "creative", "Photographer", "Fotograf", "3431", "ic", 1, "Entry / Associate", 15, 38, 55, "moderate", ["Fotograf", "Photographer"], ["photography", "editing"]),
    ("cre_graphic", "creative", "Graphic Designer", "Grafisk designer", "2172", "ic", 2, "Professional", 25, 45, 60, "moderate", ["Grafisk designer", "Graphic Designer"], ["design", "typography", "branding"]),
    ("cre_product", "creative", "Product Designer", "Industridesigner", "2171", "ic", 2, "Professional", 30, 50, 64, "moderate", ["Industridesigner", "Product Designer"], ["product design", "prototyping"]),
    ("cre_journalist", "creative", "Journalist", "Journalist", "2642", "ic", 2, "Professional", 25, 45, 60, "moderate", ["Journalist", "Reporter"], ["writing", "reporting", "editing"]),
    ("cre_writer", "creative", "Author / Writer", "Författare", "2641", "specialist", 3, "Specialist", 25, 48, 66, "limited", ["Författare", "Copywriter"], ["writing", "content", "storytelling"]),
    ("cre_comms_mgr_l2", "creative", "Communications Manager (level 2)", "Kommunikationschef, nivå 2", "1242", "management", 1, "Management", 30, 52, 70, "limited", ["Kommunikationschef", "Comms Manager"], ["communications", "team leadership"]),
    ("cre_comms_mgr_l1", "creative", "Communications Manager (level 1)", "Kommunikationschef, nivå 1", "1241", "management", 2, "Management", 45, 66, 85, "limited", ["Kommunikationsdirektör", "Head of Comms"], ["comms strategy", "org leadership"]),
    # Real Estate & Facilities
    ("re_caretaker", "real_estate", "Building Caretaker", "Fastighetsskötare", "5152", "ic", 1, "Entry / Associate", 10, 32, 50, "moderate", ["Fastighetsskötare", "Caretaker"], ["maintenance", "facilities"]),
    ("re_admin", "real_estate", "Real Estate Administrator", "Fastighetsadministratör", "3335", "ic", 2, "Professional", 20, 42, 58, "moderate", ["Fastighetsadministratör", "Property Admin"], ["administration", "tenancy", "contracts"]),
    ("re_agent", "real_estate", "Real Estate Agent", "Fastighetsmäklare", "3334", "ic", 2, "Professional", 25, 50, 72, "moderate", ["Fastighetsmäklare", "Estate Agent"], ["sales", "valuation", "negotiation"]),
    ("re_mgr_l2", "real_estate", "Real Estate Manager (level 2)", "Fastighetschef, nivå 2", "1352", "management", 1, "Management", 30, 52, 70, "limited", ["Fastighetschef", "Property Manager"], ["portfolio", "budget", "operations"]),
    ("re_mgr_l1", "real_estate", "Real Estate Manager (level 1)", "Fastighetschef, nivå 1", "1351", "management", 2, "Management", 45, 66, 85, "limited", ["Fastighetsdirektör", "Head of Real Estate"], ["portfolio strategy", "org leadership"]),
    # Manufacturing & Production
    ("mfg_assembler", "manufacturing", "Assembler", "Montör", "8211", "ic", 1, "Entry / Associate", 10, 35, 55, "moderate", ["Montör", "Assembler"], ["assembly", "quality"]),
    ("mfg_operator", "manufacturing", "Machine Operator", "Maskinoperatör", "8189", "ic", 2, "Professional", 15, 40, 58, "moderate", ["Maskinoperatör", "Machine Operator"], ["operations", "monitoring", "maintenance"]),
    ("mfg_welder", "manufacturing", "Welder", "Svetsare", "7212", "ic", 2, "Professional", 25, 48, 64, "moderate", ["Svetsare", "Welder"], ["welding", "blueprints", "safety"]),
    ("mfg_mgr_l2", "manufacturing", "Production Manager, Manufacturing (level 2)", "Produktionschef tillverkning, nivå 2", "1372", "management", 1, "Management", 35, 56, 74, "limited", ["Produktionschef", "Production Manager"], ["delivery", "budget", "lean"]),
    ("mfg_mgr_l1", "manufacturing", "Production Manager, Manufacturing (level 1)", "Produktionschef tillverkning, nivå 1", "1371", "management", 2, "Management", 50, 68, 85, "limited", ["Produktionschef", "Plant Manager"], ["plant leadership", "org leadership"]),
    # Banking & Insurance
    ("bank_clerk", "banking", "Bank Clerk", "Banktjänsteman", "3312", "ic", 1, "Entry / Associate", 15, 40, 58, "moderate", ["Banktjänsteman", "Bank Clerk"], ["banking", "customer service"]),
    ("bank_adviser", "banking", "Insurance Adviser", "Försäkringsrådgivare", "3321", "ic", 2, "Professional", 25, 48, 64, "moderate", ["Försäkringsrådgivare", "Insurance Adviser"], ["advisory", "products", "sales"]),
    ("bank_claims", "banking", "Claims Assessor", "Skadereglerare", "3314", "ic", 2, "Professional", 25, 46, 62, "moderate", ["Skadereglerare", "Claims Assessor"], ["claims", "assessment", "regulation"]),
    ("bank_trader", "banking", "Trader / Fund Administrator", "Fondadministratör / mäklare", "2414", "specialist", 3, "Specialist", 45, 64, 85, "limited", ["Fondadministratör", "Trader"], ["markets", "risk", "settlement"]),
    ("bank_mgr_l2", "banking", "Financial & Insurance Manager (level 2)", "Bank- och försäkringschef, nivå 2", "1612", "management", 1, "Management", 35, 56, 74, "limited", ["Bankchef", "Insurance Manager"], ["team leadership", "budget", "compliance"]),
    ("bank_mgr_l1", "banking", "Financial & Insurance Manager (level 1)", "Bank- och försäkringschef, nivå 1", "1611", "management", 2, "Management", 50, 70, 88, "limited", ["Bankdirektör", "Head of Banking"], ["strategy", "org leadership"]),
]
ssyk = {t[0]: t[4] for t in T}

def rel(rid, fam, a, b, typ, transf, gaps, conf, expl):
    return (rid, fam, a, b, typ, transf, gaps, conf, expl)

R = [
    rel("ao_clerk__sec", "admin_office", "ao_clerk", "ao_secretary", "progression", ["admin"], ["coordination"], "moderate", "Progress into an administrative secretary role (SSYK 4119→3359)."),
    rel("ao_sec__exec", "admin_office", "ao_secretary", "ao_exec_secretary", "progression", ["administration"], ["exec support", "governance"], "moderate", "Move into executive/specialised support (SSYK 3359→3343)."),
    rel("ao_exec__sup", "admin_office", "ao_exec_secretary", "ao_supervisor", "leadership", ["planning"], ["team leadership"], "limited", "Move into office management (SSYK 3343→3341)."),
    rel("ao_sec__sup", "admin_office", "ao_secretary", "ao_supervisor", "leadership", ["coordination"], ["team leadership"], "limited", "Move into office management (SSYK 3359→3341)."),
    rel("sc_care__assoc", "social_care", "sc_care_worker", "sc_associate", "progression", ["support"], ["support work"], "moderate", "Move into support/treatment work (SSYK 5330→3411)."),
    rel("sc_assoc__sw", "social_care", "sc_associate", "sc_social_worker", "progression", ["support work"], ["casework", "legislation"], "moderate", "Qualify as a social worker (SSYK 3411→2661)."),
    rel("sc_sw__couns", "social_care", "sc_social_worker", "sc_counsellor", "specialist", ["casework"], ["counselling"], "limited", "Specialise as a counsellor (SSYK 2661→2662)."),
    rel("sc_sw__unit", "social_care", "sc_social_worker", "sc_unit_mgr", "leadership", ["casework"], ["team leadership", "budget"], "limited", "Move into unit management (SSYK 2661→1522)."),
    rel("sc_unit__dept", "social_care", "sc_unit_mgr", "sc_dept_mgr", "leadership", ["team leadership"], ["operations leadership"], "limited", "Progress to a more senior management level (1522→1521; level 1 is senior)."),
    rel("med_res__spec", "medicine", "med_resident", "med_specialist", "progression", ["clinical work"], ["specialist care"], "moderate", "Complete specialist training (SSYK 2212→2211)."),
    rel("med_res__gp", "medicine", "med_resident", "med_gp", "progression", ["clinical work"], ["primary care"], "moderate", "Move into general practice (SSYK 2212→2219)."),
    rel("sci_asst__chem", "science", "sci_assistant", "sci_chemist", "progression", ["research support"], ["chemistry"], "moderate", "Move into a scientist role (SSYK 2313→2113)."),
    rel("sci_lab__chem", "science", "sci_labtech", "sci_chemist", "progression", ["lab work"], ["research"], "moderate", "Move into a scientist role (SSYK 3212→2113)."),
    rel("sci_chem__rd", "science", "sci_chemist", "sci_rd_mgr", "leadership", ["research"], ["research leadership"], "limited", "Move into R&D management (SSYK 2113→1331)."),
    rel("sci_bio__rd", "science", "sci_biologist", "sci_rd_mgr", "leadership", ["research"], ["research leadership"], "limited", "Move into R&D management (SSYK 2131→1331)."),
    rel("cre_gfx__prod", "creative", "cre_graphic", "cre_product", "lateral", ["design"], ["prototyping"], "limited", "Move across into product design (SSYK 2172→2171)."),
    rel("cre_jour__comms", "creative", "cre_journalist", "cre_comms_mgr_l2", "leadership", ["writing"], ["communications", "team leadership"], "limited", "Move into communications management (SSYK 2642→1242)."),
    rel("cre_gfx__comms", "creative", "cre_graphic", "cre_comms_mgr_l2", "leadership", ["branding"], ["communications"], "limited", "Move into communications management (SSYK 2172→1242)."),
    rel("cre_comms_l2__l1", "creative", "cre_comms_mgr_l2", "cre_comms_mgr_l1", "leadership", ["communications"], ["comms strategy"], "limited", "Progress to a more senior management level (1242→1241; level 1 is senior)."),
    rel("re_care__admin", "real_estate", "re_caretaker", "re_admin", "progression", ["facilities"], ["administration"], "moderate", "Move into property administration (SSYK 5152→3335)."),
    rel("re_admin__mgr", "real_estate", "re_admin", "re_mgr_l2", "leadership", ["tenancy"], ["portfolio", "budget"], "limited", "Move into property management (SSYK 3335→1352)."),
    rel("re_agent__mgr", "real_estate", "re_agent", "re_mgr_l2", "leadership", ["sales"], ["portfolio", "operations"], "limited", "Move into property management (SSYK 3334→1352)."),
    rel("re_mgr_l2__l1", "real_estate", "re_mgr_l2", "re_mgr_l1", "leadership", ["portfolio"], ["org leadership"], "limited", "Progress to a more senior management level (1352→1351; level 1 is senior)."),
    rel("mfg_asm__op", "manufacturing", "mfg_assembler", "mfg_operator", "progression", ["assembly"], ["operations"], "moderate", "Move into machine operation (SSYK 8211→8189)."),
    rel("mfg_op__mgr", "manufacturing", "mfg_operator", "mfg_mgr_l2", "leadership", ["operations"], ["delivery", "budget"], "limited", "Move into production management (SSYK 8189→1372)."),
    rel("mfg_weld__mgr", "manufacturing", "mfg_welder", "mfg_mgr_l2", "leadership", ["welding"], ["delivery", "lean"], "limited", "Move into production management (SSYK 7212→1372)."),
    rel("mfg_mgr_l2__l1", "manufacturing", "mfg_mgr_l2", "mfg_mgr_l1", "leadership", ["delivery"], ["plant leadership"], "limited", "Progress to a more senior management level (1372→1371; level 1 is senior)."),
    rel("bank_clerk__adv", "banking", "bank_clerk", "bank_adviser", "progression", ["banking"], ["advisory", "products"], "moderate", "Move into advisory (SSYK 3312→3321)."),
    rel("bank_clerk__claims", "banking", "bank_clerk", "bank_claims", "progression", ["banking"], ["claims", "assessment"], "moderate", "Move into claims (SSYK 3312→3314)."),
    rel("bank_adv__trader", "banking", "bank_adviser", "bank_trader", "specialist", ["products"], ["markets", "risk"], "limited", "Specialise into markets/fund roles (SSYK 3321→2414)."),
    rel("bank_adv__mgr", "banking", "bank_adviser", "bank_mgr_l2", "leadership", ["advisory"], ["team leadership", "budget"], "limited", "Move into management (SSYK 3321→1612)."),
    rel("bank_mgr_l2__l1", "banking", "bank_mgr_l2", "bank_mgr_l1", "leadership", ["team leadership"], ["strategy", "org leadership"], "limited", "Progress to a more senior management level (1612→1611; level 1 is senior)."),
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
