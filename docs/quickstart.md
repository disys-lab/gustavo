# Quickstart — Docker (Recommended)

Running Gustavo as a Docker container is the recommended approach. You get a self-contained image with the Next.js UI, FastAPI backend, and all Python dependencies pre-installed.

---

## Try it now

Two commands, no setup, no existing Nebula platform required — this brings up just the Gustavo container itself, with login disabled, so you can look around the dashboard immediately:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/disys-lab/gustavo/main/sample_config_files/docker-compose.quickstart.yml
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000). The first load may take a few seconds while FastAPI completes its health check.

---

## Prerequisites

For the full setup with a real Nebula platform:

- Docker Engine 20.10 or later
- Docker Compose v2 (`docker compose` command)
- A running [Nebula Manager](https://nebula-orchestrator.github.io/) with accessible API

---

## Bring up a worker

Once Gustavo itself is running and a device group exists, bring up a worker for it the same way — one `curl` to fetch a ready-made compose file, scoped to your own Nebula identity, then `docker compose up -d`:

```bash
curl -s -u your-username:your-nebula-secret http://<gustavo-host>:<port>/api/device-groups/<device-group>/worker-compose -o docker-compose.yml
docker compose up -d
```

To grant this worker GPU access, add `?gpu=true` to the URL — only do this on hardware that actually has a GPU `nvidia-container-toolkit` can expose:

```bash
curl -s -u your-username:your-nebula-secret "http://<gustavo-host>:<port>/api/device-groups/<device-group>/worker-compose?gpu=true" -o docker-compose.yml
docker compose up -d
```

See [gustavo worker](cli/worker.md) for the full CLI reference, and [Device Groups UI](ui/device-groups.md#get-worker-config) for the other download formats (native `.env`, launcher scripts for macOS/Linux/Windows).

---

---

## Full setup

The rest of this page walks through the complete setup. If you followed "Try it now", stop the trial container first (`docker compose down`).

## Prerequisites

For full setup with a real Nebula platform:

- Docker Engine 20.10 or later
- Docker Compose v2 (`docker compose` command)
- A running [Nebula Manager](https://nebula-orchestrator.github.io/) with accessible API

---

See [Deployment](deployment.md) for complete configuration examples, including [minimal setup](deployment.md#minimal-setup) and [production with authentication](deployment.md#production).

## Step 1 — Create the configuration directory

Gustavo persists its platform configuration to a YAML file mounted from the host:

```bash
mkdir -p ./config
```

Optionally pre-seed it with a `platform.yaml`.

## Step 2 — Create `docker-compose.yml`

See [Deployment](deployment.md#minimal-setup) for a minimal example, or [Deployment with authentication](deployment.md#production) for production-ready settings.

## Step 3 — Start Gustavo

```bash
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000).

## Authentication (optional)

To require login, see [Deployment with authentication](deployment.md#production).

---

## Next steps

- [End-to-End Tutorial](tutorial.md) — deploy apps to edge devices
- [Configuration Reference](configuration.md) — tune Redis expiry, network modes, and image versions
- [Native Installation](installation.md) — run Gustavo natively without Docker

---

## Building the image locally

If you want to build from source:

```bash
git clone https://github.com/disys-lab/gustavo.git
cd gustavo
docker build -t gustavo:local .
docker compose up -d
```

See [Build arguments](deployment.md#build-arguments) for customization options.

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
docker compose down        # Stop (preserves config volume)
docker compose down -v     # Stop and remove everything including config volume
```
