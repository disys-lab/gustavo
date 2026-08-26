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

## Obtaining worker.env automatically

Rather than hand-writing the env file, download one scoped to your own
Nebula identity directly from a running Gustavo instance — see
[`GET /api/config/worker-download`](../api/config.md#get-apiconfigworker-download):

```bash
curl -u <username>:<secret> http://<gustavo-host>:<port>/api/config/worker-download -o worker.env
```

This works for any authenticated user, not just admins — a regular user
gets a file scoped to only the `apps`/`device_groups` access they already
have, safe to hand to a worker node without granting anything extra. Point
`GUSTAVO_CONFIG_FILE` at the downloaded file and run `gustavo worker up`
as normal.

---

## Bringing a worker up without the CLI

The steps above assume `gustavo` is installed on the worker node. If it
isn't — or you'd rather not install it just to run a worker — each device
group's page in the UI (or the equivalent API routes directly) offers
three more ways to get the same worker running, none of which need the
`gustavo` package at all:

- A **device-group-scoped `worker.env`** (same as above, plus
  `DEVICE_GROUP` already filled in)
- A **self-contained `docker-compose.yml`** — `docker compose up -d` and
  it's running, no companion file needed
- A **self-contained launcher script** — `.command` for macOS/Linux,
  `.bat` for Windows — double-click it and it's running

See [Device Groups UI](../ui/device-groups.md#get-worker-config) for the
download buttons, or
[Device Groups API](../api/device-groups.md#worker-config-downloads) to
fetch any of them directly from a script.

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
| `REGISTRY_HOST` | Docker registry address — required; the worker fails to start without it |
| `REGISTRY_PORT` | Docker registry port — required; the worker fails to start without it |
| `WORKER_NMODE` | Docker network mode for the worker container (default: `host`) |
| `NEBULA_USERNAME` | Nebula API credentials |
| `NEBULA_PASSWORD` | Nebula API credentials |

---

## See also

- [Worker Node Setup](index.md#worker-node-setup) — full worker deployment walkthrough
