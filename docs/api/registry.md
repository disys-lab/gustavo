# Registry Auth API

::: gustavo.api.routers.registry

---

## Overview

Backs the [registry-proxy nginx setup](../deployment.md#registry-authentication-proxy-nginx)
that fronts Gustavo's Docker registry — this is what replaced a static, shared htpasswd
credential with a live check against Gustavo's own Nebula-backed users. It's not something a
person or a docker client calls directly; nginx calls it on every `/v2/...` request via its
`auth_request` directive, forwarding the client's `Authorization` header automatically.

## `GET|HEAD|PUT|POST|PATCH|DELETE /api/registry/authorize`

Returns `200` to allow the request through, `401` to deny it. The body is irrelevant either
way — `auth_request` only looks at the status code.

All HTTP methods are accepted, not just `GET`: `auth_request` forwards the *original*
client's method through unchanged, and a `docker push` arrives as `PUT`/`PATCH`/`POST`
(chunked blob upload) or `DELETE`, not `GET`.

**Auth:** `verify_session_or_basic` — the same dependency
[`/config/worker-download`](config.md#get-apiconfigworker-download) uses. Accepts either:

- **HTTP Basic**, a Nebula `username:secret` pair, verified the identity-bound way `/login`
  verifies it (`nebula_auth.resolve_basic_credentials`) — what a `docker login`/`docker pull`/
  `docker push` client actually sends.
- **Bearer**, a Gustavo session token — mostly relevant if something ever calls this
  endpoint through Gustavo's own session flow rather than as a registry client.

**Response:**

```json
{ "error": false, "response": "ok" }
```

**Tier 1 only:** identity is the entire check — any valid Nebula user, admin or not, gets a
`200` for any repository and any operation. There's no per-repo `ro`/`rw` enforcement yet. A
Tier 2 version would additionally read `X-Original-URI` (to extract the repository name from
`/v2/{name}/...`) and `X-Original-Method` (pull vs. push) — both already forwarded by the
nginx config — and cross-check `nebula_auth.compute_permissions(cfg, session.username)["apps"]`
for that specific repository, the same way every other write in Gustavo is gated.

## Design notes

- **Why not a per-repo check from the start?** A Nebula app's name isn't guaranteed to match
  its registry repository name — nothing enforces that correspondence today. Tier 2 needs
  that decided first (treat it as a hard convention, or build an explicit mapping), so Tier 1
  ships the identity-only version now rather than block on it.
- **Why this reuses `verify_session_or_basic` instead of a bespoke check:** it's the exact
  same dependency `/config/worker-download` added to let a script pull its own worker config
  in one request. Reusing it here means registry auth and worker-config auth are verified by
  the same code path, not two implementations that could drift apart.
- **A `docker login` success does not mean blanket access under Tier 2** (when it exists) —
  the login probe hits a generic path with no specific repo in it, so only identity gets
  checked at login time; each individual pull/push afterward is what would actually enforce
  the per-repo grant.
