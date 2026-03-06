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
| `AUTH_ENABLED` | Set to `true` to require Firebase login. Default: `false` |
| `FIREBASE_API_KEY` | Firebase Web API key (required when `AUTH_ENABLED=true`) |
| `AUTH_ENDPOINT` | URL of the custom token exchange endpoint (required when `AUTH_ENABLED=true`) |
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
