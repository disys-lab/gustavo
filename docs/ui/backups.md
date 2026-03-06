# Backups

Create and manage point-in-time backups of Redis (RDB snapshots) and the local Docker registry (tar archives).

---

## Layout

The Backups page has two tabs: **Redis** and **Registry**. Each tab shows the same controls for its respective service.

---

## Redis backups

Redis backups are `.rdb` snapshot files stored in `REDIS_BKP_DIR` (default: `/tmp/`).

### Creating a backup

Click **Create Backup**. The BGSAVE command is sent to Redis and a background job starts. A spinner shows while the job runs. On completion, the new backup appears in the table with a timestamp.

### Restoring a backup

Select a backup row and click **Restore**. A confirmation dialog warns that this will:
1. Stop the Redis container
2. Replace the active RDB file
3. Restart Redis

This operation runs in the background. A spinner shows during the restore.

### Deleting a backup

Select a row and click **Delete**. No confirmation dialog — the file is removed immediately.

---

## Registry backups

Registry backups are `.tar.gz` archives of the registry data directory. Stored in `REGISTRY_BKP_DIR`.

The live data path is configured via `REGISTRY_DATA_PATH` in Settings. If not set, defaults to `{REGISTRY_BKP_DIR}/docker`.

### Creating a backup

Click **Create Backup**. The registry container is stopped, the data directory is archived, and the registry restarts. Background job with polling.

### Restoring a backup

Stops the registry, extracts the archive over the live data directory, restarts the registry. Background job.

### Deleting a backup

Removes the archive file.

---

## Timestamps

Backup filenames include a UTC timestamp: `redis_backup_20260306_151045.rdb`. The table shows the timestamp in your local timezone with a relative label (e.g. "2 hours ago"). Hover the relative label to see the exact UTC time.
