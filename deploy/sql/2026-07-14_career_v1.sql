-- ─────────────────────────────────────────────────────────────────────────────
-- Career Paths v1 — job-ad evidence pipeline (admin/beta only, never public yet).
-- See docs/career-paths-assessment.md §v1. Run ONCE in the Supabase SQL editor.
--
-- Flow: JobTech ads → PII scrub → offline Claude batch → aggregates + review queue.
-- Aggregates only (no ad text, no personal data). All admin-triggered/offline; a
-- master on/off toggle gates the whole feature. Nothing here is public.
-- ─────────────────────────────────────────────────────────────────────────────

-- Master config (single row).
create table public.cp_v1_config (
  id                 integer primary key default 1,
  enabled            boolean not null default false,   -- master on/off (admin)
  model              text not null default 'claude-haiku-4-5',
  max_ads_per_ssyk   integer not null default 60,       -- bound cost per run
  min_ads_suggestion integer not null default 5,         -- suppress low-evidence suggestions
  review_level       text not null default 'light',      -- light | minimal | strict
  last_run           timestamptz,
  updated_at         timestamptz not null default now(),
  constraint cvc_single check (id = 1),
  constraint cvc_review_chk check (review_level in ('light', 'minimal', 'strict'))
);

-- Processing-run log (one row per refresh).
create table public.cp_run_log (
  run_id       uuid primary key default gen_random_uuid(),
  started_at   timestamptz not null default now(),
  finished_at  timestamptz,
  families     jsonb not null default '[]',
  ads_fetched  integer not null default 0,
  ads_processed integer not null default 0,
  suggestions  integer not null default 0,
  status       text not null default 'running',          -- running | done | failed
  error        text,
  actor        text,
  model        text
);
create index cp_run_started_idx on public.cp_run_log (started_at desc);

-- Discovered raw job-title variants → (proposed) canonical title.
create table public.cp_raw_title_map (
  id            uuid primary key default gen_random_uuid(),
  family_id     text,
  raw_title     text not null,
  ssyk          text,
  canonical_title_id text references public.cp_title(title_id),
  seniority     text,                                     -- junior|mid|senior|lead|principal|manager|null
  mgmt_signal   boolean not null default false,
  ad_count      integer not null default 0,
  first_seen    date,
  last_seen     date,
  status        text not null default 'auto',             -- auto | pending | approved | rejected
  model         text,
  updated_at    timestamptz not null default now(),
  constraint crtm_status_chk check (status in ('auto', 'pending', 'approved', 'rejected')),
  constraint crtm_unique unique (raw_title, ssyk)
);
create index cp_rtm_canon_idx on public.cp_raw_title_map (canonical_title_id);

-- Aggregated ad evidence per canonical title (auto-applied facts — no ad text).
create table public.cp_title_evidence (
  title_id        text primary key references public.cp_title(title_id),
  ad_count        integer not null default 0,
  common_skills   jsonb not null default '[]',            -- [{skill, freq}]
  common_experience jsonb not null default '[]',
  common_education jsonb not null default '[]',
  common_certs    jsonb not null default '[]',
  mgmt_freq       numeric,
  top_variants    jsonb not null default '[]',
  observed_from   date,
  observed_to     date,
  evidence_strength text default 'limited',               -- strong|moderate|limited
  updated_at      timestamptz not null default now()
);

-- Review queue: structural suggestions the AI proposes (new title / band change /
-- new relationship) above the confidence + sample thresholds.
create table public.cp_suggestion (
  id           uuid primary key default gen_random_uuid(),
  family_id    text,
  kind         text not null,                             -- new_title|band_change|new_relationship
  summary      text,
  payload      jsonb not null default '{}',
  confidence   text not null default 'limited',
  ad_support   integer not null default 0,
  status       text not null default 'pending',           -- pending | approved | rejected
  created_at   timestamptz not null default now(),
  reviewed_by  text,
  reviewed_at  timestamptz,
  model        text,
  constraint cs_kind_chk check (kind in ('new_title', 'band_change', 'new_relationship')),
  constraint cs_status_chk check (status in ('pending', 'approved', 'rejected')),
  constraint cs_conf_chk check (confidence in ('strong', 'moderate', 'limited', 'experimental'))
);
create index cp_sug_status_idx on public.cp_suggestion (status, confidence);

comment on table public.cp_title_evidence is
  'Aggregated job-ad evidence (JobTech, CC BY-SA) per canonical title — counts and
   frequencies only, no ad text, no personal data. Attribution: Arbetsförmedlingen.';

-- RLS: admin/master only (no public views — admin/offline reads via service key).
alter table public.cp_v1_config      enable row level security;
alter table public.cp_run_log        enable row level security;
alter table public.cp_raw_title_map  enable row level security;
alter table public.cp_title_evidence enable row level security;
alter table public.cp_suggestion     enable row level security;
do $$
declare t text;
begin
  foreach t in array array['cp_v1_config','cp_run_log','cp_raw_title_map',
                           'cp_title_evidence','cp_suggestion'] loop
    execute format($p$create policy %1$s_admin_all on public.%1$I for all to authenticated
      using (coalesce(auth.jwt()->'app_metadata'->>'role','') in ('admin','master'))
      with check (coalesce(auth.jwt()->'app_metadata'->>'role','') in ('admin','master'));$p$, t);
  end loop;
end $$;

insert into public.cp_v1_config (id, enabled) values (1, false) on conflict (id) do nothing;
