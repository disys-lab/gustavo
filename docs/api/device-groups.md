# Device Groups API

Manage device groups — logical collections of worker nodes that share the same application deployments.

::: gustavo.api.routers.device_groups

---

## Endpoints

### `GET /api/device-groups`

List all device groups with their current app membership.

**Response:**

```json
{
  "error": false,
  "response": {
    "device_groups": ["production", "staging"],
    "details": {
      "production": { "apps": ["test_linreg", "inference_service"] },
      "staging": { "apps": ["test_linreg"] }
    }
  }
}
```

---

### `POST /api/device-groups`

Create a new device group.

**Request body:**

```json
{
  "name": "production",
  "apps": ["test_linreg"]
}
```

---

### `GET /api/device-groups/{name}`

Get details of a single device group.

---

### `PUT /api/device-groups/{name}`

Update a device group (replace its app list).

**Request body:**

```json
{
  "apps": ["test_linreg", "inference_service"]
}
```

---

### `DELETE /api/device-groups/{name}`

Delete a device group.

---

### `POST /api/device-groups/{name}/apps/add`

Add one or more apps to a device group without replacing the existing list.

**Request body:**

```json
{ "apps": ["new_app"] }
```

---

### `POST /api/device-groups/{name}/apps/remove`

Remove one or more apps from a device group.

**Request body:**

```json
{ "apps": ["old_app"] }
```
