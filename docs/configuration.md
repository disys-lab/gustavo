# Configuration Reference

All Gustavo configuration is stored as a flat key-value map. In Docker deployments this lives at `/etc/gustavo/platform.yaml` (YAML format). In CLI-only mode it is a `KEY=VALUE` env file pointed to by `GUSTAVO_CONFIG_FILE`.

The Settings page in the web UI is the easiest way to manage configuration. Changes are written to disk immediately and take effect on the next API call — no restart required.

---

## Manager

| Key | Default | Description |
|-----|---------|-------------|
| `MANAGER_HOST` | host IP | IP or hostname of the Nebula Manager container |
| `MANAGER_PORT` | `80` | HTTP port the Manager API listens on |
| `MANAGER_NMODE` | `bridge` | Docker network mode for the Manager container (`bridge` or `host`) |
| `MANAGER_IMAGE` | `ghcr.io/disys-lab/gustavo-manager:latest` | Docker image to use when launching Manager |
| `CACHE_EXPIRE_TIME` | `120` | Seconds before cached worker metrics expire in Redis |

---

## Nebula credentials

| Key | Default | Description |
|-----|---------|-------------|
| `NEBULA_USERNAME` | `nebula` | HTTP Basic Auth username for the Nebula Manager API |
| `NEBULA_PASSWORD` | `nebula` | HTTP Basic Auth password |
| `NEBULA_AUTH_TOKEN` | `bmVidWxhOm5lYnVsYQ==` | Base64 encoded `username:password` (derived automatically from above) |
| `NEBULA_PROTOCOL` | `http` | Protocol for Nebula API calls (`http` or `https`) |

`NEBULA_USERNAME`/`NEBULA_PASSWORD` are also the **break-glass admin login** for the
Gustavo UI itself (`nebula:nebula` by default — see [Authentication](api/auth.md)).
If set as container environment variables (recommended for any non-throwaway
deployment — see below), the env var always wins over whatever is in
`platform.yaml`, so the login credential can never drift from what Gustavo
actually uses to talk to Nebula.

---

## Registry

| Key | Default | Description |
|-----|---------|-------------|
| `REGISTRY_HOST` | host IP | IP or hostname of the Docker registry |
| `REGISTRY_PORT` | `5001` | Port the registry API listens on |
| `REGISTRY_IMAGE` | `registry:2` | Docker image for the local registry |
| `REGISTRY_BKP_DIR` | `/tmp/` | Host directory where registry tar backups are stored |
| `REGISTRY_DATA_PATH` | _(empty)_ | Host path to the live registry data directory (e.g. `/data/registry/docker`). Used for backup. Falls back to `{REGISTRY_BKP_DIR}/docker` if unset. |

---

## Redis

