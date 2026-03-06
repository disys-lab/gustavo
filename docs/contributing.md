# Developer Guide

This guide covers setting up a local development environment for working on Gustavo. For deployment, see the [Quickstart](quickstart.md).

---

## Repository layout

```
gustavo/
  gustavo/
    api/            FastAPI backend (routers, config_store, background jobs)
    src/            Core Python library (Manager, Composer, Cache, NebulaBase)
    gustavo.py      CLI entry point (Click)
  gustavo-ui/       Next.js 14 frontend
  Dockerfile        Single-image production build
  docker-compose.yml
```

**Constraint:** Do not modify `gustavo/src/` unless you own those classes. The API layer wraps them without changing their interface.

---

## Prerequisites

- Python 3.11+
- Node.js 20 LTS + npm
- Docker (for running Nebula services during development)
- A running Nebula Manager (or use the CLI to bring one up locally)

---

## Backend (FastAPI)

```bash
# Clone and set up a virtual environment
git clone https://github.com/paritoshpr/gustavo.git
cd gustavo
python -m venv .venv
source .venv/bin/activate

# Install the core library in editable mode
pip install -e .

# Install API dependencies
pip install -r gustavo/api/requirements-api.txt
```

Start the dev server:

```bash
export GUSTAVO_API_CONFIG=/path/to/platform.yaml
export AUTH_ENABLED=false

uvicorn gustavo.api.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Frontend (Next.js)

```bash
cd gustavo-ui
npm ci
```

Start the dev server (hot reload):

```bash
FASTAPI_URL=http://127.0.0.1:8000 npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Next.js rewrites `/api/*` to the FastAPI server via `next.config.mjs`, so no CORS configuration is needed.

---

## Building the Docker image

```bash
docker build -t gustavo:local .
```

Run it:

```bash
docker run -p 3000:3000 \
  -v ./config:/etc/gustavo \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e GUSTAVO_API_CONFIG=/etc/gustavo/platform.yaml \
  -e AUTH_ENABLED=false \
  gustavo:local
```

---

## CI/CD

GitHub Actions workflows trigger on commit message tags:

| Tag | Effect |
|-----|--------|
| `#dockerbuild` | Build and push Docker image to GHCR |
| `#macbuild` | Build macOS binary |
| `#linuxbuild` | Build Linux binary |
| `#bump #patch` | Increment patch version |
| `#bump #minor` | Increment minor version |

Docs deploy automatically on push to `main` when files under `docs/` or `mkdocs.yml` change. See `.github/workflows/docs.yml`.

---

## Adding a new API route

1. Create `gustavo/api/routers/my_feature.py` with an `APIRouter`
2. Register it in `gustavo/api/main.py`: `app.include_router(my_router, prefix="/api")`
3. Add typed functions to `gustavo-ui/lib/api/my_feature.ts`
4. Use `useQuery` / `useMutation` from TanStack Query in your page component

All responses must follow the existing contract: `{"error": bool, "response": str | dict}`.
