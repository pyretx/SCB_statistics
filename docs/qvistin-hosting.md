# Qvistin hosting & domain architecture — `qvist.in`

Status: **PROPOSAL / implementation guide.** Nothing in here is activated yet. It
describes the target architecture and a staged, reversible migration from the
current `*.srv950186.hstgr.cloud` URLs to the `qvist.in` domain, keeping the old
URLs alive throughout.

Decisions locked with the owner (2026-07-13):
- Salary Explorer **production → `https://salaryexplorer.qvist.in`** (a subdomain,
  **not** a `/salaryexplorer/` path — chosen for the far simpler, lower-risk
  routing; prod then stays identical to test/dev).
- **`https://test.qvist.in`** and **`https://dev.qvist.in`** for the other two.
- **`https://qvist.in`** (+ `www`) → the Qvistin corporate homepage.
- **One shared Supabase project** across prod/test/dev is acceptable for Salary
  Explorer.

---

## 1. Current state (as inspected)

The three environments are **Docker containers** routed by the **existing Traefik**
reverse proxy that the Hostinger n8n template installed. There is **no NGINX, no
certbot, no systemd** — routing and TLS are done entirely through Traefik.

| Fact | Value |
|------|-------|
| Server | `srv950186.hstgr.cloud` · **148.230.110.67** · Ubuntu 24.04 |
| Proxy | Traefik (shared with n8n), network **`root_default`** |
| TLS | Traefik Let's Encrypt resolver **`mytlschallenge`** (automatic) |
| App port | Streamlit **8501** inside each container |
| Env var | `/root/.env` → `DOMAIN_NAME=srv950186.hstgr.cloud` (shared) |
| Prod | branch `main` · `/srv/scb-prod` · container `scb-prod` · `scb.srv950186.hstgr.cloud` |
| Test | branch `test` · `/srv/scb-test` · container `scb-test` · `scb-test.srv950186.hstgr.cloud` |
| Dev | branch `dev` · `/srv/scb-dev` · container `scb-dev` · `scb-dev.srv950186.hstgr.cloud` |

Routing today is a per-container Traefik label:
`traefik.http.routers.scb.rule=Host(`scb.${DOMAIN_NAME}`)` (see
`deploy/docker-compose.scb.yml`). `${DOMAIN_NAME}` resolves to the hstgr host;
Hostinger wildcards `*.srv950186.hstgr.cloud`, which is why the subdomains work
with no DNS records.

### Problems found (independent of the domain move)

1. **No environment isolation.** All three compose files mount the **same** host
   files, so dev/test/prod share one Supabase project, one settings file, and one
   admin state:
   ```
   /root/scb-secrets.toml       (Supabase, Resend, every API key, [app].url)
   /root/scb-app-settings.json
   /root/scb-wp-rules.json  /root/scb-ssyk-overrides.json
   /root/scb-guide.json     /root/scb-update-checks.json
   ```
   Critically, `[app].url` (the confirmation-email base URL, read in
   `landing.py`) can hold only **one** value for all three envs — it is currently
   the dev URL. This **must be split per-env before cutover** so prod emails go to
   `salaryexplorer.qvist.in` while test/dev keep their own. Sharing the Supabase
   *project* is fine (owner decision); sharing the *secrets/settings files* is not.

2. The homepage file is a **bundled export**, not a website (see §7).

### Why the subdomain choice keeps things simple

Because prod is a plain subdomain (no path prefix), **`.streamlit/config.toml` and
the `Dockerfile` need no changes** — no `baseUrlPath`, no health-check path change,
no WebSocket/cookie-path juggling. Every environment stays the same shape. This is
the entire reason we did not go with `qvist.in/salaryexplorer/`.

---

## 2. Target architecture

