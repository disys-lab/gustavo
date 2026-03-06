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

### With authentication

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
      FIREBASE_API_KEY: AIzaSy...
      AUTH_ENDPOINT: https://your-auth-endpoint.example.com
    restart: unless-stopped
```

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
