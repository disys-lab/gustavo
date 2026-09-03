# Gustavo

**Gustavo** is a container orchestration platform, built for the NASA HOME STRI Project. It provides a web-based dashboard and REST API to manage the full lifecycle of platform services, applications, device groups, backups, and real-time monitoring across distributed edge nodes.

---

## Architecture

```
┌───────────────────────────────┐
│   Docker Container            │
│  ┌───────────────┐  ┌────────┐ │
│  │  Next.js UI   │  │ FastAPI│ │
│  │   port 3000   │──│:8000   │ │
│  └───────────────┘  └────────┘ │
│         │                  │   │
│         └──── /api/* ──────┘   │
└────────────────────────────────┘
```

The single container exposes **only port 3000** (Next.js). FastAPI listens on `127.0.0.1:8000` (loopback only) and is proxied by Next.js rewrites.

---

## Quick Links

| Goal | Go to |
|------|-------|
| Get running in 5 minutes | [Quickstart](quickstart.md) |
| Install natively on Linux/Mac | [Native Installation](installation.md) |
| Deploy an app end-to-end | [End-to-End Tutorial](tutorial.md) |
| All configuration keys | [Configuration Reference](configuration.md) |
| CLI command reference | [CLI Reference](cli/index.md) |
| REST API reference | [FastAPI Backend](api/index.md) |
| Web UI guide | [Web UI](ui/index.md) |
| Developer Guide | [Contributing](contributing.md) |

---

## Key Features

- **Platform Services** — Launch, stop, restart, and monitor Redis, MongoDB, Docker Registry, Nebula Manager, and the Syncer service
- **App Management** — Create, update, and delete Nebula applications with full YAML import/export support
- **Device Groups** — Organise worker nodes into logical groups and assign apps to them
- **Real-time Monitoring** — Live CPU, memory, and disk metrics streamed from workers via Server-Sent Events
- **Backup & Restore** — Timestamped Redis RDB and registry data backups with one-click restore
- **Optional Authentication** — Firebase-based authentication toggled by a single environment variable
