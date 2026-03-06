# CLI Reference

The `gustavo` command-line interface provides direct access to all platform operations without a web browser. It reads configuration from a `KEY=VALUE` env file pointed to by `GUSTAVO_CONFIG_FILE`.

---

## Command groups

| Command | Description |
|---------|-------------|
| [`manager`](manager.md) | Control platform services (Redis, MongoDB, Registry, Manager, Syncer) |
| [`worker`](worker.md) | Manage worker nodes on edge devices |
| [`apps`](apps.md) | Create, update, and delete Nebula applications |
| [`device-group`](device-groups.md) | Manage device groups |
| [`registry`](registry.md) | Query the local Docker registry |
| [`cache`](cache.md) | Query real-time metrics from worker nodes |
| [`utils`](utils.md) | Utility commands |
| `ping` | Check the Nebula Manager API responds |
| `prune` | Prune images on device groups |

---

## Global options

```
gustavo [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.
```

---

## Common patterns

### Check everything is reachable

```bash
gustavo ping
gustavo manager check
```

### Full platform bring-up

```bash
gustavo manager up registry
gustavo manager up redis
gustavo manager up mongo
gustavo manager up manager
```

### Deploy an app to a device group

```bash
gustavo apps create -n my_app -f my_app.yaml
gustavo device-group create -n production -a my_app
gustavo cache vitals
```

---

## Native Setup

This section covers running Gustavo entirely via the CLI — no containers required. This is the path for contributors or environments where Docker is not available. For most deployments, use the [Docker quickstart](../quickstart.md) instead.

### Common prerequisites

These steps apply to **both** manager and worker nodes.

**1. Install Docker**

Follow the official guide for your OS: [docs.docker.com/get-docker](https://docs.docker.com/get-docker/)

Allow non-root access: [Linux post-install](https://docs.docker.com/engine/install/linux-postinstall/)

If `/home/ubuntu/.docker/config.json` exists:

```bash
sudo chmod 777 /home/ubuntu/.docker/config.json
```

**2. Configure Docker for the local (insecure) registry**

Create or edit `/etc/docker/daemon.json`:

```json
{ "insecure-registries": ["MANAGER_HOST:REGISTRY_PORT"] }
```

Replace `MANAGER_HOST` and `REGISTRY_PORT` with the values from your env file, then restart Docker:

```bash
sudo systemctl restart docker
```

**3. Install Gustavo CLI**

```bash
pip3 install --no-cache-dir --extra-index-url https://pypi.fury.io/osu-home-stri/ gustavo
```

Verify:

```bash
gustavo --version
gustavo --help
```

**4. Point Gustavo at the config file**

```bash
export GUSTAVO_CONFIG_FILE=/path/to/your.env
```

To make this permanent:

```bash
echo 'export GUSTAVO_CONFIG_FILE=/path/to/your.env' >> ~/.bashrc
source ~/.bashrc
```

---

### Manager node setup

The manager node runs the core platform services: Registry, Redis, MongoDB, Syncer, and the Nebula Manager itself.

#### `manager.env`

```bash
# Registry
REGISTRY_HOST=192.168.1.100
REGISTRY_PORT=5001
REGISTRY_IMAGE=registry:2
REGISTRY_BKP_DIR=/tmp/

# Redis
REDIS_HOST=192.168.1.100
REDIS_PORT=6379
REDIS_AUTH_TOKEN=your-redis-token
REDIS_IMAGE=redis/redis-stack:7.4.0-v1
REDIS_BKP_DIR=/tmp/

# MongoDB
MONGO_HOST=192.168.1.100
MONGO_PORT=27017
MONGO_USERNAME=nebula
MONGO_PASSWORD=nebula
MONGO_IMAGE=mongo:4.0.19
MONGO_CERTIFICATE_FOLDER_PATH=/tmp/

# Nebula Manager
MANAGER_HOST=192.168.1.100
MANAGER_PORT=80
MANAGER_IMAGE=nebulaorchestrator/manager:2.6.1
MANAGER_NMODE=host

# Nebula credentials
NEBULA_USERNAME=nebula
NEBULA_PASSWORD=nebula
NEBULA_AUTH_TOKEN=bmVidWxhOm5lYnVsYQ==
NEBULA_PROTOCOL=http

# Syncer (DREGSY)
SYNCER_IMAGE=ghcr.io/disys-lab/dregsy:latest
SYNCER_NMODE=host
DREGSY_CONFIG_FILE_PATH=/path/to/dregsy_conf.yml
DREGSY_MAPPING_FILE_PATH=/path/to/mappings_list.yml

# Cache
CACHE_EXPIRE_TIME=120
REDIS_KEY_PREFIX=gustavo-reports

# Worker containers
WORKER_NMODE=host
```

!!! note
    `NEBULA_AUTH_TOKEN` is the base64 encoding of `username:password`. For default credentials `nebula:nebula` the value is `bmVidWxhOm5lYnVsYQ==`. Generate a custom token with:
    ```bash
    echo -n "username:password" | base64
    ```

See [Syncer Setup](manager-setup.md) for the `dregsy_conf.yml` and `mappings_list.yml` file formats.

#### Bring up services

See [Manager Node Setup](manager-setup.md#step-4-bring-up-services) for the full bring-up sequence, start order, and verification steps.

---

### Worker node setup

Each edge device runs a single worker container. The worker connects to the Manager, manages assigned application containers, and reports metrics to Redis.

#### `worker.env`

The worker only needs Manager and Redis connectivity — no Registry, MongoDB, or Syncer config required.

```bash
# Nebula Manager
MANAGER_HOST=192.168.1.100
MANAGER_PORT=80

# Nebula credentials
NEBULA_USERNAME=nebula
NEBULA_PASSWORD=nebula
NEBULA_AUTH_TOKEN=bmVidWxhOm5lYnVsYQ==
NEBULA_PROTOCOL=http

# Redis (for metric reporting)
REDIS_HOST=192.168.1.100
REDIS_PORT=6379
REDIS_AUTH_TOKEN=your-redis-token
REDIS_KEY_PREFIX=gustavo-reports
CACHE_EXPIRE_TIME=120

# Worker container network mode
WORKER_NMODE=host
```

#### Deploy the worker

```bash
export GUSTAVO_CONFIG_FILE=/path/to/worker.env

gustavo worker up
```

Expected output:

```
Status: Image is up to date for ghcr.io/disys-lab/gustavo-worker:latest
nebula@192.168.1.100:80
Worker Up
```

Verify:

```bash
docker ps   # look for worker_<device_group>
gustavo cache hosts
```

#### Remove the worker

```bash
gustavo worker remove
# or by name:
gustavo worker remove -n worker_<device_group>
```
