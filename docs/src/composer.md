# Composer

`gustavo.src.Composer` wraps the NebulaPythonSDK to provide CRUD operations for Nebula applications and device groups.

Inherits from `NebulaBase`.

::: gustavo.src.Composer

---

## Key methods

### `handleAsset(asset_type, asset_name, mode, config)`

Generic CRUD for apps and device groups.

```python
comp = Composer(mode="streamlit", params=config)

# Create an app
comp.handleAsset("apps", "my_app", "create", {"docker_image": "...", "env_vars": {...}})

# Update a device group
comp.handleAsset("device_groups", "production", "update", {"apps": ["app1", "app2"]})

# Delete an app
comp.handleAsset("apps", "my_app", "delete", {})
```

Parameters:

| Parameter | Description |
|-----------|-------------|
| `asset_type` | `"apps"` or `"device_groups"` |
| `asset_name` | Name of the app or group |
| `mode` | `"create"`, `"update"`, or `"delete"` |
| `config` | Configuration dict for the asset |

---

### `handleDeviceGroup(app_list, mode, device_group)`

Add or remove apps from a device group.

```python
# Add apps
comp.handleDeviceGroup("app1,app2", "update", "production")

# Remove apps
comp.handleDeviceGroup("app1", "delete", "production")
```

The `app_list` parameter is a comma-separated string of app names.

---

### `checkLocalRepoImages(name, tag)`

Query the local Docker registry API to check if an image exists.

```python
result = comp.checkLocalRepoImages("my_app", "latest")
```

Queries `http://{REGISTRY_IP}:{REGISTRY_PORT}/v2/{name}/tags/list`.

---

### `printDiagnosticResponse(reply, accept_code, ...)`

Internal helper that parses Nebula SDK responses and returns a standardised `{"error": bool, "response": ...}` dict. Handles error codes 400 (bad request), 403 (forbidden), 409 (conflict), and 200/201 (success).
