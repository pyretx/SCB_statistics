#!/usr/bin/env python3
"""Supabase keep-alive — cron entry point.

Free-tier Supabase projects get paused when they show low database activity
over 7 days. This runs one small real query through the REST API, so the project
keeps seeing traffic even when the site has no visitors. It only reads; nothing
is written.

Cadence matters: one read a day is NOT enough. The nightly career job made
exactly that and the project still got a pause warning (Nov 2026). Supabase's
docs ask for "a few" requests a day without giving a number, so schedule this
several times a day from the HOST crontab, inside the prod container (same
pattern as cron_daily_refresh.py; must stay at repo root because deploy/ is
.dockerignored):

    0 */4 * * * docker exec scb-prod python supabase_keepalive.py >> /var/log/scb-keepalive.log 2>&1

All three environments share ONE Supabase project, so one host is enough.
Exit code is non-zero on failure so the log file flags it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import net_fix  # noqa: E402,F401 — force IPv4 before any HTTP client loads (entry-point convention)

import datetime as _dt  # noqa: E402

import auth  # noqa: E402


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    try:
        res = auth._client(service=True).table("beta_feedback").select("id").limit(1).execute()
    except Exception as e:
        print(f"[{_now()} UTC] FAILED · {type(e).__name__}: {e}", flush=True)
        return 1
    print(f"[{_now()} UTC] OK · rows={len(res.data)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
