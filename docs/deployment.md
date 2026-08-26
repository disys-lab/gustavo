# Deployment

## Single-container model

Gustavo runs as a **single Docker container** combining the Next.js frontend and FastAPI backend. Supervisor manages both processes:

```
Container (port 3000 exposed)
├── supervisord
│   ├── gustavo-api  →  uvicorn on 127.0.0.1:8000 (loopback only)
│   └── gustavo-ui   →  Node.js standalone on 0.0.0.0:3000
└── /etc/gustavo/platform.yaml  (mounted volume)
```

The browser communicates only with port 3000. Next.js rewrites `/api/*` to `http://127.0.0.1:8000/api/*` — FastAPI is never directly reachable from outside the container.

---

## Docker Compose

### Full example

The compose file below shows all three common service patterns: the Gustavo UI, deploying a worker, and removing a worker. Copy this as your starting point and fill in the placeholder values.

```yaml
services:

  # ─── Gustavo UI + API ────────────────────────────────────────────────────────
  gustavo:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo
    platform: linux/amd64
    # network_mode: "host"   # Uncomment if managed services run on the host network
    ports:
      - "3000:3000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/:/tmp/
      - ./config:/etc/gustavo          # Platform config persistence
    environment:
      PYTHONWARNINGS: "ignore"
      GUSTAVO_API_CONFIG: /etc/gustavo/platform.yaml
      AUTH_ENABLED: "false"            # Set to "true" to require login
      # Required when AUTH_ENABLED=true:
      # AUTH_ENDPOINT: "https://your-auth-endpoint.example.com"
      # FIREBASE_API_KEY: "your-firebase-web-api-key"
      # CUSTOM_TOKEN_URL: "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
    restart: unless-stopped

  # ─── Deploy a worker node ────────────────────────────────────────────────────
  # Run once with: docker compose run --rm gustavo-worker-up
  gustavo-worker-up:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo_worker-up
    network_mode: "host"
    platform: linux/amd64
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./worker/config.env:/home/worker.env   # Worker config env file
    environment:
      PYTHONWARNINGS: "ignore"
      GUSTAVO_CONFIG_FILE: "/home/worker.env"
    command: ["gustavo", "worker", "up", "-i", "ghcr.io/disys-lab/gustavo-worker:latest", "-d", "your-device-group"]
    profiles: [worker]   # Only starts when explicitly included

  # ─── Remove a worker node ────────────────────────────────────────────────────
  # Run once with: docker compose run --rm gustavo-worker-remove
  gustavo-worker-remove:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo_worker-remove
    network_mode: "host"
    platform: linux/amd64
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./worker/config.env:/home/worker.env
    environment:
      PYTHONWARNINGS: "ignore"
      GUSTAVO_CONFIG_FILE: "/home/worker.env"
    command: ["gustavo", "worker", "remove", "-n", "worker_your-device-group"]
    profiles: [worker]
```

### Minimal setup (UI only)

```yaml
services:
  gustavo:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo
    platform: linux/amd64
    ports:
      - "3000:3000"
    volumes:
      - ./config:/etc/gustavo
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp:/tmp
    environment:
      GUSTAVO_API_CONFIG: /etc/gustavo/platform.yaml
      AUTH_ENABLED: "false"
    restart: unless-stopped
```

### Production (pinned admin credentials + session secret)

`AUTH_ENABLED=true` gates the UI behind login, backed by Nebula's own user
API (see [Authentication](api/auth.md)). At minimum, override the
break-glass admin credential and pin a session secret so sessions survive a
container restart:

```yaml
services:
  gustavo:
    image: ghcr.io/disys-lab/gustavo:0.4.0b16
    container_name: gustavo
    ports:
      - "3000:3000"
    volumes:
      - ./config:/etc/gustavo
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp:/tmp
    environment:
      GUSTAVO_API_CONFIG: /etc/gustavo/platform.yaml
      AUTH_ENABLED: "true"
      NEBULA_USERNAME: your-admin-username
      NEBULA_PASSWORD: your-admin-password
      GUSTAVO_SESSION_SECRET: your-random-secret   # e.g. `openssl rand -hex 32`
      # Optional SSO bridge — hidden from the login page unless set:
      # FIREBASE_API_KEY: AIzaSy...
      # AUTH_ENDPOINT: https://your-auth-endpoint.example.com
    restart: unless-stopped
```

