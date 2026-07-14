-- ─────────────────────────────────────────────────────────────────────────────
-- Career Paths — performance-positioning overlay (INTERNAL PREVIEW, not public).
-- See docs/career-paths-assessment.md §8/§11. Run ONCE in the Supabase SQL editor.
--
-- The overlay illustrates where a five-point compensation position might sit WITHIN
-- a career level's salary range. It is NOT a measure of individual performance and
-- is NOT published (cp_perf_config.enabled_public = false). Only admins see the
-- preview in the beta tab; the read is server-side via the service key.
--
-- rel_lo/rel_hi are RELATIVE positions (0..1) inside a level's [lo_pct, hi_pct] band;
-- the actual salary is computed live from the SCB curve, never stored.
-- ─────────────────────────────────────────────────────────────────────────────

create table public.cp_perf_band (
  band_id     text primary key,           -- 'developing' … 'exceptional'
  label       text not null,
  position    integer not null,           -- 1..5 (low → high)
  rel_lo      numeric not null,           -- 0..1 within the level range
  rel_hi      numeric not null,
  description text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  constraint cpb_rel_chk check (rel_lo >= 0 and rel_hi <= 1 and rel_lo <= rel_hi)
);

create table public.cp_perf_config (
  id             integer primary key default 1,
  enabled_public boolean not null default false,   -- MUST stay false until evidence exists
  disclaimer     text,
  updated_at     timestamptz not null default now(),
  constraint cpc_single check (id = 1)
);

comment on table public.cp_perf_band is
  'Five-point compensation-positioning overlay (illustrative). Relative positions
   within a career-level salary range — NOT measured individual performance, NOT
   published (see cp_perf_config.enabled_public).';

-- RLS: admin/master only (no public view — internal preview reads via service key).
alter table public.cp_perf_band   enable row level security;
alter table public.cp_perf_config enable row level security;
do $$
declare t text;
begin
  foreach t in array array['cp_perf_band','cp_perf_config'] loop
    execute format($p$create policy %1$s_admin_all on public.%1$I for all to authenticated
      using (coalesce(auth.jwt()->'app_metadata'->>'role','') in ('admin','master'))
      with check (coalesce(auth.jwt()->'app_metadata'->>'role','') in ('admin','master'));$p$, t);
  end loop;
end $$;

-- Seed the five illustrative bands + the (disabled) config.
insert into public.cp_perf_band (band_id, label, position, rel_lo, rel_hi, description) values
  ('developing','Developing',1,0.00,0.20,'Lower part of the level range — building capability.'),
  ('progressing','Progressing',2,0.20,0.40,'Lower-middle — growing into the level.'),
  ('fully_effective','Fully effective',3,0.40,0.60,'Midpoint — the typical position for the level.'),
  ('strong','Strong',4,0.60,0.80,'Upper-middle — consistently above expectations.'),
  ('exceptional','Exceptional',5,0.80,1.00,'Upper part — rare, high-impact contribution.')
on conflict (band_id) do nothing;

insert into public.cp_perf_config (id, enabled_public, disclaimer) values
  (1, false,
   'Illustrative compensation-positioning model only. It does NOT measure individual '
   'performance and salary does not prove performance. Actual pay also depends on '
   'experience, scarcity, employer, region, tenure and negotiation.')
on conflict (id) do nothing;
