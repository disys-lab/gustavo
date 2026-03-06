# Native Installation

!!! warning "Docker is recommended"
    For most users, the [Docker quickstart](quickstart.md) is faster and simpler. Native installation is intended for contributors, CI pipelines, or environments without Docker.

---

## CLI-only installation

If you only need the `gustavo` CLI to manage platform services and workers — without the web UI — follow the [Native Setup guide](cli/index.md#native-setup) in the CLI reference. It covers:

- Installing Docker and configuring the insecure registry
- Installing the Gustavo CLI via pip
- Creating `manager.env` / `worker.env` config files
- Bringing up manager services and worker nodes

---

## Full stack installation

For running the **full stack** (FastAPI backend + Next.js UI) natively, see the [Web UI Native Installation](ui/index.md#native-installation) guide, which covers all 7 steps:

1. Install the Python package
2. Install FastAPI backend dependencies
3. Build the Next.js UI
4. Create the configuration file
5. Start the FastAPI backend
6. Start the Next.js frontend
7. Running with Supervisor (production)

