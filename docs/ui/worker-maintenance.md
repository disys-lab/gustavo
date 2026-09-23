# Worker Maintenance

Ongoing worker upkeep — credential resets, identity refresh, self-update,
moving a worker to a different device group — is handled by
[gustavo-worker-cron](https://github.com/disys-lab/gustavo-worker-cron), a
separate companion image, not by Gustavo's own UI/API. It's built `FROM`
gustavo-worker itself, so it reuses the worker's own identity/Docker-socket
code directly rather than reimplementing it.

---

## What it does

A one-shot dispatcher, not a persistent daemon — selected per run by an
`ACTION` env var, meant to be scheduled (host crontab, or as a
[Nebula cron job](../api/cron-jobs.md)), not baked into the image itself.
Five independent actions:

| `ACTION` | Does |
|---|---|
| `reset-nebula-credentials` | Restores the Nebula username/password in the worker's shared credential file to known-good values |
| `reset-registry-credentials` | Same, for the registry username/password/host |
| `refresh-identity` | Re-resolves host/remote IP and re-registers with Reporter |
| `update-worker` | Pulls a new gustavo-worker image tag and recreates the running worker container on it |
| `change-device-group` | Moves a worker to a different device group in one call — container recreate, identity refresh, and cleanup of its old-group Reporter entry |

Each action is independently schedulable — run any subset, on whatever
cadence makes sense for that one. Full env var reference and deployment
examples are in the image's own
[README](https://github.com/disys-lab/gustavo-worker-cron#readme).

---

## Deploying it as a Nebula cron job

Every cron job a worker launches automatically has access to that
worker's own mounted volumes — including its shared identity/credential
directory — via Docker's `volumes_from`, referencing the worker's own
container (`worker_<device_group>`). This is unconditional and needs no
configuration on the cron job's own `volumes` field; see
[Cron Jobs API: worker volume inheritance](../api/cron-jobs.md#worker-volume-inheritance).
That's what makes gustavo-worker-cron usable as a Nebula cron job at all,
rather than only via host crontab.

---

## Exposing a worker's node identity to a regular app

Regular apps do **not** get automatic access to a worker's volumes the
way cron jobs do — deliberately, since apps can be arbitrary images and
the worker's own directory includes real credentials, not just an id.
There's no automatic or built-in opt-in path for a specific app either.

The pattern for an admin who explicitly wants to expose this to one app
anyway: a small, separate cron job (an admin might call it something like
`tmpfs-parity`) using a minimal image (e.g. `alpine`) that copies the
worker's identity directory to another path on a schedule:

```json
{
  "docker_image": "alpine:3.19",
  "schedule": "*/15 * * * *",
  "command": ["sh", "-c", "cp -r /etc/gustavo-worker/. /dest"],
  "volumes": ["/tmp/.gustavo-worker:/dest"],
  "running": true
}
```

The destination host path (`/tmp/.gustavo-worker` above) is a plain
choice — any real, writable path works the same way. Like any other
cron job, this one already gets `/etc/gustavo-worker` for free via the
automatic `volumes_from` behavior above; the `volumes` entry here is
what makes the *copy*'s destination a real host path other containers
can also reach.

The app that should see this data then adds the **same** host path to
its own `volumes` config, mapped to wherever it expects to read it. No
worker or Gustavo code is involved in granting this — it's a plain
Docker bind mount an admin sets up per app, same as any other volume.

**Copies everything, credentials included.** `cp -r /etc/gustavo-worker/.`
copies both `host.json` (node id, IPs, device group) *and*
`credential.json` (the worker's actual Nebula/registry passwords) into
the destination. Whatever app gets the matching volume mapping gets both
— this is a deliberate, per-app admin choice, not a Gustavo-enforced
boundary. Copying only `host.json` instead (dropping the credentials
file from the `cp`) is the safer variant if an app only needs the node
id, not the credentials.

Since a cron job runs periodically, this copy is naturally kept fresh
across restarts too — no separate "resync" step needed beyond the
schedule itself.