```
                          one.com DNS (registrar + nameservers)
   qvist.in            A     -> 148.230.110.67
   www.qvist.in        A     -> 148.230.110.67   (or CNAME qvist.in)
   salaryexplorer      A     -> 148.230.110.67
   test                A     -> 148.230.110.67
   dev                 A     -> 148.230.110.67
   (MX / SPF / DKIM / DMARC  -> UNCHANGED, email keeps working)
                                   |
                                   v
                 Hostinger VPS 148.230.110.67  (ports 80/443)
                                   |
                         Traefik (root_default)
                     TLS via mytlschallenge (auto LE)
          ┌───────────────┬───────────────┬───────────────┬─────────────────┐
          v               v               v               v                 v
   qvist.in /        salaryexplorer    test.qvist.in    dev.qvist.in    (old hostnames
   www.qvist.in      .qvist.in                                           kept alive)
          |               |               |               |            scb / scb-test /
   qvistin-site      scb-prod:8501    scb-test:8501   scb-dev:8501     scb-dev .srv950186
   (nginx:alpine     (Streamlit)      (Streamlit)     (Streamlit)      -> same containers
    static site)
```

Each Streamlit router carries **both** its old hstgr hostname **and** its new
`qvist.in` hostname during the transition, so nothing breaks while DNS/SSL settle.

---

## 3. Files to create / modify

Nothing below is applied yet. This section is the review checklist.

| File | Action | Purpose |
|------|--------|---------|
| `deploy/docker-compose.scb.yml` | modify | add `Host(salaryexplorer.qvist.in)` to the router rule; switch to per-env mounts (`scb-prod-*`) |
| `deploy/docker-compose.scb-test.yml` | modify | add `Host(test.qvist.in)`; per-env mounts (`scb-test-*`) |
| `deploy/docker-compose.scb-dev.yml` | modify | add `Host(dev.qvist.in)`; per-env mounts (`scb-dev-*`) |
| `qvistin-site/` | ✅ **done** | converted static homepage (content.toml + Jinja build); see its README (§7) |
| `deploy/docker-compose.qvistin-site.yml` + `qvistin-site/Dockerfile` | ✅ **done** | nginx container that renders the homepage from `content.toml` and serves `qvist.in` + `www` |
| `deploy/docker-compose.scb{,-test,-dev}.yml` | ✅ **done** | per-env volume mounts (`/root/scb-<env>-*`) for isolation (§5) |
| `deploy/migrate-env-isolation.sh` + `deploy.sh` guard | ✅ **done** | one-time per-env file seeding + a deploy guard (§5) |
| `deploy/SETUP.md` | ✅ **done** | per-env secrets + new hostnames noted |
| `.streamlit/config.toml` | **no change** | subdomain approach needs none |
| `Dockerfile` (Streamlit app) | **no change** | health check stays `/_stcore/health` |

---

## 4. Traefik label changes (per-env)

Add the new hostname with `||` so the old URL keeps serving. Example — **production**
`deploy/docker-compose.scb.yml`:

```yaml
    labels:
      - "traefik.enable=true"
      # add the qvist.in hostname alongside the existing hstgr one
      - "traefik.http.routers.scb.rule=Host(`scb.${DOMAIN_NAME}`) || Host(`salaryexplorer.qvist.in`)"
      - "traefik.http.routers.scb.entrypoints=web,websecure"
      - "traefik.http.routers.scb.tls=true"
      - "traefik.http.routers.scb.tls.certresolver=mytlschallenge"
      - "traefik.http.services.scb.loadbalancer.server.port=8501"
```

Test → add `|| Host(`test.qvist.in`)` to `routers.scb-test.rule`.
Dev → add `|| Host(`dev.qvist.in`)` to `routers.scb-dev.rule`.

Traefik requests a certificate for each new hostname automatically on first HTTPS
request, **once DNS resolves to the server** (§6). No certbot, no renewal job.

**HTTP→HTTPS:** the n8n Traefik template usually redirects the `web` entrypoint to
`websecure` globally. **Verify on the server** (`/root/docker-compose.yml` /
Traefik static config). If it is *not* global, add this middleware to each router:

```yaml
      - "traefik.http.routers.scb.middlewares=https-redirect"
      - "traefik.http.middlewares.https-redirect.redirectscheme.scheme=https"
      - "traefik.http.middlewares.https-redirect.redirectscheme.permanent=true"
```

