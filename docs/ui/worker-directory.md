# Worker Directory

A live table of every worker that's checked in, scoped to the device
groups you have access to (all of them, for an admin).

---

## What it shows

Each row is one worker's self-reported identity:

| Column | Description |
|---|---|
| Device Group | Which group the worker belongs to |
| Worker ID | A stable id the worker generates once, on its own, at first boot — never regenerated afterward |
| Host IP | The worker's LAN-facing IP, determined locally (requires the worker to run with host networking) |
| Remote IP | The worker's externally-visible IP, as observed by [Reporter](../configuration.md#reporter) |
| Last Updated | When this entry was last refreshed |

Non-admins only see rows for device groups they've been granted (`ro`
or `rw`) — the same permission check used everywhere else in Gustavo.

---

## Where the data comes from

Gustavo has no direct connection to this data — every row comes from
a live call to Reporter's own worker directory API on page load.
Reporter is the only thing that writes and reads this in Redis; see
[Configuration: Reporter](../configuration.md#reporter) for the `DIRECTORY_TTL_SECONDS`
setting that controls whether stale entries expire.

Population is a two-part process, neither of which happens through
this UI:

1. A worker writes its own identity locally (host IP, a self-generated
   id, its device group) on first boot, and registers it with Reporter.
2. A separate, dedicated component — deployed as a Nebula cron job,
   configured independently — periodically refreshes the remote IP and
   re-registers with Reporter. This UI has no control over that
   schedule.

---

## Deleting an entry

Each row has a **Delete** button — removes that one worker's entry
immediately, no confirmation dialog (same pattern as [Backups](backups.md)).
Requires `rw` on that device group — non-admins can only delete entries
for groups they hold `rw` on, same as every other mutating action in
Gustavo.

Deleting an entry here doesn't affect the worker itself — it's purely
a Redis record. A worker that's still running and still checking in
will simply reappear on its next refresh.
