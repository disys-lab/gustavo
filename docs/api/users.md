# Users API

::: gustavo.api.routers.users

---

## Overview

Every route here is a thin wrapper over Nebula's own `users`/`user_groups`
Mongo collections (via `NebulaPythonSDK`) — Gustavo doesn't keep a
competing copy of user identity or roles. All routes require an admin
session, except `GET /me/groups` and `POST /me/regenerate-token`, which any
authenticated user can call for their own account.

A **group is a role**: `admin`, `pruning_allowed`, and the `apps`/
`device_groups` `ro`/`rw` maps are what actually govern what a user's own
Nebula token is allowed to do — Nebula enforces this itself on every write,
Gustavo doesn't re-implement the check.

## Credentials, not passwords

`create_user` and the two `regenerate-token` routes each generate a random
secret server-side and register it as that user's Nebula `token`. The
response includes the full `username:secret` login string exactly once —
Nebula never returns a usable plaintext secret from its own API, so this is
the only moment it's ever available. There is no "forgot password" flow;
losing a credential just means generating a new one.

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/users` | admin | List users with resolved groups + admin badge |
| POST | `/api/users` | admin | Create a user, optionally add to a group. Returns `{username, credential}` once |
| DELETE | `/api/users/{username}` | admin | Delete a user (and drop them from any groups) |
| POST | `/api/users/{username}/regenerate-token` | admin | Rotate another user's credential |
| POST | `/api/users/me/regenerate-token` | any | Rotate my own credential |
| GET | `/api/users/me/groups` | any | Which groups I belong to (used by the Apps page's owner-group picker) |
| GET | `/api/users/groups` | admin | List groups (roles) with full detail |
| POST | `/api/users/groups` | admin | Create a group |
| PUT | `/api/users/groups/{name}` | admin | Update a group's members/flags/grants |
| DELETE | `/api/users/groups/{name}` | admin | Delete a group |
