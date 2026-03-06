# `gustavo utils`

Utility commands.

```
Usage: gustavo utils [OPTIONS] COMMAND [ARGS]...

  utility commands
```

---

## Commands

### `syncer-auth-token`

Generate a base64-encoded auth token for the DREGSY syncer service.

```bash
gustavo utils syncer-auth-token -u USERNAME -p PASSWORD
```

| Option | Description |
|--------|-------------|
| `-u` / `--username` | Registry username |
| `-p` / `--password` | Registry password |

Output is a base64 JSON string suitable for use in the DREGSY config:

```json
{"username": "myuser", "password": "mypassword"}
```

This token is used in `dregsy_conf.yml` under the `auth` field for registry mirror entries.

---

## `gustavo prune`

Remove unused Docker images from all devices in a device group.

```bash
gustavo prune device_group -n GROUP_NAME
```

| Option | Description |
|--------|-------------|
| `-n` / `--name` | Device group name to prune |

Calls `Composer.prune_device_group_images()` for each app in the group, triggering image pruning on all worker nodes.
