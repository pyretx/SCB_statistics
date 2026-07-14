-- ─────────────────────────────────────────────────────────────────────────────
-- Compliance register for Salary Explorer — Phase 0 (schema + public view + seed).
-- Implements docs/compliance-framework.md §5 (Supabase data model) and §6 (gate).
--
-- Run ONCE in the Supabase SQL editor (Dashboard → SQL Editor → New query).
-- The project has no automated migration runner — SQL files under deploy/sql/
-- are applied manually and kept here as the record of what was run.
--
-- Model:  provider ─1:N─ dataset ─1:N─ access_method
--                            └────────── country_impl ─1:N─ transformation
--                                             └── assessment (per permission dimension)
--                                             └── review_log (append-only)
-- Terms live on the DATASET (never inherited wholesale from the provider).
-- Public pages read ONLY the curated view v_compliance_public (never base tables).
-- ─────────────────────────────────────────────────────────────────────────────

-- ══════════════════════════════════════════════════════════════════════════════
--  1. TABLES
-- ══════════════════════════════════════════════════════════════════════════════

-- ── Provider ── organisation; defaults + contacts only (terms live on datasets) ─
create table public.compliance_provider (
  provider_id         text primary key,          -- slug: 'eurostat', 'ssb', 'inegi'
  name                text not null,
  country_or_org      text,
  homepage_url        text,
  default_licence_ref text,                       -- default only, overridable per dataset
  contact_email       text,
  reuse_policy_url    text,
  notes               text,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

comment on table public.compliance_provider is
  'Data providers (organisations). Holds defaults + contacts only; operative
   licence terms live on compliance_dataset, per docs/compliance-framework.md §2.';

-- ── Dataset ── a specific table/report/microdata product. TERMS LIVE HERE. ──────
create table public.compliance_dataset (
  dataset_id                 text primary key,    -- 'eurostat_earn_ses_21', 'ssb_11418'
  provider_id                text not null references public.compliance_provider(provider_id),
  title                      text not null,
  official_table_id          text,
  dataset_url                text,
  data_type                  text not null,       -- see check below
  licence_name               text,
  licence_url                text,
  licence_version            text,
  licence_summary_plain      text,                -- plain-language summary shown publicly
  licence_verbatim_required  boolean not null default false,
  required_attribution_text  text,                -- verbatim string the UI must render
  required_disclaimer_text   text,
  required_link_url          text,
  personal_data              text not null default 'none',
  reference_period_note      text,
  revision_policy            text,
  created_at                 timestamptz not null default now(),
  updated_at                 timestamptz not null default now(),

  constraint cds_data_type_chk check (data_type in
    ('official_table','report_pdf','microdata','derived_bundle','fx_rates','cpi_index')),
  constraint cds_personal_data_chk check (personal_data in
    ('none','pseudonymised','identifiable'))
);

comment on table public.compliance_dataset is
  'Datasets. Licence + permission terms attach HERE (one provider may publish
   several datasets under different terms). FX/CPI conversion sources are datasets
   too (data_type fx_rates / cpi_index), per framework §1.6.';

-- ── Access method ── how we ingest a dataset; channel constraints live here ─────
create table public.compliance_access_method (
  access_id                       text primary key,   -- 'estat_0003426315_api'
  dataset_id                      text not null references public.compliance_dataset(dataset_id),
  method                          text not null,      -- see check below
  endpoint_or_file                text,
  requires_api_key                boolean not null default false,
  key_terms_url                   text,
  rate_limit                      text,
  automated_download_allowed      text,               -- five-state or free note
  microdata_confidentiality_terms text,               -- small-cell suppression, no re-id
  caching_allowed_note            text,
  created_at                      timestamptz not null default now(),
  updated_at                      timestamptz not null default now(),

  constraint cam_method_chk check (method in
    ('api','excel','csv','pdf','microdata_download'))
);

comment on table public.compliance_access_method is
  'Ingestion channel per dataset. API-key / rate-limit / automated-download /
   microdata-confidentiality constraints attach here, not to the numbers.';

-- ── Country implementation ── join + release gate ──────────────────────────────
create table public.compliance_country_impl (
  impl_id                    text primary key,    -- 'eu_ses__belgium', 'ssb_11418__norway'
  country_slug               text not null,       -- matches the app registry slug
  dataset_id                 text not null references public.compliance_dataset(dataset_id),
  access_id                  text not null references public.compliance_access_method(access_id),
  displayed_original_values  text,                -- what we show unchanged
  reference_period           text,                -- mirrors snapshot year/years
  clearance_overall          text not null default 'likely_verify',
  release_status             text not null default 'internal_only',
  grandfathered              boolean not null default false,
  public_publishable         boolean not null default false,
  created_at                 timestamptz not null default now(),
  updated_at                 timestamptz not null default now(),

  constraint cci_clearance_chk check (clearance_overall in
    ('confirmed','likely_verify','provider_confirm','owner_review','restricted')),
  constraint cci_release_chk check (release_status in
    ('blocked','internal_only','beta_ok','public_ok'))
);

