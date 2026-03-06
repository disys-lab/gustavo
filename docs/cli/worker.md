# `gustavo worker`

Deploy and manage the Gustavo worker agent on edge devices. The worker container runs on remote nodes, pulls assigned applications, and reports metrics back to Redis.

```
Usage: gustavo worker [OPTIONS] COMMAND [ARGS]...

  Manage worker.
```

---

## Prerequisites

Run these on **each worker node** before deploying:

1. Docker installed and running as non-root (see [Common prerequisites](index.md#common-prerequisites))
2. Docker registry configured as insecure (see [Common prerequisites](index.md#common-prerequisites))
3. `GUSTAVO_CONFIG_FILE` pointing to a valid env file with `MANAGER_HOST`, `REDIS_HOST`, etc.

---

## Commands

### `up`

Deploy the worker container on the current host.

```bash
gustavo worker up
```

The worker container:
- Connects to the Nebula Manager to register itself
- Polls for assigned applications and manages their container lifecycle
- Reports CPU, memory, disk, and container metrics to Redis at `CACHE_EXPIRE_TIME` intervals

---

### `remove`

Stop and remove the worker container.

```bash
gustavo worker remove
```

---

### `recreate`

Remove and re-deploy the worker (useful after config changes).

```bash
gustavo worker recreate
```

Equivalent to `worker remove` followed by `worker up`.

---

## Configuration keys used

| Key | Description |
|-----|-------------|
| `MANAGER_HOST` | Nebula Manager address |
| `MANAGER_PORT` | Nebula Manager port |
| `REDIS_HOST` | Redis address (for metric reporting) |
| `REDIS_PORT` | Redis port |
| `REDIS_AUTH_TOKEN` | Redis password |
| `WORKER_NMODE` | Docker network mode for the worker container (default: `host`) |
| `NEBULA_USERNAME` | Nebula API credentials |
| `NEBULA_PASSWORD` | Nebula API credentials |

---

## See also

- [Worker Node Setup](index.md#worker-node-setup) — full worker deployment walkthrough
