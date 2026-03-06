# Manager

`gustavo.src.Manager` manages the full lifecycle of the five core platform services using the Docker SDK.

Inherits from `NebulaBase`.

::: gustavo.src.Manager

---

## Services managed

| Service | Container name pattern | Description |
|---------|----------------------|-------------|
| `registry` | `registry` | Docker image registry (v2) |
| `redis` | `redis` | Redis with Redis Stack for worker metric cache |
| `mongo` | `mongo` | MongoDB for Nebula state |
| `manager` | `nebula-manager` | Nebula Manager API |
| `syncer` | `dregsy` | DREGSY image syncer |

---

## Key methods

### `run(service_name)`

Dispatcher that calls the appropriate `run*()` method based on the service name.

```python
man = Manager(mode="streamlit", params=config)
man.run("redis")   # calls runRedis()
man.run("all")     # launches all 5 services
```

### `serviceStatus(service_name)`

Check whether a service container is running.

```python
result = man.serviceStatus("redis")
# {"error": False, "response": "running"}  — if up
# {"error": True, "response": "not found"} — if container absent
```

### `handleService(service_name, action)`

Perform a lifecycle action on a running service.

```python
man.handleService("redis", "stop")
man.handleService("redis", "start")
man.handleService("redis", "restart")
man.handleService("redis", "kill")
man.handleService("redis", "remove")
```

### `waitManager()`

Polls `http://{MANAGER_IP}:{MANAGER_PORT}/api/v2/status` every 3 seconds until the Manager API responds. Used after `runManager()`. In the FastAPI context, `wait_for_manager_enabled = False` to avoid blocking the event loop.

---

## FastAPI usage

In the FastAPI backend, `Manager` is instantiated via `_build_manager(cfg)` in `dependencies.py`, which sets all attributes not auto-populated by `NebulaBase` in streamlit mode:

```python
from gustavo.api.dependencies import _build_manager
from gustavo.api import config_store

man = _build_manager(config_store.get())
result = man.run("redis")
```

::: gustavo.api.dependencies
    options:
      members:
        - _build_manager
        - _build_composer
