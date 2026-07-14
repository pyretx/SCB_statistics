-- Career Paths v1 — richer market-signal evidence.
-- Adds aggregate columns to cp_title_evidence so the career tab can show more than
-- an ad count: languages, employment-type mix, top employers, and a few example
-- ad references (with Platsbanken links). All aggregate / non-PII; ad text is still
-- never stored. Safe to re-run (IF NOT EXISTS). No RLS change (table already gated).

alter table cp_title_evidence
    add column if not exists common_languages jsonb not null default '[]'::jsonb,
    add column if not exists employment_mix   jsonb not null default '{}'::jsonb,
    add column if not exists top_employers    jsonb not null default '[]'::jsonb,
    add column if not exists example_ads      jsonb not null default '[]'::jsonb;

-- Shapes (for reference):
--   common_languages : [{"label": "Svenska", "freq": 8}, ...]
--   employment_mix   : {"Tillsvidareanställning": 12, "Behovsanställning": 3}
--   top_employers    : [{"name": "Acme AB", "freq": 4}, ...]
--   example_ads      : [{"id":"31273259","headline":"…","employer":"…",
--                        "deadline":"2026-08-13","url":"https://…/annonser/31273259"}]
