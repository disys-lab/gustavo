"""
/api/cron-jobs — Nebula cron job CRUD + YAML export.

GET    /api/cron-jobs                     → list all cron jobs (filtered to the caller's grants for non-admins)
GET    /api/cron-jobs/{name}              → get single cron job config
POST   /api/cron-jobs                     → create cron job (non-admins: auto-granted rw on their own group)
PUT    /api/cron-jobs/{name}              → update cron job (non-admins: enforced by Nebula's own rw check)
DELETE /api/cron-jobs/{name}              → delete cron job (removes from all DGs first)
GET    /api/cron-jobs/{name}/yaml         → export cron job config as YAML text

Structural mirror of apps.py's own CRUD router - same permission model,
same Composer.handleAsset/image-fallback pattern, same non-admin-token
enforcement for writes. See apps.py's own module docstring for the
permission-model rationale, unchanged here.
"""
import logging
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from gustavo.api import config_store, nebula_auth
from gustavo.api.auth import verify_firebase_token
from gustavo.api.dependencies import _build_composer, _build_composer_for
from gustavo.api.session import Session

router = APIRouter()


def _handle_cron_job_with_image_fallback(comp, name: str, mode: str, config: dict) -> dict:
    """
    Call `comp.handleAsset("cron_job", ...)`, falling back to a direct SDK call if the image isn't in the local registry.

    Mirrors apps.py's `_handleAsset_with_image_fallback` exactly, for the
    same reason: `Composer.handleAsset` calls `checkImageExists`, which
    raises `IndexError` if `config["docker_image"]` doesn't have the local
    registry's `host:port/` prefix (e.g. an image pulled from a remote
    registry via the syncer). Kept as a separate function rather than
    generalizing the apps.py one, matching this feature's own established
    "duplicate rather than risk shared code" choice for the Composer-level
    changes it depends on.

    Parameters
    ----------
    comp : Composer
    name : str
        Cron job name.
    mode : str
        `"create"` or `"update"` - `"delete"` has no fallback path.
    config : dict
        The cron job config to create/update.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.
    """
    try:
        return comp.handleAsset("cron_job", name, mode, config)
    except IndexError:
        logging.warning(
            f"handleAsset '{mode}' for cron_job '{name}': checkImageExists failed (image not in local registry), "
            "falling back to direct SDK call"
        )
        if mode == "create":
            reply = comp.nebulaObj.create_cron_job(name, config)
            if reply.get("status_code") == 200:
                return {"error": False, "response": f"created cron_job: {name}"}
        elif mode == "update":
            reply = comp.nebulaObj.update_cron_job(name, config)
            if reply.get("status_code") == 202:
                return {"error": False, "response": f"updated cron_job: {name}"}
        else:
            return {"error": True, "response": f"image not in local registry and mode '{mode}' has no fallback"}
        return {"error": True, "response": f"SDK {mode} failed (status {reply.get('status_code')}): {reply.get('reply')}"}


class CronJobCreateRequest(BaseModel):
    name: str
    config: dict[str, Any]
    device_groups: list[str] = []
    # Only consulted for non-admin callers who belong to more than one
    # user_group — picks which group gets granted rw on the new cron job.
    owner_group: str | None = None


class CronJobUpdateRequest(BaseModel):
    config: dict[str, Any]
    device_groups: list[str] | None = None


