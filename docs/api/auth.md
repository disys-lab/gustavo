# Authentication API

::: gustavo.api.routers.auth

---

## Overview

Gustavo login is backed by **Nebula's own native user-management API** (the
same `users`/`user_groups` collections the Nebula Manager already exposes) —
there's no separate password database to keep in sync. Two kinds of account
exist:

- **The break-glass admin** — `NEBULA_USERNAME`/`NEBULA_PASSWORD` (default
  `nebula`/`nebula`, override via environment variables — see
  [Configuration](../configuration.md)). This is Nebula's own `local`
  super-admin account, and it's checked directly against the container's
  environment variables, independent of whether the Nebula Manager is even
  reachable yet. It's always available, from the moment the container boots
  — there's no first-run wizard.
- **Everyone else** (regular users, and any additional admins) — real Nebula
  `db` users, created from the **Users** page (admin-only). These are
  **token-based, not password-based**: Nebula never returns a usable
  plaintext secret from `create_user`/`update_user`, so there's no practical
  way to build a password-reset flow for them — instead, losing a credential
  just means an admin (or the user themselves) regenerates a new one.

Both account types log in through the same single field.

---

## `GET /api/auth/status`

Returns which login mode(s) are available. Public — no token required.

```json
{ "auth_enabled": true, "nebula_enabled": true, "firebase_enabled": false }
```

- `auth_enabled` — if `false`, every request is treated as the break-glass
  admin with no login at all (local/dev convenience).
- `nebula_enabled` — always `true`; the Nebula-backed login is never optional.
- `firebase_enabled` — `true` only when `AUTH_ENDPOINT` is configured; the
  frontend shows the SSO form as a secondary option only in that case.

---

## `POST /api/auth/login`

The one unified login endpoint.

**Request body:**

```json
{ "credential": "identifier:secret" }
```

The credential is split on the first `:`:

1. If `identifier:secret` matches `NEBULA_USERNAME:NEBULA_PASSWORD`
   (compared directly against environment variables, no Nebula API call
   involved) — the caller is the break-glass admin.
2. Otherwise, `identifier` is treated as a Nebula username and `secret` as
   that user's Nebula token. Verified by calling the Nebula Manager's
   `/status` endpoint with the secret as a Bearer token.

**Success response** (same shape for both account types):

```json
{
  "error": false,
  "response": { "token": "eyJhbGciOi...", "username": "alice", "is_admin": false }
}
```

`token` is a Gustavo-issued session JWT — store it and send it as
`Authorization: Bearer <token>` on every subsequent request. It carries the
Nebula secret needed to act on that user's behalf, Fernet-encrypted, never
in plaintext.

**Error response**, e.g. when the Nebula Manager hasn't been started yet:

```json
{
  "error": true,
  "response": "Platform services aren't running yet — start them first (or log in with the admin credentials to do so)."
}
```

---

## `POST /api/auth/token` (optional Firebase/SSO bridge)

Only meaningful when `AUTH_ENDPOINT` is configured. Mirrors the legacy
two-step Firebase exchange (`user_id`/`user_token` → custom token → ID
token) purely as a credential check — the resulting Firebase identity is
**not** bridged to a specific Nebula user. A successful exchange is treated
as a break-glass admin login, same response shape as `/login`. This is an
explicit, temporary simplification: per-user Firebase-to-Nebula identity
mapping is not implemented yet.

---

## Session tokens

Gustavo signs its own JWT at login (`gustavo/api/session.py`) rather than
passing Nebula credentials around directly. The JWT payload carries the
username, account type, admin flag, and the Nebula secret
(Fernet-encrypted, keyed off `GUSTAVO_SESSION_SECRET`). There's no
server-side session store — a regenerated token or a rotated
`GUSTAVO_SESSION_SECRET` simply makes old sessions fail on their next
Nebula call, forcing re-login.

## Auth dependency

::: gustavo.api.auth
