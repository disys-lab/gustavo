# Quickstart — Docker (Recommended)

Running Gustavo as a Docker container is the recommended approach. You get a self-contained image with the Next.js UI, FastAPI backend, and all Python dependencies pre-installed. No virtualenv management, no Node.js setup, no system-level dependencies.

!!! tip "Recommended"
    Use Docker for any deployment — development, staging, or production. The native installation path is intended for contributors or environments where Docker is not available.

---

## Try it now

Two commands, no setup, no existing Nebula platform required — this brings up just the Gustavo container itself, with login disabled, so you can look around the dashboard immediately:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/disys-lab/gustavo/main/sample_config_files/docker-compose.quickstart.yml
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000). The first load may take a few seconds while FastAPI completes its health check.

At this point Gustavo is running against its own built-in defaults — nothing is actually connected to a real Registry, Redis, MongoDB, or Nebula Manager yet. To point it at (or bring up) a real platform, continue with the full setup below; the same container keeps running the whole time, so nothing from this step needs to be redone.

---

## Full setup

The rest of this page walks through the complete picture: persisting configuration across restarts, connecting to (or launching) real platform services, and enabling authentication. If you followed "Try it now" above, this replaces that trial compose file with a more complete one — stop the trial container first (`docker compose down`).

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
      AUTH_ENABLED: "true"            # Login is Nebula-backed and works immediately —
                                       # default admin credential is nebula:nebula.
                                       # Set to "false" to skip login entirely (local/dev only).
      # NEBULA_USERNAME: "nebula"     # Override the admin login for anything beyond a quick trial
      # NEBULA_PASSWORD: "nebula"
      # GUSTAVO_SESSION_SECRET: ""    # Pin this in production — see Deployment
      # Optional SSO bridge, hidden from the login page unless set:
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
git clone https://github.com/disys-lab/gustavo.git
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