comment on table public.compliance_country_impl is
  'One country''s use of one dataset via one access method. Holds the release gate.
   grandfathered=true = pre-existing country kept live by owner decision (framework
   §1.4). clearance_overall is the worst of its dimension assessments.';

create index cci_country_idx on public.compliance_country_impl (country_slug);
create index cci_dataset_idx on public.compliance_country_impl (dataset_id);

-- ── Assessment ── one row per permission dimension (the five-state verdict) ─────
create table public.compliance_assessment (
  assessment_id     uuid primary key default gen_random_uuid(),
  subject_type      text not null,                -- 'dataset' | 'access' | 'impl'
  subject_id        text not null,                -- FK-by-convention to the above tables
  dimension         text not null,                -- see check below
  status            text not null,                -- the five states
  evidence_url      text,
  evidence_note     text,
  reviewed_by       text,
  reviewed_date     date,
  next_review_date  date,
  outstanding_action text,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),

  constraint cas_subject_chk check (subject_type in ('dataset','access','impl')),
  constraint cas_dimension_chk check (dimension in
    ('access','commercial','redistribute','derive','store_cache','attribution',
     'api_terms','microdata_confidentiality')),
  constraint cas_status_chk check (status in
    ('confirmed','likely_verify','provider_confirm','owner_review','restricted')),
  constraint cas_unique unique (subject_type, subject_id, dimension)
);

comment on table public.compliance_assessment is
  'Per-dimension clearance verdicts (framework §4). A source can be confirmed to
   access but owner_review to redistribute — hence one row per dimension.';

create index cas_subject_idx     on public.compliance_assessment (subject_type, subject_id);
create index cas_nextreview_idx  on public.compliance_assessment (next_review_date);

-- ── Transformation ── country → shared transformation catalogue ─────────────────
create table public.compliance_transformation (
  id             uuid primary key default gen_random_uuid(),
  impl_id        text not null references public.compliance_country_impl(impl_id),
  transform_type text not null,                   -- see check below
  origin         text not null,                   -- 'source_provided' | 'salary_explorer'
  method_note    text,
  inputs         text,
  created_at     timestamptz not null default now(),

  constraint ctr_type_chk check (transform_type in
    ('currency_conversion','period_conversion','inflation_adjustment','aggregation',
     'ranking','projection','reclassification','cross_country_standardisation')),
  constraint ctr_origin_chk check (origin in ('source_provided','salary_explorer'))
);

comment on table public.compliance_transformation is
  'What Salary Explorer computes per country. origin drives the badge: source_provided
   reads "Official", salary_explorer reads "Salary Explorer calculation" (framework §7).';

create index ctr_impl_idx on public.compliance_transformation (impl_id);

-- ── Review log ── append-only history ──────────────────────────────────────────
create table public.compliance_review_log (
  log_id       uuid primary key default gen_random_uuid(),
  subject_type text not null,
  subject_id   text not null,
  action       text not null,
  actor        text,
  before_after jsonb,
  created_at   timestamptz not null default now()
);

comment on table public.compliance_review_log is
  'Append-only audit trail of register changes (framework §3). Never updated/deleted
   via the API.';

create index crl_subject_idx on public.compliance_review_log (subject_type, subject_id);

-- ══════════════════════════════════════════════════════════════════════════════
--  2. ROW LEVEL SECURITY
--  Base tables: admin/master read+write only. Anonymous/authenticated users get
--  NOTHING on the base tables — the public pages read the curated view below.
--  (The Streamlit app uses the service-role key server-side, which bypasses RLS.)
-- ══════════════════════════════════════════════════════════════════════════════

