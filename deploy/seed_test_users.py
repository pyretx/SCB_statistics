"""Seed the three PASSWORDLESS test users for the dev-only test login
(auth.test_sign_in / the "Enter as <role>" buttons on the landing auth panel).

One user per role — test-admin / test-beta / test-standard @
salary-explorer.invalid (RFC-reserved TLD: mail to it can never deliver, and
with no password set there is no credential to leak; the ONLY way in is the
test-login code path, which is dead wherever secrets lack
[test_login] enabled = true).

Idempotent: existing test users are updated in place, missing ones created.
app_metadata.test_account = true marks them for exclusion from user-facing
counts if ever needed.

Run from the repo root:  python deploy/seed_test_users.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import net_fix  # noqa: F401  (forces IPv4 — must precede any HTTP client use)
import auth

sb = auth._client(service=True)

USERS = [
    # (role, display name, extra app_metadata)
    ("admin",    "Test Admin",    {}),
    ("beta",     "Test Beta",     {}),
    ("standard", "Test Standard", {}),
]

_resp = sb.auth.admin.list_users()
existing = {u.email: u for u in
            (_resp if isinstance(_resp, list) else getattr(_resp, "users", []))}

for role, name, extra in USERS:
    email = auth.test_login_email(role)
    meta = {"role": role, "countries": list(auth.DEFAULT_COUNTRIES),
            "test_account": True, **extra}
    if email in existing:
        uid = existing[email].id
        sb.auth.admin.update_user_by_id(uid, {
            "app_metadata": meta,
            "user_metadata": {"full_name": name},
        })
        print(f"updated  {email}  role={role}  id={uid}")
    else:
        res = sb.auth.admin.create_user({
            "email": email,
            "email_confirm": True,          # no password key → passwordless
            "user_metadata": {"full_name": name},
            "app_metadata": meta,
        })
        print(f"created  {email}  role={role}  id={res.user.id}")

print("done — verify with the admin panel user list or auth.list_users().")
