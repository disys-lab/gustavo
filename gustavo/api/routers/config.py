"""
/api/config — Platform configuration endpoints.

GET  /api/config                 → full config (passwords masked)
POST /api/config                 → partial/full update, persists to YAML + .env
POST /api/config/upload          → parse .env file upload, merge into config
GET  /api/config/download        → return current config as manager.env text
GET  /api/config/worker-download → worker.env, scoped to the caller's own Nebula identity
"""
import base64
import logging
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import PlainTextResponse

from gustavo.api import config_store
from gustavo.api.auth import require_admin, verify_firebase_token, verify_session_or_basic
from gustavo.api.session import Session

router = APIRouter()


@router.get("")
async def get_config(_session=Depends(require_admin)):
    """Return the current platform config with sensitive fields masked."""
    return {"error": False, "response": config_store.masked()}


@router.post("")
async def update_config(partial: dict, _session=Depends(require_admin)):
    """Merge *partial* into the platform config and persist to disk.

    Values equal to '***' (the mask sentinel) or empty strings are silently
    dropped so that password fields left unchanged in the UI never overwrite
    the real stored value.
    """
    try:
        filtered = {k: v for k, v in partial.items() if v not in ("***", "", None)}
        config_store.update(filtered)
        return {"error": False, "response": config_store.masked()}
    except Exception as exc:
        logging.error(f"config update failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("/upload")
async def upload_config(
    file: UploadFile = File(...),
    _session=Depends(require_admin),
):
    """
    Parse a .env file upload and merge key=value pairs into the config.
    Lines starting with '#' and blank lines are ignored.
    """
    try:
        partial: dict = {}
        content = await file.read()
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(b"#"):
                continue
            if b"=" in line:
                key, _, value = line.partition(b"=")
                partial[key.decode().strip()] = value.decode().strip()
        config_store.update(partial)
        return {"error": False, "response": f"Loaded {len(partial)} keys from {file.filename}"}
    except Exception as exc:
        logging.error(f"config upload failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.get("/download", response_class=PlainTextResponse)
async def download_config(_session=Depends(require_admin)):
    """Return the current config as a manager.env text file."""
    cfg = config_store.get()
    lines = [f"{k}={v}" for k, v in cfg.items()]
    return "\n".join(lines) + "\n"


@router.get("/worker-download", response_class=PlainTextResponse)
async def download_worker_config(session: Session = Depends(verify_session_or_basic)):
    """
    Return a worker.env scoped to the CALLER's own Nebula identity — never
    a different user's, and never generated from someone else's secret. That
    makes this safe for any authenticated user, not just admins: an admin's
    session carries the platform identity (session.username/nebula_secret
    are NEBULA_USERNAME/PASSWORD), so they get the platform-wide worker
    config; a regular user's session carries their own Nebula
    username/password, so their worker config only carries the same
    apps/device_groups access they already have — nothing a leaked copy
    could use to escalate beyond what they can already do.

    Accepts either a Gustavo Bearer session token (what the UI button uses)
    or plain HTTP Basic auth with the caller's own Nebula username:secret
    (verify_session_or_basic) — the latter lets a script pull this in one
    request from a remote machine, e.g. `curl -u alice:secret .../worker-download`,
    without first calling /login to mint a session token.
    """
    cfg = config_store.get()
    username = session.username
    password = session.nebula_secret
    auth_token = base64.b64encode(f"{username}:{password}".encode()).decode()
    lines = [
        f"MANAGER_HOST={cfg.get('MANAGER_HOST', '')}",
        f"MANAGER_PORT={cfg.get('MANAGER_PORT', '')}",
        f"REDIS_HOST={cfg.get('REDIS_HOST', '')}",
        f"REDIS_PORT={cfg.get('REDIS_PORT', '')}",
        f"REDIS_AUTH_TOKEN={cfg.get('REDIS_AUTH_TOKEN', '')}",
        f"REGISTRY_HOST={cfg.get('REGISTRY_HOST', '')}",
        f"REGISTRY_PORT={cfg.get('REGISTRY_PORT', '')}",
        f"WORKER_NMODE={cfg.get('WORKER_NMODE', '')}",
        f"NEBULA_USERNAME={username}",
        f"NEBULA_PASSWORD={password}",
        f"NEBULA_AUTH_TOKEN={auth_token}",
    ]
    return "\n".join(lines) + "\n"
