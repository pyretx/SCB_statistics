# User accounts, email setup & verification — handover

**Source project:** Salary Explorer (salaryexplorer.qvist.in) — Streamlit + Supabase.
**Audience:** another project that wants to reuse this account/email design.
**Status:** describes the system as built and running in production, 2026-08.

This is a *design + gotchas* document, not an API reference. The parts worth
copying are the ones marked **⚠ lesson** — they cost real debugging time here.

---

## 1. Stack in one paragraph

Authentication is **Supabase Auth (GoTrue)** used from a Python/Streamlit
server. There is no custom user table, no custom password hashing, no session
server. Everything about a user lives in the Supabase `auth.users` row:
credentials, the confirmation state, and two metadata blobs. The app keeps the
signed-in user as a plain dict in server-side session state and re-hydrates it
from a browser cookie holding only a refresh token.

Transactional email (the confirmation mail) is sent by **Supabase's own auth
mailer**, wired to **Resend** as the SMTP provider in the Supabase dashboard.
No email code exists in the application at all — see §7.

Relevant files:

| File | Role |
|---|---|
| `auth.py` | All Supabase Auth calls. The only module that touches the service key. |
| `auth_cookie.py` | Refresh-token cookie: restore / save / clear across page refreshes. |
| `app.py` | Calls `auth_cookie.restore()` + `flush()` before routing. |
| `landing.py` | Sign-in / create-account dialog, confirm-email dialog, profile dialog. |
| `content/auth.toml` | Every user-facing string of the auth UI (no copy in code). |
| `core/access.py` | Authorization gate (tiers), separate from authentication. |
| `admin_ui.py` | Admin user management (create, role, access, password, delete). |
| `deploy/seed_test_users.py` | Seeds passwordless dev-only test accounts. |

---

## 2. Identity model

### 2.1 Two metadata blobs, and why the split matters

Supabase gives every user two JSON blobs, with very different trust levels:

- **`user_metadata`** — writable by the *user's own* session. Used here only for
  non-privileged profile data:
  - `full_name` (required at sign-up)
  - `accepted_terms_version` + `accepted_terms_at` (clickwrap proof)
- **`app_metadata`** — writable **only with the service-role key**. This is where
  every authorization fact lives:
  - `role` — one of `master | admin | beta | standard`
  - `countries` — list of country slugs the user may open
  - `beta_requested` — ISO date of a pending beta request, or absent/null
  - `test_account` — marks seeded fixtures

> **⚠ lesson — put authorization in `app_metadata`, never `user_metadata`.**
> The public self-registration path uses the anon/publishable key, which
> *cannot* write `app_metadata`. That is a structural guarantee that no
> self-registered user can ever mint themselves an admin role — it is not
> enforced by a check that someone could forget to write.
> (`auth.py:296` `sign_up()`, and the comment at `landing.py:457`.)

### 2.2 The profile dict

`auth._profile()` normalizes a GoTrue user into the single shape the whole app
consumes, kept in `st.session_state["auth_user"]`:

```python
{"id", "email", "name", "role", "countries", "beta_requested"}
```

Everything downstream (`core/access.py`, sidebar, admin gate) reads only this
dict. Copying that convention is worth it — one normalization point means the
GoTrue object model never leaks into feature code.

### 2.3 Defaults

- New accounts get `role = "standard"` implicitly (no `app_metadata` written).
- Country grants fall back to a module constant when unset:
  `DEFAULT_COUNTRIES = ("sweden", "france")`. Note the deliberate distinction in
  `_countries_of()`: an *explicitly empty* list `[]` means "no grants", while a
  *missing* key means "use the default". Don't collapse those two.

### 2.4 Authentication vs authorization

Kept strictly separate. `auth.py` answers *who are you*; `core/access.py`
answers *may you open this*. Access tiers per page: `public` (anyone) ·
`registered` (any signed-in user) · `restricted` (beta tier: admin, global
`beta` role, or a per-country grant) · `internal` (admin/master only).
Releasing a page is a config change, never a code change.

---

## 3. Key management

`auth._cfg()` reads `st.secrets["supabase"]`, falling back to a
`secrets.toml` next to the module (robust regardless of process cwd).

Two keys, two clients:

- **public/publishable** (`publishable_key`, legacy `anon_key`) — sign-up,
  sign-in, refresh, verify-OTP, resend. Anything a user does as themselves.
- **secret/service-role** (`secret_key`, legacy `service_role_key`) — admin
  API: list/create/update/delete users, and every `app_metadata` write.

Both accessor helpers accept the new *and* legacy Supabase key names, which
made the platform's key rename a non-event. Worth copying.

