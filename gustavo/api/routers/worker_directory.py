"""
/api/worker-directory — proxy onto gustavo-reporter's worker identity directory.

GET    /api/worker-directory                          → list all entries across every device group the caller can see
DELETE /api/worker-directory/{device_group}/{node_id}  → remove one worker's entry

Gustavo holds no Redis connection of its own for this data - reporter
is the only thing that talks to Redis for the directory, same as it's
the only thing that writes worker status reports. Every call here is a
synchronous HTTP round-trip to reporter's own `/api/directory/...`
endpoints, authenticated with the caller's own Nebula credential
(session.nebula_secret) - the exact same Basic auth a worker itself
uses, not a separate Gustavo-to-reporter credential.
"""
import logging

import requests
from fastapi import APIRouter, Depends, HTTPException

from gustavo.api import config_store, nebula_auth
from gustavo.api.auth import verify_firebase_token
from gustavo.api.dependencies import _build_composer
from gustavo.api.session import Session

router = APIRouter()


def _reporter_base_url(cfg: dict) -> str:
    """Reporter is always reached internally over plain http - see runReporter (gustavo/src/Manager.py)."""
    return f"http://{cfg.get('REPORTER_HOST', '')}:{cfg.get('REPORTER_PORT', '')}"


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
        Entries from device groups reporter itself refuses (e.g. a
        stale grant reporter no longer honors) are silently skipped
        rather than failing the whole request.

    Notes
    -----
    One HTTP call to reporter per visible device group - reporter has
    no "all groups at once" endpoint, since its own authorization is
    per-device-group. Acceptable at the scale this directory is meant
    for; would need reporter-side batching if that stops being true.
    """
    cfg = config_store.get()
    base_url = _reporter_base_url(cfg)
    auth = (session.username, session.nebula_secret)
    entries = []
    for device_group in _visible_device_groups(cfg, session):
        try:
            resp = requests.get(f"{base_url}/api/directory/{device_group}", auth=auth, timeout=10)
        except requests.exceptions.RequestException as exc:
            logging.error(f"list_worker_directory: reporter unreachable for '{device_group}': {exc}")
            continue
        if resp.status_code != 200:
            continue
        body = resp.json()
        if body.get("error"):
            continue
        for entry in body.get("response", []):
            entries.append({**entry, "device_group": device_group})
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
    they hold rw on.
    """
    cfg = config_store.get()
    if not session.is_admin and nebula_auth.compute_permissions(cfg, session.username)["device_groups"].get(device_group) != "rw":
        raise HTTPException(status_code=403, detail=f"Not permitted to modify device group '{device_group}'")

    base_url = _reporter_base_url(cfg)
    auth = (session.username, session.nebula_secret)
    try:
        resp = requests.delete(f"{base_url}/api/directory/{device_group}/{node_id}", auth=auth, timeout=10)
    except requests.exceptions.RequestException as exc:
        logging.error(f"remove_worker_directory_entry failed: {exc}")
        return {"error": True, "response": str(exc)}

    if resp.status_code != 200:
        return {"error": True, "response": f"reporter returned {resp.status_code}: {resp.text}"}
    return {"error": False, "response": "deleted"}
