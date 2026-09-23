# Worker Directory API

Reads the worker identity directory directly from Redis — the same
Redis, and the same `REDIS_HOST`/`REDIS_PORT`/`REDIS_AUTH_TOKEN` config,
[Monitoring](monitoring.md) already uses for cached vitals/container
reports. [gustavo-reporter](../configuration.md#reporter) is still what
*writes* this data (workers register with it, not with Gustavo), but
Gustavo no longer goes back out over HTTP to read it back — that
round trip turned out to be the actual cause of a production incident
where every directory listing re-triggered Reporter's own full
credential-verification cascade against Nebula Manager, once per
device group. Scoping to the caller's visible device groups happens
the same way it always has (`compute_permissions`/admin check) before
any Redis key is touched.

::: gustavo.api.routers.worker_directory

---

## Endpoints

### `GET /api/worker-directory`

List the worker directory across every device group the caller can see
— every group for an admin, only granted ones (`ro` or `rw`) for
anyone else.

**Response:**

```json
{
  "error": false,
  "response": [
    {
      "device_group": "production",
      "node_id": "3f9a1c2e-...",
      "host_ip": "10.0.0.5",
      "remote_ip": "203.0.113.7",
      "updated_at": 1741270000
    }
  ]
}
```

Scans Redis once per visible device group (`gustavo-directory_{device_group}@*`
keys) — a Redis error scanning any one group is logged and skipped
rather than failing the whole request.

---

### `DELETE /api/worker-directory/{device_group}/{node_id}`

Remove one worker's entry.

**Response:**

```json
{ "error": false, "response": "deleted" }
```

`rw` required on `device_group` — not admin-only. Returns `403` if the
caller isn't admin and doesn't hold `rw` on that group.