> **⚠ lesson — bump the admin client's HTTP timeout.**
> `httpx` defaults to a 5 s read timeout; Supabase admin calls
> (`list_users`, `update_user_by_id`) regularly exceed it under load, and the
> retry storm makes it worse. `_client(service=True)` sets a 30 s timeout and
> `list_users()` allows one retry. (`auth.py:57`.)

Secrets never live in the repo: `.streamlit/secrets.toml` locally (git-ignored),
`/root/scb-<env>-secrets.toml` bind-mounted on the server, one file per
environment.

---

## 4. Registration flow (self-service)

Implemented in the create-account branch of the auth dialog
(`landing.py:451-482`) and `auth.sign_up()`.

1. Form collects **name, email, password** plus a **required Terms checkbox**.
   All four commit together — see the gotcha below.
2. The app resolves its own public base URL (§6) and builds
   `redirect_to = "<base>/?confirmed=1"`.
3. It reads the current terms version from `content/terms.toml` and passes it in.
4. `sign_up()` writes `user_metadata = {full_name, accepted_terms_version,
   accepted_terms_at}` and sets `options.email_redirect_to`.
5. **Immediately after sign-up the app attempts a normal sign-in.**
   - If the Supabase project does *not* require confirmation, this succeeds and
     the user is straight in.
   - If it *does*, sign-in fails cleanly and the user sees "check your inbox".

   This single call means the same code works under either dashboard setting —
   a genuinely useful trick, because whether confirmation is required is a
   dashboard toggle, not something the code can see.

> **⚠ lesson — wrap auth fields in a real form.**
> A bare Streamlit `text_input` only commits its value on Enter/blur. Browser-
> and password-manager-autofilled passwords stayed uncommitted, so pressing the
> button read an **empty password** — reported repeatedly from mobile. Putting
> the fields in `st.form` commits every field together on submit and captures
> autofilled values. (`landing.py:414-433`.) The equivalent trap exists in any
> framework that reads inputs on change events rather than on form submit.

---

## 5. Email verification — the interesting part

### 5.1 The problem: mail scanners eat one-time links

The default Supabase confirmation email contains `{{ .ConfirmationURL }}`, which
points at Supabase's `/auth/v1/verify` endpoint and **consumes the one-time
token on GET**. Corporate mail gateways, spam filters and mail-app link previews
*prefetch* every URL in an incoming email. The result:

> The token is spent before the human ever clicks. The user clicks, gets an
> error, tries to sign in and is told "Email not confirmed". They are stuck and
> the support burden lands on you.

This is not rare and it is not the user's fault. If you are building email
verification in 2026, assume prefetching happens.

### 5.2 The fix: verify on a button press, not on a GET

The Supabase email template was customised to link to **our own app** carrying
the raw token hash instead of the Supabase verify endpoint:

```
https://<app-host>/?confirm_token={{ .TokenHash }}
```

The app then:

1. Reads `?confirm_token` on page load, moves it into session state and
   **deletes the query param** so it never lingers in the URL, history or
   referrers (`landing.py:144-148`).
2. Renders a modal with a single **"✅ Confirm my email"** button.
3. Only on that click calls `auth.confirm_email_token_with_session(token_hash)`
   → `supabase.auth.verify_otp({token_hash, type})`.
4. On success the returned session signs the user in immediately — no second
   trip through the login form.

**Prefetchers load pages; they do not press buttons.** That single property is
what makes the token survive. This is the root-cause fix and the single most
transferable idea in this document.

> **⚠ lesson — the OTP type name varies by GoTrue version.**
> `confirm_email_token_with_session()` tries `type="email"` and then
> `type="signup"`, keeping the last error. Different `gotrue`/`supabase-py`
> versions accept different spellings; hardcoding one silently breaks on
> upgrade. (`auth.py:261-277`.)

### 5.3 Both generations still work

Links from before the template change verified on Supabase's side and landed on
the app with `?confirmed=1`. That branch still exists (`landing.py:153-157`) and
shows an optimistic "please sign in" banner. **Keep the old path alive while old
emails are still in inboxes** — links live for as long as people ignore their
mail.

### 5.4 Self-service recovery: resend

If sign-in fails and the error text contains `"confirm"`, the app arms a
**"📧 Resend confirmation email"** button (`landing.py:449`, `486-494`) calling
`auth.resend_confirmation(email, redirect_to)` → `supabase.auth.resend(
{"type": "signup", "email": ...})`.

This exists specifically so a user whose first link was eaten can rescue
themselves without an administrator. Even with the button-press fix in place,
keep a resend path: links expire (24 h here, per the user-facing copy) and
people do sit on emails for days.

### 5.5 Admin visibility

`auth.list_users()` exposes `email_confirmed = bool(email_confirmed_at)`, and the
admin panel surfaces the count as a KPI tile plus a per-row badge
(`admin_ui.py:1199`, `1205`, `1347`). "Registered but never confirmed" is the
single most common support state — make it visible in your admin UI from day
one, not after the first support ticket.

