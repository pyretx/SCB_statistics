#!/usr/bin/env bash
# Pull latest code and (re)build+restart an SCB environment.
# Usage:  ./deploy.sh            # production (default)
#         ./deploy.sh test       # test env  (expects /srv/scb-test  + docker-compose.scb-test.yml)
#         ./deploy.sh dev        # dev env
set -euo pipefail

ENV="${1:-prod}"
DIR="/srv/scb-${ENV}"
FILE="docker-compose.scb.yml"
[ "$ENV" != "prod" ] && FILE="docker-compose.scb-${ENV}.yml"

echo "==> Deploying '${ENV}' from ${DIR}"
cd "$DIR"
git pull --ff-only
cd deploy

# Bind-mounted runtime files must exist as FILES before `up` — Docker would
# otherwise create directories at these paths and break the app's writes.
for f in scb-wp-rules.json scb-ssyk-overrides.json scb-app-settings.json \
         scb-guide.json scb-update-checks.json; do
  [ -f "/root/$f" ] || echo '{}' > "/root/$f"
done
# --force-recreate: rebuilding with the same image tag does NOT change Compose's
# config hash, so without it Compose leaves the OLD container running and the new
# code never goes live. Force the container swap on every deploy.
docker compose --env-file /root/.env -f "$FILE" up -d --build --force-recreate
echo "==> Done. Recent logs:"
docker logs --tail 15 "scb-${ENV}"
