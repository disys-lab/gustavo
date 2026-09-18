# Device Groups API

Manage device groups — logical collections of worker nodes that share the same application deployments.

::: gustavo.api.routers.device_groups

---

## Endpoints

### `GET /api/device-groups`

List all device groups with their current app membership.

**Response:**

```json
{
  "error": false,
  "response": {
    "device_groups": ["production", "staging"],
    "details": {
      "production": { "apps": ["test_linreg", "inference_service"] },
      "staging": { "apps": ["test_linreg"] }
    }
  }
}
```

---

### `POST /api/device-groups`

Create a new device group.

**Request body:**

```json
{
  "name": "production",
  "apps": ["test_linreg"]
}
```

---

### `GET /api/device-groups/{name}`

Get details of a single device group.

---

### `PUT /api/device-groups/{name}`

Update a device group (replace its app list).

**Request body:**

```json
{
  "apps": ["test_linreg", "inference_service"]
}
```

---

### `DELETE /api/device-groups/{name}`

Delete a device group.

---

### `POST /api/device-groups/{name}/apps/add`

Add one or more apps to a device group without replacing the existing list.

**Request body:**

```json
{ "apps": ["new_app"] }
```

---

### `POST /api/device-groups/{name}/apps/remove`

Remove one or more apps from a device group.

**Request body:**

```json
{ "apps": ["old_app"] }
```

---

### `POST /api/device-groups/{name}/cron-jobs/add`

Add one or more cron jobs to a device group without replacing the
existing list. Mirrors `apps/add`.

**Request body:**

```json
{ "cron_jobs": ["new_cron_job"] }
```

---

### `POST /api/device-groups/{name}/cron-jobs/remove`

Remove one or more cron jobs from a device group. Mirrors `apps/remove`.

**Request body:**

```json
{ "cron_jobs": ["old_cron_job"] }
```

---

## Worker config downloads

Four independent ways to get a worker running for this device group — the
native env file for [`gustavo worker up`](../cli/worker.md), a
self-contained `docker-compose.yml`, and self-contained launcher scripts
for macOS/Linux and Windows. "Independent" is deliberate: downloading one
has no effect on the others, and none of them needs a companion file —
pick whichever modality fits, there's no wrong choice. All four pull from
the same underlying value set (`nebula_auth.build_worker_env`), so they
can't drift out of sync with each other even though each is generated
fresh, scoped to the caller's own Nebula identity and this device group.

All four accept the same two authentication methods as
[`GET /api/config/worker-download`](config.md#get-apiconfigworker-download)
— a Bearer session token, or HTTP Basic auth with the caller's own
`username:secret` (for one-shot use from a remote script). All four also
require the caller to actually have access to this device group — admin,
or a member of a group it's granted to — otherwise `403`.

All four also accept these optional query params:

| Param | Default | Effect |
|---|---|---|
| `gpu` | `false` | Adds `GPU_ENABLED=true` — only for a device group whose hardware actually has a GPU `nvidia-container-toolkit` can expose. Applies to every container that worker launches, not to any individual app. |
| `reporter` | `false` | Emits `REPORTER_HOST`/`REPORTER_PORT`/`REPORTER_PROTOCOL` instead of `REDIS_HOST`/`REDIS_PORT`/`REDIS_AUTH_TOKEN` — mutually exclusive with direct Redis reporting. Forced `true` server-side for a caller in any `EXTERNAL_USER_GROUPS` group, regardless of what's passed — `REDIS_AUTH_TOKEN` is a single shared, unscoped credential an external caller must never receive. |
| `check_in_time` | `60` | `NEBULA_MANAGER_CHECK_IN_TIME` in seconds — the same loop tick drives both the Nebula poll and the status report, there's no separate timer. |
| `public_endpoints` | `false` | Uses `PUBLIC_MANAGER_HOST`/`PORT` (and `PUBLIC_REPORTER_HOST`/`PORT` if `reporter` is also set) instead of the internal LAN addresses. Forced `true` server-side for a caller in any `EXTERNAL_USER_GROUPS` group. |

Registry inclusion is never a caller-supplied param — it's derived
entirely from `PUBLIC_REGISTRY_ENABLED` and whether the caller is an
external-group member. See [Registry: internal vs. external access](../ui/registry.md#internal-vs-external-access).

```bash
curl -u alice:her_secret "http://<gustavo-host>:<port>/api/device-groups/production/worker-env?reporter=true&public_endpoints=true&check_in_time=30"
```

---

### `GET /api/device-groups/{name}/worker-env`

Same shape as `GET /api/config/worker-download`, scoped to this device
group — adds `DEVICE_GROUP={name}` so the `gustavo worker up` invocation
needs one less flag.

```bash
curl -u alice:her_secret http://<gustavo-host>:<port>/api/device-groups/production/worker-env -o worker.env
```

---

### `GET /api/device-groups/{name}/worker-compose`

A self-contained `docker-compose.yml` — every value baked directly into
the service's `environment:` block as a literal, not `${VAR}` substitution
from a companion `.env`. Nothing else to download:

```bash
curl -u alice:her_secret http://<gustavo-host>:<port>/api/device-groups/production/worker-compose -o docker-compose.yml
docker compose up -d
```

---

### `GET /api/device-groups/{name}/worker-script`

A self-contained `docker run` launcher script for macOS/Linux — same
independence guarantee as `worker-compose`, every value baked in directly.
Save it with a `.command` extension and it's double-click-runnable from
macOS Finder (once marked executable); as a plain `.sh` it's a normal
terminal script on either macOS or Linux:

```bash
curl -u alice:her_secret http://<gustavo-host>:<port>/api/device-groups/production/worker-script -o worker.command
chmod +x worker.command
./worker.command
```

---

### `GET /api/device-groups/{name}/worker-script-windows`

The same launcher, generated as a Windows `.bat` instead of a bash script
— `cmd.exe` has different line-continuation syntax and its own quoting
rules, so this is its own generator rather than a converted copy of
`worker-script`. Double-clicking the downloaded `.bat` in Windows Explorer
runs it directly with no setup — unlike a PowerShell `.ps1`, which Windows
opens in a text editor rather than running on double-click by default.
