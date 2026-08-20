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

nginx terminates that connection, enforces HTTP Basic Auth via an htpasswd file, and
forwards the request to the real registry container, which was moved to an internal-only
port (`5051`) that is not exposed outside the host.

One path is deliberately left open without authentication: `/v2/_catalog`. This is the
registry's repository-listing endpoint and is what `gustavo registry list` calls. Since
Gustavo's container could not reliably reach the proxy under per-IP allowlisting without
breaking the "always address the registry as `REGISTRY_HOST:REGISTRY_PORT`"
requirement, the simplest fix was to make the catalog endpoint public and gate everything
else (pulls, pushes, deletes, tag listings) behind auth.

### Port layout

| Port | Bound to | Purpose |
|------|----------|---------|
| `REGISTRY_PORT` | host, all interfaces | nginx — public-facing entry point, same port every client and downstream app has always used |
| `5051` | host, loopback-reachable | the real `registry:2` container — no auth, not meant to be reached directly by anyone except nginx |

`REGISTRY_PORT` in Gustavo's config (`platform.yaml` / Settings page) was changed from
`REGISTRY_PORT` to `5051`, so the registry container itself now binds to `5051` on the host instead
of `REGISTRY_PORT`. nginx claims `REGISTRY_PORT`.

`REGISTRY_HOST` in Gustavo's config stays as the external FQDN
(`REGISTRY_HOST`), unchanged, since that value is also what gets used
downstream when apps are deployed and needs to stay consistent.

### Directory structure

```
registry-proxy/
├── nginx.conf
└── nginx-auth.htpasswd
```

There is no separate `docker-compose.yml` for the proxy. The `registry-proxy` service is
defined as an additional service inside Gustavo's own `docker-compose.yml`, alongside the
existing `gustavo` service. This `registry-proxy/` directory just holds the two files nginx
needs (its config and the credentials file), referenced by relative path from wherever
Gustavo's compose file lives.

It does not define or manage the `registry` container itself — that container is owned and
launched separately by Gustavo's own `Manager.runRegistry()` logic, not by Compose.

### Important: lock down port `5051` on the host firewall

`5051` is the real, unauthenticated registry. Nothing about Docker's port binding makes
this local-only by default — `docker run`/the Docker SDK call Gustavo uses publishes ports
to `0.0.0.0` (all interfaces) unless told otherwise, so `5051` is reachable from the network,
not just from `localhost`, until the host firewall is explicitly configured to block it.

This has to be done on the host, nginx and Docker config alone do not provide this:

```bash
sudo ufw deny 5051
```

Or, if not using `ufw`, an equivalent `iptables` rule restricting `5051` to loopback only.
Verify after applying:

```bash
# from the host itself — should succeed
curl http://127.0.0.1:5051/v2/_catalog

# from any other machine on the network — should fail/time out
curl http://REGISTRY_HOST:5051/v2/_catalog
```

If the second command succeeds from a remote machine, the entire point of the proxy is
defeated, since anyone could bypass nginx and the auth layer entirely by talking to `5051`
directly. This check should be repeated any time firewall rules on the host are changed for
any other reason.

### Step 1 — Move the real registry off the public port

This step has an ordering requirement tied to how Gustavo launches the registry container.
`runRegistry()` reads `REGISTRY_PORT` from config at the moment it starts the container, so
the value has to already be `5051` *before* the registry is first brought up, not changed
 afterward while it's running.

On initial setup, the sequence is:

1. In Gustavo's Settings page (or `platform.yaml` directly), set:

   ```
   REGISTRY_PORT: 5051
   ```

2. Start the registry service from Gustavo (first-time `gustavo registry run`, or the
   equivalent action in the UI) **with `REGISTRY_PORT` still set to `5051`**. This is what
   makes the container actually bind to `5051` on the host.

3. Once the registry container is confirmed up and bound to `5051` (see the check below),
   go back into Settings and change `REGISTRY_PORT` back to `REGISTRY_PORT`.

This last step does not restart or move the already-running registry container, since
Gustavo only applies `REGISTRY_PORT` when a service is launched or restarted. It updates
the config value that everything else (Gustavo's UI calls, downstream app deployments,
`REGISTRY_HOST`/`REGISTRY_PORT` consistency) reads going forward, so that the
externally-visible, documented address stays `REGISTRY_HOST:REGISTRY_PORT` even
though the registry container itself is still physically listening on `5051` underneath
the proxy.

**Do not restart or re-run the registry service after switching `REGISTRY_PORT` back to
`REGISTRY_PORT`.** Doing so would cause Gustavo to relaunch the registry container bound to `REGISTRY_PORT`
instead of `5051`, which collides with nginx and breaks the whole setup. The config value
shown in Settings after this point is intentionally out of sync with the container's actual
bound port — that mismatch is expected and is what makes the proxy arrangement work.

