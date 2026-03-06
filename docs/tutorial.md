# End-to-End Tutorial

This tutorial walks through the complete workflow — from a fresh Gustavo install to a running application on edge devices. It assumes Gustavo is already up (via Docker or natively). If not, start with the [Quickstart](quickstart.md).

---

## What you will build

```
Manager node                    Edge devices
─────────────────               ─────────────────────
Registry  ←── syncs images ──   Worker (reports metrics)
Redis                           Worker (runs app containers)
MongoDB
Nebula Manager ──── manages ──▶ Device Group: "production"
                                  └── App: "my-app"
```

---

## Step 1 — Bring up platform services

From the **Dashboard**, expand **Manage Platform Services** and launch each service in order:

1. **Registry** — local Docker image store
2. **Redis** — metric cache and worker heartbeat
3. **MongoDB** — Nebula application state
4. **Manager** — Nebula orchestration API

Wait for each status pill to turn green before starting the next.

**Or via CLI:**

```bash
gustavo manager up registry
gustavo manager up redis
gustavo manager up mongo
gustavo manager up manager
```

Verify:

```bash
gustavo manager check
```

---

## Step 2 — Configure platform settings

Go to **Settings** and fill in the connection details for your infrastructure. At minimum:

| Section | Fields to set |
|---------|--------------|
| Manager | Host, Port |
| Registry | Host, Port |
| Redis | Host, Port, Auth Token |
| MongoDB | Host, Port, Username, Password |

Click **Save Settings**. Use the **Apply to all** button to copy the Manager host to Redis, MongoDB, and Registry if they all run on the same machine.

---

## Step 3 — Push an image to the local registry

Your application image must be present in the local registry before you can deploy it. Push it from the manager node:

```bash
docker tag myorg/my-app:latest REGISTRY_HOST:REGISTRY_PORT/my-app
docker push REGISTRY_HOST:REGISTRY_PORT/my-app
```

Verify it arrived:

```bash
gustavo registry list
```

You should see `my-app` in the output.

---

## Step 4 — Create the application

### Via the web UI

Go to **Apps → New App** and fill in:

- **Name:** `my-app`
- **Image:** `REGISTRY_HOST:REGISTRY_PORT/my-app` (no tag)
- **Environment Variables:** add any config your app needs
- **Ports / Volumes:** as required

Click **Create App**.

### Via CLI

Create `my-app.yaml`:

```yaml
my-app:
  docker_image: "REGISTRY_HOST:REGISTRY_PORT/my-app"
  env_vars:
    APP_ID: my-app
    REDIS_DB_HOST: REDIS_HOST
    REDIS_DB_PORT: "6379"
    REDIS_DB_PWD: your-redis-token
    MANAGER_HOST: MANAGER_HOST
    MANAGER_PORT: "80"
    NEBULA_AUTH_TOKEN: bmVidWxhOm5lYnVsYQ==
  running: true
  networks:
    - nebula
  rolling_restart: true
  containers_per:
    server: 1
  privileged: false
  devices: []
```

```bash
gustavo apps create -n my-app -f my-app.yaml
```

---

## Step 5 — Set up worker nodes

On **each edge device**, follow the [Worker Node Setup](cli/index.md#worker-node-setup) to install Docker, create `worker.env`, and start the worker:

```bash
export GUSTAVO_CONFIG_FILE=/path/to/worker.env
gustavo worker up
```

Confirm the worker is registered:

```bash
# From the manager node
gustavo cache hosts
```

You should see the worker's device group and host ID in the output.

---

## Step 6 — Create a device group and assign the app

### Via the web UI

Go to **Device Groups → New Group**:

- **Name:** `production`
- **Apps:** select `my-app`

Click **Create**.

### Via CLI

```bash
gustavo device-group create -n production -a my-app
```

Nebula will immediately push `my-app` to all workers in the `production` group.

---

## Step 7 — Verify the app is running

On any worker node:

```bash
docker ps
```

You should see a running container for `my-app`.

From the manager node, check container status across all workers:

```bash
gustavo cache containers
```

Or open the **Monitoring** page in the web UI — you should see CPU, memory, and disk metrics flowing within `CACHE_EXPIRE_TIME` seconds.

---

## Step 8 — Update the app

Edit `my-app.yaml` (e.g. change an env var or switch the image) and apply:

```bash
gustavo apps update -n my-app -f my-app.yaml
```

With `rolling_restart: true`, Nebula rolls the update across devices without downtime.

---

## Step 9 — Clean up

```bash
# Remove the app from all device groups and delete it
gustavo apps delete -n my-app

# Remove a worker node
gustavo worker remove   # run on the worker node

# Tear down platform services (run on manager node)
gustavo manager remove
```

---

## Next steps

- [Configuration Reference](configuration.md) — tune Redis expiry, network modes, and image versions
- [Backups](ui/backups.md) — set up Redis and registry backups before going to production
- [Authentication](api/auth.md) — enable Firebase login if the dashboard is externally accessible
