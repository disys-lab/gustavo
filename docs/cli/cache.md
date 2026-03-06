# `gustavo cache`

Query real-time metrics reported by worker nodes. Workers push CPU, memory, disk, and container statistics to Redis. The `cache` commands read directly from that Redis store.

```
Usage: gustavo cache [OPTIONS] COMMAND [ARGS]...

  obtain status of various workers on the platform
```

---

## Commands

### `vitals`

Show system vitals (CPU, memory, disk) for all workers or a specific device group / host.

```bash
gustavo cache vitals [-d DEVICE_GROUP] [-h HOST]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-d` / `--device-group` | `all` | Filter by device group name |
| `-h` / `--host` | `all` | Filter by specific host |

Examples:

```bash
# All workers
gustavo cache vitals

# Specific device group
gustavo cache vitals -d production

# Specific host
gustavo cache vitals -h 192.168.1.50
```

---

### `containers`

Show running container statistics (per-container CPU and memory) from worker nodes.

```bash
gustavo cache containers [-d DEVICE_GROUP] [-h HOST]
```

Uses the same filter options as `vitals`.

---

## Data format

Metrics are stored in Redis as pickled Python objects. Workers write entries with keys in the format:

```
{device_group}@{host_id}_{timestamp}
```

The `cache` commands scan for the most recent entry per host, unpickle the data, and return structured metrics:

**Vitals:**
```
host@ip at time:TIMESTAMP  mem:{total:..., used:..., free:...}  disk:{...}  cpu_cores:N  cpu_percent:X.X
```

**Containers:**
```
containers:[{docker stats dict}, ...]
```

---

## Configuration keys used

| Key | Description |
|-----|-------------|
| `REDIS_HOST` | Redis address |
| `REDIS_PORT` | Redis port |
| `REDIS_AUTH_TOKEN` | Redis password |
| `CACHE_EXPIRE_TIME` | TTL in seconds for cache entries |
