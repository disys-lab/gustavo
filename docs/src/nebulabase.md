# NebulaBase

`gustavo.src.NebulaBase` is the base configuration class inherited by `Manager`, `Composer`, and `Cache`. It loads platform parameters from either a Streamlit session state dict (UI mode) or a dotenv file (CLI mode).

::: gustavo.src.NebulaBase

---

## Modes

### CLI mode

Used by the `gustavo` CLI and (via `cache_shim.py`) by the FastAPI backend for `Cache` construction.

Set `GUSTAVO_CONFIG_FILE` to the path of a `KEY=VALUE` env file before instantiating:

```bash
export GUSTAVO_CONFIG_FILE=/path/to/manager.env
```

```python
from gustavo.src.NebulaBase import NebulaBase
nb = NebulaBase(mode="CLI")
```

`setNebulaParams()` calls `load_dotenv(override=True)` to load the file, then reads individual keys from `os.environ`.

### Streamlit mode

Used when passing a dict (formerly `st.session_state`, now `config_store.get()` in the FastAPI context):

```python
from gustavo.api import config_store
nb = NebulaBase(mode="streamlit", params=config_store.get())
```

In this mode, attributes are read directly from the `params` dict.

---

## Attributes

| Attribute | Source key | Description |
|-----------|------------|-------------|
| `REGISTRY_IP` | `REGISTRY_HOST` | Docker registry address |
| `REGISTRY_PORT` | `REGISTRY_PORT` | Docker registry port |
| `REDIS_IP` | `REDIS_HOST` | Redis address |
| `REDIS_PORT` | `REDIS_PORT` | Redis port |
| `REDIS_AUTH_TOKEN` | `REDIS_AUTH_TOKEN` | Redis password |
| `MANAGER_IP` | `MANAGER_HOST` | Nebula Manager address |
| `MANAGER_PORT` | `MANAGER_PORT` | Nebula Manager port |
| `NEBULA_USERNAME` | `NEBULA_USERNAME` | API username |
| `NEBULA_PASSWORD` | `NEBULA_PASSWORD` | API password |
| `NEBULA_AUTH_TOKEN` | `NEBULA_AUTH_TOKEN` | Base64 auth token |
| `NEBULA_PROTOCOL` | `NEBULA_PROTOCOL` | `http` or `https` |
| `WORKER_NMODE` | `WORKER_NMODE` | Worker Docker network mode |

Note the `*_HOST` → `*_IP` key mapping: config keys use the `_HOST` suffix, but `NebulaBase` attributes use `_IP`.
