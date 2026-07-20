"""Browser session-cookie persistence for the Supabase login.

Login state lives in st.session_state["auth_user"], which dies on F5. This
module keeps the user signed in across refreshes by holding ONLY the Supabase
refresh token in a browser SESSION cookie (`sb_refresh`) — no expiry, so it
dies when the browser closes. Never the access token, never the password.

How the pieces fit (both called from app.py, before st.navigation runs):
  restore()  reads the cookie via st.context.cookies — synchronous and present
             on the very first script run, so there is no async component
             roundtrip and no login-form flash — then rebuilds auth_user via
             auth.restore_from_refresh(). Refresh tokens ROTATE: the new token
             returned by Supabase is queued for write-back to the cookie.
  flush()    performs the queued cookie set/delete by rendering a tiny
             document.cookie script (components.html iframes share the app's
             origin, so the cookie lands on the app). Login/logout call sites
             must NOT write the cookie inline: they all st.rerun() on the
             next line, which tears the iframe down before its JS ever runs
             in the browser (cookie silently never written). They call
             queue_save()/queue_clear() instead; flush() does the real write
             on the next run, which renders normally.

Why not extra-streamlit-components' CookieManager: its frontend does
`new Date(options.expires)` unconditionally, so with expires omitted the
serializer throws (Invalid Date) and the set silently no-ops — a true session
cookie (no expires) is IMPOSSIBLE through that component. Verified against
v0.1.81's build JS before switching to the document.cookie approach.
"""
import json

import streamlit as st
import streamlit.components.v1 as components

import auth

COOKIE_NAME = "sb_refresh"
_PENDING = "_sb_pending_cookie"   # queued cookie value, or the delete marker
_DELETE = "\x00delete"            # sentinel — never a valid refresh token
_LOGGED_OUT = "_sb_logged_out"    # st.context.cookies is a connection-time
#                                   snapshot: after logout it still shows the
#                                   old cookie, so without this flag restore()
#                                   would sign the user straight back in.


def queue_save(refresh_token) -> None:
    """Queue the refresh token for write-back on the next flush()."""
    if refresh_token:
        st.session_state[_PENDING] = refresh_token
        st.session_state.pop(_LOGGED_OUT, None)


def queue_clear() -> None:
    """Queue cookie deletion and block restore() for this browser session."""
    st.session_state[_PENDING] = _DELETE
    st.session_state[_LOGGED_OUT] = True


def restore() -> None:
    """Rebuild the login from the sb_refresh cookie after a page refresh.
    No-op when already signed in, after a logout, or for visitors without the
    cookie — anonymous traffic pays zero cost here."""
    if (st.session_state.get("auth_user")
            or st.session_state.get(_LOGGED_OUT)
            or st.session_state.get(_PENDING)):
        return
    token = st.context.cookies.get(COOKIE_NAME)
    if not token:
        return
    user, new_token = auth.restore_from_refresh(token)
    if user:
        st.session_state["auth_user"] = user
        queue_save(new_token or token)
    else:
        # Dead cookie (expired/revoked/garbage): delete it and fall through to
        # the normal logged-out flow. _LOGGED_OUT (via queue_clear) also stops
        # us re-trying the same dead token on every rerun of this session.
        queue_clear()


def flush() -> None:
    """Write the queued cookie change. Renders a zero-height iframe whose JS
    runs in the browser after this script run completes — callers must not
    st.rerun() immediately after flush()."""
    pending = st.session_state.pop(_PENDING, None)
    if pending is None:
        return
    if pending == _DELETE:
        cookie = f"{COOKIE_NAME}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT"
    else:
        # No expires / max-age → a true browser session cookie (dies on close).
        cookie = f"{COOKIE_NAME}={pending}; path=/; SameSite=Strict; Secure"
    # Collapse the empty iframe row so the write is invisible in the layout.
    st.markdown(
        '<style>.element-container:has(iframe[height="0"]) {display:none;}</style>',
        unsafe_allow_html=True)
    components.html(f"<script>document.cookie = {json.dumps(cookie)};</script>",
                    height=0)