### Homepage container (`deploy/docker-compose.qvistin-site.yml`)

```yaml
name: qvistin-site
services:
  site:
    image: nginx:alpine
    container_name: qvistin-site
    restart: always
    volumes:
      - /srv/qvistin-site:/usr/share/nginx/html:ro   # the converted static site
    networks:
      - traefik
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.qvistin.rule=Host(`qvist.in`) || Host(`www.qvist.in`)"
      - "traefik.http.routers.qvistin.entrypoints=web,websecure"
      - "traefik.http.routers.qvistin.tls=true"
      - "traefik.http.routers.qvistin.tls.certresolver=mytlschallenge"
      - "traefik.http.services.qvistin.loadbalancer.server.port=80"
      # www -> apex redirect
      - "traefik.http.routers.qvistin.middlewares=www-to-apex"
      - "traefik.http.middlewares.www-to-apex.redirectregex.regex=^https?://www\\.qvist\\.in/(.*)"
      - "traefik.http.middlewares.www-to-apex.redirectregex.replacement=https://qvist.in/$${1}"
      - "traefik.http.middlewares.www-to-apex.redirectregex.permanent=true"
networks:
  traefik:
    external: true
    name: root_default
```

(The `$${1}` doubles the `$` so Docker Compose does not interpolate it.)

---

## 5. Per-env secrets/settings split (do this FIRST — see §8 Phase 1)

Give each environment its own copies so `[app].url` and admin state diverge and
prod is never affected by dev/test edits. This is **implemented** — the compose
files mount per-env paths, `deploy.sh` aborts if the per-env secrets file is
missing, and a one-time script seeds the files. **On the server, once:**

```bash
bash /srv/scb-prod/deploy/migrate-env-isolation.sh   # idempotent; seeds /root/scb-<env>-* from the shared files
```

Target per-env filenames on the host:

| Purpose | prod | test | dev |
|---------|------|------|-----|
| Supabase/API secrets | `/root/scb-prod-secrets.toml` | `/root/scb-test-secrets.toml` | `/root/scb-dev-secrets.toml` |
| App settings | `/root/scb-prod-app-settings.json` | `…test…` | `…dev…` |
| WP rules | `/root/scb-prod-wp-rules.json` | … | … |
| SSYK overrides | `/root/scb-prod-ssyk-overrides.json` | … | … |
| Guide | `/root/scb-prod-guide.json` | … | … |
| Update checks | `/root/scb-prod-update-checks.json` | … | … |

Then set the **only value that must differ** per env, in each secrets file:

```toml
# /root/scb-prod-secrets.toml
[app]
url = "https://salaryexplorer.qvist.in"
# /root/scb-test-secrets.toml -> https://test.qvist.in
# /root/scb-dev-secrets.toml  -> https://dev.qvist.in
```

And repoint each compose file's `volumes:` at its own copies, e.g. prod:

```yaml
    volumes:
      - /root/scb-prod-secrets.toml:/app/.streamlit/secrets.toml:ro
      - /root/scb-prod-wp-rules.json:/app/wp_rules.json:rw
      - /root/scb-prod-ssyk-overrides.json:/app/ssyk_overrides.json:rw
      - /root/scb-prod-app-settings.json:/app/app_settings.json:rw
      - /root/scb-prod-guide.json:/app/guide.json:rw
      - /root/scb-prod-update-checks.json:/app/update_checks.json:rw
```

> Secrets never enter git or the image — only the host paths change. Back up the
> originals first: `cp /root/scb-secrets.toml /root/scb-secrets.toml.bak-YYYYMMDD`.

---

## 6. Manual one.com DNS steps

Add/adjust these at one.com (registrar + DNS). **Do not touch MX / SPF / DKIM /
DMARC.** one.com does not allow a CNAME on the apex, so `qvist.in` must be an **A**
record.