!!! warning "Don't skip GUSTAVO_SESSION_SECRET in production"
    If unset, a random secret is generated each time the container starts,
    which invalidates every active session on every restart/redeploy. Fine
    for local development, not for anything users depend on staying logged
    into.

---

## Network modes

### Bridge mode (default, recommended)

The container joins Docker's default bridge network. Use container names for service addresses when other services are also containerised on the same host.

```bash
docker compose up -d
```

Access Gustavo at `http://<host-ip>:3000`.

### Host mode

In host mode the container shares the host's network namespace. FastAPI on `127.0.0.1:8000` is accessible from the host machine but not from outside.

```yaml
services:
  gustavo:
    network_mode: host
```

!!! note
    In host mode, set `REDIS_HOST`, `MONGO_HOST`, etc. to `127.0.0.1` if those services are running directly on the host.

---

## Volume mounts

| Mount | Purpose |
|-------|---------|
| `./config:/etc/gustavo` | Persists `platform.yaml` across container restarts |
| `/var/run/docker.sock:/var/run/docker.sock` | Required for `Manager` and backup handlers to control Docker |
| `/tmp:/tmp` | Backup scratch space for Redis RDB files and registry tarballs |

---

## Build arguments

```bash
docker build \
  --build-arg gustavo_version=0.4.0-beta.3 \
  --build-arg py_version=3.11 \
  --build-arg node_version=20 \
  --build-arg NEXT_PUBLIC_AUTH_ENABLED=false \
  -t gustavo:local .
```

!!! warning "NEXT_PUBLIC_AUTH_ENABLED is baked at build time"
    This build argument is embedded into the Next.js JS bundle during `npm run build`. For runtime auth control, use the `AUTH_ENABLED` environment variable instead. The middleware and AuthContext both read `AUTH_ENABLED` at runtime.

---

## CI/CD build tags

The GitHub Actions workflows use commit message tags to trigger builds:

| Tag | Effect |
|-----|--------|
| `#dockerbuild` | Build and push Docker image |
| `#macbuild` | Build macOS binary |
| `#linuxbuild` | Build Linux binary |
| `#bump` | Increment version |
| `#patch` / `#minor` / `#major` | Version bump level |

---

## Ports summary

| Port | Service | Bound to |
|------|---------|----------|
| 3000 | Next.js frontend | `0.0.0.0` (all interfaces) |
| 8000 | FastAPI backend | `127.0.0.1` (loopback only) |

---

## Log access

```bash
# All logs (supervisord, FastAPI, Next.js)
docker logs gustavo

# Follow
docker logs -f gustavo
```

Individual service logs within the container are written to stdout by supervisord.

---

## Health check

```bash
# From outside the container
curl http://localhost:3000/api/health

# From inside the container
docker exec gustavo curl -s http://127.0.0.1:8000/health
```

Expected response: `{"status":"ok"}`

---

## Registry Authentication Proxy (nginx)

### Problem

Gustavo's `registry` service (`registry:2`) runs with no authentication. Anyone who can
reach `REGISTRY_HOST:REGISTRY_PORT` can push, pull, or delete images. The goal was to add
access control without modifying Gustavo's source code, and without disturbing Gustavo's
own internal tooling (`gustavo registry list`, the Settings page, the dashboard's registry
view).

### Approach

Put an nginx reverse proxy in front of the registry. Clients (developers, downstream apps,
remote nodes) keep talking to the same external address and port they always have:

```
REGISTRY_HOST:REGISTRY_PORT
```

nginx terminates that connection, enforces HTTP Basic Auth, and forwards the request to the
real registry container, which was moved to an internal-only port (`5051`) that is not
exposed outside the host.

