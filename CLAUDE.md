# Salary Explorer — project instructions for Claude Code

Multi-country Streamlit app over official government salary statistics
(salaryexplorer.qvist.in). Streamlit + Supabase (auth, career data, register
tables) + Plotly, deployed with Docker on a Hostinger VPS.

## Architecture (short)

- `app.py` — entry point; page routing (`?country=<url_path>`), auth/session.
- `core/` — shared framework: `model.py` (Capabilities/CountryConfig),
  `provider.py`, `tabs/` (overview, distribution, sex, trend, breakdown for
  age/education/region, leaderboard, …), `charts.py`, `sidebar.py`, `i18n.py`.
- `countries/<slug>/` — one folder per country: `config.py` (CountryConfig +
  i18n dict), `provider.py` (fetch + normalize that country's API), optional
  extra tabs (e.g. `se2/career.py`, `se2/workpermit.py`).
- `theme.py` — design tokens + `style_fig()`. Every Plotly chart gets
  `theme.style_fig(fig)` before `st.plotly_chart`. Fonts: Hanken Grotesk
  (body), JetBrains Mono (labels/numbers). Accent `#0A63A6`, red `#C0453A`
  reserved for mean/negative.
- `landing.py` — public start page; content from `content/*.toml` (editable
  text lives there, loaded via `content.py` — don't hardcode copy).
- `scb_salaries.py` / `france.py` — LEGACY standalone pages (admin-only
  routes). The public Sweden/France pages are `countries/se2` / `countries/fr2`.
- `admin_ui.py` — full-page /admin (role-gated), incl. Career Paths admin.
- Career Paths (Sweden beta): `careerpaths.py` (curated register),
  `careerpaths_v1.py` + `career_pipeline.py` + `career_jobtech.py` +
  `career_ai.py` (job-ad evidence pipeline), `cron_daily_refresh.py`
  (nightly incremental refresh — must stay at repo ROOT, see Docker note).

**Scope convention:** changes to shared tabs/charts in `core/` apply to ALL
framework countries by default. State the intended scope when asked to change
a chart/tab. Sweden/France legacy pages are separate code and not affected.

## Workflow rules

- **Branches:** work on `dev`. Commit + push to `dev` after every change with
  a descriptive message (confirm wording with the user when asked).
  **Never merge/push `test` or `main` without explicit approval.** Promotion
  is local: `dev → test → main` (fast-forward merges), always run on the dev
  machine — never git operations on the server.
- **Verify before committing:** `python -m py_compile` on touched files, then
  check the running app. The review server is `localhost:8502`
  (`.claude/launch.json`, name `scb-8502`); it must be RESTARTED after
  changes to imported modules (Streamlit hot-reload doesn't pick them up).
- Admin-gated code paths need real render verification (importing the module
  and checking callables is the minimum: a missing `def` once reached prod).
- **PowerShell gotcha:** commit messages with quotes/`%`/`&`/parens break
  here-strings — write the message to a temp file and use `git commit -F`.
- Windows dev machine has broken IPv6: every entry point imports `net_fix`
  FIRST (forces IPv4) before any HTTP client loads. Keep that convention.

## Deploy (Hostinger VPS)

- SSH `root@148.230.110.67`; one env per dir:
  `cd /srv/scb-<env>/deploy && ./deploy.sh <env>` for `dev` / `test` / `prod`.
  `deploy.sh` = `git pull --ff-only` + docker compose rebuild
  (`--force-recreate`, container names `scb-<env>` stay stable).
- **All three environments share ONE Supabase.** SQL migrations
  (`deploy/sql/*.sql`) run ONCE — the user pastes them into the Supabase SQL
  editor (Claude has only the REST service key, no DDL access). Data written
  by one env is visible in all.
- Secrets: `.streamlit/secrets.toml` locally (git-ignored),
  `/root/scb-<env>-secrets.toml` on the server (bind-mounted). Never commit,
  print, or paste secret values. The `[anthropic] api_key` must exist in prod
  secrets or job-ad classification silently returns 0.
- **`deploy/` is in `.dockerignore`** — anything that must exist inside the
  container image (e.g. cron entry points) goes at the repo root.
- Career daily refresh: host crontab on prod (03:15 UTC) runs
  `docker exec scb-prod python cron_daily_refresh.py`; run on ONE host only.
  Monitor: Admin → Career Paths → Run log, or `/var/log/scb-career-refresh.log`.

## Data / register conventions

- Register/data inserts (compliance register, career seeds) go through direct
  Supabase service-key Python scripts — not SQL files. Report what was
  inserted for owner sign-off.
- Career salary ranges are percentile bands (`lo/mid/hi_pct`) evaluated live
  against the official SCB curve — never store absolute salaries.
- Expired job ads (application deadline passed) are KEPT in `cp_ad_class`
  for history but excluded from the live market signal.

## Things NOT to touch without asking

- `test`/`main` branches and prod deploys (explicit approval each time).
- Supabase settings, DNS, email (Resend) config.
- The host crontab on the server.