| Type | Host / name | Value / target | TTL | Notes |
|------|-------------|----------------|-----|-------|
| A | `@` (qvist.in) | `148.230.110.67` | 600 | homepage; **replace** any existing one.com parking/hosting A record |
| A | `www` | `148.230.110.67` | 600 | or CNAME → `qvist.in`; **replace** existing `www` if it points to one.com |
| A | `salaryexplorer` | `148.230.110.67` | 600 | Salary Explorer **prod** |
| A | `test` | `148.230.110.67` | 600 | Salary Explorer **test** |
| A | `dev` | `148.230.110.67` | 600 | Salary Explorer **dev** |

**Preserve (do not edit/remove):** `MX`, any `TXT` SPF (`v=spf1 …`), DKIM
(`…_domainkey`), `DMARC` (`_dmarc`), and any records needed by existing email/other
services.

**Likely conflicts to fix:** one.com typically pre-populates `@` and `www` with
records pointing at one.com's own web hosting / a parking page — those must be
changed to the values above, or the homepage won't resolve to the VPS.

Use a low TTL (600s — one.com's minimum) during migration; raise to 3600s once verified.

The old `*.srv950186.hstgr.cloud` URLs are Hostinger's wildcard and are **unaffected**
by any of this — they keep working the entire time.

---

## 7. Homepage conversion

`Qvistin Homepage.html` (in Downloads) is a **Claude Artifact "Bundled Page"
export**: `<title>Bundled Page</title>`, a `#__bundler_loading` "Unpacking…"
overlay, and a JS routine that unpacks base64-embedded assets at runtime. It is
**not** suitable for direct hosting (visitors see "Unpacking…", it depends on
client-side JS to assemble itself, and SEO is nil — the served title is literally
"Bundled Page").

Plan: convert it to a clean static site, **design/animations/fonts preserved**:

```
qvistin-site/            (deployed to /srv/qvistin-site, served by nginx:alpine)
├── index.html           real <title>Qvistin</title>, meta/OG tags, server-rendered markup
├── css/                 extracted stylesheets
├── js/                  extracted scripts (only what the design needs)
├── images/  assets/     fonts + images as normal files (not base64 blobs)
└── favicon, robots.txt, sitemap.xml
```

Update the site's Salary Explorer CTA to point at **`https://salaryexplorer.qvist.in`**
(a "Launch Salary Explorer →" button). This is a separate build task, done after the
architecture is approved.

---

## 8. Staged, reversible migration (order matters)

Each phase is independently reversible and keeps the old URLs live.

**Phase 0 — prep (no live changes).** Review this doc. On the server, back up:
`/root/scb-secrets.toml`, the admin JSONs, and `docker inspect` output for the three
containers.

**Phase 1 — environment isolation (no DNS).** Do §5: per-env secrets/settings files,
repoint each compose `volumes:`, redeploy each env **on its existing URL**. Verify
each still works and that a dev settings edit no longer affects prod. Safe, fully
independent of the domain move.

**Phase 2 — DNS (no server changes).** Add the five A records at one.com (§6), low
TTL. Wait for propagation (`getent hosts salaryexplorer.qvist.in` → 148.230.110.67).
Old URLs unaffected.

**Phase 3 — Traefik hostnames.** Add the `|| Host(...qvist.in)` rules (§4) to the
three compose files, redeploy. Traefik issues certs on first HTTPS hit. Now each env
answers on **both** the old and new hostnames.

**Phase 4 — homepage.** Convert the site (§7), place at `/srv/qvistin-site`, bring up
`docker-compose.qvistin-site.yml`. `qvist.in` + `www` now serve the homepage.

**Phase 5 — Supabase.** Set Site URL + redirect allow-list (§9). Keep the old
hostnames in the allow-list for now.

**Phase 6 — app URLs.** Confirm each env's `[app].url` (§5) points at its new
hostname; redeploy. **Test the confirmation-email flow on `test.qvist.in` first**,
then prod.

**Phase 7 — validate.** Run the §10 checklist against all four hostnames.

**Phase 8 — retire old URLs (optional, later).** Once confident, drop the
`Host(scb*.srv950186…)` clauses from the router rules and remove those entries from
the Supabase allow-list. Until then they remain as a safety net.

---

## 9. Manual Supabase steps

Authentication → **URL Configuration**:

- **Site URL:** `https://salaryexplorer.qvist.in`
- **Redirect URLs (allow-list)** — add all, keep the old ones during transition:
  - `https://salaryexplorer.qvist.in/**`
  - `https://test.qvist.in/**`
  - `https://dev.qvist.in/**`
  - `https://scb.srv950186.hstgr.cloud/**` (keep until Phase 8)
  - `https://scb-test.srv950186.hstgr.cloud/**` (keep until Phase 8)
  - `https://scb-dev.srv950186.hstgr.cloud/**` (keep until Phase 8)

Notes:
- Confirmation/password-reset links use the app-supplied `redirect_to`
  (`[app].url` + `/?confirmed=1`), so they resolve correctly per env as long as each
  URL is in the allow-list above.
- Email templates in Supabase generally use `{{ .ConfirmationURL }}` — no hardcoded
  host to change. Verify there is no hardcoded hstgr URL in any custom template.
- No OAuth providers are configured today; if you add Google/etc. later, add
  `https://<host>/auth/v1/callback`-style callbacks then.
- One shared project (owner-approved) means dev/test signups land in the same user
  table as prod — deliberate when running `deploy/sql/*` or testing auth.

---

## 10. Validation checklist

Server / TLS (from any shell):

```bash
getent hosts salaryexplorer.qvist.in    # -> 148.230.110.67 (repeat for test/dev/qvist.in/www)
curl -sSI https://salaryexplorer.qvist.in/_stcore/health   # 200
curl -sSI http://salaryexplorer.qvist.in                   # 301/308 -> https
curl -sSI https://www.qvist.in                             # redirect -> https://qvist.in
docker ps                                                  # scb-prod/test/dev + qvistin-site all Up
```

Browser (each of the four hostnames):
- `https://qvist.in/` loads the Qvistin homepage (real title, no "Unpacking…").
- `https://salaryexplorer.qvist.in/` loads Salary Explorer; URL stays on that host.
- Streamlit WebSocket connects (no console errors); static assets 200; no mixed
  content; no CORS/WebSocket errors in console.
- Internal navigation (`?country=…`, `?admin=1`) and a hard refresh both work.
- Login, registration, **email confirmation returns to the right env URL**, password
  reset returns correctly, logout — all work.
- `https://test.qvist.in` and `https://dev.qvist.in` load their environments.
- Old `https://scb*.srv950186.hstgr.cloud` URLs still work (until Phase 8).
- HTTP→HTTPS redirect and `www`→apex both behave.

---

## 11. Rollback

| If this fails | Undo |
|---------------|------|
| Traefik hostname (Phase 3) | remove the `|| Host(...qvist.in)` clause, redeploy → old URL only |
| Homepage (Phase 4) | `docker compose -f docker-compose.qvistin-site.yml down` |
| Supabase (Phase 5/6) | revert Site URL to the old value; the extra allow-list entries are harmless |
| App URL (Phase 6) | restore `[app].url` from the `.bak` secrets file, redeploy |
| Env isolation (Phase 1) | repoint `volumes:` back to the shared `/root/scb-*` files, redeploy |
| DNS (Phase 2) | remove/revert the A records at one.com |

Because the old `*.srv950186.hstgr.cloud` URLs are never removed until Phase 8, a
full production outage is not possible during Phases 1–7 — the old address always
works.

---

## 12. What is automatable vs manual

**Automatable on the server** (scripts/compose — to be written after approval):
per-env secrets split, compose label edits + redeploy, homepage container bring-up,
the validation/smoke-test checks in §10, TLS issuance (Traefik does it).

**Manual (must be done by the owner):** the one.com DNS records (§6), the Supabase
URL settings (§9), and the visual review of the converted homepage (§7). None of
these can be safely automated from here.

**Deliberately NOT added** (would be over-engineering for this Traefik/Docker stack):
NGINX config, certbot/SSL scripts, systemd units, proxy log-rotation, GitHub Actions
CI/CD. The existing `deploy.sh` git-pull model stays.
```
