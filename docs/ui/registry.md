# Registry

Browse the images and tags available in the Docker registry from the web
UI (`/registry`).

---

## Image list

Shows every repository in the registry with its tags as badges. Each row's
name is prefixed with the registry URL currently in effect (see
[Internal vs. external access](#internal-vs-external-access) below), so
it's always clear which registry you're looking at. **Refresh** re-queries
the catalog.

If the registry has no images, or the catalog request fails, the page
shows the raw catalog URL and response instead of a blank table — useful
for diagnosing a misconfigured `REGISTRY_HOST`/`REGISTRY_PORT` without
leaving the browser.

---

## Internal vs. external access

Which registry a request actually reaches is derived entirely from the
caller's identity and one config flag — never a per-request choice made in
the UI. The same policy governs both this page (`GET /api/apps/registry/images`)
and the registry fields baked into worker config downloads
(`GET /api/device-groups/{name}/worker-*`).

| Caller | `PUBLIC_REGISTRY_ENABLED` off | `PUBLIC_REGISTRY_ENABLED` on |
|---|---|---|
| Non-external | Internal `REGISTRY_HOST`/`PORT` | Public `PUBLIC_REGISTRY_HOST`/`PORT` |
| [External](users.md#external-user-groups) | No registry access at all | Public `PUBLIC_REGISTRY_HOST`/`PORT` |

- **Off by default.** Until an admin sets `PUBLIC_REGISTRY_HOST`/`PORT`
  and enables the flag in [Settings](settings.md#public-registry-access),
  external users simply have no registry: the page shows "Could not access
  registry. Check with Admin to see if Registry access is enabled." and no
  request is attempted.
- **Once enabled, it applies to everyone**, not just external users — a
  public endpoint is reachable from anywhere, so there's no reason to keep
  routing internal callers to the internal-only address.
- This is the same reasoning `EXTERNAL_USER_GROUPS` applies to Manager and
  Reporter (see [Device Groups: worker config](device-groups.md#get-worker-config)):
  identity determines the endpoint, the caller doesn't choose it.

---

## Registry proxy (nginx `auth_request`)

Pushes and pulls against the registry itself (not this UI page) are
gated separately, at the reverse proxy in front of the registry: every
`/v2/...` request is authorized against Nebula's own users via
[`GET|HEAD|PUT|POST|PATCH|DELETE /api/registry/authorize`](../api/registry.md)
before it reaches the registry. A valid Nebula `username:secret` (Basic
auth) or Gustavo session Bearer token is required; anything else gets a
`401` before the registry ever sees the request. This check is
identity-only — it does not yet distinguish which repository is being
pushed or pulled.
