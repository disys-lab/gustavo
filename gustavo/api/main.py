"""
Gustavo FastAPI application factory.

Start with:
    uvicorn gustavo.api.main:app --host 0.0.0.0 --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gustavo.api import config_store
from gustavo.api.routers import (
    config as config_router,
    services as services_router,
    apps as apps_router,
    device_groups as dg_router,
    monitoring as monitoring_router,
    backups as backups_router,
    auth as auth_router,
    users as users_router,
    registry as registry_router,
)

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load config on startup."""
    logging.info("Gustavo API starting — loading platform config …")
    config_store.load()
    logging.info(f"Config loaded from {config_store.CONFIG_PATH}")
    yield
    logging.info("Gustavo API shutting down.")


app = FastAPI(
    title="Gustavo API",
    description="FastAPI backend for the Gustavo container orchestration UI",
    version="2.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the Next.js dev server and the same-origin production proxy
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten in production via env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router.router,       prefix="/api/auth",          tags=["auth"])
app.include_router(config_router.router,     prefix="/api/config",        tags=["config"])
app.include_router(services_router.router,   prefix="/api/services",      tags=["services"])
app.include_router(apps_router.router,       prefix="/api/apps",          tags=["apps"])
app.include_router(dg_router.router,         prefix="/api/device-groups", tags=["device-groups"])
app.include_router(monitoring_router.router, prefix="/api/monitoring",    tags=["monitoring"])
app.include_router(backups_router.router,    prefix="/api/backups",       tags=["backups"])
app.include_router(users_router.router,      prefix="/api/users",         tags=["users"])
app.include_router(registry_router.router,   prefix="/api/registry",      tags=["registry"])


@app.get("/health")
async def health():
    return {"status": "ok"}
