"""
/api/worker-directory — reads the worker identity directory gustavo-reporter
writes to Redis, directly.

GET    /api/worker-directory                          → list all entries across every device group the caller can see
DELETE /api/worker-directory/{device_group}/{node_id}  → remove one worker's entry

Gustavo already resolves the caller's own identity and device-group
permissions before ever touching this data (verify_firebase_token +
compute_permissions/_visible_device_groups below). Going back out over
HTTP to reporter's own /api/directory endpoints only to have reporter
re-verify that same credential a second time - its own full
compute_permissions cascade against Nebula Manager, once per device
group in the loop - added a slow, redundant round trip on top of an
already-resolved auth decision, and was the actual cause of
"reporter unreachable ... Read timed out" errors here even when every
worker and reporter itself were perfectly healthy.

Gustavo has held its own REDIS_HOST/PORT/AUTH_TOKEN config since the
original vitals/container cache (Cache.py, via cache_shim.build_cache) -
this reads the exact same Redis directly, in the exact key/value shape
reporter's own redis_store.py writes it, with no reporter round trip
(and no second auth cascade) at all.
"""
import logging
import pickle

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException

from gustavo.api import config_store, nebula_auth
from gustavo.api.auth import verify_firebase_token
from gustavo.api.dependencies import _build_composer
from gustavo.api.session import Session

router = APIRouter()

# Must match gustavo-reporter's own DIRECTORY_PREFIX default (reporter/config.py).
# Gustavo never passes a DIRECTORY_PREFIX override when launching reporter (see
# Manager.runReporter, which only forwards DIRECTORY_TTL_SECONDS) - so reporter
# always runs on this default in practice, the same way CACHE_PREFIX's
# "gustavo-reports" default is relied on rather than threaded through config.
_DIRECTORY_PREFIX = "gustavo-directory"


def _redis_client(cfg: dict) -> redis.Redis:
    """Fresh async Redis client from the current config - same host/port/auth Cache.py already uses."""
    return redis.Redis(
        host=cfg.get("REDIS_HOST", ""), port=int(cfg.get("REDIS_PORT", 6379) or 6379),
        password=cfg.get("REDIS_AUTH_TOKEN", ""),
    )


def _visible_device_groups(cfg: dict, session: Session) -> list[str]:
    """
    All device group names the caller may view - every group for an
    admin, only granted ones (ro or rw) for anyone else.
    """
    comp = _build_composer(cfg)
    result = comp.nebulaObj.list_device_groups()
    if result.get("status_code") != 200:
        return []
    all_groups = result.get("reply", {}).get("device_groups", [])
    if session.is_admin:
        return all_groups
    perms = nebula_auth.compute_permissions(cfg, session.username)
    return [g for g in all_groups if g in perms["device_groups"]]


@router.get("")
async def list_worker_directory(session: Session = Depends(verify_firebase_token)):
    """
    List the worker directory for every device group the caller can see.

    Parameters
    ----------
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": [{"device_group": ..., "node_id": ...,
        "host_ip": ..., "remote_ip": ..., "updated_at": ...}, ...]}``.

    Notes
    -----
    Reads Redis directly - see module docstring for why this doesn't
    go through reporter's HTTP API. A device group with a Redis error
    mid-scan is silently skipped rather than failing the whole request,
    same tolerance the old reporter-HTTP version had for a device group
    reporter itself refused.
    """
    cfg = config_store.get()
    client = _redis_client(cfg)
    entries = []
    try:
        for device_group in _visible_device_groups(cfg, session):
            try:
                async for key in client.scan_iter(match=f"{_DIRECTORY_PREFIX}_{device_group}@*"):
                    value = await client.get(key)
                    if value is not None:
                        entries.append({**pickle.loads(value), "device_group": device_group})
            except redis.RedisError as exc:
                logging.error(f"list_worker_directory: redis error for '{device_group}': {exc}")
                continue
    finally:
        await client.aclose()
    return {"error": False, "response": entries}


@router.delete("/{device_group}/{node_id}")
async def remove_worker_directory_entry(
    device_group: str,
    node_id: str,
    session: Session = Depends(verify_firebase_token),
):
    """
    Remove one worker's entry from the directory.

    Parameters
    ----------
    device_group : str
        The device group the entry belongs to.
    node_id : str
        The worker's own id.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.

    Raises
    ------
    HTTPException
        403 if the caller isn't admin and isn't granted rw on `device_group`.

    Notes
    -----
    rw-gated like every other mutating action in this codebase - not
    admin-only. A non-admin can delete entries only for device groups
    they hold rw on. Deletes the Redis key directly - see module
    docstring.
    """
    cfg = config_store.get()
    if not session.is_admin and nebula_auth.compute_permissions(cfg, session.username)["device_groups"].get(device_group) != "rw":
        raise HTTPException(status_code=403, detail=f"Not permitted to modify device group '{device_group}'")

    client = _redis_client(cfg)
    try:
        await client.delete(f"{_DIRECTORY_PREFIX}_{device_group}@{node_id}")
    except redis.RedisError as exc:
        logging.error(f"remove_worker_directory_entry failed: {exc}")
        return {"error": True, "response": str(exc)}
    finally:
        await client.aclose()
    return {"error": False, "response": "deleted"}
