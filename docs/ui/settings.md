# Settings

Configure all platform connection parameters from the web UI. Changes are persisted to `platform.yaml` on disk immediately.

---

## Sections

The Settings page uses an accordion layout with one section expanded by default (Manager).

### Manager

| Field | Key | Description |
|-------|-----|-------------|
| Host | `MANAGER_HOST` | Nebula Manager IP or hostname |
| Port | `MANAGER_PORT` | Manager API port (default: 80) |
| Network Mode | `MANAGER_NMODE` | Docker network mode for Manager container |
| Image | `MANAGER_IMAGE` | Manager Docker image |
| Cache Expire Time | `CACHE_EXPIRE_TIME` | Worker metric TTL in seconds |

### Nebula Credentials

| Field | Key | Description |
|-------|-----|-------------|
| Username | `NEBULA_USERNAME` | HTTP Basic Auth username |
| Password | `NEBULA_PASSWORD` | HTTP Basic Auth password (masked) |
| Auth Token | `NEBULA_AUTH_TOKEN` | Base64 encoded credentials (masked) |
| Protocol | `NEBULA_PROTOCOL` | `http` or `https` |

### Registry

| Field | Key | Description |
|-------|-----|-------------|
| Host | `REGISTRY_HOST` | Registry IP or hostname |
| Port | `REGISTRY_PORT` | Registry API port |
| Image | `REGISTRY_IMAGE` | Registry Docker image |
| Backup Directory | `REGISTRY_BKP_DIR` | Host path for registry backups |
| Data Path | `REGISTRY_DATA_PATH` | Live registry data directory |

### Redis

| Field | Key | Description |
|-------|-----|-------------|
| Host | `REDIS_HOST` | Redis IP or hostname |
| Port | `REDIS_PORT` | Redis port |
| Auth Token | `REDIS_AUTH_TOKEN` | Redis password (masked) |
| Image | `REDIS_IMAGE` | Redis Docker image |
| Backup Directory | `REDIS_BKP_DIR` | Host path for RDB backups |

### MongoDB

| Field | Key | Description |
|-------|-----|-------------|
| Host | `MONGO_HOST` | MongoDB IP or hostname |
| Port | `MONGO_PORT` | MongoDB port |
| Username | `MONGO_USERNAME` | MongoDB admin username |
| Password | `MONGO_PASSWORD` | MongoDB admin password (masked) |
| Image | `MONGO_IMAGE` | MongoDB Docker image |
| Certificate Folder | `MONGO_CERTIFICATE_FOLDER_PATH` | TLS certificates directory |

### Syncer

| Field | Key | Description |
|-------|-----|-------------|
| Image | `SYNCER_IMAGE` | DREGSY Docker image |
| Network Mode | `SYNCER_NMODE` | Docker network mode for Syncer |
| Config File Path | `DREGSY_CONFIG_FILE_PATH` | Host path to `dregsy_conf.yml` |
| Mappings File Path | `DREGSY_MAPPING_FILE_PATH` | Host path to `mappings_list.yml` |

---

## Apply to all

The **Apply to all** button copies `MANAGER_HOST` to `REDIS_HOST`, `MONGO_HOST`, and `REGISTRY_HOST`. Useful when all platform services run on the same machine.

---

## Upload / Download config

- **Download** — saves the current config as a `manager.env` file (plain `KEY=VALUE` format)
- **Upload** — parses a `.env` file and merges it into the current config

!!! warning
    Downloaded config files contain plaintext passwords. Store them securely.

---

## Masked fields

Password and token fields display `***` when a value is stored. Leaving the field as `***` when saving does **not** overwrite the stored value. Only clear the field and enter a new value to change it.

---

## Syncer config editor (`/settings/syncer`)

A Monaco-based YAML editor for the DREGSY configuration files. Set the file paths in the main Settings page first, then use this page to view and edit the YAML content.