Confirm the registry container is actually bound to `5051` before flipping the config back:

```bash
docker inspect registry --format '{{json .HostConfig.PortBindings}}'
```

Should show `5051` on the host side.

### Step 2 — Generate the htpasswd credentials file

Credentials are stored using Apache's `htpasswd` utility, bcrypt-hashed, via a disposable
`httpd` container (no need to install `apache2-utils` on the host). Run this from the same
directory that holds Gustavo's `docker-compose.yml`:

```bash
mkdir -p registry-proxy && cd registry-proxy

docker run --rm --entrypoint htpasswd httpd:2 -Bbn cypress-user YOUR_PASSWORD > nginx-auth.htpasswd

cd ..
```

Flags used:

- `-B` — force bcrypt hashing (required; nginx's `auth_basic` module only accepts certain
  hash formats and the registry/nginx combination here was verified against bcrypt)
- `-b` — take the password from the command line argument rather than prompting
  interactively
- `-n` — print the result to stdout instead of writing to a file in place, so it can be
  redirected into `nginx-auth.htpasswd`

To add a second user later, append rather than regenerate from scratch:

```bash
docker run --rm --entrypoint htpasswd httpd:2 -Bbn anotheruser theirpassword >> nginx-auth.htpasswd
```

Note: if a password ever needs to be **changed** for an existing user, regenerate the
whole file cleanly (`-Bbn` redirected with `>`, not `>>`) rather than appending, to avoid
duplicate or conflicting entries for the same username, which caused exactly this kind of
silent failure during setup.

### Step 3 — nginx configuration

`registry-proxy/nginx.conf`:

```nginx
server {
    listen REGISTRY_PORT;

    location /v2/_catalog {
        proxy_pass http://127.0.0.1:5051;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /v2/ {
        auth_basic "Registry";
        auth_basic_user_file /etc/nginx/nginx-auth.htpasswd;

        proxy_pass http://127.0.0.1:5051;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 900;
    }
}
```

What each block does:

- `location /v2/_catalog` — exact-path match, no `auth_basic` directive, so nginx proxies
  this straight through with no credential check. This is what makes
  `gustavo registry list` (and the dashboard's registry view) work without needing
  Gustavo to supply credentials.
- `location /v2/` — catches everything else under the registry's v2 API: manifest
  pulls/pushes, blob uploads, tag listings, deletes. `auth_basic` here means nginx will
  return `401 Unauthorized` with a `WWW-Authenticate: Basic realm="Registry"` challenge
  unless valid credentials matching an entry in `nginx-auth.htpasswd` are supplied.
- `proxy_read_timeout 900` on the authenticated block — large image layer uploads/downloads
  can take a while; this avoids nginx timing out a slow push/pull.

`nginx`'s location-matching picks the more specific match (`= ` exact or longest prefix)
over the general one, so `/v2/_catalog` is correctly intercepted before falling through to
the catch-all `/v2/` block.

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
      AUTH_ENDPOINT: "https://us-central1-blockalytics-6ebbb.cloudfunctions.net/datachat"
      FIREBASE_API_KEY: "AIzaSyCzqiJpsZQbNbJ1LDXoelzjW7Iuvdj8GQg"
      CUSTOM_TOKEN_URL: "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
    restart: unless-stopped

  registry-proxy:
    image: nginx:1.27-alpine
    container_name: registry-proxy
    restart: always
    network_mode: "host"
    volumes:
      - ./registry-proxy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./registry-proxy/nginx-auth.htpasswd:/etc/nginx/nginx-auth.htpasswd:ro
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

# Authenticated pull — should succeed after login
docker login REGISTRY_HOST:REGISTRY_PORT
docker pull REGISTRY_HOST:REGISTRY_PORT/some-image:latest

# Gustavo's own registry list, from inside its container
docker exec gustavo curl -s http://REGISTRY_HOST:REGISTRY_PORT/v2/_catalog
```

### Important Notes

`/v2/_catalog` is public to anyone who can reach port `REGISTRY_PORT` on the network, no credentials
required. Repository names and the existence of images are visible to anyone, but actually
pulling, pushing, or deleting image content still requires valid credentials from
`nginx-auth.htpasswd`. This was an explicit, deliberate simplification: per-source-IP
allowlisting (restricting the anonymous catalog exception to Gustavo's container only) was
attempted first but added complexity without a corresponding benefit, since Gustavo's
container could not consistently reach nginx under an IP-based allowlist while also
preserving the requirement that every client, including downstream deployed apps and remote
nodes, address the registry at the same consistent `REGISTRY_HOST:REGISTRY_PORT`.

