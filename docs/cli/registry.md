# `gustavo registry`

Query the local Docker registry.

```
Usage: gustavo registry [OPTIONS] COMMAND [ARGS]...

  Manage local registry.
```

---

## Commands

### `list`

List images available in the local registry.

```bash
gustavo registry list [-n IMAGE_NAME] [-t TAG]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-n` / `--name` | _(none)_ | Filter by image name |
| `-t` / `--tag` | _(none)_ | Filter by tag |

Examples:

```bash
# List all images
gustavo registry list

# Check if a specific image:tag exists
gustavo registry list -n my_app -t latest
```

Queries the registry v2 API at `http://{REGISTRY_HOST}:{REGISTRY_PORT}/v2/`.

---

## Configuration keys used

| Key | Description |
|-----|-------------|
| `REGISTRY_HOST` | Registry IP or hostname |
| `REGISTRY_PORT` | Registry API port |
