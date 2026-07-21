"""User feedback — the in-app "Report an issue or suggest an improvement"
form (any signed-in user) and its Supabase persistence (table: beta_feedback,
see deploy/sql/2026-07-12_beta_feedback.sql).

Layering: the DB functions (submit / list_feedback / update_feedback) are plain
and UI-free so the admin panel and the dialog share one implementation; the
dialog + entry-point button live below them. All user-facing text is in
content/feedback.toml.

Writes go through auth's existing service client (server-side only — this is a
server-rendered Streamlit app, so the user's Supabase JWT is not persisted and
the publishable key never performs table writes from a browser). The table's
RLS policies still guard the PostgREST surface independently. Deliberately NOT
captured: search selections, uploaded salary data or any other app content —
only the identity/context columns listed in _payload().
"""
from __future__ import annotations

import uuid

import streamlit as st

import auth
import content

# Dropdown values — must match the CHECK constraints in the SQL migration.
TYPES = ["Bug", "Incorrect data", "Usability issue", "Suggestion", "Other"]
IMPACTS = ["Minor", "Significant", "Blocking"]
# The AI session may set exactly two statuses (triage procedure in CLAUDE.md):
# 'Reviewing' — alongside the ai_triage verdict, so a triaged row never still
# reads 'New' — and 'Build pending review' — after a fix is deployed to dev.
# 'Planned' is the owner's OPTIONAL backlog park; the owner confirms a build
# via the admin panel's Mark-resolved button. 'Resolved'/'Closed' stay
# human-only.
STATUSES = ["New", "Reviewing", "Planned", "Build pending review",
            "Resolved", "Closed"]
TITLE_MAX = 150
DESC_MAX = 5000
GENERAL = "General application"


def _T() -> dict:
    """All feedback text (content/feedback.toml). Uncached — edits show live."""
    return content.load("feedback")


def _country_options() -> list[str]:
    """Country display names for the form dropdown + 'General application'."""
    names = []
    try:
        from core import registry
        names = [c.name for c in registry.all_countries() if c.slug != "demo"]
    except Exception:
        pass
    return [GENERAL] + names


# ── Database layer (UI-free) ──────────────────────────────────────────────────
def submit(user: dict, *, feedback_type: str, country: str | None, page: str,
           title: str, description: str, impact: str,
           permission_to_contact: bool,
           app_version: str | None = None) -> str | None:
    """Insert one feedback row. Returns None on success, or a SAFE error string
    (never raw DB details — those go to the server log only)."""
    title = (title or "").strip()
    description = (description or "").strip()
    if feedback_type not in TYPES or impact not in IMPACTS:
        return _T()["messages"]["invalid"]
    if not title or not description:
        return _T()["messages"]["missing"]
    if len(title) > TITLE_MAX or len(description) > DESC_MAX:
        return _T()["messages"]["too_long"]
    if not user or not user.get("id"):
        return _T()["messages"]["not_signed_in"]
    row = {
        "user_id": user["id"],
        "user_email": user.get("email"),
        "feedback_type": feedback_type,
        "country": country or None,
        "page": page,
        "title": title,
        "description": description,
        "impact": impact,
        "permission_to_contact": bool(permission_to_contact),
        "app_version": app_version,
        # status defaults to 'New' in the table
    }
    try:
        auth._client(service=True).table("beta_feedback").insert(row).execute()
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[feedback] insert failed: {e}")     # server log only
        return _T()["messages"]["failed"]


def list_feedback() -> tuple[list[dict], str | None]:
    """All submissions, newest first (admin panel). (rows, safe_error)."""
    try:
        res = (auth._client(service=True).table("beta_feedback")
               .select("*").order("created_at", desc=True).execute())
        return list(res.data or []), None
    except Exception as e:  # noqa: BLE001
        print(f"[feedback] list failed: {e}")
        return [], _T()["admin"]["load_failed"]


def update_feedback(feedback_id: str, *, status: str | None = None,
                    admin_notes: str | None = None,
                    ai_triage: str | None = None) -> str | None:
    """Admin update of status and/or private notes. ``ai_triage`` is the
    bug-hunter agent's replication verdict, recorded server-side after a
    triage run (shown read-only in the admin panel). None on success."""
    changes: dict = {}
    if status is not None:
        if status not in STATUSES:
            return _T()["messages"]["invalid"]
        changes["status"] = status
    if admin_notes is not None:
        changes["admin_notes"] = admin_notes
    if ai_triage is not None:
        changes["ai_triage"] = ai_triage
    if not changes:
        return None
    try:
        (auth._client(service=True).table("beta_feedback")
         .update(changes).eq("id", feedback_id).execute())
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[feedback] update failed: {e}")
        return _T()["admin"]["save_failed"]


