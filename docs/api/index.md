# FastAPI Backend

The Gustavo FastAPI backend exposes a REST API consumed by the Next.js frontend and optionally by external tools. It is the server-side replacement for the legacy Streamlit pages.

---

## Base URL

In production (Docker): requests come from the Next.js proxy and are received at `http://127.0.0.1:8000`.

From outside the container, all `/api/*` paths are accessible via port 3000:

```
http://localhost:3000/api/...
```

---

## Interactive docs

FastAPI generates Swagger UI and ReDoc automatically:

```
http://localhost:3000/api/docs      # Swagger UI (proxied)
http://127.0.0.1:8000/docs         # Direct (inside container)
http://127.0.0.1:8000/redoc        # ReDoc
```

---

## Response contract

All endpoints return the standard Nebula response envelope:

```json
{
  "error": false,
  "response": { ... }
}
```

On error:

```json
{
  "error": true,
  "response": "human-readable error message"
}
```

---

## Authentication

When `AUTH_ENABLED=true`, all endpoints (except `/api/auth/status` and `/api/auth/token`) require:

```
Authorization: Bearer <firebase-id-token>
```

The Next.js frontend injects this header automatically from the stored token. When `AUTH_ENABLED=false`, all routes pass through without a token.

See [Authentication](auth.md) for the full login flow.

---

## Routers

| Prefix | Module | Description |
|--------|--------|-------------|
| `/api/auth` | `routers/auth.py` | Firebase token exchange, auth status |
| `/api/config` | `routers/config.py` | Platform configuration CRUD |
| `/api/services` | `routers/services.py` | Service lifecycle (Redis, MongoDB, etc.) |
| `/api/apps` | `routers/apps.py` | Nebula application CRUD + registry |
| `/api/device-groups` | `routers/device_groups.py` | Device group management |
| `/api/monitoring` | `routers/monitoring.py` | Worker vitals, containers, SSE stream |
| `/api/backups` | `routers/backups.py` | Redis and registry backup management |
| `/health` | `main.py` | Health check (no auth) |

---

## Architecture

```python
# main.py — application factory
from gustavo.api import config_store
from gustavo.api.dependencies import _build_manager, _build_composer
from gustavo.api.cache_shim import build_cache
from gustavo.api.background import create_job, run_in_background
```

**Config singleton** (`config_store`): YAML-backed dict holding all platform parameters. Loaded at startup, updated by `POST /api/config`, read by every router.

**Dependency factories** (`dependencies.py`): `_build_manager(cfg)` and `_build_composer(cfg)` instantiate the core Python library classes from the current config dict. Called inside route handlers.

**Cache bridge** (`cache_shim.py`): `build_cache()` writes the config to `/tmp/gustavo_api.env`, sets `GUSTAVO_CONFIG_FILE`, then constructs `Cache()`. Needed because `Cache` hardcodes `mode="CLI"` and reads from an env file.

**Background jobs** (`background.py`): Long-running operations (service launch, backup restore) return a `job_id` immediately. Clients poll `GET /api/services/jobs/{job_id}` for completion.
