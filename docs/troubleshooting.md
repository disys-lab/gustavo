# Troubleshooting

## GUSTAVO_CONFIG_FILE not defined

**Error:** `GUSTAVO_CONFIG_FILE environment variable is not defined`

**Cause:** The CLI requires `GUSTAVO_CONFIG_FILE` to point to a valid env file.

**Fix:**

```bash
export GUSTAVO_CONFIG_FILE=/path/to/manager.env
```

Verify the file exists and contains at least `MANAGER_HOST` and `MANAGER_PORT`.

---

## Container name conflict

**Error:** `docker: Error response from daemon: Conflict. The container name "/redis" is already in use.`

**Cause:** A container with that name already exists (possibly stopped).

**Fix:**

```bash
docker rm redis      # or: docker rm mongo, registry, etc.
```

Or use `gustavo manager remove redis` via the CLI, or the **Remove** button in the Dashboard.

---

## Port already in use

**Error:** `bind: address already in use`

**Cause:** Another process is bound to the same port.

**Fix:**

```bash
# Find what's using the port (e.g., 5001)
lsof -i :5001

# Kill the process or stop the conflicting container
docker stop <container_name>
```

---

## Settings save times out (30 s)

**Cause:** Next.js cannot reach FastAPI at `http://127.0.0.1:8000`. This typically happens because the `FASTAPI_URL` environment variable is set to `localhost`, which resolves to IPv6 `::1` in Ubuntu 24.04 — but FastAPI listens on IPv4 only.

**Fix:** Ensure `FASTAPI_URL=http://127.0.0.1:8000` (not `localhost`).

Verify FastAPI is running inside the container:

```bash
docker exec gustavo curl -s http://127.0.0.1:8000/health
# Expected: {"status":"ok"}
```

---

## Redis connectivity error after changing IP

**Error:** `getVitals failed: Error 111 connecting to 172.x.x.x:6379. Connection refused.`

**Cause:** In Docker bridge mode, container IPs are dynamic and change when containers restart. The old IP stored in config is no longer valid.

**Fix:** Use container names instead of IPs. With a named Docker network:

```yaml
services:
  redis:
    networks: [nebula]
  gustavo:
    networks: [nebula]
networks:
  nebula:
```

Then set `REDIS_HOST: redis` in Settings. After saving, the monitoring stream picks up the new address within ~10 seconds — no restart required.

---

## Login page shows broken image

**Cause:** Middleware was intercepting static asset requests (`.png`, `.jpg`, etc.) and redirecting unauthenticated requests to `/login`, causing images to receive a redirect response instead of the file.

**Fix:** Update to the latest image which excludes file-extension paths from the auth middleware matcher:

```bash
docker compose pull && docker compose up -d
```

---

## Repeated 401 errors in logs

**Cause:** `AUTH_ENABLED=true` but `FIREBASE_API_KEY` or `AUTH_ENDPOINT` are not set, or the client's auth token has not been acquired yet.

**Check:**

```bash
docker inspect gustavo --format '{{range .Config.Env}}{{println .}}{{end}}' | grep AUTH
```

If `AUTH_ENABLED=false` is intended, verify the runtime env var is correct (the build-time `NEXT_PUBLIC_AUTH_ENABLED` build arg is separate and does not affect runtime behaviour).

---

## Monitoring shows no data / "No vitals available"

**Causes and fixes:**

1. **Redis not running** — check Dashboard → Platform Services → Redis shows `Up`
2. **No workers running** — run `gustavo cache hosts` to verify worker nodes are reporting
3. **CACHE_EXPIRE_TIME too low** — data may expire before it is read; increase to `120` or higher
4. **Wrong Redis IP** — see Redis connectivity error above

---

## "No space left on device" during Docker build

**Fix:**

```bash
docker system prune -a --volumes
```

!!! warning
    This removes all unused images, containers, volumes, and build cache. Run `docker images` and `docker ps -a` first to identify what you want to keep.

---

## podman users

If using Podman instead of Docker, authenticate first:

```bash
podman login docker.io
```

Before launching any services with Gustavo.
