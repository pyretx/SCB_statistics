-- ─────────────────────────────────────────────────────────────────────────────
-- Feedback-form hardening (security review 2026-07-21).
-- Closes the direct-PostgREST holes in beta_feedback: any authenticated user
-- could previously insert rows (bypassing the app's beta-only gate), spoof
-- another user's email, put unbounded text in the context columns, and flood
-- the queue. The app itself inserts via the service key (bypasses RLS), so
-- none of this changes in-app behaviour — the trigger in §3 is the only part
-- that also applies to the app path, by design.
-- Run ONCE (applied via the Supabase MCP on 2026-07-21).
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Length caps on the previously unconstrained free-text context columns
--    (title/description already had caps from the original migration).
alter table public.beta_feedback
  add constraint beta_feedback_country_chk
      check (country is null or char_length(country) <= 100);
alter table public.beta_feedback
  add constraint beta_feedback_page_chk
      check (page is null or char_length(page) <= 200);
alter table public.beta_feedback
  add constraint beta_feedback_appver_chk
      check (app_version is null or char_length(app_version) <= 50);
alter table public.beta_feedback
  add constraint beta_feedback_email_chk
      check (user_email is null or char_length(user_email) <= 254);

-- 2. Tighten the INSERT policy: (a) user_email must match the caller's own
--    JWT email — no more spoofing another user's address in the admin panel;
--    (b) mirror the app's beta/admin gate so a standard-role account can no
--    longer insert via PostgREST at all. Per-country testers still submit
--    fine through the app (service key). DROP+CREATE because CREATE OR
--    REPLACE POLICY does not exist — the replacement is strictly stronger.
drop policy beta_feedback_insert_own on public.beta_feedback;
create policy beta_feedback_insert_own
  on public.beta_feedback
  for insert
  to authenticated
  with check (
    user_id = auth.uid()
    and (user_email is null
         or lower(user_email) = lower(coalesce(auth.jwt() ->> 'email', '')))
    and coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '')
        in ('beta', 'admin', 'master')
  );

-- 3. Rate limit: max 20 submissions per user per hour. A trigger (not RLS)
--    so it also covers the app's service-key path — triggers fire regardless
--    of role. SECURITY DEFINER so the count sees all rows despite RLS.
create or replace function public.beta_feedback_rate_limit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if (select count(*) from public.beta_feedback
      where user_id = new.user_id
        and created_at > now() - interval '1 hour') >= 20 then
    raise exception 'feedback rate limit exceeded';
  end if;
  return new;
end;
$$;

drop trigger if exists beta_feedback_rate_limit_trg on public.beta_feedback;
create trigger beta_feedback_rate_limit_trg
  before insert on public.beta_feedback
  for each row execute function public.beta_feedback_rate_limit();
