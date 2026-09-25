# Scarlet Distributed CSV Average — Continuous Example

This example extends the basic Gustavo/Scarlet CSV averaging demo into a continuously updating distributed application.

Each physical node periodically rereads its local `input.csv`, republishes the latest array to Scarlet/Redis, discovers the currently active nodes, and recalculates the distributed average whenever membership or data changes.

> **Behavior of this version:** no averaging-container restart is required when a CSV file changes, when a new worker joins, or when a worker leaves. A departed node disappears after its Scarlet data TTL expires.

## 1. What this example demonstrates

A new worker joining:

```text
new physical worker joins scarlet-worker-dg
        ↓
Gustavo deploys the same continuous app
        ↓
new Scarlet node publishes its local data
        ↓
membership changes
        ↓
average recalculates automatically
```

A local CSV changing:

```text
input.csv changes
        ↓
application rereads it on the next heartbeat
        ↓
new data is published to Redis
        ↓
shared state changes
        ↓
average recalculates automatically
```

## 2. Deployment architecture

Use two Gustavo device groups:

```text
Gustavo
├── scarlet-head-dg
│   └── Head Device
│       ├── Gustavo worker
│       ├── Redis
│       └── Continuous Scarlet average app
│
└── scarlet-worker-dg
    ├── Worker Device B
    │   ├── Gustavo worker
    │   └── Continuous Scarlet average app
    ├── Worker Device C
    │   ├── Gustavo worker
    │   └── Continuous Scarlet average app
    └── Worker Device D ...
```

The head device runs the same continuous Python application as every worker. Its extra responsibility is hosting Redis.

## 3. Prerequisites

On every physical machine:

- Docker/Docker Desktop installed and running.
- Network access to the Gustavo/Nebula Manager.
- Network access to Redis on the head device.
- A clone of this repository.
- A local `scarlet_data/input.csv`.

On Windows, Gustavo's Windows worker launcher requires WSL2, Docker Desktop using the WSL2 backend, and WSL integration enabled.

Clone:

```bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY>
```

## 4. Suggested repository layout

```text
scarlet_csv_avg_cntns/
├── scarlet-composer-avg-cntns.py
├── Dockerfile.continuous
├── scarlet_data/
│   └── input.csv
├── README_avg_continuous.md
└── .gitignore
```

`scarlet_data/` may remain in Git as sample data.

Each machine uses its own local copy. The application creates:

```text
scarlet_data/.scarlet_node_id
```

through the `/data` bind mount. Do not commit or copy that generated file.

## 5. Docker image

Create `Dockerfile`:

```dockerfile
FROM ghcr.io/disys-lab/scarlet-agent-base:latest

WORKDIR /app

COPY scarlet_average_cntns.py /app/scarlet_average_cntns.py

ENTRYPOINT []

CMD ["python", "-u", "/app/scarlet_average_cntns.py"]
```

Build and push:

```powershell
docker buildx build `
  --platform linux/amd64,linux/arm64 `
  --no-cache `
  -f .\Dockerfile `
  -t docker.io/<DOCKERHUB_USER>/scarlet-composer-avg-cntns:v1 `
  --push .
```

Verify:

```powershell
docker buildx imagetools inspect `
  docker.io/<DOCKERHUB_USER>/scarlet-composer-avg-cntns:v1
```

Confirm `linux/amd64` and `linux/arm64` are present.

## 6. Create the Gustavo device groups

In the Gustavo UI:

```text
Device Groups → New Group
```

Create:

```text
scarlet-head-dg
scarlet-worker-dg
```

Use `scarlet-head-dg` for the machine hosting Redis and `scarlet-worker-dg` for the other participating devices.

## 7. Deploy the head worker

Open:

```text
Device Groups → scarlet-head-dg
```

Use **Get worker config**. Gustavo can generate:

- a native `worker.env`,
- Docker Compose,
- a macOS/Linux launcher,
- a Windows `.bat` launcher.

Run the selected worker configuration on the head machine.

Verify:

```powershell
docker ps
```

Look for:

```text
worker_scarlet-head-dg
```

## 8. Deploy worker agents

Open:

```text
Device Groups → scarlet-worker-dg
```

Generate a worker configuration or launcher and run it independently on each worker device.

Verify:

```powershell
docker ps
```

Look for:

```text
worker_scarlet-worker-dg
```

Do not share `.gustavo-worker` between physical machines.

When an app is assigned to a device group, every worker in that group will pull and run it on its next sync cycle.

## 9. Deploy Redis on the head device

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

## 10. Create the continuous Scarlet app in Gustavo

Go to:

```text
Apps → New App
```

Configure:

| Setting | Value |
|---|---|
| App Name | `scarlet-csv-average-cntns` |
| Docker Image | `docker.io/<DOCKERHUB_USER>/scarlet-composer-avg-cntns:v1` |
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
SCARLET_NAME=scarlet_csv_avg_cntns_v1

MIN_NODES=2
HEARTBEAT_SECONDS=2
NODE_TTL_SECONDS=10
```

Do not manually add:

```text
EXPECTED_NODES
NODE_ADDRESS
MANAGER_HOST
MANAGER_PORT
KEYGEN_PUBLIC_KEY
SLEEP_SECS
```

The application creates a persistent local node ID automatically.

### Port mapping

Leave **Ports empty**. The application does not expose an inbound service port.

### Volume mapping

Mount each machine's local `scarlet_data` directory to `/data`.

Windows example:

```text
HOST PATH
/run/desktop/mnt/host/c/gustavo/examples/scarlet_csv_avg_cntns/scarlet_data

