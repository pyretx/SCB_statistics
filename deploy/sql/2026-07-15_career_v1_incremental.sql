-- Career Paths v1 — incremental refresh support.
-- A rolling per-ad classification store so a refresh only classifies NEW ads
-- (JobTech published-after) and re-aggregates evidence from the rolling window,
-- instead of re-fetching + re-classifying every ad each run.
-- Non-PII: no ad body text; only the aggregate-relevant fields + a public
-- Platsbanken reference (id/url). Admin/master only. Run once (shared Supabase).

create table if not exists cp_ad_class (
    ad_id            text primary key,
    ssyk             text,
    seniority        text,
    mgmt             boolean,
    years            integer,
    norm_title       text,
    skills           jsonb not null default '[]'::jsonb,
    education        text,
    certs            jsonb not null default '[]'::jsonb,
    languages        jsonb not null default '[]'::jsonb,
    employment_type  text,
    region           text,
    employer         text,
    deadline         text,
    url              text,
    headline         text,
    publication_date text,
    classified_at    timestamptz not null default now()
);
create index if not exists cp_ad_class_ssyk_idx on cp_ad_class (ssyk);

alter table cp_ad_class enable row level security;

drop policy if exists cp_ad_class_admin on cp_ad_class;
create policy cp_ad_class_admin on cp_ad_class for all
    using ((auth.jwt() -> 'app_metadata' ->> 'role') in ('admin', 'master'))
    with check ((auth.jwt() -> 'app_metadata' ->> 'role') in ('admin', 'master'));
