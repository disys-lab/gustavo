# End-to-End Tutorial

This tutorial walks through the complete workflow — from a fresh Gustavo install to a running application on edge devices. It assumes Gustavo is already up (via Docker or natively). If not, start with the [Quickstart](quickstart.md).

---

## Step 1 — Configure platform settings

Go to **Settings** and fill in the connection details for your infrastructure. At minimum:

| Section | Fields to set |
|---------|--------------|
| Manager | Host, Port |
| Registry | Host, Port |
| Redis | Host, Port, Auth Token |
| MongoDB | Host, Port, Username, Password |

Click **Save Settings**.

---

## Step 2 — Push an image to the local registry

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

## Step 3 — Create the application

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

## Step 4 — Set up worker nodes

On **each edge device**, install Docker, create `worker.env`, and start the worker:

```bash
export GUSTAVO_CONFIG_FILE=/path/to/worker.env
gustavo worker up
```

Confirm the worker is registered:

```bash
gustavo cache hosts
```

You should see the worker's device group and host ID in the output.

---

## Step 5 — Create a device group and assign the app

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

## Step 6 — Verify the app is running

On any worker node:

```bash
docker ps
```

You should see a running container for `my-app`.

From the manager node:

```bash
gustavo cache containers
```

Or open the **Monitoring** page in the web UI.

---

## Step 7 — Update the app

Edit `my-app.yaml` and apply:

```bash
gustavo apps update -n my-app -f my-app.yaml
```

With `rolling_restart: true`, Nebula rolls updates across devices without downtime.

---

## Clean up

```bash
gustavo apps delete -n my-app
gustavo worker remove
gustavo manager remove
```

---

## Next steps

- [Configuration Reference](configuration.md)
- [Backups](ui/backups.md)
- [Authentication](api/auth.md)
