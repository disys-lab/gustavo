# Services API

Manage the lifecycle of the five core platform services: **redis**, **mongo**, **registry**, **syncer**, and **manager**.

::: gustavo.api.routers.services

---

## Valid service names

| Name | Description |
|------|-------------|
| `redis` | Redis in-memory data store (worker metric cache) |
| `mongo` | MongoDB (Nebula state database) |
| `registry` | Local Docker image registry |
| `syncer` | DREGSY image syncer |
| `manager` | Nebula Manager API |
| `all` | All five services (for `run` endpoint only) |

---

## Endpoints

### `GET /api/services`

Return the status of all five services in a single response.

**Response:**

```json
{
  "error": false,
  "response": {
    "redis":    { "error": false, "response": "running" },
    "mongo":    { "error": false, "response": "running" },
    "registry": { "error": false, "response": "running" },
    "syncer":   { "error": true,  "response": "not found" },
    "manager":  { "error": false, "response": "running" }
  }
}
```

Each entry has `error: false` when the service is up and `error: true` when it is not running or not found.

---

### `GET /api/services/{svc}/status`

Check the status of a single service.

```
GET /api/services/redis/status
```

**Response:**

```json
{ "error": false, "response": "running" }
```

---

### `POST /api/services/{svc}/run`

Launch a service in the background. Returns a `job_id` immediately.

```
POST /api/services/redis/run
```

**Response:**

```json
{ "error": false, "response": { "job_id": "550e8400-e29b-41d4-a716-446655440000" } }
```

Poll `GET /api/services/jobs/{job_id}` until `status` is `done` or `error`.

---

### `POST /api/services/{svc}/action`

Perform a lifecycle action on a running service.

```
POST /api/services/redis/action
```

**Request body:**

```json
{ "action": "restart" }
```

Valid actions: `stop`, `start`, `kill`, `remove`, `restart`

**Response:**

```json
{ "error": false, "response": "redis restarted" }
```

---

### `GET /api/services/jobs/{job_id}`

Poll the result of a background service launch.

**Response while running:**

```json
{
  "id": "550e8400-...",
  "status": "running",
  "result": null,
  "error": null
}
```

**Response on completion:**

```json
{
  "id": "550e8400-...",
  "status": "done",
  "result": { "error": false, "response": "redis started successfully" },
  "error": null
}
```

---

## Background job system

::: gustavo.api.background
    options:
      members:
        - create_job
        - complete_job
        - fail_job
        - get_job
        - run_in_background
