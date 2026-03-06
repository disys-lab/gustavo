# Web UI

The Gustavo web interface is built with **Next.js 14** (App Router), **Tailwind CSS**, and **shadcn/ui** components. It communicates exclusively with the FastAPI backend via `/api/*` rewrites.

---

## Technology stack

| Library | Version | Purpose |
|---------|---------|---------|
| Next.js | 14.2 | App Router, server-side rendering, API proxy |
| React | 18 | Component model |
| TypeScript | 5 | Type safety |
| Tailwind CSS | 3.4 | Utility-first styling |
| shadcn/ui | latest | Radix UI-based component library |
| TanStack Query | v5 | Server state management, caching |
| React Hook Form + Zod | — | Form validation |
| Recharts | — | CPU/memory time-series charts |
| Monaco Editor | — | YAML editor for syncer config |
| date-fns | — | Relative timestamps |
| Lucide React | — | Icons |
| Axios | — | HTTP client with auto-auth headers |

---

## Route structure

```
/                         → redirects to /dashboard
/login                    → Firebase auth (when AUTH_ENABLED=true)
/dashboard                → Overview: services, vitals, stats, activity
/apps                     → App list + create
/apps/[name]              → Edit single app
/registry                 → Registry image browser
/device-groups            → Device group management
/monitoring               → Real-time CPU/memory charts
/backups                  → Redis + registry backup management
/settings                 → Platform configuration
/settings/syncer          → DREGSY YAML editor
/manager                  → Service control table (also embedded in Dashboard)
```

---

## Native Installation

Running the full stack natively (FastAPI backend + Next.js UI) without Docker. For most deployments use the [Docker quickstart](../quickstart.md). For CLI-only setup see [CLI Native Setup](../cli/index.md#native-setup).

### System requirements

| Requirement | Minimum |
|-------------|---------|
| OS | Ubuntu 22.04 / macOS 13 / WSL2 |
| Python | 3.11 |
| Node.js | 20 LTS |
| Docker Engine | 20.10 (for managing Nebula services) |

### Step 1 — Install the Python package

**From pip (stable):**

```bash
pip3 install --no-cache-dir --extra-index-url https://pypi.fury.io/osu-home-stri/ gustavo
```

**From source (latest):**

```bash
git clone https://github.com/paritoshpr/gustavo.git
cd gustavo
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Verify:

```bash
gustavo --version
gustavo --help
```

### Step 2 — Install FastAPI backend dependencies

```bash
pip install -r gustavo/api/requirements-api.txt
```

### Step 3 — Build the Next.js UI

```bash
cd gustavo-ui
npm ci
npm run build
cd ..
```

This produces `gustavo-ui/.next/standalone/` — a self-contained Node.js server.

### Step 4 — Create the configuration file

```bash
mkdir -p /etc/gustavo
```

Create `/etc/gustavo/platform.yaml`:

```yaml
MANAGER_HOST: 127.0.0.1
MANAGER_PORT: "80"
REGISTRY_HOST: 127.0.0.1
REGISTRY_PORT: "5001"
REDIS_HOST: 127.0.0.1
REDIS_PORT: "6379"
REDIS_AUTH_TOKEN: your-redis-token
MONGO_HOST: 127.0.0.1
MONGO_PORT: "27017"
MONGO_USERNAME: nebula
MONGO_PASSWORD: nebula
NEBULA_USERNAME: nebula
NEBULA_PASSWORD: nebula
NEBULA_AUTH_TOKEN: bmVidWxhOm5lYnVsYQ==
NEBULA_PROTOCOL: http
```

Or leave it empty and configure everything from the Settings page after starting.

### Step 5 — Start the FastAPI backend

```bash
export GUSTAVO_API_CONFIG=/etc/gustavo/platform.yaml
export AUTH_ENABLED=false

uvicorn gustavo.api.main:app --host 127.0.0.1 --port 8000
```

Verify:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

### Step 6 — Start the Next.js frontend

In a separate terminal:

```bash
export FASTAPI_URL=http://127.0.0.1:8000
export HOSTNAME=0.0.0.0
export PORT=3000

node gustavo-ui/.next/standalone/server.js
```

Open [http://localhost:3000](http://localhost:3000).

### Step 7 — Running with Supervisor (production)

For a managed process setup that survives reboots:

```bash
pip install supervisor
```

Create `/etc/supervisord.conf`:

```ini
[supervisord]
nodaemon=true
logfile=/var/log/supervisord.log

[program:gustavo-api]
command=/path/to/.venv/bin/uvicorn gustavo.api.main:app --host 127.0.0.1 --port 8000
directory=/path/to/gustavo
environment=GUSTAVO_API_CONFIG="/etc/gustavo/platform.yaml",AUTH_ENABLED="false"
autostart=true
autorestart=true
stdout_logfile=/var/log/gustavo-api.log
stderr_logfile=/var/log/gustavo-api.log

[program:gustavo-ui]
command=node /path/to/gustavo-ui/.next/standalone/server.js
directory=/path/to/gustavo-ui/.next/standalone
environment=HOSTNAME="0.0.0.0",PORT="3000",FASTAPI_URL="http://127.0.0.1:8000"
autostart=true
autorestart=true
stdout_logfile=/var/log/gustavo-ui.log
stderr_logfile=/var/log/gustavo-ui.log
```

Start:

```bash
supervisord -n -c /etc/supervisord.conf
```

---

## State management

**Server state** is managed by TanStack React Query. All API calls go through typed functions in `lib/api/`.

**Auth state** lives in `AuthContext` (`lib/context/AuthContext.tsx`):
- Fetches runtime auth status from `/api/auth/status`
- Stores the Firebase ID token in `localStorage` and a browser cookie
- `isAuthenticated` is `true` immediately when `AUTH_ENABLED=false`

**Config state** lives in `ConfigContext` (`lib/context/ConfigContext.tsx`):
- Fetches platform config from `/api/config` (gated on `isAuthenticated`)
- Caches in `localStorage` as optimistic fallback
- Exposes `save(partial)` for the Settings page

---

## API client

All HTTP calls go through `lib/api/client.ts` — an Axios instance that:
- Injects `Authorization: Bearer <token>` from `localStorage` on every request
- Redirects to `/login` on 401 (when `AUTH_ENABLED=true` and not already on `/login`)

---

## Pages

| Page | Description |
|------|-------------|
| [Dashboard](dashboard.md) | Platform overview with services, vitals, activity |
| [Apps](apps.md) | Application CRUD with YAML import/export |
| [Device Groups](device-groups.md) | Group management and app assignment |
| [Monitoring](monitoring.md) | Live CPU/memory charts and container stats |
| [Backups](backups.md) | Redis and registry backup management |
| [Settings](settings.md) | Platform configuration editor |

---

## Component library

See [Component Reference](components.md) for a full list of reusable components.
