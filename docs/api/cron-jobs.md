# Cron Jobs API

Create, read, update, and delete Nebula cron jobs. Structural mirror of
the [Apps API](apps.md) — same permission model, minus registry-image and
YAML-import endpoints (reuses `/api/apps/registry/images` and
`/api/apps/yaml/parse` on the frontend), plus YAML export.

::: gustavo.api.routers.cron_jobs

---

## Endpoints

### `GET /api/cron-jobs`

List all cron jobs, filtered to the caller's grants if not an admin.

**Response:**

```json
{
  "error": false,
  "response": {
    "cron_jobs": ["nightly_cleanup", "hourly_sync"]
  }
}
```

---

### `GET /api/cron-jobs/{name}`

Get the full configuration of a single cron job.

```
GET /api/cron-jobs/nightly_cleanup
```

---

### `POST /api/cron-jobs`

Create a new cron job.

**Request body:**

```json
{
  "name": "nightly_cleanup",
  "config": {
    "docker_image": "192.168.1.100:5001/cleanup:latest",
    "schedule": "0 2 * * *",
    "env_vars": {"RETENTION_DAYS": "7"},
    "running": true,
    "privileged": false,
    "networks": ["nebula"]
  },
  "device_groups": ["production"]
}
```

Unlike `POST /api/apps`, no `APP_ID`-style env var is auto-injected —
cron job containers don't self-report through the Redis/Reporter path.

After creating the cron job, it is added to all specified `device_groups`.

---

### `PUT /api/cron-jobs/{name}`

Update an existing cron job. Same `config` body as POST. Device group
membership is not read from this request — manage it via the
[Device Groups API](device-groups.md#post-apidevice-groupsnamecron-jobsadd).

---

### `DELETE /api/cron-jobs/{name}`

Delete a cron job. Removed from all device groups before deletion.

---

### `GET /api/cron-jobs/{name}/yaml`

Export a cron job's configuration as a YAML string.

**Response:** `text/plain`

```yaml
docker_image: 192.168.1.100:5001/cleanup:latest
schedule: 0 2 * * *
running: true
```

---

## Worker volume inheritance

Every cron job container a worker launches automatically has access to
that worker's own mounted volumes — including its shared identity/
credential directory — via Docker's `volumes_from`, referencing the
worker's own container (`worker_<device_group>`). This is unconditional:
no `volumes_from` field on the cron job's own `config`, no admin action,
nothing in the UI. It's why [gustavo-worker-cron](../ui/worker-maintenance.md)
is deployable as a Nebula cron job at all, not just via host crontab.

Regular apps do **not** get this — only cron jobs. If a cron job's own
`volumes` entries target a different container path, both mounts coexist
fine; a `volumes` entry that also targets the worker's own mount path
overrides the inherited one for that path.
