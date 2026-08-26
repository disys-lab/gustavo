# `gustavo apps`

Create, read, update, and delete Nebula applications.

```
Usage: gustavo apps [OPTIONS] COMMAND [ARGS]...

  Manage applications
```

---

## Key concepts

| Term | Definition |
|------|------------|
| **App** | A YAML configuration that governs how a container image runs on edge devices. Registered with Gustavo so the image can run correctly. |
| **Image** | A static container image (e.g. on Docker Hub or your local registry). Not yet running. |
| **Container** | A running instance of an image on a device. |

An **App** is not the image itself — it is the configuration that tells Nebula *how* to run the image across your device groups.

---

## Commands

### `list`

List all deployed applications.

```bash
gustavo apps list
```

---

### `create`

Create a single application from a YAML file.

```bash
gustavo apps create -n APP_NAME -f CONFIG_FILE
```

| Option | Required | Description |
|--------|----------|-------------|
| `-n` / `--name` | Yes | Application name |
| `-f` / `--file` | Yes | Path to YAML config file |

Example:

```bash
gustavo apps create -n test_linreg -f test_linreg.yaml
```

Expected output:

```
nebula@192.168.1.100:80
DOCKER_HOST:unix:/var/run/docker.sock
{'name': 'test_linreg', 'tags': ['latest']}
test_linreg:latest have been found in local registry
created nebula app : test_linreg
created nebula device_group : bca
```

---

### `createm`

Create multiple applications from a YAML file containing a list.

```bash
gustavo apps createm -f CONFIG_FILE
```

---

### `update`

Update an existing application.

```bash
gustavo apps update -n APP_NAME -f CONFIG_FILE
```

To update the image associated with an app, change the `docker_image` field in the YAML and re-run `update`:

```yaml
# Before
docker_image: "192.168.1.100:5001/test_linreg"

# After — switching to a different image
docker_image: "192.168.1.100:5001/test_linreg_v2"
```

```bash
gustavo apps update -n test_linreg -f test_linreg.yaml
```

---

### `updatem`

Update multiple applications from a YAML file.

```bash
gustavo apps updatem -f CONFIG_FILE
```

---

### `delete`

Delete an application.

```bash
gustavo apps delete -n APP_NAME
```

---

## Application YAML format

```yaml
app_name:                          # (REQUIRED) top-level key must match the app name
  docker_image: "REGISTRY_HOST:REGISTRY_PORT/image_name"  # (REQUIRED) no tag — use image name only
  env_vars:                        # (OPTIONAL) environment variables passed to the container
    APP_ID: app_name
    REDIS_DB_HOST: 192.168.1.100
    REDIS_DB_PORT: "6379"
    REDIS_DB_PWD: your-redis-token
    MANAGER_HOST: 192.168.1.100
    MANAGER_PORT: "80"
    NEBULA_AUTH_TOKEN: bmVidWxhOm5lYnVsYQ==
  volumes:                         # (OPTIONAL) host:container path mappings
    - "/tmp/:/tmp/1"
    - "/var/tmp/:/var/tmp/1:rw"
  starting_ports:                  # (OPTIONAL) host:container port mappings
    - 9000: 9000
    - 8080: 8080
  running: true                    # start the container immediately
  networks:
    - "nebula"
  rolling_restart: true            # rolling update across devices
  containers_per:
    server: 1                      # one container per device
  privileged: false
  devices: []
```

!!! warning "Do not include image tags in `docker_image`"
    Specify the image name only — no `:latest` or version tag. Nebula manages image resolution via the local registry. Including a tag may cause unexpected behaviour.

!!! warning "Only include NEBULA_AUTH_TOKEN/MANAGER_AUTH if this app actually needs it"
    `env_vars` become real environment variables on whatever device group the app is deployed to. `NEBULA_AUTH_TOKEN` is `base64("username:password")` — encoding, not encryption — so anyone with Docker or shell access on that device can trivially recover the plaintext credential. Only add it for apps that genuinely need to call back into the Nebula Manager themselves (e.g. a comms/reporting container), and prefer a credential scoped for that purpose over your own personal login. The create-app form's auto-filled defaults deliberately leave this out for exactly this reason.

!!! note "APP_ID"
    The `APP_ID` env var is automatically set to the application name if not provided. All Nebula apps must have `APP_ID` in their env_vars to register with the cache.

---

## Device group assignment

After creating an application, add it to device groups:

```bash
gustavo device-group update -n my_group -a my_app
```

Or specify device groups at creation time using the web UI (the CLI create command does not accept device group arguments directly).
