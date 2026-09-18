# Cron Jobs

Create, view, edit, and delete Nebula cron jobs. A cron job is a
one-shot Docker container that a worker launches on a schedule, rather
than a long-running service — mirrors [Apps](apps.md), minus ports and
network mode, plus a `schedule` field.

---

## Cron job list (`/cron-jobs`)

Shows all cron jobs as expandable cards. Each card displays:
- Docker image name
- Schedule (cron expression)
- Enabled / disabled state
- Device group membership
- Env var count, volume count

Click **Edit** to open the full edit form. Click **Delete** to remove the cron job (with confirmation).

---

## Create cron job (`/cron-jobs` → New Cron Job button)

Opens the `CronJobForm` with blank fields.

### Form sections

**Basic Configuration**

| Field | Description |
|-------|-------------|
| Cron Job Name | Lowercase letters, numbers, dashes, underscores. Cannot be changed after creation. |
| Docker Image | Select from the registry dropdown or type a full image reference. |
| Schedule | A 5-field cron expression (e.g. `*/15 * * * *`), fed to `croniter` on the worker. |
| Running (enabled) | Whether the schedule is active. |
| Privileged | Run with extended Docker privileges. |
| Networks | Comma-separated Docker network names. Defaults to `nebula`. |

**Device Groups**

Multi-select of available device groups. The cron job is added to all selected groups on save.

**Environment Variables**

Dynamic list of `KEY` / `VALUE` pairs. Click `+ Add` to add a row, `✕` to remove.

Unlike Apps, cron jobs have no server-side default env vars — a cron job
container doesn't self-report through the Redis/Reporter path, so
there's no `APP_ID`-equivalent to inject.

**Volumes**

Dynamic list of `HOST PATH` / `CONTAINER PATH` string pairs.

**Command & Shared Memory**

| Field | Description |
|-------|-------------|
| Container Command | Dynamic list of command arguments overriding the image's default entrypoint/command. One argument per row, in order. Leave empty to use the image's default command. |
| Shared Memory Size | Text field for `shm_size` (e.g. `2g`). Leave empty for Docker's default (64m). |

### YAML import

Click **Upload YAML** to upload a `.yaml` file. The parsed config populates all form fields, which you can review before saving.

---

## Edit cron job (`/cron-jobs/[name]`)

Same form as Create, with the name field disabled. Device group
membership is shown read-only here — manage it from
[Device Groups](device-groups.md#current-cron-jobs) instead.

**Export YAML** button downloads the current deployed config as a YAML file.

---

## Validation

Form validation is handled by Zod:

- Cron job name: `/^[a-z0-9_-]+$/`
- Docker image: required string
- Schedule: 5 whitespace-separated fields
