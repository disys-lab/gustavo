# Cache

`gustavo.src.Cache` queries worker-reported metrics stored in Redis. Workers pickle and push CPU, memory, disk, and container statistics periodically; `Cache` reads and deserialises this data.

Inherits from `NebulaBase`. Hardcodes `mode="CLI"`.

::: gustavo.src.Cache

---

## Redis key format

Worker metrics are stored under keys with the pattern:

```
{device_group}@{host_id}_{timestamp}
```

Example: `production@192.168.1.50_1741270000`

`scanLatest()` finds the most recent key per host by parsing timestamps.

---

## Key methods

### `getHosts(device_group, host)`

Return a map of hosts to their device group memberships.

```python
cache = Cache()
result = cache.getHosts("all", "all")
# {"error": False, "response": {"192.168.1.50": ["production"]}}
```

### `getAssetsForAll(asset, device_group_id, host_id)`

Main query interface. Retrieves the latest vitals or container stats.

```python
vitals = cache.getAssetsForAll("vitals", "all", "all")
containers = cache.getAssetsForAll("containers", "production", "192.168.1.50")
```

`asset` must be one of: `"vitals"`, `"containers"`

Raises `ErrorHandling` if Redis is unreachable.

### `unpickleData(device_group, host)`

Retrieve the pickled data blob from Redis for the given host and deserialise it.

---

## Raw data format

**Vitals string:**

```
192.168.1.50@192.168.1.50 at time:1741270000  mem:{'total':8192,'used':4096,'free':4096}  disk:{'total':100000,'used':50000,'free':50000}  cpu_cores:4  cpu_percent:23.5
```

**Containers string:**

```
containers:[{'name': '/my_app', 'cpu_stats': {...}, 'memory_stats': {...}, ...}]
```

The FastAPI monitoring router parses these strings into structured JSON via `_extract_vitals()` and `_extract_containers()`.

---

## FastAPI bridge

Because `Cache` hardcodes `mode="CLI"` and reads from `GUSTAVO_CONFIG_FILE`, the FastAPI backend uses `build_cache()` from `cache_shim.py`:

```python
from gustavo.api.cache_shim import build_cache

cache = build_cache()
result = cache.getAssetsForAll("vitals", "all", "all")
```

`build_cache()` writes the current config to `/tmp/gustavo_api.env`, sets `GUSTAVO_CONFIG_FILE`, and returns a fresh `Cache()` instance.

::: gustavo.api.cache_shim