Credentials are checked against Gustavo's own Nebula-backed users, not a static file: nginx
delegates the decision to `GET|HEAD|PUT|POST|PATCH|DELETE /api/registry/authorize` via its
`auth_request` directive, forwarding the client's `Authorization` header automatically. That
endpoint is just `verify_session_or_basic` (the same dependency `/config/worker-download`
uses) wrapped in a route that returns 200 on success — any Basic-auth pair that resolves to
a real Nebula user (via the identity-bound check `/login` also uses) or a valid Gustavo
session Bearer token is allowed through; anything else gets a 401 before the real registry
ever sees the request. This means registry access is provisioned and revoked exactly the
same way as everything else in Gustavo — creating, deleting, or regenerating a user's
credential in the Users page immediately changes what they can pull/push, with nothing
registry-specific to manage separately. See [Registry API](api/registry.md) for the endpoint
itself.

This is currently identity-only (Tier 1): any valid Nebula user can pull/push any repo, the
same as the old shared htpasswd credential could — just individually attributable and
revocable now instead of one secret shared by everyone. A future per-repo version (Tier 2)
would additionally check the requester's `apps` grants against the specific repo being
pulled/pushed, using the `X-Original-URI`/`X-Original-Method` headers the proxy already
forwards but the endpoint doesn't yet act on.

Two paths are deliberately left open without authentication: `/v2/_catalog` (repository
listing) and `/v2/{repo}/tags/list` (tag listing for a given repo). Browsing what images and
tags exist is not a secret — only pulling/pushing the actual image data is. Everything else
under `/v2/` (manifest/blob reads and writes — the actual pull/push traffic) stays behind
`auth_request`.

### Port layout

`REGISTRY_PORT` means exactly one thing everywhere in Gustavo — the port every client (the
Settings page, downstream app deployments, workers, Gustavo's own catalog/tag calls) uses to
reach "the registry". Once a proxy is in front of the real registry, this is the proxy's
port, and stays that way permanently — nothing needs to be temporarily pointed at the raw
registry to bootstrap it.

The raw `registry:2` container's own bind port is a **separate** config key,
`REGISTRY_CONTAINER_PORT`. Empty by default (falls back to `REGISTRY_PORT`, correct for any
deployment with no proxy); set it explicitly once a proxy exists, so the raw container and
the proxy aren't both trying to bind the same port.

| Port | Config key | Bound to | Purpose |
|------|-----------|----------|---------|
| `REGISTRY_PORT` (e.g. `5001`) | `REGISTRY_PORT` | host, all interfaces | nginx — public-facing entry point, same port every client and downstream app has always used |
| `5051` | `REGISTRY_CONTAINER_PORT` | host, loopback-only *if* `REGISTRY_BIND_LOCALHOST` is set — see below | the real `registry:2` container — no auth, not meant to be reached directly by anyone except nginx |

`REGISTRY_HOST` in Gustavo's config stays as the external FQDN, unchanged, since that value
is also what gets used downstream when apps are deployed and needs to stay consistent.

### Directory structure

```
registry-proxy/
└── nginx.conf
```

No credentials file lives here anymore — there's nothing left for nginx to read locally,
since auth is checked live against Gustavo (`/api/registry/authorize`) on every request
instead of a static file it used to load at startup.

There is no separate `docker-compose.yml` for the proxy. The `registry-proxy` service is
defined as an additional service inside Gustavo's own `docker-compose.yml`, alongside the
existing `gustavo` service. This `registry-proxy/` directory just holds the nginx config
nginx needs, referenced by relative path from wherever Gustavo's compose file lives.

It does not define or manage the `registry` container itself — that container is owned and
launched separately by Gustavo's own `Manager.runRegistry()` logic, not by Compose.

### Important: lock down port `5051`

`5051` is the real, unauthenticated registry. Nothing about Docker's port binding makes
this local-only by default — `docker run`/the Docker SDK call Gustavo uses publishes ports
to `0.0.0.0` (all interfaces) unless told otherwise, so `5051` is reachable from the network,
not just from `localhost`, until this is explicitly closed off. The whole point of the proxy
is defeated otherwise: anyone can bypass nginx and the auth layer entirely by talking to
`5051` directly.

**Preferred: set `REGISTRY_BIND_LOCALHOST: true`** in Gustavo's config (Settings page or
`platform.yaml`), then restart/recreate the registry service (`gustavo registry recreate`,
or the equivalent Services-page action). This makes Gustavo itself publish `5051` to
`127.0.0.1` instead of `0.0.0.0` — only other processes on the same host (nginx) can reach
it, nothing external can. Off by default, to avoid silently breaking existing deployments
that pull directly from `5051`; only turn it on once clients have actually been repointed at
the authenticated port (`REGISTRY_PORT`, i.e. the port nginx listens on), or they'll lose
registry access entirely the moment it's flipped.

