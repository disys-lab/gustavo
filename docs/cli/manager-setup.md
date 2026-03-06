# Manager Node Setup

Full setup guide for the manager node: machine preparation, config files, and bringing up platform services.

For a quick summary see [Native Setup](index.md#native-setup) in the CLI overview.

---

## Step 1 — Prepare the machine

Follow the [Common prerequisites](index.md#common-prerequisites) in the CLI overview (Docker install, insecure registry config, Gustavo CLI install).

---

## Step 2 — Create `manager.env`

See the full template in [Native Setup → Manager node setup](index.md#managerenv).

Key fields to customise:

- `REGISTRY_HOST`, `MANAGER_HOST`, `REDIS_HOST`, `MONGO_HOST` — set to the manager machine's IP
- `REDIS_AUTH_TOKEN` — your Redis password
- `DREGSY_CONFIG_FILE_PATH`, `DREGSY_MAPPING_FILE_PATH` — absolute paths to the syncer config files (see below)

---

## Step 3 — Create syncer config files

The syncer (DREGSY) pulls images from a remote registry into your local registry. It requires two files.

### `dregsy_conf.yml`

```yaml
relay: skopeo
skopeo:
  binary: skopeo
  certs-dir: /etc/skopeo/certs.d

tasks:
  - name: sync-task
    interval: 30
    verbose: true
    source:
      registry: registry.hub.docker.com
      auth: <base64-encoded-credentials>   # see below
    target:
      registry: 192.168.1.100:5001
      skip-tls-verify: true
    mappings_file: /path/to/mappings_list.yml
```

Generate the `auth` value using the built-in utility:

```bash
gustavo utils syncer-auth-token
```

Follow the prompts:

```
Username: johndoe123
Password:
Repeat for confirmation:
eyJ1c2VybmFtZSI6ICJqb2huZG9lMTIzIiwgInBhc3N3b3JkIjogImZvdW50YWluaGVhZCJ9
```

Copy the output string into the `auth` field of `dregsy_conf.yml`.

### `mappings_list.yml`

Lists which images to sync from the remote registry into the local one:

```yaml
mappings:
  # Generic Docker Hub images need "library/" prepended to the source path
  - from: library/nginx
    to: nginx
    tags: ['latest']

  - from: myorg/my-app
    to: my-app
    tags: ['latest', '1.2.3']
```

Add one entry per image your edge applications require. The `to` field is the name the image will have in your local registry.

---

## Step 4 — Bring up services

```bash
export GUSTAVO_CONFIG_FILE=/path/to/manager.env

gustavo manager up registry
gustavo manager up redis
gustavo manager up mongo
gustavo manager up manager
```

!!! tip "Start order matters"
    Bring up Registry first (the syncer and manager depend on it), then Redis and MongoDB, then the Manager last.

To also start the syncer:

```bash
gustavo manager up syncer
```

---

## Step 5 — Verify

```bash
gustavo manager check
docker ps
```

Expected running containers: `registry`, `redis`, `mongo`, `manager` (and `syncer` if started).

Check the registry has been populated with synced images:

```bash
gustavo registry list
```

---

## Tear down

```bash
# Stop and remove all services
gustavo manager remove

# Or remove a single service
gustavo manager remove -s mongo
```

Answer `y` to each prompt.
