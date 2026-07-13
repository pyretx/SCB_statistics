#!/usr/bin/env bash
# One-time: split the SHARED /root/scb-* runtime files into per-env copies so
# prod/test/dev stop sharing Supabase settings + admin state (see
# docs/qvistin-hosting.md §5). Idempotent — existing per-env files are never
# overwritten, so it is safe to re-run.
#
# Run this ONCE on the server BEFORE deploying the per-env compose files:
#   bash /srv/scb-prod/deploy/migrate-env-isolation.sh   (any clone works)
set -euo pipefail

FILES=(secrets.toml wp-rules.json ssyk-overrides.json app-settings.json guide.json update-checks.json)

echo "==> Seeding /root/scb-<env>-* from the current shared /root/scb-* files"
for env in prod test dev; do
  for n in "${FILES[@]}"; do
    src="/root/scb-$n"
    dst="/root/scb-$env-$n"
    if [ -e "$dst" ]; then
      echo "    keep    $dst (exists)"
    elif [ -e "$src" ]; then
      cp "$src" "$dst"
      echo "    create  $dst  <- $src"
    elif [ "$n" = "secrets.toml" ]; then
      echo "    WARN    $src missing — create $dst by hand (it holds secrets)"
    else
      echo '{}' > "$dst"
      echo "    create  $dst  (empty {})"
    fi
  done
done

cat <<'EOF'

Done. Next steps (manual):
  1. Set the public URL PER ENV in each secrets file (they currently all share
     one value). For now use the existing hstgr URLs; switch to the qvist.in URLs
     during the domain cutover:
       /root/scb-prod-secrets.toml   [app] url = "https://scb.srv950186.hstgr.cloud"
       /root/scb-test-secrets.toml   [app] url = "https://scb-test.srv950186.hstgr.cloud"
       /root/scb-dev-secrets.toml    [app] url = "https://scb-dev.srv950186.hstgr.cloud"
  2. Redeploy each env so it mounts its own files:
       cd /srv/scb-prod/deploy && ./deploy.sh prod   # then test, then dev
     (deploy.sh now aborts if the per-env secrets file is missing, so a mistimed
      deploy fails cleanly instead of breaking auth.)
  3. Verify each env still works, and that a change in dev/test no longer shows up
     in prod. The old shared /root/scb-*.{toml,json} files can be kept as a backup
     and removed once you are satisfied.
EOF