Verify after applying:

```bash
# from the host itself — should succeed
curl http://127.0.0.1:5051/v2/_catalog

docker inspect registry --format '{{json .NetworkSettings.Ports}}'
# should show "HostIp":"127.0.0.1", not "0.0.0.0"

# from any other machine on the network — should fail/time out
curl http://REGISTRY_HOST:5051/v2/_catalog
```

**Fallback, if the toggle isn't available (older Gustavo build) or host-level defense in
depth is wanted on top of it:** a firewall rule achieves the same thing independent of
Gustavo's own port-binding config —

```bash
sudo ufw deny 5051
```

— or an equivalent `iptables` rule restricting `5051` to loopback only. This check should
be repeated any time firewall rules on the host are changed for any other reason, same as
the toggle-based verification above.

### Step 1 — Move the real registry off the public port

Set both config keys up front, in Gustavo's Settings page (or `platform.yaml` directly) —
no juggling or temporary values needed, since `REGISTRY_PORT` and `REGISTRY_CONTAINER_PORT`
are independent from the start:

```
REGISTRY_PORT: 5001              # nginx's port — what everything else keeps using
REGISTRY_CONTAINER_PORT: 5051    # the raw registry container's own bind port
```

Then start (or restart/recreate) the registry service from Gustavo — it binds to
`REGISTRY_CONTAINER_PORT` (`5051`), leaving `REGISTRY_PORT` (`5001`) free for nginx.

Confirm the registry container is actually bound to `5051`:

```bash
docker inspect registry --format '{{json .HostConfig.PortBindings}}'
```

Should show `5051` on the host side.

### Step 2 — Credentials (no longer needed)

There's nothing to generate or manage here anymore. Every Nebula user already has a
credential (their `username:secret`, the same one used to log into Gustavo) — that's what
gets checked on every registry request now, live, via `/api/registry/authorize`. Creating a
user, deleting one, or regenerating a credential from the Users page takes effect on the
registry immediately, with nothing registry-specific to keep in sync.

### Step 3 — nginx configuration

`registry-proxy/nginx.conf`:

```nginx
server {
    listen REGISTRY_PORT;

    # Unauthenticated: repo listing stays open, so gustavo registry list
    # and the dashboard's registry view work without needing credentials.
    location /v2/_catalog {
        proxy_pass http://127.0.0.1:5051;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Unauthenticated: tag listing is the other half of "browsing is free" -
    # same rationale as /v2/_catalog above. Regex (not a plain prefix) so it
    # matches namespaced repo names containing slashes (e.g. foo/bar/tags/list)
    # without also matching /v2/<name>/manifests/... or /v2/<name>/blobs/...,
    # which must stay behind auth_request below.
    location ~ ^/v2/(?<repo_name>.+)/tags/list$ {
        proxy_pass http://127.0.0.1:5051;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Internal-only: nginx calls this for every /v2/ request below.
    # Not reachable directly from outside - "internal" enforces that.
    location = /_registry_auth {
        internal;

        proxy_pass http://127.0.0.1:GUSTAVO_PORT/api/registry/authorize;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";

        # Forwarded so a future per-repo (Tier 2) check can see who's
        # asking and for what. Authorization is forwarded automatically
        # (default subrequest behavior) - not set explicitly here, but
        # relied on.
        proxy_set_header X-Original-URI    $request_uri;
        proxy_set_header X-Original-Method $request_method;
    }

    location /v2/ {
        # The actual decision comes from Gustavo (Nebula-backed), not a
        # static file. auth_request alone doesn't send WWW-Authenticate
        # the way auth_basic used to — without it, Docker's client never
        # learns it should retry with Basic credentials and just accepts
        # the first unauthenticated 401 as final. "always" so it's added
        # on error responses too, not just 2xx/3xx.
        auth_request /_registry_auth;
        add_header WWW-Authenticate 'Basic realm="Registry"' always;

        proxy_pass http://127.0.0.1:5051;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 900;
    }
}
```

