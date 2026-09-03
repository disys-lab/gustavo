"""
/api/config — Platform configuration endpoints.

GET  /api/config                 → full config (passwords masked)
POST /api/config                 → partial/full update, persists to YAML + .env
POST /api/config/upload          → parse .env file upload, merge into config
GET  /api/config/download        → return current config as manager.env text
GET  /api/config/worker-download → worker.env, scoped to the caller's own Nebula identity
POST /api/config/mongo/rotate    → rotate the Mongo password in place (does not touch Manager)
"""
import base64
import logging
import secrets
import shutil
from datetime import datetime, timezone

import pymongo
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import PlainTextResponse

from gustavo.api import config_store
from gustavo.api.auth import require_admin, verify_firebase_token, verify_session_or_basic
from gustavo.api.session import Session

router = APIRouter()


@router.get("")
async def get_config(_session=Depends(require_admin)):
    """
    Return the current platform config with sensitive fields masked.

    Returns
    -------
    dict
        ``{"error": False, "response": <masked config dict>}``.
    """
    return {"error": False, "response": config_store.masked()}


@router.post("")
async def update_config(partial: dict, _session=Depends(require_admin)):
    """
    Merge `partial` into the platform config and persist to disk.

    Parameters
    ----------
    partial : dict
        Config keys to update.

    Returns
    -------
    dict
        ``{"error": False, "response": <masked config dict>}`` on
        success, or ``{"error": True, "response": <str(exception)>}``
        on failure.

    Notes
    -----
    Values equal to `"***"` (the mask sentinel) or empty strings are
    silently dropped, so that password fields left unchanged in the
    UI never overwrite the real stored value.
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
    Parse a `.env` file upload and merge `key=value` pairs into the config.

    Lines starting with `#` and blank lines are ignored.

    Parameters
    ----------
    file : UploadFile
        A `.env`-formatted file in the request's multipart form data.

    Returns
    -------
    dict
        ``{"error": False, "response": "Loaded N keys from <filename>"}``
        on success, or ``{"error": True, "response": <str(exception)>}``
        on failure.
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
    """
    Return the current config as a `manager.env` text file.

    Returns
    -------
    str
        `key=value` lines for every key in the config, `text/plain`.
    """
    cfg = config_store.get()
    lines = [f"{k}={v}" for k, v in cfg.items()]
    return "\n".join(lines) + "\n"


@router.get("/worker-download", response_class=PlainTextResponse)
async def download_worker_config(gpu: bool = False, session: Session = Depends(verify_session_or_basic)):
    """
    Return a `worker.env` scoped to the caller's own Nebula identity.

    Parameters
    ----------
    gpu : bool, optional
        If `True`, adds `GPU_ENABLED=true`. Only set this for a
        machine that actually has a GPU `nvidia-container-toolkit`
        can grant access to - the worker applies it to every
        container it launches on that machine.
    session : Session
        The authenticated caller, via `verify_session_or_basic`.

    Returns
    -------
    str
        `key=value` lines including `MANAGER_HOST`/`PORT`,
        `REDIS_HOST`/`PORT`/`AUTH_TOKEN`, `REGISTRY_HOST`/`PORT`/
        `AUTH_USER`/`AUTH_PASSWORD`, `WORKER_NMODE`,
        `NEBULA_USERNAME`/`PASSWORD`/`AUTH_TOKEN`, `text/plain`.

    Notes
    -----
    Scoped to the CALLER's own Nebula identity - never a different
    user's, and never generated from someone else's secret. That
    makes this safe for any authenticated user, not just admins: an
    admin's session carries the platform identity
    (`session.username`/`nebula_secret` are `NEBULA_USERNAME`/
    `PASSWORD`), so they get the platform-wide worker config; a
    regular user's session carries their own Nebula username/
    password, so their worker config only carries the same apps/
    device_groups access they already have - nothing a leaked copy
    could use to escalate beyond what they can already do.

    Accepts either a Gustavo Bearer session token (what the UI button
    uses) or plain HTTP Basic auth with the caller's own Nebula
    `username:secret` (`verify_session_or_basic`) - the latter lets a
    script pull this in one request from a remote machine, e.g.
    `curl -u alice:secret .../worker-download`, without first calling
    `/login` to mint a session token.

    Also includes `REGISTRY_AUTH_USER`/`PASSWORD` - the same Nebula
    identity, reused as the registry credential too - so a worker can
    log in to the registry-proxy (see `docs/deployment.md`'s Registry
    Authentication Proxy section) using this same `worker.env`, with
    nothing registry-specific to provision separately.
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
        f"REGISTRY_AUTH_USER={username}",
        f"REGISTRY_AUTH_PASSWORD={password}",
        f"WORKER_NMODE={cfg.get('WORKER_NMODE', '')}",
        f"NEBULA_USERNAME={username}",
        f"NEBULA_PASSWORD={password}",
        f"NEBULA_AUTH_TOKEN={auth_token}",
    ]
    if gpu:
        lines.append("GPU_ENABLED=true")
    return "\n".join(lines) + "\n"


@router.post("/mongo/rotate")
async def rotate_mongo_credential(_session=Depends(require_admin)):
    """
    Rotate the Mongo password in place, backing up `platform.yaml` first.

    Generates a new random password
    (`secrets.token_urlsafe(32)`), applies it to the existing Mongo
    user via `updateUser`, and persists it to `config_store`.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``. `error` is
        `True` if the `platform.yaml` backup fails (nothing else runs
        in that case) or the Mongo `updateUser` command fails.

    Notes
    -----
    Rotates in place - same username throughout, no new user, no
    roles to copy, nothing to drop afterward. Deliberately does not
    touch Manager: Manager's `MONGO_URL` is only ever built once, at
    container creation (see `Manager.runManager`), so it keeps using
    its already-open connection under the old password until it's
    manually removed/recreated from the Dashboard - that's the step
    that actually picks up this change.

    Backing up `platform.yaml` is a hard precondition, not
    best-effort: if it fails, nothing else runs. That backup is the
    recovery path if the new password turns out to be wrong for any
    reason - revert Mongo's password to the value in the `.bak` file,
    restore it over `platform.yaml`, restart the gustavo container so
    it reloads that file, then remove/recreate Manager again.
    """
    cfg = config_store.get()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_path = config_store.CONFIG_PATH.with_name(
        f"{config_store.CONFIG_PATH.name}.bak-{timestamp}-pre-mongo-rotate"
    )
    try:
        shutil.copy2(config_store.CONFIG_PATH, backup_path)
    except Exception as exc:
        logging.error(f"mongo credential rotation: platform.yaml backup failed: {exc}")
        return {"error": True, "response": f"Failed to rotate credential: could not back up platform.yaml ({exc})"}

    username = cfg.get("MONGO_USERNAME", "")
    new_password = secrets.token_urlsafe(32)
    try:
        client = pymongo.MongoClient(
            host=cfg.get("MONGO_HOST", ""),
            port=int(cfg.get("MONGO_PORT", 27017) or 27017),
            username=username,
            password=cfg.get("MONGO_PASSWORD", ""),
            authSource="admin",
            serverSelectionTimeoutMS=5000,
        )
        client.admin.command("updateUser", username, pwd=new_password)
        client.close()
    except Exception as exc:
        logging.error(f"mongo credential rotation: password change failed: {exc}")
        return {"error": True, "response": f"Failed to rotate credential: could not update Mongo password ({exc})"}

    config_store.update({"MONGO_PASSWORD": new_password})
    return {
        "error": False,
        "response": "Mongo credential rotated. Remove and recreate the Manager service to apply it.",
    }