do $$
declare t text;
begin
  foreach t in array array[
    'compliance_provider','compliance_dataset','compliance_access_method',
    'compliance_country_impl','compliance_assessment','compliance_transformation',
    'compliance_review_log']
  loop
    execute format('alter table public.%I enable row level security;', t);

    -- Admins/master may SELECT (reuses app_metadata.role — only the service key can
    -- set it, so users cannot self-escalate).
    execute format($p$
      create policy %1$s_admin_select on public.%1$I
        for select to authenticated
        using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role','') in ('admin','master'));
    $p$, t);

    -- Admins/master may INSERT + UPDATE. No DELETE policy (register rows are not
    -- deleted through the API; the service key can if ever needed).
    execute format($p$
      create policy %1$s_admin_insert on public.%1$I
        for insert to authenticated
        with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role','') in ('admin','master'));
    $p$, t);
    execute format($p$
      create policy %1$s_admin_update on public.%1$I
        for update to authenticated
        using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role','') in ('admin','master'))
        with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role','') in ('admin','master'));
    $p$, t);
  end loop;
end $$;

-- ══════════════════════════════════════════════════════════════════════════════
--  3. PUBLIC VIEW  (the ONLY thing anonymous visitors can read)
--  A normal (non-security_invoker) view runs with the owner's privileges, so it
--  bypasses the base-table RLS above and returns exactly the curated columns/rows
--  we choose. It exposes only PUBLISHABLE rows, per the release gate (framework §6):
--     public_publishable = true
--     AND (clearance_overall = 'confirmed' OR grandfathered = true)
--     AND release_status <> 'blocked'
-- ══════════════════════════════════════════════════════════════════════════════

create or replace view public.v_compliance_public as
select
  ci.country_slug,
  ci.reference_period,
  ci.displayed_original_values,
  ci.release_status,
  ci.grandfathered,
  d.title                     as dataset_title,
  d.official_table_id,
  d.dataset_url,
  d.data_type,
  d.licence_name,
  d.licence_url,
  d.licence_summary_plain,
  d.licence_verbatim_required,
  d.required_attribution_text,
  d.required_disclaimer_text,
  d.required_link_url,
  d.reference_period_note,
  d.revision_policy,
  p.name                      as provider_name,
  p.homepage_url              as provider_url,
  -- transformations as a JSON array: [{type, origin, method_note, inputs}, ...]
  coalesce((
    select jsonb_agg(jsonb_build_object(
             'transform_type', tr.transform_type,
             'origin',         tr.origin,
             'method_note',    tr.method_note,
             'inputs',         tr.inputs)
           order by tr.transform_type)
    from public.compliance_transformation tr
    where tr.impl_id = ci.impl_id
  ), '[]'::jsonb)             as transformations
from public.compliance_country_impl ci
join public.compliance_dataset  d on d.dataset_id  = ci.dataset_id
join public.compliance_provider p on p.provider_id = d.provider_id
where ci.public_publishable = true
  and (ci.clearance_overall = 'confirmed' or ci.grandfathered = true)
  and ci.release_status <> 'blocked';

comment on view public.v_compliance_public is
  'Curated public projection of the compliance register for the Data Sources &
   Methodology page. Exposes publishable columns/rows only; anon/authenticated read.';

grant select on public.v_compliance_public to anon, authenticated;

-- ══════════════════════════════════════════════════════════════════════════════
--  4. SEED — three contrasting pilots (framework §12 Phase 0):
--     Eurostat SES  → one dataset, 20 countries, source-provided EUR
--     Norway (SSB)  → live API, native NOK/monthly, no transformation
--     Mexico (INEGI)→ microdata, Salary Explorer weighted-mean computation
--  Clearance is seeded conservatively (likely_verify / provider_confirm) with
--  evidence links and NO reviewed_by — the owner flips dimensions to 'confirmed'
--  on review (framework §1.2). Nothing here asserts approval on assumption.
-- ══════════════════════════════════════════════════════════════════════════════

-- ── Providers ──────────────────────────────────────────────────────────────────
insert into public.compliance_provider
  (provider_id, name, country_or_org, homepage_url, reuse_policy_url, contact_email) values
  ('eurostat','Eurostat','European Union','https://ec.europa.eu/eurostat',
     'https://ec.europa.eu/eurostat/about-us/policies/copyright', null),
  ('ssb','Statistics Norway (SSB)','Norway','https://www.ssb.no/en',
     'https://www.ssb.no/en/informasjon/copyright', null),
  ('inegi','INEGI','Mexico','https://www.inegi.org.mx/',
     'https://www.inegi.org.mx/inegi/terminos.html', null);

