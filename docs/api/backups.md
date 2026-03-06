# Backups API

Create, list, restore, and delete backups for Redis (RDB files) and the local Docker registry (tar archives).

::: gustavo.api.routers.backups

---

## Redis backups

Redis backups are `.rdb` files stored in `REDIS_BKP_DIR`. Each backup is timestamped.

### `GET /api/backups/redis`

List all Redis backup files.

**Response:**

```json
{
  "error": false,
  "response": {
    "backups": [
      { "filename": "redis_backup_20260306_151045.rdb", "size_mb": 2.4, "created": "2026-03-06T15:10:45" }
    ]
  }
}
```

---

### `POST /api/backups/redis/create`

Trigger a background Redis backup (BGSAVE). Returns a `job_id`.

**Response:**

```json
{ "error": false, "response": { "job_id": "550e8400-..." } }
```

Poll `GET /api/services/jobs/{job_id}` for completion.

---

### `POST /api/backups/redis/restore/{filename}`

Restore a Redis backup. This is a destructive operation:

1. Stop the Redis container
2. Copy the backup `.rdb` to the Redis data directory
3. Restart Redis

Returns a `job_id`. Poll for completion.

```
POST /api/backups/redis/restore/redis_backup_20260306_151045.rdb
```

---

### `DELETE /api/backups/redis/{filename}`

Delete a Redis backup file.

---

## Registry backups

Registry backups are tar archives of the registry data directory, stored in `REGISTRY_BKP_DIR`.

### `GET /api/backups/registry`

List all registry backup archives.

---

### `POST /api/backups/registry/create`

Create a registry backup. Stops the registry, tars the data directory, restarts the registry. Returns a `job_id`.

---

### `POST /api/backups/registry/restore/{filename}`

Restore a registry backup. Returns a `job_id`.

---

### `DELETE /api/backups/registry/{filename}`

Delete a registry backup archive.

---

## Configuration keys used

| Key | Description |
|-----|-------------|
| `REDIS_BKP_DIR` | Directory for Redis RDB backup files |
| `REGISTRY_BKP_DIR` | Directory for registry tar archives |
| `REGISTRY_DATA_PATH` | Live registry data directory (e.g. `/data/registry/docker`). Falls back to `{REGISTRY_BKP_DIR}/docker` if unset. |