What each block does:

- `location /v2/_catalog` — exact-path match, no `auth_request`, so nginx proxies this
  straight through with no credential check.
- `location ~ ^/v2/(?<repo_name>.+)/tags/list$` — regex match, same treatment as
  `/v2/_catalog`. Must be a regex (not a plain prefix) so it only catches the `tags/list`
  suffix and doesn't accidentally also match `/v2/<name>/manifests/...` or
  `/v2/<name>/blobs/...` under the same repo name, which still need auth.
- `location = /_registry_auth` — `internal` means it can only be reached via nginx's own
  `auth_request` mechanism, never directly by a client. This is the sub-request nginx fires
  for every `/v2/` call below, forwarding the original `Authorization` header automatically
  (default subrequest behavior). `proxy_pass_request_body off` / `Content-Length ""` because
  the check doesn't need the request body (a docker push's actual image data), only the
  headers.
- `location /v2/` — catches everything else under the registry's v2 API: manifest
  pulls/pushes, blob uploads, deletes. `auth_request` fires the sub-request above first; a
  non-2xx response there (401) makes nginx return that status to the client directly, without
  the real request ever reaching the registry.
- `proxy_set_header Host $http_host` (not `$host`) — `$host` strips the port from the Host
  header. A registry's blob-upload flow can construct absolute self-referential URLs for its
  redirect steps using that header; with the port missing it defaults to `80`, breaking
  `docker push` specifically (`docker pull` never hits this — no redirect chain involved) with
  a `connection refused` error on port 80. `$http_host` preserves the port as the client
  actually sent it.
- `proxy_read_timeout 900` on the registry-facing block — large image layer uploads/downloads
  can take a while; this avoids nginx timing out a slow push/pull.

`GUSTAVO_PORT` above is whatever host port Gustavo's own container publishes (`3000` in the
compose example below) — `_registry_auth` reaches it over `127.0.0.1` because
`registry-proxy` runs in host network mode, same as it reaches the registry itself at
`127.0.0.1:5051`.

`nginx`'s location-matching picks the exact match first, then a matching regex location
(regardless of file order relative to prefix locations) over the longest plain-prefix match,
so `/v2/_catalog`, the `tags/list` regex, and `/_registry_auth` are all correctly intercepted
before falling through to the catch-all `/v2/` block.

### Step 4 — Add the proxy service to Gustavo's `docker-compose.yml`

The `registry-proxy` service is added directly into the same compose file that already
defines `gustavo`, not a separate file:

```yaml
services:
  gustavo:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo
    platform: linux/amd64
    ports:
      - "3000:3000"
    volumes:
      - ./config:/etc/gustavo
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/:/tmp/
    environment:
      PYTHONWARNINGS: "ignore"
      GUSTAVO_API_CONFIG: /etc/gustavo/platform.yaml
      AUTH_ENABLED: "true"
      AUTH_ENDPOINT: "https://your-auth-endpoint.example.com"
      FIREBASE_API_KEY: "your-firebase-web-api-key"
      CUSTOM_TOKEN_URL: "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
    restart: unless-stopped

  registry-proxy:
    image: nginx:1.27-alpine
    container_name: registry-proxy
    restart: always
    network_mode: "host"
    volumes:
      - ./registry-proxy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
```

`network_mode: "host"` on `registry-proxy` is required, not optional: `proxy_pass` targets
`127.0.0.1:5051`, which only resolves to the real registry if nginx shares the host's
network namespace directly. Without host networking, `127.0.0.1` inside the nginx
container would refer to the container itself, where nothing is listening on `5051`.

With host networking, a `ports:` mapping is unused (host mode shares the host's ports
directly), so it is correctly omitted for this service. `gustavo` keeps its own normal
`ports:` mapping since it is not on host networking.

