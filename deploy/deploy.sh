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
# --force-recreate: rebuilding with the same image tag does NOT change Compose's
# config hash, so without it Compose leaves the OLD container running and the new
# code never goes live. Force the container swap on every deploy.
docker compose --env-file /root/.env -f "$FILE" up -d --build --force-recreate
echo "==> Done. Recent logs:"
docker logs --tail 15 "scb-${ENV}"
