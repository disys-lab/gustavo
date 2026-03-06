# `gustavo device-group`

Manage device groups — logical collections of worker nodes that share the same deployed application set.

```
Usage: gustavo device-group [OPTIONS] COMMAND [ARGS]...

  Manage device groups.
```

---

## Commands

### `list`

List all device groups and their members.

```bash
gustavo device-group list
```

---

### `create`

Create a new device group, optionally seeding it with applications.

```bash
gustavo device-group create -n GROUP_NAME [-a APP_NAME ...]
```

| Option | Required | Description |
|--------|----------|-------------|
| `-n` / `--name` | Yes | Device group name |
| `-a` / `--app` | No | App name(s) to include (repeatable) |

Examples:

```bash
# Empty group
gustavo device-group create -n production

# Group with apps
gustavo device-group create -n production -a my_app -a another_app
```

---

### `update`

Add or update applications in a device group.

```bash
gustavo device-group update -n GROUP_NAME -a APP_NAME
```

---

### `delete`

Delete a device group.

```bash
gustavo device-group delete -n GROUP_NAME
```

---

## Relationship to apps

A Nebula app can belong to multiple device groups. Workers in a group pull and run all apps assigned to that group.

```
App (test_linreg)
  ├── device-group: production   → runs on production workers
  └── device-group: staging      → runs on staging workers
```

Use `gustavo device-group update` to add an app to additional groups, or the web UI's Device Groups page for bulk membership management.
