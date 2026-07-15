#!/usr/bin/env python3
"""Daily Career Paths incremental refresh — cron entry point.

Run INSIDE the prod container from the HOST crontab (survives deploys because
the host crontab isn't in the repo and `--force-recreate` keeps the container
name `scb-prod` stable):

    docker exec scb-prod python cron_daily_refresh.py

What it does: fetch only ads published since the last run (JobTech
`published-after` — a free, open API), classify just that small daily delta on
the configured Haiku model (the only paid step, fractions of a cent), upsert
the rolling cp_ad_class store, prune stale rows, and re-aggregate the live
evidence. Expired ads are kept in the store but excluded from the live signal.

IMPORTANT — run on exactly ONE host. All three environments (dev/test/prod)
share ONE Supabase database, so a single nightly run updates the data for all
of them. Running it on more than one host just duplicates work and races on the
`last_run` marker.

Every run is logged to cp_v1_runs → visible in the app at
Admin → Career Paths → Run log. Exit code is non-zero on failure so cron mail /
the log file flag it.
"""
import os
import sys

# Lives at the repo root (which IS /app in the image; deploy/ is .dockerignored,
# so the script must sit at root to be baked into the container). Put its own
# dir on the path so the app modules import regardless of the launch cwd.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import net_fix  # noqa: E402,F401 — force IPv4 before any HTTP client loads (entry-point convention)

import datetime as _dt  # noqa: E402

import career_pipeline as pipe  # noqa: E402
import careerpaths_v1 as v1  # noqa: E402


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    started = _now()
    if not v1.enabled():
        print(f"[{started} UTC] career v1 pipeline disabled — skipping.", flush=True)
        return 0

    print(f"[{started} UTC] daily incremental refresh starting (all families)…", flush=True)
    res = pipe.run(incremental=True, actor="cron-daily")
    done = _now()

    if res.get("ok"):
        print(f"[{done} UTC] OK · mode={res.get('mode')} "
              f"fetched={res.get('ads_fetched')} classified={res.get('ads_processed')} "
              f"titles_with_evidence={res.get('titles_with_evidence')} "
              f"suggestions={res.get('suggestions')}", flush=True)
        return 0

    print(f"[{done} UTC] FAILED · {res.get('error')}", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
