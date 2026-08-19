"""
/api/config — Platform configuration endpoints.

GET  /api/config          → full config (passwords masked)
POST /api/config          → partial/full update, persists to YAML + .env
POST /api/config/upload   → parse .env file upload, merge into config
GET  /api/config/download → return current config as manager.env text
"""
import logging
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import PlainTextResponse

from gustavo.api import config_store
from gustavo.api.auth import require_admin

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
