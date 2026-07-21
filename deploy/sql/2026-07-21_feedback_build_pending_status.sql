-- ─────────────────────────────────────────────────────────────────────────────
-- New beta_feedback status: 'Build pending review'.
-- Set by the AI session AFTER a fix for the item is committed and deployed to
-- the dev environment — the ONLY status value the AI is allowed to write (see
-- the triage procedure in CLAUDE.md). The owner reviews and presses the
-- one-click "Mark resolved" button in the admin panel; Resolved/Closed remain
-- human-only. DROP+ADD because CHECK constraints cannot be altered in place;
-- the replacement is a strict superset (adds one allowed value).
-- Run ONCE (applied via the Supabase MCP on 2026-07-21).
-- ─────────────────────────────────────────────────────────────────────────────

alter table public.beta_feedback
  drop constraint beta_feedback_status_chk;
alter table public.beta_feedback
  add constraint beta_feedback_status_chk check (status in
      ('New', 'Reviewing', 'Planned', 'Build pending review',
       'Resolved', 'Closed'));
