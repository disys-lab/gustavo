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

### `GET /api/config/worker-download`

Download a `worker.env` scoped to the **caller's own** Nebula identity —
the way to obtain worker configuration automatically instead of
hand-writing a `worker.env` file. Available to any authenticated user, not
just admins: an admin gets the platform-wide identity, a regular user gets
their own Nebula username/token, so the returned file only ever carries
the same `apps`/`device_groups` access that caller already has — nothing a
leaked copy could use to escalate beyond what they can already do.

Accepts two authentication methods:

- **Bearer** — the normal Gustavo session token, obtained from
  [`POST /api/auth/login`](auth.md#post-apiauthlogin) (what the UI's
  sidebar "Worker config" button uses).
- **HTTP Basic** — the caller's Nebula `username:secret` directly, verified
  the same identity-bound way `/login` verifies it. Lets a script on a
  remote machine fetch its own worker config in a single request, without
  first minting a session token:

```bash
curl -u alice:her_secret http://<gustavo-host>:<port>/api/config/worker-download -o worker.env
```

**Response:** `text/plain`

```
MANAGER_HOST=cypress-man.example.edu
MANAGER_PORT=8080
REDIS_HOST=cypress-man.example.edu
REDIS_PORT=6379
REDIS_AUTH_TOKEN=...
REGISTRY_HOST=cypress-man.example.edu
REGISTRY_PORT=5051
WORKER_NMODE=host
NEBULA_USERNAME=alice
NEBULA_PASSWORD=...
NEBULA_AUTH_TOKEN=...
```

The resulting file is ready to use directly as `GUSTAVO_CONFIG_FILE` for
[`gustavo worker up`](../cli/worker.md).

---

## config_store module

::: gustavo.api.config_store
    options:
      members:
        - load
        - get
        - update
        - masked