@router.get("")
async def list_cron_jobs(session: Session = Depends(verify_firebase_token)):
    """
    List all cron jobs from Nebula, filtered to the caller's grants if not an admin.

    Parameters
    ----------
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": ...}``. On success, `response`
        is Nebula's `list_cron_jobs` reply, with `"cron_jobs"` filtered
        down to `nebula_auth.compute_permissions(...)["cron_jobs"]` for
        non-admins.
    """
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.nebulaObj.list_cron_jobs()
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to list cron jobs (status {result.get('status_code')})"}
        reply = result.get("reply", {})
        if not session.is_admin:
            perms = nebula_auth.compute_permissions(cfg, session.username)
            reply = {**reply, "cron_jobs": [c for c in reply.get("cron_jobs", []) if c in perms["cron_jobs"]]}
        return {"error": False, "response": reply}
    except Exception as exc:
        logging.error(f"list_cron_jobs failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.get("/{name}/yaml", response_class=PlainTextResponse)
async def export_cron_job_yaml(name: str, session: Session = Depends(verify_firebase_token)):
    """
    Export a single cron job's config as YAML text.

    Parameters
    ----------
    name : str
        Cron job name.
    session : Session
        The authenticated caller.

    Returns
    -------
    str
        The cron job's config, YAML-dumped (`text/plain` response).

    Raises
    ------
    HTTPException
        403 if the caller isn't admin and isn't granted this cron job;
        404 if Nebula doesn't have a cron job by this name; 500 on any
        other failure.
    """
    cfg = config_store.get()
    if not session.is_admin and name not in nebula_auth.compute_permissions(cfg, session.username)["cron_jobs"]:
        raise HTTPException(status_code=403, detail=f"Not permitted for cron job '{name}'")
    try:
        comp = _build_composer(cfg)
        result = comp.nebulaObj.list_cron_job_info(name)
        if result.get("status_code") != 200:
            raise HTTPException(status_code=404, detail=f"Cron job '{name}' not found")
        return yaml.dump(result.get("reply", {}), default_flow_style=False)
    except HTTPException:
        raise
    except Exception as exc:
        logging.error(f"export yaml for cron_job {name} failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{name}")
async def get_cron_job(name: str, session: Session = Depends(verify_firebase_token)):
    """
    Get a single cron job config.

    Parameters
    ----------
    name : str
        Cron job name.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": ...}``. On success, `response`
        is Nebula's cron job config reply.

    Raises
    ------
    HTTPException
        403 if the caller isn't admin and isn't granted this cron job.
    """
    cfg = config_store.get()
    if not session.is_admin and name not in nebula_auth.compute_permissions(cfg, session.username)["cron_jobs"]:
        raise HTTPException(status_code=403, detail=f"Not permitted for cron job '{name}'")
    comp = _build_composer(cfg)
    try:
        result = comp.nebulaObj.list_cron_job_info(name)
        if result.get("status_code") == 200:
            return {"error": False, "response": result.get("reply", {})}
        return {"error": True, "response": f"Cron job '{name}' not found (status {result.get('status_code')})"}
    except Exception as exc:
        logging.error(f"get_cron_job {name} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("")
async def create_cron_job(req: CronJobCreateRequest, session: Session = Depends(verify_firebase_token)):
    """
    Create a new Nebula cron job and optionally assign it to device groups.

    Parameters
    ----------
    req : CronJobCreateRequest
        `name`, `config`, `device_groups` to assign, and (for
        non-admins with more than one group) `owner_group`.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``. On success but
        with per-device-group or grant warnings, `response` still has
        `error=False` with the warnings appended as text.

    Notes
    -----
    Nebula's own `create_cron_job` check is rw-gated against the cron
    job name, which can't exist in anyone's group yet - so this always
    creates via the admin composer. For non-admins, this then
    immediately grants their own group rw on the new cron job name so
    Nebula's own checks govern it from here on. Mirrors create_app
    exactly, except no APP_ID-style env var injection - cron job
    containers don't self-report through the same Redis/Reporter path
    apps do, so nothing in the worker's own cron-job launch path reads
    an equivalent identity env var.
    """
    cfg = config_store.get()
    comp = _build_composer(cfg)

    owner_group = None
    if not session.is_admin:
        owner_group, err = nebula_auth.resolve_owner_group(cfg, session.username, req.owner_group)
        if err:
            return {"error": True, "response": err}

    try:
        config = dict(req.config)
        result = _handle_cron_job_with_image_fallback(comp, req.name, "create", config)
        if result.get("error"):
            return {"error": True, "response": result.get("response", "create failed")}

        errors = []
        for dg in req.device_groups:
            dg_result = comp.handleDeviceGroupCronJobs(req.name, "update", dg)
            if dg_result.get("error"):
                errors.append(f"Failed to add {req.name} to {dg}: {dg_result.get('response', '')}")

        if owner_group:
            try:
                group_result = comp.nebulaObj.list_user_group(owner_group)
                existing_cron_jobs = group_result.get("reply", {}).get("cron_jobs", {}) if group_result.get("status_code") == 200 else {}
                comp.nebulaObj.update_user_group(owner_group, {"cron_jobs": {**existing_cron_jobs, req.name: "rw"}})
            except Exception as exc:
                logging.error(f"granting '{owner_group}' rw on cron_job '{req.name}' failed: {exc}")
                errors.append(f"Cron job created but failed to grant access to group '{owner_group}': {exc}")

        response = f"Cron job '{req.name}' created successfully"
        if errors:
            response += f"; warnings: {'; '.join(errors)}"
        return {"error": False, "response": response}
    except Exception as exc:
        logging.error(f"create_cron_job failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.put("/{name}")
async def update_cron_job(name: str, req: CronJobUpdateRequest, session: Session = Depends(verify_firebase_token)):
    """
    Update an existing cron job's config.

    Parameters
    ----------
    name : str
        Cron job name.
    req : CronJobUpdateRequest
        `config`. `req.device_groups` is accepted by the request model
        but not read by this handler - device group membership is
        managed via the Device Groups router, not here (mirrors
        update_app exactly).
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.

    Notes
    -----
    Non-admins go through a Composer authenticated as their own
    Nebula token - Nebula's own rw check is the real gate here, not
    anything Gustavo decides locally.
    """
    cfg = config_store.get()
    comp = _build_composer(cfg) if session.is_admin else _build_composer_for(cfg, token=session.nebula_secret)
    try:
        config = dict(req.config)
        result = _handle_cron_job_with_image_fallback(comp, name, "update", config)
        logging.info(f"update_cron_job '{name}' handleAsset result: {result}")
        if not result.get("error"):
            return {"error": False, "response": f"Cron job '{name}' updated successfully"}
        return {"error": True, "response": result.get("response", "You do not have write access to this cron job")}
    except Exception as exc:
        logging.error(f"update_cron_job {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}


@router.delete("/{name}")
async def delete_cron_job(name: str, session: Session = Depends(verify_firebase_token)):
    """
    Delete a cron job. Removes it from all device groups first.

    Parameters
    ----------
    name : str
        Cron job name.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.

    Notes
    -----
    The device-group cleanup is best-effort (failures are silently
    ignored) and always runs as the admin composer, since it's just
    removing an association, not a security boundary. The actual
    delete, for non-admins, runs as their own Nebula token so Nebula's
    own rw check is the real gate.
    """
    cfg = config_store.get()
    admin_comp = _build_composer(cfg)
    comp = admin_comp if session.is_admin else _build_composer_for(cfg, token=session.nebula_secret)
    try:
        dgs_result = admin_comp.nebulaObj.list_device_groups()
        if dgs_result.get("status_code") == 200:
            for dg in dgs_result.get("reply", {}).get("device_groups", []):
                try:
                    admin_comp.handleDeviceGroupCronJobs(name, "delete", dg)
                except Exception:
                    pass

        result = comp.handleAsset("cron_job", name, "delete")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "You do not have write access to this cron job")}
        return {"error": False, "response": f"Cron job '{name}' deleted"}
    except Exception as exc:
        logging.error(f"delete_cron_job {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}
