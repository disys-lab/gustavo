# Quickstart — Docker (Recommended)

Running Gustavo as a Docker container is the recommended approach. You get a self-contained image with the Next.js UI, FastAPI backend, and all Python dependencies pre-installed. No virtualenv management, no Node.js setup, no system-level dependencies.

!!! tip "Recommended"
    Use Docker for any deployment — development, staging, or production. The native installation path is intended for contributors or environments where Docker is not available.

---

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose v2 (`docker compose` command)
- A running [Nebula Manager](https://nebula-orchestrator.github.io/) with accessible API

---

## Step 1 — Create the configuration directory

Gustavo persists its platform configuration to a YAML file mounted from the host:

```bash
mkdir -p ./config
```

Optionally pre-seed it with a `platform.yaml`:

```yaml
# config/platform.yaml
MANAGER_HOST: 192.168.1.100
MANAGER_PORT: "80"
REGISTRY_HOST: 192.168.1.100
REGISTRY_PORT: "5001"
REDIS_HOST: 192.168.1.100
REDIS_PORT: "6379"
REDIS_AUTH_TOKEN: your-redis-token
MONGO_HOST: 192.168.1.100
MONGO_PORT: "27017"
MONGO_USERNAME: nebula
MONGO_PASSWORD: nebula
NEBULA_USERNAME: nebula
NEBULA_PASSWORD: nebula
NEBULA_AUTH_TOKEN: bmVidWxhOm5lYnVsYQ==
NEBULA_PROTOCOL: http
```

If the file doesn't exist, Gustavo creates it on first save from the Settings page.

---

## Step 2 — Create `docker-compose.yml`

```yaml
services:
  gustavo:
    image: ghcr.io/disys-lab/gustavo:latest
    container_name: gustavo
    platform: linux/amd64
    ports:
      - "3000:3000"
    volumes:
      - ./config:/etc/gustavo        # Platform config persistence
      - /var/run/docker.sock:/var/run/docker.sock  # Docker management
      - /tmp/:/tmp/                   # Backup scratch space
    environment:
      PYTHONWARNINGS: "ignore"
      GUSTAVO_API_CONFIG: /etc/gustavo/platform.yaml
      AUTH_ENABLED: "false"           # Set to "true" to enable login
      # Required only when AUTH_ENABLED=true:
      # AUTH_ENDPOINT: "https://your-auth-endpoint.example.com"
      # FIREBASE_API_KEY: "your-firebase-web-api-key"
      # CUSTOM_TOKEN_URL: "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
    restart: unless-stopped
```

!!! tip "Worker deployment"
    For deploying and removing worker nodes via Docker Compose, see the [full example in Deployment](deployment.md#full-example).

---

## Step 3 — Start Gustavo

```bash
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

The first load may take a few seconds while FastAPI completes its health check.

---

## Step 4 — Configure the platform

Navigate to **Settings** (gear icon in the sidebar) and fill in the connection details for your Nebula platform:

| Section | Fields |
|---------|--------|
| Manager | Host, port, network mode, image |
| Registry | Host, port, image, backup directory |
| Redis | Host, port, auth token, image |
| MongoDB | Host, port, username, password, image |
| Syncer | Image, network mode, DREGSY config paths |

Click **Save Settings**. The values are written to `/etc/gustavo/platform.yaml` on the volume and take effect immediately.

---

## Step 5 — Launch platform services

Go to the **Dashboard** and expand **Manage Platform Services**. Click **Launch** next to each service in order:

1. Registry
2. Redis
3. MongoDB
4. Manager

Each launch runs in the background; a spinner shows while the job is pending. The status pill turns green when the service is up.

---

## Authentication (optional)

To require login before accessing Gustavo, see [Deployment — With authentication](deployment.md#with-authentication) for the full docker-compose snippet and explanation.

---

## Building the image locally

If you want to build from source rather than pulling from the registry:

```bash
# Clone the repo
git clone https://github.com/paritoshpr/gustavo.git
cd gustavo

# Build
docker build -t gustavo:local .

# Run
docker compose up -d
```

For available build arguments see [Deployment — Build arguments](deployment.md#build-arguments).

---

## Updating

```bash
docker compose pull
docker compose up -d
```

Configuration in `./config/platform.yaml` is preserved across updates.

---

## Stopping and removing

```bash
# Stop (preserves config volume)
docker compose down

# Stop and remove everything including the config volume
docker compose down -v
```
