# Deployment

## Single-container model

Gustavo runs as a **single Docker container** combining the Next.js frontend and FastAPI backend. Supervisor manages both processes:

```
Container (port 3000 exposed)
├── supervisord
│   ├── gustavo-api  →  uvicorn on 127.0.0.1:8000 (loopback only)
│   └── gustavo-ui   →  Node.js standalone on 0.0.0.0:3000
└── /etc/gustavo/platform.yaml  (mounted volume)
```

The browser communicates only with port 3000. Next.js rewrites `/api/*` to `http://127.0.0.1:8000/api/*` — FastAPI is never directly reachable from outside the container.

---

## Docker Compose

### Full example

The compose file below shows all three common service patterns: the Gustavo UI, deploying a worker, and removing a worker. Copy this as your starting point and fill in the placeholder values.

```yaml
services:

  # ─── Gustavo UI + API ────────────────────────────────────────────────────────
  gustavo:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo
    platform: linux/amd64
    # network_mode: "host"   # Uncomment if managed services run on the host network
    ports:
      - "3000:3000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/:/tmp/
      - ./config:/etc/gustavo          # Platform config persistence
    environment:
      PYTHONWARNINGS: "ignore"
      GUSTAVO_API_CONFIG: /etc/gustavo/platform.yaml
      AUTH_ENABLED: "false"            # Set to "true" to require login
      # Required when AUTH_ENABLED=true:
      # AUTH_ENDPOINT: "https://your-auth-endpoint.example.com"
      # FIREBASE_API_KEY: "your-firebase-web-api-key"
      # CUSTOM_TOKEN_URL: "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
    restart: unless-stopped

  # ─── Deploy a worker node ────────────────────────────────────────────────────
  # Run once with: docker compose run --rm gustavo-worker-up
  gustavo-worker-up:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo_worker-up
    network_mode: "host"
    platform: linux/amd64
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./worker/config.env:/home/worker.env   # Worker config env file
    environment:
      PYTHONWARNINGS: "ignore"
      GUSTAVO_CONFIG_FILE: "/home/worker.env"
    command: ["gustavo", "worker", "up", "-i", "ghcr.io/disys-lab/gustavo-worker:latest", "-d", "your-device-group"]
    profiles: [worker]   # Only starts when explicitly included

  # ─── Remove a worker node ────────────────────────────────────────────────────
  # Run once with: docker compose run --rm gustavo-worker-remove
  gustavo-worker-remove:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo_worker-remove
    network_mode: "host"
    platform: linux/amd64
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./worker/config.env:/home/worker.env
    environment:
      PYTHONWARNINGS: "ignore"
      GUSTAVO_CONFIG_FILE: "/home/worker.env"
    command: ["gustavo", "worker", "remove", "-n", "worker_your-device-group"]
    profiles: [worker]
```

### Minimal setup (UI only)

```yaml
services:
  gustavo:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo
    platform: linux/amd64
    ports:
      - "3000:3000"
    volumes:
      - ./config:/etc/gustavo
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp:/tmp
    environment:
      GUSTAVO_API_CONFIG: /etc/gustavo/platform.yaml
      AUTH_ENABLED: "false"
    restart: unless-stopped
```

### Production (pinned admin credentials + session secret)

`AUTH_ENABLED=true` gates the UI behind login, backed by Nebula's own user
API (see [Authentication](api/auth.md)). At minimum, override the
break-glass admin credential and pin a session secret so sessions survive a
container restart:

```yaml
services:
  gustavo:
    image: ghcr.io/disys-lab/gustavo:0.4.0b16
    container_name: gustavo
    ports:
      - "3000:3000"
    volumes:
      - ./config:/etc/gustavo
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp:/tmp
    environment:
      GUSTAVO_API_CONFIG: /etc/gustavo/platform.yaml
      AUTH_ENABLED: "true"
      NEBULA_USERNAME: your-admin-username
      NEBULA_PASSWORD: your-admin-password
      GUSTAVO_SESSION_SECRET: your-random-secret   # e.g. `openssl rand -hex 32`
      # Optional SSO bridge — hidden from the login page unless set:
      # FIREBASE_API_KEY: AIzaSy...
      # AUTH_ENDPOINT: https://your-auth-endpoint.example.com
    restart: unless-stopped
```

!!! warning "Don't skip GUSTAVO_SESSION_SECRET in production"
    If unset, a random secret is generated each time the container starts,
    which invalidates every active session on every restart/redeploy. Fine
    for local development, not for anything users depend on staying logged
    into.

---

## Network modes

### Bridge mode (default, recommended)

The container joins Docker's default bridge network. Use container names for service addresses when other services are also containerised on the same host.

