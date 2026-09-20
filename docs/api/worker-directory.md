# Worker Directory API

Proxies onto [gustavo-reporter](../configuration.md#reporter)'s own worker
identity directory. Gustavo holds no direct Redis connection for this
data — every call here is a synchronous HTTP round-trip to Reporter's
`/api/directory/...` endpoints, authenticated with the caller's own
Nebula credential (the same one used for every other write in Gustavo).

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

Issues one HTTP call to Reporter per visible device group — Reporter
has no "all groups at once" endpoint, since its own authorization is
per-device-group. A device group Reporter itself rejects (e.g. a stale
grant) is silently skipped rather than failing the whole request.

---

### `DELETE /api/worker-directory/{device_group}/{node_id}`

Remove one worker's entry.

**Response:**

```json
{ "error": false, "response": "deleted" }
```

`rw` required on `device_group` — not admin-only. Returns `403` if the
caller isn't admin and doesn't hold `rw` on that group.
