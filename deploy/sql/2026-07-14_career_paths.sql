-- ─────────────────────────────────────────────────────────────────────────────
-- Career Paths (Sweden beta) — schema + curated v0 seed.
-- See docs/career-paths-assessment.md. Run ONCE in the Supabase SQL editor.
--
-- v0 is a CURATED, deterministic scaffold (no AI, no job-ad import). The runtime
-- reads approved rows; salaries are computed LIVE from the official SCB curve via
-- core.interp, so this table stores only INDICATIVE PERCENTILE BANDS (Qvistin
-- estimates), never salaries, and never the official statistics themselves.
--
-- Each title's band is interpreted against its OWN primary SSYK's SCB distribution
-- (a "Senior Developer" band is a position within SSYK 2512; an "ICT Manager L2"
-- band is a position within SSYK 1312). All SSYK-2012 codes verified against SCB.
--
-- Model:  cp_family ─1:N─ cp_title ─┐
--                                   ├─ cp_relationship (from_title → to_title)
-- Public pages read the curated view v_cp_public (published rows only).
-- ─────────────────────────────────────────────────────────────────────────────

-- ══ TABLES ═══════════════════════════════════════════════════════════════════
create table public.cp_family (
  family_id     text primary key,             -- 'hr' | 'software_ict'
  name_en       text not null,
  name_sv       text not null,
  level_labels  jsonb not null default '[]',  -- ordered level names for this family
  published     boolean not null default false,
  notes         text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create table public.cp_title (
  title_id      text primary key,             -- 'sw_senior_dev'
  family_id     text not null references public.cp_family(family_id),
  name_en       text not null,
  name_sv       text not null,
  primary_ssyk  text not null,                -- 4-digit SSYK-2012 (its salary curve)
  alt_ssyk      jsonb not null default '[]',
  track         text not null,                -- 'ic' | 'specialist' | 'management'
  level_index   integer not null default 1,   -- ordinal within the family/track
  level_label   text not null,                -- e.g. 'Senior Professional'
  -- INDICATIVE percentile band within primary_ssyk's own SCB distribution.
  lo_pct        numeric not null,
  mid_pct       numeric not null,
  hi_pct        numeric not null,
  confidence    text not null default 'limited',   -- strong|moderate|limited|experimental
  evidence      text not null default 'curated',   -- curated|ai_estimate|rule|human
  review_status text not null default 'draft',      -- draft|reviewed|approved
  published     boolean not null default false,
  raw_variants  jsonb not null default '[]',   -- example real-world title variants
  skills        jsonb not null default '[]',   -- typical skills (curated for v0)
  notes         text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  constraint cpt_track_chk check (track in ('ic','specialist','management')),
  constraint cpt_conf_chk  check (confidence in ('strong','moderate','limited','experimental')),
  constraint cpt_rev_chk   check (review_status in ('draft','reviewed','approved')),
  constraint cpt_pct_chk   check (lo_pct >= 0 and hi_pct <= 100 and lo_pct <= mid_pct and mid_pct <= hi_pct)
);
create index cp_title_family_idx on public.cp_title(family_id);
create index cp_title_ssyk_idx   on public.cp_title(primary_ssyk);

create table public.cp_relationship (
  rel_id        text primary key,
  family_id     text not null references public.cp_family(family_id),
  from_title    text not null references public.cp_title(title_id),
  to_title      text not null references public.cp_title(title_id),
  rel_type      text not null,                -- progression|leadership|specialist|lateral|entry|related
  same_ssyk     boolean not null default false,
  transferable_skills jsonb not null default '[]',
  skill_gaps    jsonb not null default '[]',
  confidence    text not null default 'limited',
  review_status text not null default 'draft',
  published     boolean not null default false,
  explanation   text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  constraint cpr_type_chk check (rel_type in ('progression','leadership','specialist','lateral','entry','related')),
  constraint cpr_conf_chk check (confidence in ('strong','moderate','limited','experimental')),
  constraint cpr_rev_chk  check (review_status in ('draft','reviewed','approved'))
);
create index cp_rel_family_idx on public.cp_relationship(family_id);
create index cp_rel_from_idx   on public.cp_relationship(from_title);

comment on table public.cp_title is
  'Career Paths canonical titles. lo/mid/hi_pct are INDICATIVE Qvistin percentile
   estimates within the title''s primary_ssyk SCB distribution — not official, not
   salaries. Salaries are computed live from the SCB curve (core.interp).';

-- ══ RLS (admin write; anon/authenticated get nothing on base tables) ═════════
alter table public.cp_family       enable row level security;
alter table public.cp_title        enable row level security;
alter table public.cp_relationship enable row level security;

do $$
declare t text;
begin
  foreach t in array array['cp_family','cp_title','cp_relationship'] loop
    execute format($p$create policy %1$s_admin_sel on public.%1$I for select to authenticated
      using (coalesce(auth.jwt()->'app_metadata'->>'role','') in ('admin','master'));$p$, t);
    execute format($p$create policy %1$s_admin_ins on public.%1$I for insert to authenticated
      with check (coalesce(auth.jwt()->'app_metadata'->>'role','') in ('admin','master'));$p$, t);
    execute format($p$create policy %1$s_admin_upd on public.%1$I for update to authenticated
      using (coalesce(auth.jwt()->'app_metadata'->>'role','') in ('admin','master'))
      with check (coalesce(auth.jwt()->'app_metadata'->>'role','') in ('admin','master'));$p$, t);
  end loop;
end $$;

-- ══ PUBLIC VIEW (published rows only) ════════════════════════════════════════
create or replace view public.v_cp_title_public as
  select t.* from public.cp_title t
  join public.cp_family f on f.family_id = t.family_id
  where t.published = true and f.published = true;

create or replace view public.v_cp_rel_public as
  select r.* from public.cp_relationship r
  join public.cp_family f on f.family_id = r.family_id
  where r.published = true and f.published = true;

grant select on public.v_cp_title_public, public.v_cp_rel_public to anon, authenticated;

-- ══ SEED — families ══════════════════════════════════════════════════════════
insert into public.cp_family (family_id, name_en, name_sv, level_labels, published) values
  ('hr','Human Resources','HR och personal',
     '["Entry / Associate","Professional","Senior Professional","Lead / Advanced","Management"]', true),
  ('software_ict','Software & ICT','Mjukvara och IT',
     '["Entry / Associate","Professional","Senior Professional","Lead / Advanced","Principal / Staff","Management"]', true);

-- ══ SEED — HR titles (bands are indicative positions within each primary_ssyk) ═
insert into public.cp_title
  (title_id, family_id, name_en, name_sv, primary_ssyk, track, level_index, level_label,
   lo_pct, mid_pct, hi_pct, confidence, published, raw_variants, skills) values
  ('hr_admin','hr','HR Administrator','HR-administratör','4112','ic',1,'Entry / Associate',
     25,42,60,'moderate',true,'["HR-administratör","Löneadministratör","HR Assistant"]','["HR admin","payroll basics","HR systems"]'),
  ('hr_coordinator','hr','HR Coordinator','HR-koordinator','2423','ic',1,'Entry / Associate',
     10,28,45,'moderate',true,'["HR-koordinator","HR Coordinator"]','["coordination","recruitment support","onboarding"]'),
  ('hr_specialist','hr','HR Specialist','HR-specialist','2423','ic',2,'Professional',
     30,48,62,'moderate',true,'["HR-specialist","HR Generalist","HR Advisor"]','["labour law","recruitment","employee relations"]'),
  ('hr_senior_specialist','hr','Senior HR Specialist','Senior HR-specialist','2423','ic',3,'Senior Professional',
     50,64,78,'moderate',true,'["Senior HR-specialist","Senior HR Advisor"]','["complex ER","policy","stakeholder mgmt"]'),
  ('hr_bp','hr','HR Business Partner','HR Business Partner','2423','ic',3,'Senior Professional',
     50,66,80,'moderate',true,'["HRBP","HR Business Partner","People Partner","HR Partner"]','["business partnering","org design","change"]'),
  ('hr_senior_bp','hr','Senior HR Business Partner','Senior HR Business Partner','2423','ic',4,'Lead / Advanced',
     62,74,88,'limited',true,'["Senior HRBP","Sr HR Business Partner","Lead People Partner"]','["strategic partnering","leadership coaching"]'),
  ('hr_reward','hr','Compensation & Benefits Specialist','Comp & Benefits-specialist','2423','specialist',3,'Senior Professional',
     55,70,82,'limited',true,'["C&B Specialist","Reward Specialist","Ersättningsspecialist"]','["reward","benchmarking","job architecture"]'),
  ('hr_senior_reward','hr','Senior Reward Specialist','Senior Reward-specialist','2423','specialist',4,'Lead / Advanced',
     65,78,90,'limited',true,'["Senior Reward Specialist","Total Reward Lead"]','["total reward","incentive design","governance"]'),
  ('hr_org_dev','hr','Organisation Developer','Lednings- och organisationsutvecklare','2421','specialist',4,'Lead / Advanced',
     50,68,82,'limited',true,'["Organisationsutvecklare","OD Specialist","L&D Lead"]','["org development","L&D","facilitation"]'),
  ('hr_manager_l2','hr','HR Manager (level 2)','Personal- och HR-chef, nivå 2','1222','management',1,'Management',
     30,52,72,'limited',true,'["HR-chef","HR Manager","People Manager"]','["team leadership","budget","HR strategy"]'),
  ('hr_manager_l1','hr','Head of HR (level 1)','Personal- och HR-chef, nivå 1','1221','management',2,'Management',
     45,66,85,'limited',true,'["Head of HR","HR Director","HR-direktör"]','["HR strategy","exec stakeholder","org leadership"]');

-- ══ SEED — Software & ICT titles ═════════════════════════════════════════════
insert into public.cp_title
  (title_id, family_id, name_en, name_sv, primary_ssyk, track, level_index, level_label,
   lo_pct, mid_pct, hi_pct, confidence, published, raw_variants, skills) values
  ('sw_junior','software_ict','Junior Software Developer','Juniorutvecklare','2512','ic',1,'Entry / Associate',
     10,25,40,'moderate',true,'["Junior Developer","Graduate Developer","Juniorutvecklare"]','["programming basics","git","one language"]'),
  ('sw_dev','software_ict','Software Developer','Systemutvecklare','2512','ic',2,'Professional',
     25,45,58,'strong',true,'["Software Developer","Systemutvecklare","Backend Developer","Frontend Developer"]','["software design","testing","CI/CD"]'),
  ('sw_senior','software_ict','Senior Software Developer','Senior systemutvecklare','2512','ic',3,'Senior Professional',
     50,64,78,'strong',true,'["Senior Developer","Senior Systemutvecklare","Senior Engineer"]','["architecture","mentoring","complex systems"]'),
  ('sw_lead','software_ict','Lead Developer','Ledande utvecklare','2512','ic',4,'Lead / Advanced',
     62,74,86,'moderate',true,'["Lead Developer","Tech Lead","Ledande utvecklare"]','["technical leadership","design ownership","cross-team"]'),
  ('sw_staff','software_ict','Staff Engineer','Staff Engineer','2512','ic',5,'Principal / Staff',
     72,82,92,'limited',true,'["Staff Engineer","Staff Software Engineer"]','["org-wide impact","systems strategy"]'),
  ('sw_principal','software_ict','Principal Engineer','Principal Engineer','2512','ic',5,'Principal / Staff',
     78,87,95,'limited',true,'["Principal Engineer","Principalutvecklare"]','["technical strategy","deep expertise"]'),
  ('sw_architect','software_ict','ICT Architect','IT-arkitekt','2511','specialist',4,'Lead / Advanced',
     45,66,80,'moderate',true,'["IT-arkitekt","Solution Architect","System Architect","Lösningsarkitekt"]','["solution architecture","integration","non-functional design"]'),
  ('sw_tester','software_ict','System Tester','Systemtestare','2514','ic',2,'Professional',
     25,45,60,'moderate',true,'["Systemtestare","QA Engineer","Testare"]','["test design","automation","QA"]'),
  ('sw_test_lead','software_ict','Test Manager','Testledare','2514','specialist',3,'Senior Professional',
     55,70,85,'limited',true,'["Testledare","Test Manager","QA Lead"]','["test strategy","team coordination","quality gates"]'),
  ('sw_security','software_ict','ICT Security Specialist','IT-säkerhetsspecialist','2516','specialist',3,'Senior Professional',
     45,66,82,'moderate',true,'["IT-säkerhetsspecialist","Security Engineer","Cybersäkerhetsspecialist"]','["security","threat modelling","compliance"]'),
  ('sw_ict_manager_l2','software_ict','ICT Manager (level 2)','IT-chef, nivå 2','1312','management',1,'Management',
     30,52,70,'limited',true,'["IT-chef","Engineering Manager","Utvecklingschef"]','["people leadership","delivery","budget"]'),
  ('sw_ict_manager_l1','software_ict','ICT Manager (level 1)','IT-chef, nivå 1','1311','management',2,'Management',
     45,66,85,'limited',true,'["Head of Engineering","CTO-nära","IT-direktör"]','["org leadership","tech strategy","exec stakeholder"]');

-- ══ SEED — relationships (career moves; direction from_title → to_title) ══════
insert into public.cp_relationship
  (rel_id, family_id, from_title, to_title, rel_type, same_ssyk, confidence, published,
   transferable_skills, skill_gaps, explanation) values
  -- HR progression
  ('hr_admin__specialist','hr','hr_admin','hr_specialist','progression',false,'moderate',true,
     '["HR admin","HR systems"]','["labour law","recruitment"]','Move from administration into a specialist HR role (SSYK changes 4112→2423).'),
  ('hr_specialist__senior','hr','hr_specialist','hr_senior_specialist','progression',true,'moderate',true,
     '["labour law","employee relations"]','["complex ER","policy design"]','Deepen expertise within the same SSYK (2423).'),
  ('hr_specialist__bp','hr','hr_specialist','hr_bp','progression',true,'moderate',true,
     '["employee relations","stakeholder mgmt"]','["business partnering","org design"]','Move onto the business-partnering track within the same SSYK (2423).'),
  ('hr_bp__senior_bp','hr','hr_bp','hr_senior_bp','progression',true,'moderate',true,
     '["business partnering"]','["strategic partnering"]','Seniority progression within the same SSYK (2423).'),
  ('hr_senior_bp__manager_l2','hr','hr_senior_bp','hr_manager_l2','leadership',false,'limited',true,
     '["stakeholder mgmt","org design"]','["people leadership","budget ownership"]','Move into people management (SSYK changes 2423→1222).'),
  ('hr_manager_l2__l1','hr','hr_manager_l2','hr_manager_l1','leadership',false,'limited',true,
     '["team leadership","HR strategy"]','["exec stakeholder","org leadership"]','Progress to a more senior management level (1222→1221; level 1 is senior).'),
  ('hr_specialist__reward','hr','hr_specialist','hr_reward','specialist',true,'limited',true,
     '["HR analysis"]','["reward","benchmarking"]','Specialise in compensation & benefits (largely within 2423).'),
  ('hr_reward__senior_reward','hr','hr_reward','hr_senior_reward','specialist',true,'limited',true,
     '["reward","benchmarking"]','["total reward strategy"]','Seniority within the reward specialism.'),
  ('hr_senior_reward__org_dev','hr','hr_senior_reward','hr_org_dev','specialist',false,'limited',true,
     '["governance","analysis"]','["org development","L&D"]','Broaden into organisation development (SSYK changes 2423→2421).'),
  -- Software progression (same SSYK 2512)
  ('sw_junior__dev','software_ict','sw_junior','sw_dev','progression',true,'strong',true,
     '["programming"]','["software design","testing"]','Standard early progression within SSYK 2512.'),
  ('sw_dev__senior','software_ict','sw_dev','sw_senior','progression',true,'strong',true,
     '["software design","CI/CD"]','["architecture","mentoring"]','Seniority progression within SSYK 2512.'),
  ('sw_senior__lead','software_ict','sw_senior','sw_lead','progression',true,'moderate',true,
     '["architecture","mentoring"]','["technical leadership","cross-team"]','Into technical leadership, still within SSYK 2512.'),
  ('sw_lead__staff','software_ict','sw_lead','sw_staff','progression',true,'limited',true,
     '["technical leadership"]','["org-wide impact"]','Advanced individual-contributor track within SSYK 2512.'),
  ('sw_lead__principal','software_ict','sw_lead','sw_principal','progression',true,'limited',true,
     '["design ownership"]','["technical strategy"]','Principal IC track within SSYK 2512.'),
  -- Software specialist moves (SSYK changes)
  ('sw_dev__architect','software_ict','sw_dev','sw_architect','specialist',false,'moderate',true,
     '["software design","integration"]','["solution architecture","non-functional design"]','Move to an architecture specialism (SSYK changes 2512→2511).'),
  ('sw_dev__security','software_ict','sw_dev','sw_security','specialist',false,'moderate',true,
     '["software fundamentals"]','["security","threat modelling"]','Move to an ICT security specialism (SSYK changes 2512→2516).'),
  ('sw_dev__tester','software_ict','sw_dev','sw_tester','lateral',false,'limited',true,
     '["testing"]','["test strategy","automation"]','Lateral move into a testing/QA role (SSYK changes 2512→2514).'),
  -- Software management (SSYK changes)
  ('sw_lead__manager_l2','software_ict','sw_lead','sw_ict_manager_l2','leadership',false,'limited',true,
     '["technical leadership","cross-team"]','["people leadership","budget"]','Move into engineering management (SSYK changes 2512→1312).'),
  ('sw_manager_l2__l1','software_ict','sw_ict_manager_l2','sw_ict_manager_l1','leadership',false,'limited',true,
     '["delivery","people leadership"]','["org leadership","tech strategy"]','Progress to a more senior management level (1312→1311; level 1 is senior).');

-- ══ Audit note ═══════════════════════════════════════════════════════════════
comment on view public.v_cp_title_public is 'Published career-path titles for the Sweden beta tab.';