def delete_feedback(feedback_id: str) -> str | None:
    """Admin delete of one submission (e.g. a test entry). Service-key only:
    the table deliberately has NO DELETE policy, so PostgREST callers cannot
    do this — the admin panel is the single path. None on success."""
    try:
        (auth._client(service=True).table("beta_feedback")
         .delete().eq("id", feedback_id).execute())
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[feedback] delete failed: {e}")
        return _T()["admin"]["delete_failed"]


# ── UI: entry-point button + dialog ──────────────────────────────────────────
def _can_report(cfg=None) -> bool:
    """Any signed-in user (opened up from beta/admin-only 2026-07-21 to
    lower the reporting barrier). Signed-out visitors still get nothing:
    accountability per submission is a deliberate part of the security
    model — the RLS insert policy stays stricter than this gate on purpose
    (the app inserts via the service key; direct PostgREST needs no wider
    access)."""
    u = st.session_state.get("auth_user")
    return bool(u and u.get("id"))


def _dialog_body():
    T = _T()
    F, M = T["form"], T["messages"]
    user = st.session_state.get("auth_user") or {}
    ctx = st.session_state.get("_fb_ctx") or {}
    if st.session_state.get("_fb_done"):
        st.success(M["submitted"])
        if st.button(F["close"], key="_fb_close_done"):
            for k in ("_fb_done", "_fb_ctx", "_fb_nonce"):
                st.session_state.pop(k, None)
            st.rerun()                       # app-scope: closes the dialog
        return

    opts = _country_options()
    pre = ctx.get("country") if ctx.get("country") in opts else GENERAL
    with st.form("beta_feedback_form", clear_on_submit=True):
        ftype = st.selectbox(F["type_label"], TYPES, key="_fb_type")
        fcountry = st.selectbox(F["country_label"], opts,
                                index=opts.index(pre), key="_fb_country")
        ftitle = st.text_input(F["title_label"], max_chars=TITLE_MAX,
                               placeholder=F["title_ph"], key="_fb_title")
        fdesc = st.text_area(F["desc_label"], max_chars=DESC_MAX, height=170,
                             placeholder=F["desc_ph"], key="_fb_desc")
        st.caption(F["privacy"])
        fimpact = st.selectbox(F["impact_label"], IMPACTS, key="_fb_impact")
        fcontact = st.checkbox(F["contact_label"], key="_fb_contact")
        sent = st.form_submit_button(F["submit"], type="primary",
                                     use_container_width=True)
    if sent:
        # One insert per dialog-open (nonce): a double-click or stray rerun of
        # the submit can never create a duplicate row.
        nonce = st.session_state.get("_fb_nonce")
        done = st.session_state.setdefault("_fb_sent_nonces", set())
        if nonce in done:
            st.session_state["_fb_done"] = True
            st.rerun(scope="fragment")       # stay inside the open dialog
        if not (ftitle or "").strip() or not (fdesc or "").strip():
            st.error(M["missing"])
        else:
            err = submit(user, feedback_type=ftype,
                         country=None if fcountry == GENERAL else fcountry,
                         page=ctx.get("page", ""), title=ftitle,
                         description=fdesc, impact=fimpact,
                         permission_to_contact=fcontact)
            if err:
                st.error(err)
            else:
                done.add(nonce)
                st.session_state["_fb_done"] = True
                # fragment-scope: re-render the dialog body (shows the thank-you
                # message); an app-scope rerun here would close the dialog before
                # the user ever saw the confirmation.
                st.rerun(scope="fragment")
    if st.button(F["cancel"], key="_fb_cancel"):
        for k in ("_fb_done", "_fb_ctx", "_fb_nonce"):
            st.session_state.pop(k, None)
        st.rerun()                           # app-scope: closes the dialog


def feedback_entry(page: str, country: str | None = None, cfg=None,
                   key: str = "fb_open") -> None:
    """The persistent entry point: renders the button (beta/admin only) and,
    while open, the dialog. Call once per page; ``country`` preselects the
    form's country dropdown, ``page`` is stored with the submission."""
    if not _can_report(cfg):
        return
    T = _T()
    if st.button(T["button"], key=key, use_container_width=True,
                 icon=":material/feedback:"):
        # Open the dialog ONLY on the click's own run — no persistent "open"
        # flag. st.dialog is fragment-based: interactions inside it rerun just
        # the dialog body, and dismissing it (X / click outside) simply ends it.
        # The previous _fb_open flag survived an X-dismissal, so the dialog
        # kept re-opening on every later rerun of the page.
        st.session_state["_fb_ctx"] = {"page": page, "country": country}
        st.session_state["_fb_nonce"] = uuid.uuid4().hex
        st.session_state.pop("_fb_done", None)
        st.dialog(T["dialog_title"], width="large")(_dialog_body)()
