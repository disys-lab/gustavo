# Apps

Create, view, edit, and delete Nebula applications. An application is a Docker container configuration that Nebula deploys to worker nodes.

---

## App list (`/apps`)

Shows all deployed applications as expandable cards. Each card displays:
- Docker image name
- Running / stopped state
- Device group membership
- Env var count, port count, volume count

Click **Edit** to open the full edit form. Click **Delete** to remove the app (with confirmation).

---

## Create app (`/apps` → New App button)

Opens the `AppForm` with blank fields and server-side defaults pre-populated.

### Form sections

**Basic Configuration**

| Field | Description |
|-------|-------------|
| Name | Lowercase letters, numbers, dashes, underscores. Cannot be changed after creation. |
| Docker Image | Select from the registry dropdown or type a full image reference. |
| Running | Whether containers should be started immediately on deployment. |
| Privileged | Run with extended Docker privileges. |
| Network Mode | Optional Docker network mode override. |

**Environment Variables**

Dynamic list of `KEY` / `VALUE` pairs. Click `+` to add a row, `×` to remove.

Server-side defaults (from `/api/apps/defaults`) are pre-filled on new apps:

| Variable | Source |
|----------|--------|
| `REDIS_DB_HOST` | `REDIS_HOST` config |
| `REDIS_DB_PORT` | `REDIS_PORT` config |
| `REDIS_DB_PWD` | `REDIS_AUTH_TOKEN` config |
| `MANAGER_HOST` | `MANAGER_HOST` config |
| `MANAGER_PORT` | `MANAGER_PORT` config |
| `NEBULA_AUTH_TOKEN` | `NEBULA_AUTH_TOKEN` config |
| `SLEEP_SECS` | `600` |

**Ports**

Dynamic list of `HOST PORT` / `CONTAINER PORT` number pairs.

**Volumes**

Dynamic list of `HOST PATH` / `CONTAINER PATH` string pairs.

**Device Groups**

Multi-select of available device groups. The app is added to all selected groups on save.

**Command & Shared Memory**

| Field | Description |
|-------|-------------|
| Container Command | Dynamic list of command arguments overriding the image's default entrypoint/command. One argument per row, in order (e.g. `python3`, `-m`, `vllm.entrypoints.openai.api_server`). Leave empty to use the image's default command. |
| Shared Memory Size | Text field for `shm_size` (e.g. `2g`). Leave empty for Docker's default (64m). |

See [Deploying LLMs](../llm-deployments.md) for a worked example — these two fields are what make GPU inference servers like vLLM deployable through Gustavo.

### YAML import

Click **Upload YAML** to upload a `.yaml` file. The parsed config populates all form fields — including Command & Shared Memory — which you can review before saving.

---

## Edit app (`/apps/[name]`)

Same form as Create, with the app name field disabled. All other fields are editable.

**Export YAML** button downloads the current deployed config as a YAML file.

---

## Validation

Form validation is handled by Zod:

- App name: `/^[a-z0-9_-]+$/`
- Docker image: required string
- Port numbers: integers
- Volume paths: non-empty strings

Errors are shown inline below each field.
