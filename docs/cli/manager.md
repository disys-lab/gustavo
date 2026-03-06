# `gustavo manager`

Control the lifecycle of the five core platform services: **registry**, **redis**, **mongo**, **manager**, and **syncer**.

```
Usage: gustavo manager [OPTIONS] COMMAND [ARGS]...

  Administer the manager.
```

---

## Commands

### `check`

Verify the Nebula Manager API is responding.

```bash
gustavo manager check
```

Pings `http://{MANAGER_HOST}:{MANAGER_PORT}/api/v2/status`. Returns success if the API responds with HTTP 200.

---

### `up`

Launch a platform service.

```bash
gustavo manager up [SERVICE]
```

| Argument | Values |
|----------|--------|
| `SERVICE` | `registry`, `redis`, `mongo`, `manager`, `syncer`, `all` |

Examples:

```bash
# Launch all services in dependency order
gustavo manager up all

# Launch individual services
gustavo manager up registry
gustavo manager up redis
gustavo manager up mongo
gustavo manager up manager
gustavo manager up syncer
```

!!! note "Service dependencies"
    Launch services in this order: Registry → Redis → MongoDB → Manager → Syncer.
    Manager depends on MongoDB and Redis being available.

---

### `stop`

Stop a running service container.

```bash
gustavo manager stop [SERVICE]
```

---

### `start`

Start a previously stopped service container (without recreating it).

```bash
gustavo manager start [SERVICE]
```

---

### `kill`

Send SIGKILL to a service container.

```bash
gustavo manager kill [SERVICE]
```

---

### `remove`

Stop and remove a service container.

```bash
gustavo manager remove [SERVICE]
```

---

### `restart`

Restart a service container.

```bash
gustavo manager restart [SERVICE]
```

---

## Configuration keys used

| Key | Required for |
|-----|-------------|
| `MANAGER_HOST` | All `manager` commands |
| `MANAGER_PORT` | All `manager` commands |
| `MANAGER_IMAGE` | `manager up manager` |
| `MANAGER_NMODE` | `manager up manager` |
| `REGISTRY_HOST` | `manager up registry` |
| `REGISTRY_PORT` | `manager up registry` |
| `REGISTRY_IMAGE` | `manager up registry` |
| `REDIS_HOST` | `manager up redis` |
| `REDIS_PORT` | `manager up redis` |
| `REDIS_IMAGE` | `manager up redis` |
| `REDIS_AUTH_TOKEN` | `manager up redis` |
| `MONGO_HOST` | `manager up mongo` |
| `MONGO_PORT` | `manager up mongo` |
| `MONGO_IMAGE` | `manager up mongo` |
| `SYNCER_IMAGE` | `manager up syncer` |
| `DREGSY_CONFIG_FILE_PATH` | `manager up syncer` |
| `DREGSY_MAPPING_FILE_PATH` | `manager up syncer` |
