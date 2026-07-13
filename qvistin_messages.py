"""Qvistin homepage contact-form messages — admin-side read/update.

The messages are INSERTED anonymously by the static Qvistin homepage
(qvistin-site) straight into Supabase with the publishable/anon key + RLS
(insert-only); see deploy/sql/2026-07-13_qvistin_messages.sql. This module is the
Salary Explorer admin side: it READS them via auth's existing service client
(server-side only) and lets an admin set a status / private note. TEMPORARY —
the table lives in the Salary Explorer project for now.

Security: stored messages are plain text and are NEVER rendered as HTML — the
admin panel html-escapes every field and shows the body via st.text(), so script
or markup pasted into a message cannot execute.
"""
from __future__ import annotations

import auth

STATUSES = ["New", "Read", "Archived"]
_TABLE = "qvistin_messages"


def list_messages() -> tuple[list[dict], str | None]:
    """All messages, newest first. Returns (rows, safe_error)."""
    try:
        res = (auth._client(service=True).table(_TABLE)
               .select("*").order("created_at", desc=True).execute())
        return list(res.data or []), None
    except Exception as e:  # noqa: BLE001
        print(f"[qvistin_messages] list failed: {e}")   # server log only
        return [], "Could not load messages."


def update_message(message_id: str, *, status: str | None = None,
                   admin_notes: str | None = None) -> str | None:
    """Admin update of status and/or private notes. None on success."""
    changes: dict = {}
    if status is not None:
        if status not in STATUSES:
            return "Invalid status."
        changes["status"] = status
    if admin_notes is not None:
        changes["admin_notes"] = admin_notes
    if not changes:
        return None
    try:
        (auth._client(service=True).table(_TABLE)
         .update(changes).eq("id", message_id).execute())
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[qvistin_messages] update failed: {e}")
        return "Could not save."