| Key | Default | Description |
|-----|---------|-------------|
| `REDIS_HOST` | host IP | IP or hostname of the Redis instance |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_AUTH_TOKEN` | _(see defaults)_ | Redis `requirepass` value |
| `REDIS_IMAGE` | `redis/redis-stack:7.4.0-v1` | Docker image used when launching Redis |
| `REDIS_BKP_DIR` | `/tmp/` | Host directory for Redis RDB backup files |

---

## MongoDB

| Key | Default | Description |
|-----|---------|-------------|
| `MONGO_HOST` | host IP | IP or hostname of MongoDB |
| `MONGO_PORT` | `27017` | MongoDB port |
| `MONGO_USERNAME` | `nebula` | MongoDB admin username |
| `MONGO_PASSWORD` | `nebula` | MongoDB admin password |
| `MONGO_IMAGE` | `mongo:4.0.19` | Docker image used when launching MongoDB |
| `MONGO_CERTIFICATE_FOLDER_PATH` | `/tmp/` | Path to TLS certificates directory |

---

## Syncer

| Key | Default | Description |
|-----|---------|-------------|
| `SYNCER_IMAGE` | `ghcr.io/disys-lab/dregsy:latest` | Docker image for the DREGSY image syncer |
| `SYNCER_NMODE` | `host` | Docker network mode for the Syncer container |
| `DREGSY_CONFIG_FILE_PATH` | _(empty)_ | Absolute path to the DREGSY YAML config file on the host |
| `DREGSY_MAPPING_FILE_PATH` | _(empty)_ | Absolute path to the DREGSY mappings YAML file on the host |

---

## Reporter

`REPORTER_*` configures the Reporter platform service — a REST endpoint
workers can report status to instead of writing to Redis directly. See
[Services: Reporter](ui/dashboard.md#platform-services-card) for the
service lifecycle, and [Device Groups: worker config](ui/device-groups.md#get-worker-config)
for how a worker is told to use it.

| Key | Default | Description |
|-----|---------|-------------|
| `REPORTER_IMAGE` | `ghcr.io/disys-lab/gustavo-reporter:latest` | Docker image for the Reporter service |
| `REPORTER_HOST` | host IP | IP or hostname of the Reporter instance |
| `REPORTER_PORT` | `8090` | Port the Reporter API listens on |
| `GUSTAVO_API_HOST` | host IP | Host Reporter uses to reach Gustavo's own API to verify worker credentials |
| `GUSTAVO_API_PORT` | `3002` | Gustavo's **host-published** port — not FastAPI's internal `8000` (bound to `127.0.0.1` inside Gustavo's own container, unreachable from Reporter's separate container) |

!!! note
    `GUSTAVO_API_PORT` must match whatever port the `gustavo` container is
    actually published on for the deployment (e.g. `3000:3000` in this
    repo's own `docker-compose.yml`, but `3002:3000` on a host where port
    3000 was already taken by something else). Getting this wrong makes
    Reporter's credential-verification calls fail silently.

---

## Public Facing Endpoints

Externally-reachable addresses for Manager, Reporter, and Gustavo itself —
e.g. behind a Cloudflare Tunnel — separate from the internal LAN addresses
above. Only applied when a worker config download explicitly opts in, or
the caller belongs to an [external user group](#external-user-groups).
Protocol is always `https` for these: a public endpoint always terminates
TLS at the edge.

| Key | Default | Description |
|-----|---------|-------------|
| `PUBLIC_ENDPOINTS_ENABLED` | `false` | Master switch. Off means every download keeps using the internal `*_HOST`/`*_PORT` values regardless of anything below |
| `PUBLIC_MANAGER_HOST` / `PUBLIC_MANAGER_PORT` | _(empty)_ / `443` | Public Manager address |
| `PUBLIC_REPORTER_HOST` / `PUBLIC_REPORTER_PORT` | _(empty)_ / `443` | Public Reporter address |
| `PUBLIC_GUSTAVO_HOST` / `PUBLIC_GUSTAVO_PORT` | _(empty)_ / `443` | Public Gustavo address (reserved for future use — no current consumer) |

See [Settings: Public Facing Endpoints](ui/settings.md#public-facing-endpoints)
and [Device Groups: Public Facing Access](ui/device-groups.md#get-worker-config).

---

## Public Registry Access

A separate, stricter opt-in from `PUBLIC_ENDPOINTS_ENABLED` above — off by
default even when that's on.

| Key | Default | Description |
|-----|---------|-------------|
| `PUBLIC_REGISTRY_ENABLED` | `false` | When `true`, `PUBLIC_REGISTRY_HOST`/`PORT` becomes *the* registry for every worker config and the Registry tab, for every caller — not just external users. When `false`, external users get no registry access at all; everyone else keeps the internal `REGISTRY_HOST`/`PORT` unconditionally |
| `PUBLIC_REGISTRY_HOST` / `PUBLIC_REGISTRY_PORT` | _(empty)_ / `443` | Public registry address |

See [Registry](ui/registry.md) for the full pull/push policy this drives.

---

## External User Groups

| Key | Default | Description |
|-----|---------|-------------|
| `EXTERNAL_USER_GROUPS` | `[]` | Nebula user groups whose members are treated as external — see [External Users](ui/users.md#external-user-groups) |

Membership in any listed group makes worker-config downloads and Registry
access mandatory-public for that user, regardless of any per-device-group
checkbox they'd otherwise control. Nobody is external until an admin
explicitly adds a group here.

---

## Worker / Misc

| Key | Default | Description |
|-----|---------|-------------|
| `WORKER_NMODE` | `host` | Docker network mode for worker containers |

---

## Environment variables (runtime, not stored in YAML)

These are set on the Docker container and are not persisted to `platform.yaml`:

| Variable | Description |
|----------|-------------|
| `GUSTAVO_API_CONFIG` | Path to the YAML config file (default: `/etc/gustavo/platform.yaml`) |
| `AUTH_ENABLED` | Set to `true` to require login. Default: `true` (see [Authentication](api/auth.md)) |
| `NEBULA_USERNAME` / `NEBULA_PASSWORD` | Break-glass admin login (`identifier:secret` on the sign-in page). Overrides `platform.yaml` when set. Default: `nebula` / `nebula` — override for any non-throwaway deployment |
| `GUSTAVO_SESSION_SECRET` | Signs/encrypts Gustavo session tokens. If unset, a random secret is generated at startup and **every restart invalidates all sessions**. Pin this (e.g. `openssl rand -hex 32`) for production |
| `GUSTAVO_SESSION_TTL` | Session lifetime in seconds. Default: `43200` (12h) |
| `FIREBASE_API_KEY` | Firebase Web API key (only used if `AUTH_ENDPOINT` is also set) |
| `AUTH_ENDPOINT` | URL of the custom token exchange endpoint. If unset, the Firebase/SSO login option is hidden and the Nebula-backed login is the only path |
| `CUSTOM_TOKEN_URL` | Firebase `signInWithCustomToken` URL (has a working default; override only if needed) |
| `GUSTAVO_CONFIG_FILE` | Path to the env-format config shim used by the CLI and Cache (set automatically by the API) |
| `FASTAPI_URL` | Used by Next.js to proxy `/api/*` requests. Default: `http://127.0.0.1:8000` |

---

## Sensitive values

The following keys are masked as `***` in all API responses and the UI. They are stored in plaintext in `platform.yaml` on the server but never returned to the browser:

- `NEBULA_PASSWORD`
- `NEBULA_AUTH_TOKEN`
- `REDIS_AUTH_TOKEN`
- `MONGO_PASSWORD`

When saving settings from the UI, leaving a masked field unchanged (still showing `***`) does not overwrite the stored value.

---

## Docker-in-Bridge-mode networking note

When running Gustavo in Docker bridge mode and the managed services (Redis, MongoDB, etc.) are also in Docker containers, use **Docker container names** (via a shared network) rather than dynamic bridge IPs (`172.x.x.x`). Bridge IPs change when containers restart.

Example:

```yaml
# docker-compose.yml
services:
  redis:
    image: redis/redis-stack:7.4.0-v1
    networks:
      - nebula

  gustavo:
    image: ghcr.io/disys-lab/gustavo:0.4.0b16
    environment:
      # Use container name, not 172.x.x.x
      # Set in Settings page after startup
    networks:
      - nebula

networks:
  nebula:
    driver: bridge
```

Then set `REDIS_HOST: redis` in Settings.
