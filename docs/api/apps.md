# Apps API

Create, read, update, and delete Nebula applications. Also exposes registry image queries and YAML import/export.

::: gustavo.api.routers.apps

---

## Endpoints

### `GET /api/apps`

List all deployed applications.

**Response:**

```json
{
  "error": false,
  "response": {
    "apps": ["test_linreg", "inference_service"]
  }
}
```

---

### `GET /api/apps/{name}`

Get the full configuration of a single application.

```
GET /api/apps/test_linreg
```

---

### `POST /api/apps`

Create a new application.

**Request body:**

```json
{
  "name": "test_linreg",
  "docker_image": "192.168.1.100:5001/test_linreg:latest",
  "env_vars": {
    "APP_ID": "test_linreg",
    "SLEEP_SECS": "600"
  },
  "ports": [{"host": 8080, "container": 8080}],
  "volumes": [{"host": "/data", "container": "/data"}],
  "running": true,
  "privileged": false,
  "network_mode": "bridge",
  "device_groups": ["production"]
}
```

`APP_ID` is injected automatically from `name` if not provided.

After creating the app, it is added to all specified `device_groups`.

---

### `PUT /api/apps/{name}`

Update an existing application. Same body as POST.

---

### `DELETE /api/apps/{name}`

Delete an application. The app is removed from all device groups before deletion.

---

### `GET /api/apps/defaults`

Return server-side default environment variables for new applications. These include the current platform connection details (Redis, Manager) resolved from `config_store`.

**Response:**

```json
{
  "error": false,
  "response": {
    "env_vars": {
      "REDIS_DB_HOST": "192.168.1.100",
      "REDIS_DB_PORT": "6379",
      "REDIS_DB_PWD": "your-token",
      "MANAGER_HOST": "192.168.1.100",
      "MANAGER_PORT": "80",
      "NEBULA_AUTH_TOKEN": "bmVidWxhOm5lYnVsYQ==",
      "MANAGER_AUTH": "bmVidWxhOm5lYnVsYQ==",
      "SLEEP_SECS": "600",
      "KEYGEN_PUBLIC_KEY": "06ede5b6..."
    }
  }
}
```

!!! warning "Sensitive values"
    This endpoint returns unmasked secrets (Redis token, Nebula auth token). It requires a valid Bearer token when `AUTH_ENABLED=true`.

---

### `GET /api/apps/registry/images`

List all images and their tags in the local Docker registry.

**Response:**

```json
{
  "error": false,
  "response": {
    "images": [
      { "name": "test_linreg", "tags": ["latest", "v1.2"] }
    ],
    "registry_url": "192.168.1.100:5001",
    "catalog_url": "http://192.168.1.100:5001/v2/_catalog"
  }
}
```

---

### `POST /api/apps/yaml/parse`

Upload a YAML file and receive the parsed application config as JSON.

**Form field:** `file` — a `.yaml` or `.yml` file

**Response:**

```json
{
  "error": false,
  "response": {
    "docker_image": "...",
    "env_vars": { ... },
    ...
  }
}
```

---

### `GET /api/apps/{name}/yaml`

Export a deployed application's configuration as a YAML string.

**Response:** `text/plain`

```yaml
docker_image: 192.168.1.100:5001/test_linreg:latest
env_vars:
  APP_ID: test_linreg
running: true
privileged: false
```
