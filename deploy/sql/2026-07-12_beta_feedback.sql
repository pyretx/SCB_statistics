-- ─────────────────────────────────────────────────────────────────────────────
-- Beta-user feedback table for Salary Explorer.
-- Run ONCE in the Supabase SQL editor (Dashboard → SQL Editor → New query).
-- The project has no automated migration runner — SQL files under deploy/sql/
-- are applied manually and kept here as the record of what was run.
-- ─────────────────────────────────────────────────────────────────────────────

create table public.beta_feedback (
  id                    uuid primary key default gen_random_uuid(),
  created_at            timestamptz not null default now(),
  user_id               uuid not null,
  user_email            text,
  feedback_type         text not null,
  country               text,
  page                  text,
  title                 text not null,
  description           text not null,
  impact                text not null,
  permission_to_contact boolean not null default false,
  app_version           text,
  status                text not null default 'New',
  admin_notes           text,

  -- Validation: mirror the app's dropdowns / length limits.
  constraint beta_feedback_type_chk   check (feedback_type in
      ('Bug', 'Incorrect data', 'Usability issue', 'Suggestion', 'Other')),
  constraint beta_feedback_impact_chk check (impact in
      ('Minor', 'Significant', 'Blocking')),
  constraint beta_feedback_status_chk check (status in
      ('New', 'Reviewing', 'Planned', 'Resolved', 'Closed')),
  constraint beta_feedback_title_chk  check (char_length(title) between 1 and 150),
  constraint beta_feedback_desc_chk   check (char_length(description) between 1 and 5000)
);

comment on table public.beta_feedback is
  'In-app feedback from beta users/admins (Salary Explorer). Screenshot/file
   attachments deliberately not modelled yet — add a separate
   beta_feedback_attachments table later rather than widening this one.';

-- ── Row Level Security ────────────────────────────────────────────────────────
alter table public.beta_feedback enable row level security;

-- 1. Authenticated users may INSERT feedback, but only as themselves.
create policy beta_feedback_insert_own
  on public.beta_feedback
  for insert
  to authenticated
  with check (user_id = auth.uid());

-- 2+4. Only admins/master may READ submissions (reuses the app's existing
--      role system: app_metadata.role, which only the service key can set —
--      users cannot self-escalate). No select policy for normal users at all,
--      so they cannot read their own or anyone else's submissions via the API.
create policy beta_feedback_admin_select
  on public.beta_feedback
  for select
  to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '')
         in ('admin', 'master'));

-- 3+4. Only admins/master may UPDATE (status / admin notes).
create policy beta_feedback_admin_update
  on public.beta_feedback
  for update
  to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '')
         in ('admin', 'master'))
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '')
              in ('admin', 'master'));

-- No DELETE policy: nobody deletes feedback through the API.
-- (The service-role key bypasses RLS by design; it is only ever used
--  server-side by the Streamlit app and never reaches a browser.)

create index beta_feedback_created_idx on public.beta_feedback (created_at desc);
create index beta_feedback_status_idx  on public.beta_feedback (status);
