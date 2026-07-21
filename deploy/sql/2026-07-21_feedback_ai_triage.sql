-- ─────────────────────────────────────────────────────────────────────────────
-- AI triage notes on beta feedback.
-- The bug-hunter agent's replication verdict (reproduced / not-reproduced /
-- needs-info + evidence) is recorded here by the main Claude session after a
-- triage run — separate from admin_notes (the owner's private notes) so the
-- two never overwrite each other. Read-only in the admin panel.
-- Run ONCE (applied via the Supabase MCP on 2026-07-21).
-- ─────────────────────────────────────────────────────────────────────────────

alter table public.beta_feedback add column ai_triage text;

comment on column public.beta_feedback.ai_triage is
  'AI bug-hunter triage verdict + evidence. Written server-side (service key)
   after a triage run; shown read-only in the admin panel. Untrusted user
   report text is never executed - this column holds the AI''s assessment.';