---

## 6. Knowing your own public URL

The confirmation email must come back to *the environment that sent it*. Behind
a reverse proxy the app cannot reliably guess its own public URL, so
`landing._app_base_url()` (`landing.py:168-191`) resolves it in order:

1. **Explicit config** — `[app] url` in that environment's secrets file. This is
   the recommended, rock-solid option.
2. **Forwarded headers** — `X-Forwarded-Host` / `X-Forwarded-Proto`, read
   case-insensitively (Traefik/HTTP2 may lowercase them), taking the first value
   of a comma-separated list.
3. `None` — the link still works, it just lands on the start page without the
   greeting.

> **⚠ lesson — with several environments on one Supabase project, `[app] url`
> must be set per environment.** Otherwise a signup on dev sends a confirmation
> link pointing at prod. This project runs dev/test/prod against **one** shared
> Supabase project (a deliberate, owner-approved choice), which makes per-env
> URL config mandatory rather than optional.

Matching Supabase dashboard config (Authentication → URL Configuration):

- **Site URL** = the production URL, no wildcard.
- **Redirect URLs allow-list** = `<each env URL>/**`, including old hostnames
  during a domain migration.

Anything not on the allow-list is silently dropped back to the Site URL — a
confusing failure mode, because the link "works", just not where you expected.

---

## 7. Email delivery infrastructure

**There is no email-sending code in the application.** Nothing imports an email
SDK; the app never composes or sends a message. Every email a user receives is
sent by Supabase's built-in auth mailer.

Delivery is configured entirely in the Supabase dashboard, with **Resend** as the
SMTP provider. The only trace of this in the repo is the privacy policy, which
names Resend (United States) as the processor that "delivers our transactional
emails and therefore processes your email address"
(`content/terms.toml`), and a project rule listing email/Resend config as
owner-only, do-not-touch.

Consequences worth carrying over:

- **Do not use Supabase's default built-in SMTP for production.** It is heavily
  rate-limited and intended for testing. Wire a real provider before launch.
- **Domain DNS is the fragile part.** The hosting/cutover runbooks
  (`docs/qvistin-hosting.md`, `deploy/qvistin-cutover-runbook.md`) mark
  `MX`, SPF (`v=spf1 …`), DKIM (`*_domainkey`) and DMARC (`_dmarc`) as
  **preserve — do not edit or delete**, repeated in two places and in the
  project's do-not-touch list. A domain migration that rewrites DNS wholesale
  will silently kill deliverability, and you'll find out via users who never got
  their confirmation mail.
- Because delivery is dashboard config rather than code, **it is invisible to
  code review and to your test suite**. Treat "send a real confirmation email
  end-to-end" as an explicit item on every deployment/migration checklist. The
  cutover runbook here does exactly that: test the confirmation flow on the test
  hostname before prod.

---

## 8. Session persistence

`auth_cookie.py` is small but has three hard-won details.

**What is stored:** only the **refresh token**, in a browser cookie named
`sb_refresh` with `path=/; SameSite=Strict; Secure` and **no `expires`/`max-age`**
— a true session cookie that dies when the browser closes. Never the access
token, never the password.

**Restore:** `restore()` runs before routing (`app.py:87`), reads the cookie
synchronously from the request context (so there is no async round-trip and no
login-form flash on first paint), and rebuilds the profile via
`auth.restore_from_refresh()`.

> **⚠ lesson 1 — Supabase rotates refresh tokens.** Every refresh returns a
> *new* token; the old one dies. If you don't write the new one back, the user
> is logged out on their second refresh. `restore_from_refresh()` returns
> `(user, new_token)` and the caller must persist it.

> **⚠ lesson 2 — don't write the cookie inline before a rerun.** The cookie is
> written by a tiny `document.cookie` script in a zero-height iframe. Every
> login/logout call site immediately reruns the script, which tears the iframe
> down *before its JS ever executes* — the cookie silently never lands. The fix
> is a queue: call sites call `queue_save()` / `queue_clear()`, and `flush()`
> performs the real write on the next run. Any framework that re-renders
> aggressively has this shape of bug.

> **⚠ lesson 3 — the cookie snapshot is stale after logout.** The request
> context's cookie jar is captured at connection time, so right after logout it
> still shows the old cookie and `restore()` would sign the user straight back
> in. A `_LOGGED_OUT` session flag blocks that. The same flag also stops a dead
> token being retried on every rerun.

A dead cookie (expired/revoked/garbage) is deleted and the user falls through to
the normal logged-out flow.

**Logout** (`auth.revoke_refresh()`): rehydrate a throwaway client from the
refresh token, then `sign_out()` to kill that session chain server-side — the
app holds no access token, so this is the only revoke path available. All
failures are swallowed: **logout must always succeed locally, even offline.**