Volume paths are relative to `registry-proxy/`, sitting next to wherever this
`docker-compose.yml` lives (e.g. alongside the existing `./config` directory already used
for Gustavo's own settings).

Bring everything up (or reload just the new service):

```bash
docker compose up -d
```

### Step 5 — Docker daemon: insecure registry entries

Since the registry/proxy speaks plain HTTP (no TLS), Docker's daemon must be told to treat
`REGISTRY_HOST:REGISTRY_PORT` (and `localhost:REGISTRY_PORT` for local testing) as insecure,
or `docker login`/`docker pull`/`docker push` will fail with a TLS handshake error.

This host runs **snap-installed Docker**, which has a non-obvious config path. `snap set
docker insecure-registries=...` writes to the snap's config database, but in the revision
installed here, the generated `daemon.json` came out malformed (`""value""` — doubled
quotes), and separately, the actual file the running `dockerd` process reads is **not**
`/etc/docker/daemon.json` or `/var/snap/docker/current/...`, but rather a path tied to the
specific snap revision number:

```
/var/snap/docker/<revision-number>/config/daemon.json
```

Found by checking the running process's actual launch flags:

```bash
ps aux | grep dockerd
# --config-file=/var/snap/docker/<revision>/config/daemon.json
```

Final working content of that file:

```json
{
  "insecure-registries": [
    "REGISTRY_HOST:REGISTRY_PORT",
    "localhost:REGISTRY_PORT"
  ]
}
```

After editing, restart the daemon:

```bash
sudo snap restart docker
docker info | grep -A 5 "Insecure Registries"
```

**Note for future maintenance:** because `snap set` produced broken JSON in this revision,
prefer editing this file directly going forward rather than using `snap set
docker insecure-registries=...` again. The revision number in the path will also change on
the next snap update, so re-check `ps aux | grep dockerd` if this setting ever appears to
silently stop applying after an update.

### Verification

```bash
# Anonymous catalog read — should succeed with no credentials
curl http://REGISTRY_HOST:REGISTRY_PORT/v2/_catalog

# Anonymous pull attempt — should 401
docker pull REGISTRY_HOST:REGISTRY_PORT/some-image:latest

# Authenticated pull — use a real Nebula user's own username:secret
# (the same credential they log into Gustavo with), not a separate
# registry-specific account
docker login REGISTRY_HOST:REGISTRY_PORT
docker pull REGISTRY_HOST:REGISTRY_PORT/some-image:latest

# A push exercises the auth check on PUT/PATCH, not just GET, and is a
# good end-to-end sanity check after any nginx change
docker tag some-image:latest REGISTRY_HOST:REGISTRY_PORT/some-image:test
docker push REGISTRY_HOST:REGISTRY_PORT/some-image:test

# Gustavo's own registry list, from inside its container
docker exec gustavo curl -s http://REGISTRY_HOST:REGISTRY_PORT/v2/_catalog

# The check endpoint directly, bypassing Docker's own login negotiation —
# useful for isolating whether a failure is in nginx/Gustavo's wiring or
# in Docker's client-side auth handshake
curl -u someuser:theirsecret http://REGISTRY_HOST:REGISTRY_PORT/v2/some-image/manifests/latest
```

### Important Notes

`/v2/_catalog` and `/v2/{repo}/tags/list` are public to anyone who can reach port
`REGISTRY_PORT` on the network, no credentials required. Repository names, tags, and the
existence of images are visible to anyone, but actually pulling, pushing, or deleting image
content still requires a valid Nebula credential, checked live via `/api/registry/authorize`.
This was an explicit, deliberate simplification: per-source-IP allowlisting (restricting the
anonymous catalog/tag exception to Gustavo's container only) was attempted first but added
complexity without a corresponding benefit, since Gustavo's container could not consistently
reach nginx under an IP-based allowlist while also preserving the requirement that every
client, including downstream deployed apps and remote nodes, address the registry at the
same consistent `REGISTRY_HOST:REGISTRY_PORT`.

This is currently identity-only: any valid Nebula user, admin or not, can pull and push any
repository — not scoped to the `apps`/`device_groups` grants that gate everything else in
Gustavo. See the note on Tier 1 vs. Tier 2 above.

