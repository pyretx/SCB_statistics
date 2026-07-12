# Deploying SCB Salary Explorer to the Hostinger VPS

This app runs as its own Docker container that plugs into the **existing Traefik**
reverse proxy that already serves n8n. n8n is never modified.

- **Server:** `srv950186.hstgr.cloud` (148.230.110.67), Ubuntu 24.04
- **Traefik network:** `root_default`  ·  **cert resolver:** `mytlschallenge`
- **Production URL:** https://scb.srv950186.hstgr.cloud  *(wildcard DNS already resolves)*

Run all commands as `root` in the Hostinger **Browser Terminal** (or via SSH).

---

## 1. One-time: get the code onto the server

```bash
# Tools (git is usually present; docker comes with the Hostinger n8n template)
apt-get update && apt-get install -y git

# Clone the repo into /srv/scb-prod  (production = main branch)
mkdir -p /srv
git clone https://github.com/pyretx/SCB_statistics.git /srv/scb-prod
cd /srv/scb-prod
```

> Private repo? Use a GitHub Personal Access Token in the URL, or add a deploy key.
> The repo is currently public, so a plain clone works.

## 2. Confirm the subdomain resolves to this server

```bash
getent hosts scb.srv950186.hstgr.cloud
```
You should see `148.230.110.67`. (Hostinger wildcards `*.srv950186.hstgr.cloud`,
so no DNS record needs to be created.)

## 3. Build & start the container

```bash
cd /srv/scb-prod/deploy
docker compose --env-file /root/.env -f docker-compose.scb.yml up -d --build
```

`--env-file /root/.env` reuses the same `DOMAIN_NAME` value n8n uses.

## 4. Verify

```bash
docker ps                      # expect scb-prod = Up (healthy) alongside root-n8n-1, root-traefik-1
docker logs --tail 30 scb-prod # should show "You can now view your Streamlit app"
```

Then open **https://scb.srv950186.hstgr.cloud** in a browser. Traefik issues the
TLS certificate automatically on first request (may take ~10–20 s the first time).

n8n at https://n8n.srv950186.hstgr.cloud is unaffected — verify it still loads.

---

## Redeploying after a code change

Whenever new commits are pushed to GitHub:

```bash
cd /srv/scb-prod
git pull
cd deploy
docker compose --env-file /root/.env -f docker-compose.scb.yml up -d --build --force-recreate
```

> **Always include `--force-recreate` when redeploying.** Rebuilding with the same
> image tag does not change Compose's config hash, so without this flag Compose
> leaves the OLD container running and your new code never goes live (it prints
> "Running" instead of "Recreated").

(Or use `deploy.sh` — see below.)

## Useful commands

```bash
docker logs -f scb-prod                                   # live logs
docker compose -f docker-compose.scb.yml restart          # restart
docker compose -f docker-compose.scb.yml down             # stop & remove (n8n untouched)
```

---

## Adding TEST and DEV environments later

Each environment = a separate clone on its own branch + a copy of the compose file
with a unique container name and Host rule. Single-label subdomains stay inside the
Hostinger wildcard, so `scb-test.` / `scb-dev.` resolve automatically.

| Env  | Branch | Clone dir       | Container  | URL                                  |
|------|--------|-----------------|------------|--------------------------------------|
| prod | main   | /srv/scb-prod   | scb-prod   | scb.srv950186.hstgr.cloud            |
| test | test   | /srv/scb-test   | scb-test   | scb-test.srv950186.hstgr.cloud       |
| dev  | dev    | /srv/scb-dev    | scb-dev    | scb-dev.srv950186.hstgr.cloud        |

## Database migrations (Supabase SQL)

There is no automated migration runner. SQL files live under `deploy/sql/` and
are applied **manually, once**, in the Supabase dashboard (SQL Editor → New
query → paste → Run). The project is shared across dev/test/prod, so each file
is run exactly once regardless of environment. Applied so far:

| File | Purpose |
|------|---------|
| `deploy/sql/2026-07-12_beta_feedback.sql` | `beta_feedback` table + RLS (in-app beta feedback form + admin Feedback tab) |

## Auth: the confirmation-email popup (`[app] url`)

For the "Thanks for confirming — please sign in" popup to work, the app must send
the confirmation-email link back to itself with `?confirmed=1`. Behind Traefik the
app can't reliably guess its own public URL, so set it explicitly in the server
secrets file (`/root/scb-secrets.toml`, mounted into every container):

```toml
[app]
url = "https://scb-dev.srv950186.hstgr.cloud"   # or scb. / scb-test. per env
```

Then in Supabase → **Authentication → URL Configuration**: **Site URL** = that same
URL (no wildcard), and add `<that URL>/**` to the **Redirect URLs** allow-list.
Restart the container after editing secrets. Without `[app] url` the confirmation
link still works but lands on the start page with no popup.

---

For each new env, copy `docker-compose.scb.yml`, then change **four** things so the
two routers don't clash in Traefik (router name `scb` must be unique per env):

```yaml
    container_name: scb-test
    labels:
      - "traefik.http.routers.scb-test.rule=Host(`scb-test.${DOMAIN_NAME}`)"
      - "traefik.http.routers.scb-test.entrypoints=web,websecure"
      - "traefik.http.routers.scb-test.tls=true"
      - "traefik.http.routers.scb-test.tls.certresolver=mytlschallenge"
      - "traefik.http.services.scb-test.loadbalancer.server.port=8501"
```

Ask Claude and it will generate the test/dev compose files for you.