The module docstring also records that `extra-streamlit-components`'
`CookieManager` *cannot* produce a true session cookie — its frontend calls
`new Date(options.expires)` unconditionally, so omitting `expires` throws and
the set silently no-ops. Verified against v0.1.81's build JS. Useful if you land
on the same library.

---

## 9. Admin-created users

`auth.create_user()` (service key) creates a user with **`email_confirm: True`**
— no verification email, usable immediately — plus the required display name and
an explicit role + country grant. Admin surface (`admin_ui.py`): create user,
change role, change country access, set password, delete user, and resolve
pending beta requests.

The **beta request workflow** is a nice small pattern: a signed-in user presses a
button in their profile dialog → `auth.request_beta()` writes
`app_metadata.beta_requested = <ISO date>` **server-side with the service key**,
so the user still cannot touch their own role. An admin then accepts (role →
`beta`) or declines; either way the pending flag clears and the user may ask
again.

---

## 10. Dev-only passwordless test logins

Three seeded accounts (`test-admin@`, `test-beta@`, `test-standard@
salary-explorer.invalid`) let automated browser testing and manual role checks
enter the app with no credentials. The security design is worth stealing:

- Domain is `.invalid` — an **RFC-reserved TLD**, so mail can never deliver.
- The accounts have **no password at all** — `create_user` is called without a
  `password` key. There is no credential to leak.
- The only way in is `auth.test_sign_in()`, which is **dead code unless
  `[test_login] enabled = true` exists in that environment's secrets**. Set
  locally and on dev; absent on test/prod. So even though all environments share
  one Supabase project and prod *knows* these users, they cannot be entered
  there.
- The login produces no Supabase session and no cookie — it lasts one browser
  session and cannot be replayed.
- `delete_own_account()` refuses to delete them (and the master account), so a
  self-service delete can never remove shared fixtures. The UI hides the control
  in the same cases; the server-side check is the backstop.

> **⚠ lesson — belt and braces.** Every one of those five properties is
> individually sufficient. That is the point: a test-login backdoor is exactly
> the feature that ends up in a breach write-up, so it is worth over-engineering.

---

## 11. Account deletion (GDPR)

`auth.delete_own_account()` — self-service, from the profile dialog, two-step
(arm, then type your own email to confirm).

**Order matters, and it is the interesting bit:** the user's feedback rows are
**anonymised first** (`user_id` → an all-zeroes sentinel UUID, email and
contact-permission cleared), *then* the auth user is deleted. The feedback table
has a `NOT NULL` user id, so the sentinel keeps the product history intact while
unlinking it from any real person — exactly what the privacy policy promises.

If you have related rows with FK/NOT NULL constraints, decide up front for each
one: cascade-delete, or anonymise-and-keep. Doing it after the first deletion
request is much more painful.

---

## 12. What this system deliberately does **not** have

Know these before assuming feature parity:

- **No self-service password reset.** There is no "forgot password" flow at all.
  Passwords are set by an admin (`auth.set_password()`) or at sign-up. If you
  reuse this design, this is the first gap to close — Supabase provides
  `reset_password_for_email`, and it needs the same button-press-not-GET
  treatment as §5 (reset links are prefetched exactly the same way).
- **No OAuth / social login.** None configured. Adding one requires
  `https://<host>/auth/v1/callback` in the allow-list.
- **No MFA.**
- **No self-service email change.**
- **No rate limiting on sign-up or sign-in in app code** — you are relying
  entirely on Supabase's built-in auth rate limits. (The project *does* rate-limit
  its public contact form, but that is separate code.)
- **No automated tests over the auth flows.** Verification is manual plus a
  browser-driving agent.

---

## 13. If you are building this from scratch — the short checklist

1. Put every authorization fact in a store the user's own token **cannot** write.
2. Normalize the identity provider's user object into one app-shaped dict, once.
3. Wrap credential fields in a real form so autofill commits.
4. **Never verify an email on a GET.** Link to your own page, verify on a button
   press. Assume every link in every email is prefetched.
5. Strip the token from the URL as soon as you have it.
6. Ship a resend path on day one, and show unconfirmed accounts in your admin UI.
7. Configure your own public URL explicitly per environment; keep the redirect
   allow-list in sync.
8. Use a real SMTP provider, and treat SPF/DKIM/DMARC as untouchable during any
   DNS work. Put "send one real confirmation email" on the deploy checklist,
   because no test covers dashboard config.
9. Store only the refresh token client-side, in a session cookie; expect it to
   rotate and write it back.
10. Decide the deletion story (cascade vs anonymise) for every related table
    before launch.

---

*Generated from the Salary Explorer codebase at the commit this document was
added. File references are accurate as of that commit; treat them as pointers,
not permalinks.*
