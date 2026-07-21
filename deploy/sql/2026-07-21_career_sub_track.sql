-- Career Paths — specialisation sub-clusters (Option A).
-- Applied once via the Supabase MCP server (all envs share one database).
-- Recorded here for repo history; do NOT re-run.

-- 1. Grouping label on titles. When set, a title renders as a member of a
--    collapsed sub-cluster card in the career map instead of as a graph node.
ALTER TABLE cp_title ADD COLUMN IF NOT EXISTS sub_track text;
COMMENT ON COLUMN cp_title.sub_track IS
  'Specialisation grouping label. When set, the title renders as a member of a collapsed sub-cluster card in the career map instead of as a graph node.';

-- 2. Expose sub_track through the public view the app reads (column appended
--    last so CREATE OR REPLACE stays valid).
CREATE OR REPLACE VIEW v_cp_title_public AS
 SELECT t.title_id, t.family_id, t.name_en, t.name_sv, t.primary_ssyk, t.alt_ssyk,
   t.track, t.level_index, t.level_label, t.lo_pct, t.mid_pct, t.hi_pct,
   t.confidence, t.evidence, t.review_status, t.published, t.raw_variants,
   t.skills, t.notes, t.created_at, t.updated_at, t.sub_track
 FROM cp_title t
   JOIN cp_family f ON f.family_id = t.family_id
 WHERE t.published = true AND f.published = true;

-- 3. Initial HR grouping backfill (data — the two clean clusters).
UPDATE cp_title SET sub_track = 'Payroll & Staffing'
 WHERE family_id = 'hr' AND title_id IN ('4112-1','4112-2','4112-3','4112-4');
UPDATE cp_title SET sub_track = 'Recruitment & Talent Acquisition'
 WHERE family_id = 'hr' AND title_id IN ('2423-2','2423-3','2423-4','2423-5','2423-6','2423-7');
