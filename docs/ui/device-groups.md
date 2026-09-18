# Device Groups

Organise worker nodes into logical groups and assign applications to them.

---

## Device group list (`/device-groups`)

Shows all configured device groups as expandable rows. Each row displays the group name and its current app membership.

---

## Create a device group

Click **New Group**. Enter:

| Field | Description |
|-------|-------------|
| Name | Group identifier |
| Apps | Select apps to include in this group |

---

## Edit a device group

Click on a group to expand it. Use **Add Apps** or **Remove Apps** to manage membership without replacing the full list.

Or click **Edit** to open the full form and replace the app list entirely.

---

## Delete a device group

Click **Delete** on the group row. A confirmation dialog appears before deletion.

---

## App assignment

Apps can belong to multiple device groups. When an app is assigned to a group, all worker nodes in that group will pull and run the app's Docker container.

Changes take effect on the next Nebula sync cycle on each worker.

---

## Current Cron Jobs

Each device group's row lists its assigned cron jobs the same way it lists
apps. Use **Add Cron Jobs** / **Remove Cron Jobs** to manage membership
without replacing the full list, or **Edit** to replace it entirely. See
[Cron Jobs](cron-jobs.md) for creating the cron jobs themselves.

Changes take effect on the next Nebula sync cycle on each worker, same as
app assignment.

---

## Get worker config

Each device group's row has a **Get worker config** section with four
download buttons — pick whichever fits how you want to bring a worker up
for that group. They're independent: downloading one has no bearing on
the others, and none of them needs a second file alongside it.

| Button | Downloads | Use it when |
|---|---|---|
| **Native (.env)** | `worker-{group}.env` | You have `gustavo` installed and want to run `gustavo worker up` directly. |
| **Docker Compose** | `docker-compose-{group}.yml` | You'd rather manage the worker as a compose service — `docker compose up -d` and it's running. |
| **Launcher script (Mac/Linux)** | `worker-{group}.command` | You want a single double-click-and-go file on macOS (or a plain terminal script on Linux) — no compose file, no `.env`, nothing else to keep track of. |
| **Launcher script (Windows)** | `worker-{group}.bat` | Same idea, for Windows — double-click in Explorer to run, no setup. |

Every filename includes the device group's name, so downloads for
different groups never collide or silently overwrite each other in your
downloads folder.

Four controls sit above the buttons and apply to whichever format you
download next:

| Control | Effect |
|---|---|
| **GPU Enabled** | Adds `GPU_ENABLED=true`, granting every container the worker launches GPU access. Only check this for hardware that actually has a GPU `nvidia-container-toolkit` can expose. Applies to the worker as a whole, not per-app. |
| **Report via Reporter** | Switches worker status reporting from direct Redis writes to HTTP(S) calls to the [Reporter](../configuration.md#reporter) service. Unchecked (direct Redis) is the default. |
| **Public Facing Access** | Bakes in the public Manager/Reporter addresses ([Settings: Public Facing Endpoints](settings.md#public-facing-endpoints)) instead of the internal ones, for a worker reaching this platform from outside — e.g. behind a Cloudflare Tunnel. Disabled until an admin turns on `PUBLIC_ENDPOINTS_ENABLED` in Settings. |
| **Check-in / Report Interval (seconds)** | How often the worker polls Nebula and reports status — one shared timer, not two. Defaults to 60. |

If you belong to an [external user group](users.md#external-user-groups),
**Report via Reporter** and **Public Facing Access** are locked on and
can't be unchecked — an external caller is never handed the shared
internal Redis credential or a LAN address it can't reach anyway.
Registry inclusion is not a checkbox at all: it's decided automatically by
[registry policy](registry.md#internal-vs-external-access).

All four downloads require you to actually have access to the device
group whose button you clicked — same permission check as everything else
on this page. See [Device Groups API](../api/device-groups.md#worker-config-downloads)
for the underlying endpoints, including how to fetch these the same way
from a script over SSH instead of clicking a button.
