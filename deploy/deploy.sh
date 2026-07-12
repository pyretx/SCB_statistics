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

# Bind-mounted runtime files must exist as FILES before `up` — Docker creates
# a DIRECTORY at any missing mount path, which then breaks the app's writes
# AND this very guard (echo into a directory aborts the script). Self-heal:
# replace an empty Docker-made directory with an empty JSON file.
for f in scb-wp-rules.json scb-ssyk-overrides.json scb-app-settings.json \
         scb-guide.json scb-update-checks.json; do
  p="/root/$f"
  if [ -d "$p" ]; then
    echo "==> $p is a directory (Docker mount artifact) — replacing with a file"
    rmdir "$p"
  fi
  [ -f "$p" ] || echo '{}' > "$p"
done
# --force-recreate: rebuilding with the same image tag does NOT change Compose's
# config hash, so without it Compose leaves the OLD container running and the new
# code never goes live. Force the container swap on every deploy.
docker compose --env-file /root/.env -f "$FILE" up -d --build --force-recreate
echo "==> Done. Recent logs:"
docker logs --tail 15 "scb-${ENV}"