CONTAINER PATH
/data
```

The container reads:

```text
/data/input.csv
```

and creates:

```text
/data/.scarlet_node_id
```

### Container command

Leave **Container Command empty** because the image already contains:

```dockerfile
CMD ["python", "-u", "/app/scarlet-composer-avg-cntns.py"]
```

Save the app.

## 11. Verify the deployment

On each device:

```powershell
docker ps
```

Inspect logs:

```powershell
docker logs -f <continuous-averaging-container-name>
```

Typical startup output:

```text
SCARLET DISTRIBUTED CSV AVERAGE - CONTINUOUS VERSION
Node ID       : node-...
CSV file      : /data/input.csv
Scarlet name  : scarlet_csv_avg_cntns_v1
Minimum nodes : 2
```

When enough nodes are active:

```text
MEMBERSHIP CHANGED
Active nodes (2): [...]
```

Then:

```text
DISTRIBUTED STATE UPDATED
ACTIVE NODES = 2
node-...: [...]
node-...: [...]
NEW AVERAGE = [...]
```

The application does not need to print the same average continuously when nothing changes. It recalculates when the distributed state changes.

## 12. Test a live CSV update

On one worker, edit its local:

```text
scarlet_data/input.csv
```

For example, change:

```text
4,5,6
```

to:

```text
10,20,30
```

Do not restart the container.

Within approximately the heartbeat interval, the application rereads the file, publishes the new values, and the active nodes calculate a new average.

## 13. Test a new node joining

To add Device D:

1. Install Docker/Docker Desktop.
2. Clone the repository.
3. Give Device D its own `scarlet_data/input.csv`.
4. Obtain/run the worker configuration for `scarlet-worker-dg`.
5. Wait for Gustavo to deploy the continuous app.

The existing averaging containers do not restart.

They detect the new Mapper key and should log:

```text
MEMBERSHIP CHANGED
Active nodes (4): [...]
```

followed by a new distributed average.

## 14. Test a worker leaving

Stop the continuous averaging container, or stop the Gustavo worker, on one worker device.

That node stops refreshing its Scarlet data. After `NODE_TTL_SECONDS`, its data expires. The remaining nodes then observe a membership change and calculate a new average.

With:

```text
NODE_TTL_SECONDS=10
```

allow roughly ten seconds plus the heartbeat interval for this change to become visible.

## 15. Why `MIN_NODES` is used

The application does not need `EXPECTED_NODES`.

It discovers however many nodes are currently active.

`MIN_NODES` only prevents a distributed calculation from running with too few participants.

For:

```text
MIN_NODES=2
```

behavior is:

```text
1 active node  → wait
2 active nodes → calculate
3 active nodes → calculate
4 active nodes → calculate
```

There is no configured maximum number of workers.

## 17. Run one-time and continuous examples together

Both examples can use the same Redis server as long as they use different Scarlet namespaces.

Example:

```text
One-time:
SCARLET_NAME=scarlet_csv_avg_once_v1

Continuous:
SCARLET_NAME=scarlet_csv_avg_cntns_v1
```

This keeps their Mapper keys separate.

## 18. Security and `.gitignore`

Never commit:

- `gustavo_config/`,
- worker `.env` files,
- Gustavo/Nebula passwords or tokens,
- Redis passwords,
- `.gustavo-worker/`,
- `.scarlet_node_id`.

Recommended entries:

```gitignore
gustavo_config/
scarlet_data/.scarlet_node_id
__pycache__/
*.pyc
```

The `scarlet_data/` folder may remain in Git if it contains only safe sample input.

## 19. Troubleshooting

### CSV change is not detected

Confirm the edited host directory is the directory mounted to `/data`.

Inspect the file inside the container:

```powershell
docker exec <container-name> cat /data/input.csv
```

The contents should match the host file.

### New worker does not appear

Check:

```powershell
Test-NetConnection <HEAD_DEVICE_IP> -Port 6379
```

Also verify:

- the Gustavo worker belongs to `scarlet-worker-dg`,
- the continuous app is assigned to that group,
- the app is running,
- all continuous instances use the same `SCARLET_NAME`.

### A departed worker remains visible temporarily

This is expected until its Redis-backed Scarlet data expires according to `NODE_TTL_SECONDS`.

### Two machines have the same node ID

Delete `.scarlet_node_id` on one machine and restart that machine's continuous averaging container. Never copy the generated ID file between devices.

### Harmless warning messages

The example code filters the known noisy messages:

```text
SCARLET_CONFIG_FILE not specified
Failed to enable maintenance notifications
```

## 20. Final deployment structure

```text
                         Gustavo / Nebula
                               │
                ┌──────────────┴──────────────┐
                │                             │
        scarlet-head-dg               scarlet-worker-dg
                │                             │
          Head Device               Worker B / C / D / ...
                │                             │
        ┌───────┴────────┐                    │
        │                │                    │
      Redis       Continuous Avg App    Continuous Avg App
      :6379              │                    │
        ▲                │                    │
        └────────────────┴────────────────────┘
                   shared Scarlet Mapper
```

Each physical machine has:

```text
local scarlet_data/
├── input.csv
└── .scarlet_node_id   # generated locally; never commit
```

This provides a reproducible starting point for experimenting with distributed data exchange, dynamic membership, and live input changes using Gustavo, Scarlet, and Redis.
