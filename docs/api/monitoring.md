# Monitoring API

Real-time worker metrics via polling endpoints and a Server-Sent Events stream.

::: gustavo.api.routers.monitoring

---

## Endpoints

### `GET /api/monitoring/hosts`

Return the map of hosts and their device group memberships.

**Query params:** `device_group` (default: `all`), `host` (default: `all`)

**Response:**

```json
{
  "error": false,
  "response": {
    "192.168.1.50": ["production"],
    "192.168.1.51": ["production", "staging"]
  }
}
```

---

### `GET /api/monitoring/vitals`

Return the latest system vitals (CPU, memory, disk) from worker nodes.

**Query params:** `device_group` (default: `all`), `host` (default: `all`)

**Response:**

```json
{
  "error": false,
  "response": {
    "error": false,
    "response": "192.168.1.50@192.168.1.50 at time:1741270000\tmem:{'total':8192,'used':4096,'free':4096}\tdisk:{'total':100000,'used':50000,'free':50000}\tcpu_cores:4\tcpu_percent:23.5"
  }
}
```

The raw response string is parsed by the frontend and the SSE stream into structured metrics.

---

### `GET /api/monitoring/containers`

Return per-container CPU and memory statistics from worker nodes.

Same query params as `/vitals`.

---

### `GET /api/monitoring/stream`

**Server-Sent Events** stream emitting a monitoring snapshot every 10 seconds.

**Query params:** `device_group` (default: `all`), `host` (default: `all`)

**Event format:**

```
event: monitoring
data: {"vitals": {...}, "containers": [...]}
```

**Vitals object:**

```json
{
  "host": "192.168.1.50@192.168.1.50",
  "timestamp": 1741270000,
  "cpu_percent": 23.5,
  "cpu_cores": 4,
  "memory_mb": { "total": 8192, "used": 4096, "free": 4096 },
  "disk_mb": { "total": 100000, "used": 50000, "free": 50000 }
}
```

**Containers array:**

```json
[
  {
    "name": "test_linreg",
    "cpu_percent": 5.2,
    "memory_mb": 256.0,
    "memory_limit_mb": 2048.0,
    "memory_percent": 12.5
  }
]
```

!!! note "No auth on SSE"
    The `/stream` endpoint omits the auth dependency because browsers cannot send `Authorization` headers on `EventSource` connections. In production, the Next.js proxy layer handles authentication before forwarding SSE connections.

---

## How metrics flow

```
Worker node
  └── Reports CPU/mem/disk/containers to Redis
         (every CACHE_EXPIRE_TIME seconds)

FastAPI /api/monitoring/stream
  └── build_cache() → Cache.getAssetsForAll("vitals")
         └── Reads latest pickle from Redis per host
              └── Emits structured JSON over SSE

Next.js useMonitoringStream hook
  └── EventSource → receives SSE events
       └── Updates Dashboard vitals and MetricsChart
```
