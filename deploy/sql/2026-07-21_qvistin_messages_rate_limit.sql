-- ─────────────────────────────────────────────────────────────────────────────
-- Rate limit for the qvist.in contact form (follow-up to the 2026-07-21
-- feedback-form hardening — qvistin_messages was the one public-insert table
-- left without one).
--
-- The form posts ANONYMOUSLY with the public anon key, so there is no user_id
-- to key a per-user limit on, and Postgres triggers cannot see the client IP.
-- A GLOBAL cap is the practical bound: legitimate volume is near zero, so
-- max 30 inserts/hour across the whole table stops a scripted flood at the
-- PostgREST endpoint while never touching real visitors. Trigger (not RLS)
-- so it also covers any service-key path.
-- Run ONCE (applied via the Supabase MCP on 2026-07-21).
-- ─────────────────────────────────────────────────────────────────────────────

create or replace function public.qvistin_messages_rate_limit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if (select count(*) from public.qvistin_messages
      where created_at > now() - interval '1 hour') >= 30 then
    raise exception 'contact form rate limit exceeded';
  end if;
  return new;
end;
$$;

drop trigger if exists qvistin_messages_rate_limit_trg on public.qvistin_messages;
create trigger qvistin_messages_rate_limit_trg
  before insert on public.qvistin_messages
  for each row execute function public.qvistin_messages_rate_limit();
