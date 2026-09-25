# Scarlet Distributed CSV Average — One-Time Example

This example shows how to deploy a simple distributed averaging application with **Gustavo + Scarlet + Redis**. It is written for a first-time Gustavo user.

Each physical device runs a Gustavo worker. Gustavo deploys the same Scarlet averaging container to the selected device groups. Each container reads a local `input.csv`, publishes its array to a shared Scarlet `Mapper` backed by Redis, discovers the other active nodes, waits until membership is stable, and calculates the average once.

> **Important behavior:** this version reads `input.csv` once when the container starts and calculates the distributed average once. If the CSV changes later, or if a new node joins after the calculation has finished, restart the averaging containers to start a new round.

## 1. Deployment architecture

Use two Gustavo device groups:

```text
Gustavo
├── scarlet-head-dg
│   └── Head Device
│       ├── Gustavo worker
│       ├── Redis
│       └── Scarlet CSV average app
│
└── scarlet-worker-dg
    ├── Worker Device B
    │   ├── Gustavo worker
    │   └── Scarlet CSV average app
    ├── Worker Device C
    │   ├── Gustavo worker
    │   └── Scarlet CSV average app
    └── Worker Device D ...
```

The head device hosts Redis and also participates in the average. Worker devices run the same averaging image and connect to Redis on the head device.

The application creates a persistent local Scarlet node ID at:

```text
/data/.scarlet_node_id
```

Because `/data` is a host-mounted folder, the ID survives container recreation.

## 2. Prerequisites

On every physical device:

- Install Docker or Docker Desktop.
- Make sure the device can reach the Gustavo/Nebula Manager.
- Make sure worker devices can reach the head device on Redis port `6379`.
- Clone this repository.
- Give each device its own local `input.csv`.

On Windows, Gustavo's Windows worker launcher requires WSL2, Docker Desktop using the WSL2 backend, and WSL integration enabled.

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY>
```

## 3. Suggested repository layout

```text
scarlet_csv_avg/
├── scarlet_average.py
├── Dockerfile
├── .dockerignore 
├── scarlet_data/
│   └── input.csv
├── README_avg.md
└── .gitignore
```

Inside the `scarlet_csv_avg/scarlet_data/` directory, input.csv file contains sample data for the distributed averaging.

Example local values:

Device A:

```text
1,2,3
```

Device B:

```text
4,5,6
```

Device C:

```text
7,8,9
```

Do not commit or copy `.scarlet_node_id` between devices.

## 4. Docker image

Create `Dockerfile`:

```dockerfile
FROM ghcr.io/disys-lab/scarlet-agent-base:latest

WORKDIR /app

COPY scarlet_average.py /app/scarlet_average.py

ENTRYPOINT []

CMD ["python", "-u", "/app/scarlet_average.py"]
```

Build and push a multi-architecture image:

```powershell
docker buildx build `
  --platform linux/amd64,linux/arm64 `
  --no-cache `
  -f .\Dockerfile `
  -t docker.io/<DOCKERHUB_USER>/scarlet-csv-average:<VERSION NAME> `
  --push .
```

Verify:

```powershell
docker buildx imagetools inspect `
  docker.io/<DOCKERHUB_USER>/scarlet-csv-average:<VERSION NAME>
```

You should see both `linux/amd64` and `linux/arm64`.

## 5. Create the Gustavo device groups

In the Gustavo web UI, go to:

```text
Device Groups → New Group
```

Create:

```text
scarlet-head-dg
scarlet-worker-dg
```

Use `scarlet-head-dg` for the head machine and `scarlet-worker-dg` for all additional worker machines.

An app assigned to a Gustavo device group is pulled and run by every worker registered to that group.

## 6. Create and deploy the head worker

Open:

```text
Device Groups → scarlet-head-dg
```

Use **Get worker config**. Gustavo can generate:

- a native `worker.env`,
- a Docker Compose file,
- a macOS/Linux launcher,
- a Windows `.bat` launcher.

Run the generated worker configuration on the head machine.
```powershell
docker compose -f <GUSTAVO_WORKER_CONFIG_FILE>.yml up -d
```

Verify:

```powershell
docker ps
```

You should see a Gustavo worker similar to:

```text
worker_scarlet-head-dg
```

## 7. Create and deploy worker agents

Open:

```text
Device Groups → scarlet-worker-dg
```

Generate the worker configuration or launcher for that group and run it independently on each worker device.

Run the generated worker configuration on each worker device.

```powershell
docker compose -f <GUSTAVO_WORKER_CONFIG_FILE>.yml up -d
```

Verify on each device:

```powershell
docker ps
```

You should see:

```text
worker_scarlet-worker-dg
```

Each Gustavo worker maintains its own local identity. Do not copy the `.gustavo-worker` directory from one physical device to another.

## 8. Create the Redis app in Gustavo

Redis runs only on the head device.

Go to:

```text
Apps → New App
```

Configure:

| Setting | Value |
|---|---|
| App Name | `scarlet-redis` |
| Docker Image | `redis:7.4-alpine` |
| Running | On |
| Privileged | Off |
| Device Group | `scarlet-head-dg` |
| Network | bridge/default |

### Environment variables

```text
APP_ID = scarlet-redis
```
### Port mapping

```text
HOST PORT      CONTAINER PORT
6379           6379
```

This publishes Redis so the other physical machines can reach it.

### Volume mapping

No Redis volume is required for this basic experiment.

### Container command

Gustavo expects one command argument per row:

```text
redis-server
--requirepass
<REDIS_PASSWORD>
```

Save the app and allow the head worker to deploy it.

Verify on the head device:

```powershell
docker ps
```

You should see a Redis mapping similar to:

```text
0.0.0.0:6379->6379/tcp
```

Test locally:

```powershell
Test-NetConnection 127.0.0.1 -Port 6379
```

Test from a worker device:

```powershell
Test-NetConnection <HEAD_DEVICE_IP> -Port 6379
```

`TcpTestSucceeded` should be `True`.

## 9. Create the one-time averaging app in Gustavo

Go to:

```text
Apps → New App
```

Configure:

| Setting | Value |
|---|---|
| App Name | `scarlet-csv-average` |
| Docker Image | `docker.io/<DOCKERHUB_USER>/scarlet-csv-average:v1` |
| Running | On |
| Privileged | Off |
| Networks | `host` |
| Device Groups | `scarlet-head-dg`, `scarlet-worker-dg` |

### Environment variables

```text
REDIS_DB_HOST=<HEAD_DEVICE_IP>
REDIS_DB_PORT=6379
REDIS_DB_PWD=<REDIS_PASSWORD>