-- ── Datasets (terms live here) ─────────────────────────────────────────────────
insert into public.compliance_dataset
  (dataset_id, provider_id, title, official_table_id, dataset_url, data_type,
   licence_name, licence_url, licence_summary_plain, required_attribution_text,
   personal_data, reference_period_note) values
  ('eurostat_earn_ses_21','eurostat',
     'Structure of Earnings Survey (earn_ses_21)','earn_ses_21',
     'https://ec.europa.eu/eurostat/web/labour-market/earnings','official_table',
     'Eurostat reuse policy (CC BY 4.0)','https://creativecommons.org/licenses/by/4.0/',
     'Free reuse, including for commercial purposes, with attribution to Eurostat. Eurostat is not liable for reuse.',
     'Source: Eurostat','none','4-yearly SES editions (2006–2022); mean earnings in EUR.'),
  ('ssb_11418','ssb',
     'Monthly earnings by occupation (SSB table 11418)','11418',
     'https://www.ssb.no/en/statbank/table/11418','official_table',
     'CC BY 4.0','https://creativecommons.org/licenses/by/4.0/',
     'Free reuse with attribution to Statistics Norway; commercial use permitted.',
     'Source: Statistics Norway (SSB)','none','Annual; monthly gross earnings in NOK.'),
  ('inegi_enoe','inegi',
     'National Survey of Occupation and Employment (ENOE) microdata','ENOE-SDEMT',
     'https://www.inegi.org.mx/programas/enoe/15ymas/','microdata',
     'INEGI terms of free use','https://www.inegi.org.mx/inegi/terminos.html',
     'Free use and reproduction of INEGI open data with attribution; verify conditions for microdata reuse.',
     'Source: INEGI, ENOE','none','Quarterly microdata (SDEMT); income in MXN.');

-- ── Access methods (channel constraints) ───────────────────────────────────────
insert into public.compliance_access_method
  (access_id, dataset_id, method, endpoint_or_file, requires_api_key, caching_allowed_note,
   microdata_confidentiality_terms) values
  ('eurostat_earn_ses_21_api','eurostat_earn_ses_21','api',
     'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/earn_ses22_21',
     false,'Bundled snapshot; API re-fetched on rebuild. Caching permitted under the reuse policy.',null),
  ('ssb_11418_api','ssb_11418','api',
     'https://data.ssb.no/api/v0/en/table/11418', false,
     'Live fetch, disk-cached. SSB permits reuse/caching with attribution.', null),
  ('inegi_enoe_microdata','inegi_enoe','microdata_download',
     'ENOE SDEMT microdata (CSV/DBF)', false,
     'Bundled snapshot; rebuild re-downloads and recomputes.',
     'Aggregated survey-weighted results only; no re-identification. Verify INEGI microdata reuse conditions.');

-- ── Country implementations ────────────────────────────────────────────────────
-- Eurostat SES: 20 countries, one dataset. All grandfathered (already published).
insert into public.compliance_country_impl
  (impl_id, country_slug, dataset_id, access_id, displayed_original_values,
   grandfathered, public_publishable, release_status, clearance_overall)
select 'eu_ses__' || slug, slug, 'eurostat_earn_ses_21', 'eurostat_earn_ses_21_api',
       'Mean earnings (EUR) by ISCO occupation', true, true, 'beta_ok', 'likely_verify'
from (values
  ('lithuania'),('belgium'),('portugal'),('austria'),('poland'),('luxembourg'),
  ('latvia'),('croatia'),('romania'),('bulgaria'),('greece'),('hungary'),
  ('slovakia'),('czechia'),('ireland'),('italy'),('cyprus'),('malta'),
  ('serbia'),('northmacedonia')
) as t(slug);

insert into public.compliance_country_impl
  (impl_id, country_slug, dataset_id, access_id, displayed_original_values,
   grandfathered, public_publishable, release_status, clearance_overall) values
  ('ssb_11418__norway','norway','ssb_11418','ssb_11418_api',
     'Mean/quartile monthly earnings (NOK) by STYRK occupation', true, true, 'beta_ok', 'likely_verify'),
  ('inegi_enoe__mexico','mexico','inegi_enoe','inegi_enoe_microdata',
     'Survey-weighted mean & median monthly income (MXN) by ENOE occupation group',
     true, false, 'beta_ok', 'provider_confirm');

-- ── Transformations (drive the Official / SE-calculation badge) ─────────────────
-- Eurostat: EUR is source-provided → reads "Official".
insert into public.compliance_transformation (impl_id, transform_type, origin, method_note, inputs)
select 'eu_ses__' || slug, 'currency_conversion', 'source_provided',
       'Earnings published in EUR by Eurostat.', 'Eurostat earn_ses_21 (EUR)'
from (values
  ('lithuania'),('belgium'),('portugal'),('austria'),('poland'),('luxembourg'),
  ('latvia'),('croatia'),('romania'),('bulgaria'),('greece'),('hungary'),
  ('slovakia'),('czechia'),('ireland'),('italy'),('cyprus'),('malta'),
  ('serbia'),('northmacedonia')
) as t(slug);

