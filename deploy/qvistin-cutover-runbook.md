# Qvistin cutover runbook — DNS + staged test→prod

A step-by-step operational checklist for pointing `qvist.in` at the server. Assumes
`docs/qvistin-hosting.md` (the architecture) and that **environment isolation is
already migrated** (`deploy/migrate-env-isolation.sh`). Targets:

| Public URL | Serves |
|------------|--------|
| `https://qvist.in` + `https://www.qvist.in` | Qvistin homepage |
| `https://salaryexplorer.qvist.in` | Salary Explorer **prod** |
| `https://test.qvist.in` | Salary Explorer **test** |
| `https://dev.qvist.in` | Salary Explorer **dev** |

Server IP: **148.230.110.67**. Old `*.srv950186.hstgr.cloud` URLs stay live the whole
time. TLS is automatic (Traefik `mytlschallenge`) — no certbot.

---

## 1. DNS records to add at one.com  ·  MANUAL

Log in to one.com → `qvist.in` → DNS settings. Add these **A records**. one.com does
not allow a CNAME on the apex, so `qvist.in` is an A record.

| Type | Host / name | Points to | TTL |
|------|-------------|-----------|-----|
| A | `@`              | `148.230.110.67` | 300 |
| A | `www`            | `148.230.110.67` | 300 |
| A | `salaryexplorer` | `148.230.110.67` | 300 |
| A | `test`           | `148.230.110.67` | 300 |
| A | `dev`            | `148.230.110.67` | 300 |

- **Preserve — do NOT edit or delete:** `MX`, SPF `TXT` (`v=spf1 …`), DKIM
  (`*_domainkey`), `DMARC` (`_dmarc`), and anything email-related.
- **Likely conflicts to replace:** one.com usually pre-fills `@` and `www` pointing
  at one.com hosting / a parking page — change those two to `148.230.110.67`.
- TTL 300 (5 min) during migration; raise to 3600 once everything is verified.
- Adding all five now is fine — hosts with no container yet just return a Traefik
  404 until their service is deployed (harmless). You can also add `test` first and
  the rest later.

Verify from any machine once propagated (seconds–minutes at TTL 300):

```bash
nslookup test.qvist.in            # → 148.230.110.67   (repeat for the others)
```

---

## 2. Dry-run on TEST first  ·  prod stays untouched

`test.qvist.in` is already wired in `deploy/docker-compose.scb-test.yml`
(`… || Host(\`test.qvist.in\`)`). Rehearse the **entire** mechanism on test before
touching prod.

**2a. Supabase** (shared project) — Authentication → URL Configuration → Redirect
URLs: add `https://test.qvist.in/**` (keep all existing entries). Leave Site URL
alone for now.

**2b. Server — point test at its new URL and redeploy:**
```bash
cd /srv/scb-test
git pull
bash deploy/migrate-env-isolation.sh    # no-op if already run
# set test's own public URL:
#   /root/scb-test-secrets.toml  →  [app]\n  url = "https://test.qvist.in"
nano /root/scb-test-secrets.toml
cd deploy && ./deploy.sh test
```

**2c. TLS + health (Traefik issues the cert on first HTTPS hit):**
```bash
curl -sSI https://test.qvist.in/_stcore/health     # HTTP/2 200
curl -sSI http://test.qvist.in                     # 3xx → https
```

**2d. Browser smoke test — https://test.qvist.in:**
- [ ] Page loads; URL stays on `test.qvist.in`.
- [ ] No console CORS / WebSocket / mixed-content errors; Streamlit reconnects on refresh.
- [ ] Internal nav (`?country=…`, `?admin=1`) works; hard-refresh on a nested route works.
- [ ] **Register** a throwaway account → confirmation email arrives → its link
      returns to **`https://test.qvist.in/?confirmed=1`** and shows the "thanks" popup.
- [ ] **Login**, **password reset** returns to the right URL, **logout**.
- [ ] Old `https://scb-test.srv950186.hstgr.cloud` still loads.

If all green, the exact same recipe works for prod. If not, fix on test — prod is
still completely untouched.

---

## 3. Roll out to DEV, then PROD

Only after the test dry-run passes. Each is the same one-line router edit + the same
`[app].url` + Supabase entry.

**3a. Dev** — in `deploy/docker-compose.scb-dev.yml`, extend the router rule:
```yaml
- "traefik.http.routers.scb-dev.rule=Host(`scb-dev.${DOMAIN_NAME}`) || Host(`dev.qvist.in`)"
```
Supabase: add `https://dev.qvist.in/**`. Server: set `/root/scb-dev-secrets.toml`
`[app].url = "https://dev.qvist.in"`, then `cd /srv/scb-dev/deploy && ./deploy.sh dev`.
Smoke-test `https://dev.qvist.in`.

**3b. Prod** — in `deploy/docker-compose.scb.yml`, extend the router rule:
```yaml
- "traefik.http.routers.scb.rule=Host(`scb.${DOMAIN_NAME}`) || Host(`salaryexplorer.qvist.in`)"
```
Supabase: **Site URL → `https://salaryexplorer.qvist.in`** and add
`https://salaryexplorer.qvist.in/**`. Server: set `/root/scb-prod-secrets.toml`
`[app].url = "https://salaryexplorer.qvist.in"`, then
`cd /srv/scb-prod/deploy && ./deploy.sh prod`. Run the §2d checklist against
`https://salaryexplorer.qvist.in`.

**3c. Homepage** — bring up the corporate site for `qvist.in` + `www`:
```bash
git clone -b main https://github.com/pyretx/SCB_statistics.git /srv/qvistin-site   # or dev until merged
cd /srv/qvistin-site/deploy
docker compose -f docker-compose.qvistin-site.yml up -d --build
curl -sSI https://qvist.in                 # 200 (Traefik cert issues on first hit)
curl -sSI https://www.qvist.in             # 3xx → https://qvist.in
```

---

## 4. Full validation (all four hostnames)

```bash
for h in qvist.in www.qvist.in salaryexplorer.qvist.in test.qvist.in dev.qvist.in; do
  echo "== $h =="; curl -sSI "https://$h" | head -n1
done
curl -sSI https://salaryexplorer.qvist.in/_stcore/health   # 200
docker ps   # scb-prod / scb-test / scb-dev / qvistin-site all Up; n8n untouched
```
Browser: homepage at `qvist.in`, each explorer on its host, the §2d auth flow on
prod, no console errors, old hstgr URLs still work.

---

## 5. Rollback (per step, old URLs never removed until step 6)

| If it fails | Undo |
|-------------|------|
| A router edit (§2/§3) | remove the `|| Host(...qvist.in)` clause, `./deploy.sh <env>` → old URL only |
| Homepage (§3c) | `docker compose -f docker-compose.qvistin-site.yml down` |
| Supabase Site URL | revert to the old value; extra redirect entries are harmless |
| `[app].url` | restore from `/root/scb-<env>-secrets.toml` backup, redeploy |
| DNS | revert/remove the A records at one.com |

Because the old `*.srv950186.hstgr.cloud` URLs stay live throughout, there is no
prod outage window during steps 1–4.

## 6. Retire the old URLs (optional, later)

Once confident: drop the `Host(scb*.srv950186…)` clauses from the three router
rules and remove those entries from the Supabase redirect allow-list. Raise DNS TTLs
to 3600.