```bash
docker compose up -d
```

Access Gustavo at `http://<host-ip>:3000`.

### Host mode

In host mode the container shares the host's network namespace. FastAPI on `127.0.0.1:8000` is accessible from the host machine but not from outside.

```yaml
services:
  gustavo:
    network_mode: host
```

!!! note
    In host mode, set `REDIS_HOST`, `MONGO_HOST`, etc. to `127.0.0.1` if those services are running directly on the host.

---

## Volume mounts

| Mount | Purpose |
|-------|---------|
| `./config:/etc/gustavo` | Persists `platform.yaml` across container restarts |
| `/var/run/docker.sock:/var/run/docker.sock` | Required for `Manager` and backup handlers to control Docker |
| `/tmp:/tmp` | Backup scratch space for Redis RDB files and registry tarballs |

---

## Build arguments

```bash
docker build \
  --build-arg gustavo_version=0.4.0-beta.3 \
  --build-arg py_version=3.11 \
  --build-arg node_version=20 \
  --build-arg NEXT_PUBLIC_AUTH_ENABLED=false \
  -t gustavo:local .
```

!!! warning "NEXT_PUBLIC_AUTH_ENABLED is baked at build time"
    This build argument is embedded into the Next.js JS bundle during `npm run build`. For runtime auth control, use the `AUTH_ENABLED` environment variable instead. The middleware and AuthContext both read `AUTH_ENABLED` at runtime.

---

## CI/CD build tags

The GitHub Actions workflows use commit message tags to trigger builds:

| Tag | Effect |
|-----|--------|
| `#dockerbuild` | Build and push Docker image |
| `#macbuild` | Build macOS binary |
| `#linuxbuild` | Build Linux binary |
| `#bump` | Increment version |
| `#patch` / `#minor` / `#major` | Version bump level |

---

## Ports summary

| Port | Service | Bound to |
|------|---------|----------|
| 3000 | Next.js frontend | `0.0.0.0` (all interfaces) |
| 8000 | FastAPI backend | `127.0.0.1` (loopback only) |

---

## Log access

```bash
# All logs (supervisord, FastAPI, Next.js)
docker logs gustavo

# Follow
docker logs -f gustavo
```

Individual service logs within the container are written to stdout by supervisord.

---

## Health check

```bash
# From outside the container
curl http://localhost:3000/api/health

# From inside the container
docker exec gustavo curl -s http://127.0.0.1:8000/health
```

Expected response: `{"status":"ok"}`

---

## Registry Authentication Proxy (nginx)

### Summary

Proxy `REGISTRY_PORT` (e.g. `5001`) through nginx with Basic Auth, backed by Gustavo's Nebula users. The actual registry moves to port `5051` (localhost-only).

### Setup

1. **Configure ports** in `platform.yaml`:
   ```yaml
   REGISTRY_PORT: 5001
   REGISTRY_CONTAINER_PORT: 5051
   REGISTRY_BIND_LOCALHOST: true
   ```

2. **Lock down port `5051`** (fallback if `REGISTRY_BIND_LOCALHOST` unavailable):
   ```bash
   sudo ufw deny 5051
   ```

3. **Nginx config** (`registry-proxy/nginx.conf`):
   ```nginx
   server {
       listen REGISTRY_PORT;
       
       location /v2/_catalog { proxy_pass http://127.0.0.1:5051; }
       location ~ ^/v2/(?<repo>.+)/tags/list$ { proxy_pass http://127.0.0.1:5051; }
       
       location = /_registry_auth {
           internal;
           proxy_pass http://127.0.0.1:GUSTAVO_PORT/api/registry/authorize;
           proxy_pass_request_body off;
           proxy_set_header Content-Length "";
       }
       
       location /v2/ {
           auth_request /_registry_auth;
           add_header WWW-Authenticate 'Basic realm="Registry"' always;
           proxy_pass http://127.0.0.1:5051;
           proxy_read_timeout 900;
       }
   }
   ```

4. **Add to `docker-compose.yml`**:
   ```yaml
   registry-proxy:
     image: nginx:1.27-alpine
     network_mode: host
     volumes:
       - ./registry-proxy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
   ```

5. **Docker daemon config** (`/var/snap/docker/<revision>/config/daemon.json`):
   ```json
   {"insecure-registries": ["REGISTRY_HOST:REGISTRY_PORT"]}
   ```

### Key points

- **Auth**: Any Nebula user can pull/push (identity-only, no repo-level grants yet)
- **Open**: `/v2/_catalog` and `/v2/{repo}/tags/list` require no auth
- **Credentials**: Use existing Nebula `username:secret` (no separate registry creds)