-- Norway: native NOK, native monthly → no transformation (a pure-official contrast).

-- Mexico: survey-weighted mean/median from microdata → Salary Explorer calculation.
insert into public.compliance_transformation (impl_id, transform_type, origin, method_note, inputs) values
  ('inegi_enoe__mexico','aggregation','salary_explorer',
     'Survey-weighted mean & median monthly income computed from ENOE microdata.',
     'ENOE SDEMT person weights (fac); grouped by ENOE occupation × sex');

-- ── Dataset-level assessments (per permission dimension) ────────────────────────
-- Seeded to likely_verify (Eurostat/SSB) / provider_confirm (INEGI microdata) with
-- evidence links; reviewed_by intentionally NULL until the owner reviews.
insert into public.compliance_assessment
  (subject_type, subject_id, dimension, status, evidence_url, next_review_date) values
  -- Eurostat SES
  ('dataset','eurostat_earn_ses_21','access','likely_verify',
     'https://ec.europa.eu/eurostat/about-us/policies/copyright', (now() + interval '12 months')::date),
  ('dataset','eurostat_earn_ses_21','commercial','likely_verify',
     'https://ec.europa.eu/eurostat/about-us/policies/copyright', (now() + interval '12 months')::date),
  ('dataset','eurostat_earn_ses_21','redistribute','likely_verify',
     'https://ec.europa.eu/eurostat/about-us/policies/copyright', (now() + interval '12 months')::date),
  ('dataset','eurostat_earn_ses_21','derive','likely_verify',
     'https://ec.europa.eu/eurostat/about-us/policies/copyright', (now() + interval '12 months')::date),
  ('dataset','eurostat_earn_ses_21','store_cache','likely_verify',
     'https://ec.europa.eu/eurostat/about-us/policies/copyright', (now() + interval '12 months')::date),
  ('dataset','eurostat_earn_ses_21','attribution','confirmed',
     'https://ec.europa.eu/eurostat/about-us/policies/copyright', (now() + interval '12 months')::date),
  -- SSB 11418
  ('dataset','ssb_11418','access','likely_verify',
     'https://www.ssb.no/en/informasjon/copyright', (now() + interval '12 months')::date),
  ('dataset','ssb_11418','commercial','likely_verify',
     'https://www.ssb.no/en/informasjon/copyright', (now() + interval '12 months')::date),
  ('dataset','ssb_11418','redistribute','likely_verify',
     'https://www.ssb.no/en/informasjon/copyright', (now() + interval '12 months')::date),
  ('dataset','ssb_11418','derive','likely_verify',
     'https://www.ssb.no/en/informasjon/copyright', (now() + interval '12 months')::date),
  ('dataset','ssb_11418','attribution','confirmed',
     'https://www.ssb.no/en/informasjon/copyright', (now() + interval '12 months')::date),
  -- INEGI ENOE (microdata — higher scrutiny)
  ('dataset','inegi_enoe','access','likely_verify',
     'https://www.inegi.org.mx/inegi/terminos.html', (now() + interval '12 months')::date),
  ('dataset','inegi_enoe','commercial','provider_confirm',
     'https://www.inegi.org.mx/inegi/terminos.html', (now() + interval '12 months')::date),
  ('dataset','inegi_enoe','redistribute','provider_confirm',
     'https://www.inegi.org.mx/inegi/terminos.html', (now() + interval '12 months')::date),
  ('dataset','inegi_enoe','derive','likely_verify',
     'https://www.inegi.org.mx/inegi/terminos.html', (now() + interval '12 months')::date),
  ('dataset','inegi_enoe','attribution','confirmed',
     'https://www.inegi.org.mx/inegi/terminos.html', (now() + interval '12 months')::date);

-- Access-method-level assessment: INEGI microdata confidentiality (framework §11).
insert into public.compliance_assessment
  (subject_type, subject_id, dimension, status, evidence_note, next_review_date) values
  ('access','inegi_enoe_microdata','microdata_confidentiality','provider_confirm',
     'Publish survey-weighted aggregates only; confirm INEGI microdata reuse conditions.',
     (now() + interval '12 months')::date);

-- ── Seed audit-log entry ───────────────────────────────────────────────────────
insert into public.compliance_review_log (subject_type, subject_id, action, actor, before_after) values
  ('impl','(phase0-seed)','seed_created','system',
   jsonb_build_object('note','Phase 0 seed: Eurostat(20)+Norway+Mexico pilots inserted'));
