# Configuration API

::: gustavo.api.config_store

---

## Endpoints

### `GET /api/config`

Return the current platform configuration. Sensitive fields (`NEBULA_PASSWORD`, `NEBULA_AUTH_TOKEN`, `REDIS_AUTH_TOKEN`, `MONGO_PASSWORD`) are replaced with `***`.

**Response:**

```json
{
  "error": false,
  "response": {
    "MANAGER_HOST": "192.168.1.100",
    "MANAGER_PORT": "80",
    "REDIS_AUTH_TOKEN": "***",
    ...
  }
}
```

---

### `POST /api/config`

Update the platform configuration. Accepts a partial or full config dict. Values equal to `***` or empty strings are ignored (this allows the Settings UI to submit masked password fields without overwriting stored values).

**Request body:**

```json
{
  "MANAGER_HOST": "10.0.0.5",
  "REDIS_PORT": "6379"
}
```

**Response:** Updated config (with sensitive fields masked).

The update is persisted to `platform.yaml` on disk immediately and takes effect on the next API call that constructs a `Manager`, `Composer`, or `Cache` object.

---

### `POST /api/config/upload`

Upload a `manager.env` file (plain text `KEY=VALUE` format) to merge into the config.

**Form field:** `file` — a `.env` file

**Response:**

```json
{
  "error": false,
  "response": "Loaded 14 keys from manager.env"
}
```

Lines beginning with `#` and blank lines are ignored.

---

### `GET /api/config/download`

Download the current configuration as a `manager.env` text file.

**Response:** `text/plain`

```
MANAGER_HOST=192.168.1.100
MANAGER_PORT=80
REDIS_HOST=192.168.1.100
...
```

!!! warning
    The downloaded file includes plaintext passwords. Handle it securely.

---

## config_store module

::: gustavo.api.config_store
    options:
      members:
        - load
        - get
        - update
        - masked