CSV_FILE=/data/input.csv
SCARLET_NAME=scarlet_csv_avg_once_v1

MIN_NODES=2
HEARTBEAT_SECONDS=2
NODE_TTL_SECONDS=10
DISCOVERY_STABLE_SECONDS=15
```

`MIN_NODES=2` is only the minimum number required before calculation is allowed. It is not the final node count.

Do not manually add:

```text
EXPECTED_NODES
NODE_ADDRESS
MANAGER_HOST
MANAGER_PORT
KEYGEN_PUBLIC_KEY
SLEEP_SECS
```

The Python application creates its own persistent `NODE_ADDRESS` before Scarlet initializes.

### Port mapping

Leave **Ports empty**. The averaging app makes an outbound connection to Redis and does not expose an inbound application port.

### Volume mapping

Mount the local sample-data directory to `/data`.

Windows example:

```text
HOST PATH
/run/desktop/mnt/host/c/gustavo/examples/scarlet-worker-average/static-worker-average/scarlet_csv_avg/scarlet_data

CONTAINER PATH
/data
```

Linux/macOS: use the corresponding absolute host path.

The container reads:

```text
/data/input.csv
```

and creates:

```text
/data/.scarlet_node_id
```

### Container command

Leave **Container Command empty**.

The image already contains:

```dockerfile
CMD ["python", "-u", "/app/scarlet_average.py"]
```

A command entered in Gustavo overrides the Docker image command, so do not add one unless intentionally overriding the image.

Save the app.

## 10. Verify the averaging deployment

On each participating device:

```powershell
docker ps
```

Then inspect the averaging container log. The generated container name may vary:

```powershell
docker logs -f <averaging-container-name>
```

Typical output:

```text
SCARLET DISTRIBUTED CSV AVERAGE - ONE-TIME VERSION
Node ID      : node-...
CSV file     : /data/input.csv
Local array  : [...]
Scarlet name : scarlet_csv_avg_once_v1
```

Then:

```text
Active nodes (1): [...]
Waiting for at least 2 nodes...
```

After another worker joins:

```text
Active nodes (2): [...]
Membership changed. Restarting stability timer.
```

After membership remains unchanged for the configured stability interval:

```text
ACTIVE PARTICIPANTS = 2
node-...: [...]
node-...: [...]
AVERAGE = [...]
```

## 11. Add another physical worker

To add Device D:

1. Install Docker/Docker Desktop.
2. Clone the repository.
3. Give Device D its own `scarlet_data/input.csv`.
4. Obtain/run the worker configuration for `scarlet-worker-dg`.
5. Wait for Gustavo to deploy the assigned app.

No new Docker image is required.

Because this version calculates only once, if the existing nodes already completed their calculation, restart the averaging containers to run a new round including Device D.

## 12. Change CSV data

This version reads `input.csv` only when the container starts.

If you edit the file after startup, restart the averaging container before the next calculation.

For automatic live updates, use `README_avg_continuous.md` and the continuous image.


## 14. Security and `.gitignore`

Never commit:

- Redis passwords,
- Gustavo/Nebula passwords or tokens,
- downloaded worker configuration,
- `gustavo_config/`,
- `.gustavo-worker/`,
- `.scarlet_node_id`.

Recommended entries:

```gitignore
gustavo_config/
scarlet_data/.scarlet_node_id
__pycache__/
*.pyc
```

The `scarlet_data/` directory can remain tracked if it contains only safe sample data.

## 15. Troubleshooting

### Only one Scarlet node appears

Confirm all machines:

- use the same `SCARLET_NAME`,
- point to the same Redis host,
- can reach `<HEAD_DEVICE_IP>:6379`,
- have a writable `/data` mount,
- have different `.scarlet_node_id` files.

### Two machines have the same Scarlet node ID

Delete `.scarlet_node_id` on one machine and restart its averaging container. Never distribute that generated file.

### Redis cannot be reached

From a worker:

```powershell
Test-NetConnection <HEAD_DEVICE_IP> -Port 6379
```

If it fails, check Redis is running, `6379:6379` is published, the firewall permits the connection, and `REDIS_DB_HOST` is the reachable head-device address.

### `SCARLET_CONFIG_FILE not specified`

This example uses environment variables supplied by Gustavo. The application code filters this harmless warning.

### `MAINT_NOTIFICATIONS` debug message

This is Redis-client debug noise and is filtered by the example logging configuration.

## 16. Final deployment summary

```text
Head Device
├── Gustavo worker → scarlet-head-dg
├── Redis → 6379:6379
└── Scarlet average app
    └── local scarlet_data → /data

Worker Device B/C/D/...
├── Gustavo worker → scarlet-worker-dg
└── Scarlet average app
    └── local scarlet_data → /data
```

All averaging containers communicate through the shared Redis instance on the head device.
