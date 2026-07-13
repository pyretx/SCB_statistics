-- ─────────────────────────────────────────────────────────────────────────────
-- Qvistin homepage "Send message" contact form → messages table.
-- TEMPORARY: reuses the Salary Explorer Supabase project; migrate to its own
-- project once volume grows. Read in the Salary Explorer admin panel (Messages).
-- Run ONCE in the Supabase SQL editor (Dashboard → SQL Editor → New query).
-- ─────────────────────────────────────────────────────────────────────────────

create table public.qvistin_messages (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  name        text not null,
  email       text not null,
  topic       text not null,
  message     text not null,
  source      text not null default 'qvistin-home',
  status      text not null default 'New',
  admin_notes text,

  -- Length limits double as an abuse guard: the anonymous public form can insert,
  -- so cap every field. (Stored content is plain text — never rendered as HTML;
  -- the admin panel html-escapes it, so script/markup in a message can't execute.)
  constraint qm_name_chk    check (char_length(name)    between 1 and 200),
  constraint qm_email_chk   check (char_length(email)   between 3 and 320),
  constraint qm_topic_chk   check (char_length(topic)   between 1 and 60),
  constraint qm_message_chk check (char_length(message) between 1 and 5000),
  constraint qm_status_chk  check (status in ('New', 'Read', 'Archived'))
);

comment on table public.qvistin_messages is
  'Contact-form submissions from the Qvistin homepage (qvist.in). Temporary home
   in the Salary Explorer project; anonymous INSERT only, admin-only read.';

-- ── Row Level Security ────────────────────────────────────────────────────────
alter table public.qvistin_messages enable row level security;

-- 1. Anyone (the anonymous public form, using the publishable/anon key in the
--    browser) may INSERT — but ONLY insert. The table CHECK constraints above
--    bound every field, and there is deliberately NO select/update/delete policy
--    for anon/authenticated, so a visitor can never read anyone's messages back
--    through the API (the form posts with Prefer: return=minimal).
create policy qm_public_insert
  on public.qvistin_messages
  for insert
  to anon, authenticated
  with check (true);

-- 2. Admins/master may READ (reuses the app role in the JWT app_metadata, which
--    only the service key can set — users cannot self-escalate). The admin panel
--    actually reads via the service key (which bypasses RLS); this policy is
--    defence-in-depth for any JWT-based access.
create policy qm_admin_select
  on public.qvistin_messages
  for select
  to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '')
         in ('admin', 'master'));

-- 3. Admins/master may UPDATE (status / private notes).
create policy qm_admin_update
  on public.qvistin_messages
  for update
  to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '')
         in ('admin', 'master'))
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '')
              in ('admin', 'master'));

-- No DELETE policy (nobody deletes via the API; the service key can if ever needed).

create index qvistin_messages_created_idx on public.qvistin_messages (created_at desc);
create index qvistin_messages_status_idx  on public.qvistin_messages (status);
