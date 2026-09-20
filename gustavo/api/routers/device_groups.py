"""
/api/device-groups — Nebula device group CRUD + app membership.

GET    /api/device-groups                          → list all (with app membership)
POST   /api/device-groups                          → create
GET    /api/device-groups/{name}                   → get single
PUT    /api/device-groups/{name}                   → update
DELETE /api/device-groups/{name}                   → delete
POST   /api/device-groups/{name}/apps/add          → body: {apps: []}
POST   /api/device-groups/{name}/apps/remove       → body: {apps: []}
POST   /api/device-groups/{name}/cron-jobs/add     → body: {cron_jobs: []}
POST   /api/device-groups/{name}/cron-jobs/remove  → body: {cron_jobs: []}
GET    /api/device-groups/{name}/worker-env        → native `gustavo worker up` env file for this device group
GET    /api/device-groups/{name}/worker-compose    → self-contained docker-compose.yml for this device group
GET    /api/device-groups/{name}/worker-script     → self-contained `docker run` launcher script (macOS/Linux)
GET    /api/device-groups/{name}/worker-script-windows → same, as a Windows .bat
"""
import base64
import logging
import shlex

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from gustavo.api import config_store, nebula_auth
from gustavo.api.auth import verify_firebase_token, verify_session_or_basic
from gustavo.api.dependencies import _build_composer, _build_composer_for
from gustavo.api.session import Session

_WORKER_IMAGE = "ghcr.io/disys-lab/gustavo-worker:latest"

router = APIRouter()


class DeviceGroupCreateRequest(BaseModel):
    name: str
    apps: list[str] = []
    # Only consulted for non-admin callers who belong to more than one
    # user_group — picks which group gets granted rw on the new device group.
    owner_group: str | None = None


class DeviceGroupUpdateRequest(BaseModel):
    apps: list[str]


class AppListRequest(BaseModel):
    apps: list[str]


class CronJobListRequest(BaseModel):
    cron_jobs: list[str]


@router.get("")
async def list_device_groups(session: Session = Depends(verify_firebase_token)):
    """
    List all device groups with their app membership.

    Parameters
    ----------
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": {"device_groups": [{"name": ...,
        "apps": [...], "cron_jobs": [...]}, ...]}}``, filtered to the
        caller's grants if not an admin (Nebula's own list endpoint is
        unfiltered).
    """
    cfg = config_store.get()
    comp = _build_composer(cfg)
    perms = None if session.is_admin else nebula_auth.compute_permissions(cfg, session.username)
    try:
        result = comp.nebulaObj.list_device_groups()
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to list device groups (status {result.get('status_code')})"}

        groups_list = result.get("reply", {}).get("device_groups", [])
        if perms is not None:
            groups_list = [g for g in groups_list if g in perms["device_groups"]]
        groups = []
        for group_name in groups_list:
            group_result = comp.nebulaObj.list_device_group(group_name)
            apps = []
            cron_jobs = []
            if group_result.get("status_code") == 200:
                apps = group_result.get("reply", {}).get("apps", []) or []
                cron_jobs = group_result.get("reply", {}).get("cron_jobs", []) or []
            groups.append({"name": group_name, "apps": apps, "cron_jobs": cron_jobs})

        return {"error": False, "response": {"device_groups": groups}}
    except Exception as exc:
        logging.error(f"list_device_groups failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("")
async def create_device_group(req: DeviceGroupCreateRequest, session: Session = Depends(verify_firebase_token)):
    """
    Create a new device group.

    Parameters
    ----------
    req : DeviceGroupCreateRequest
        `name`, `apps` to assign, and (for non-admins with more than
        one group) `owner_group`.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``. On success but
        with a grant warning, `response` still has `error=False` with
        the warning appended as text.

    Notes
    -----
    Nebula's own `create_device_group` check is rw-gated against the
    group name, which can't exist in anyone's grants yet - so this
    always creates via the admin composer. For non-admins, this then
    immediately grants their own group rw on the new device group so
    Nebula's own checks govern it from here on (mirrors `create_app`
    in `apps.py`).
    """
    cfg = config_store.get()
    comp = _build_composer(cfg)

    owner_group = None
    if not session.is_admin:
        owner_group, err = nebula_auth.resolve_owner_group(cfg, session.username, req.owner_group)
        if err:
            return {"error": True, "response": err}

    try:
        result = comp.handleAsset("device_group", req.name, "create", {"apps": req.apps})
        if result.get("error"):
            return {"error": True, "response": result.get("response", "create failed")}

        response = f"Device group '{req.name}' created"
        if owner_group:
            try:
                group_result = comp.nebulaObj.list_user_group(owner_group)
                existing = group_result.get("reply", {}).get("device_groups", {}) if group_result.get("status_code") == 200 else {}
                comp.nebulaObj.update_user_group(owner_group, {"device_groups": {**existing, req.name: "rw"}})
            except Exception as exc:
                logging.error(f"granting '{owner_group}' rw on device group '{req.name}' failed: {exc}")
                response += f"; warning: failed to grant access to group '{owner_group}': {exc}"

        return {"error": False, "response": response}
    except Exception as exc:
        logging.error(f"create_device_group failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.get("/{name}")
async def get_device_group(name: str, session: Session = Depends(verify_firebase_token)):
    """
    Get a single device group's config.

    Parameters
    ----------
    name : str
        Device group name.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": ...}``. `error` is `True` if the
        caller isn't admin and isn't granted this device group, or
        Nebula doesn't have a device group by this name.
    """
    cfg = config_store.get()
    if not session.is_admin and name not in nebula_auth.compute_permissions(cfg, session.username)["device_groups"]:
        return {"error": True, "response": f"Not permitted for device group '{name}'"}
    comp = _build_composer(cfg)
    try:
        result = comp.nebulaObj.list_device_group(name)
        if result.get("status_code") == 200:
            return {"error": False, "response": result.get("reply", {})}
        return {"error": True, "response": f"Device group '{name}' not found"}
    except Exception as exc:
        logging.error(f"get_device_group {name} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.put("/{name}")
async def update_device_group(
    name: str,
    req: DeviceGroupUpdateRequest,
    session: Session = Depends(verify_firebase_token),
):
    """
    Update a device group's app list.

    Parameters
    ----------
    name : str
        Device group name.
    req : DeviceGroupUpdateRequest
        `apps` - the full replacement app list.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.

    Notes
    -----
    Non-admins go through a Composer authenticated as their own
    Nebula token - Nebula's own rw check is the real gate, same as
    `apps.py`.
    """
    cfg = config_store.get()
    comp = _build_composer(cfg) if session.is_admin else _build_composer_for(cfg, token=session.nebula_secret)
    try:
        result = comp.handleAsset("device_group", name, "update", {"apps": req.apps})
        if result.get("error"):
            return {"error": True, "response": result.get("response", "You do not have write access to this device group")}
        return {"error": False, "response": f"Device group '{name}' updated"}
    except Exception as exc:
        logging.error(f"update_device_group {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}


@router.delete("/{name}")
async def delete_device_group(name: str, session: Session = Depends(verify_firebase_token)):
    """
    Delete a device group.

    Parameters
    ----------
    name : str
        Device group name.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.

    Notes
    -----
    Fetches the device group's current state (logged, not returned)
    before deleting it, matching the legacy Streamlit tool's pattern.
    That diagnostic fetch always runs as admin (read-only, not a
    security boundary); the actual delete, for non-admins, runs as
    their own token.
    """
    cfg = config_store.get()
    admin_comp = _build_composer(cfg)
    comp = admin_comp if session.is_admin else _build_composer_for(cfg, token=session.nebula_secret)
    try:
        # Diagnostic fetch before delete (mirrors Streamlit pattern)
        diag = admin_comp.nebulaObj.list_device_group(name)
        logging.info(f"delete_device_group diagnostic for '{name}': status={diag.get('status_code')} reply={diag.get('reply')}")

        result = comp.handleAsset("device_group", name, "delete")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "You do not have write access to this device group")}
        return {"error": False, "response": f"Device group '{name}' deleted"}
    except Exception as exc:
        logging.error(f"delete_device_group {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}


def _merge_device_group_apps(cfg: dict, session: Session, name: str, apps: list[str], mode: str) -> dict:
    """
    Add or remove apps from a device group's app list, working around a Nebula rw/ro permission gap.

    Parameters
    ----------
    cfg : dict
        Current platform config.
    session : Session
        The authenticated caller.
    name : str
        Device group name.
    apps : list of str
        App names to add or remove.
    mode : str
        `"add"` (skip apps already present) or anything else, treated
        as remove.

    Returns
    -------
    dict
        ``{"error": bool, "response": ...}``. On success, `response`
        is the resulting app list (`list`). On failure, `response` is
        a message string.

    Notes
    -----
    Shared implementation for `apps/add` and `apps/remove`.
    `Composer.handleDeviceGroup` (`gustavo/src/Composer.py`) bundles a
    read-before, write, and read-after into one call - but the read is
    ro-gated on Nebula's side, and a non-admin's grant on a device
    group is typically rw only. Since Nebula's permission check is
    exact-match (rw does NOT imply ro), running the whole bundled call
    through a per-user token 403s on the internal read even when the
    actual write would have been allowed. So: read the current app
    list via the admin composer (never a security boundary - reads
    are already Python-filtered elsewhere), then perform only the
    write through the caller's own composer, so Nebula's own rw check
    is what actually gates it.
    """
    admin_comp = _build_composer(cfg)
    write_comp = admin_comp if session.is_admin else _build_composer_for(cfg, token=session.nebula_secret)

    current = admin_comp.nebulaObj.list_device_group(name)
    if current.get("status_code") != 200:
        return {"error": True, "response": f"Device group '{name}' not found"}
    existing_apps = current.get("reply", {}).get("apps", []) or []

    if mode == "add":
        new_apps = list(existing_apps)
        for app in apps:
            if app not in new_apps:
                new_apps.append(app)
    else:
        new_apps = [a for a in existing_apps if a not in apps]

    result = write_comp.handleAsset("device_group", name, "update", {"apps": new_apps})
    if result.get("error"):
        return {"error": True, "response": result.get("response", "You do not have write access to this device group")}
    return {"error": False, "response": new_apps}


def _merge_device_group_cron_jobs(cfg: dict, session: Session, name: str, cron_jobs: list[str], mode: str) -> dict:
    """
    Add or remove cron jobs from a device group's cron_jobs list, working around the same Nebula rw/ro permission gap.

    Structural mirror of `_merge_device_group_apps` - same rw/ro-gap
    rationale, same read-via-admin/write-via-caller split. Deliberately
    does not call `Composer.handleDeviceGroupCronJobs` (which bundles
    read+write+read-after) for the same reason `_merge_device_group_apps`
    doesn't call `handleDeviceGroup`: a non-admin's grant is typically
    rw-only, and Nebula's permission check is exact-match, so a bundled
    call routed entirely through a per-user token would 403 on its own
    internal read even when the write itself would be allowed.

    Parameters
    ----------
    cfg : dict
        Current platform config.
    session : Session
        The authenticated caller.
    name : str
        Device group name.
    cron_jobs : list of str
        Cron job names to add or remove.
    mode : str
        `"add"` (skip cron jobs already present) or anything else,
        treated as remove.

    Returns
    -------
    dict
        ``{"error": bool, "response": ...}``. On success, `response`
        is the resulting cron_jobs list (`list`). On failure,
        `response` is a message string.
    """
    admin_comp = _build_composer(cfg)
    write_comp = admin_comp if session.is_admin else _build_composer_for(cfg, token=session.nebula_secret)

    current = admin_comp.nebulaObj.list_device_group(name)
    if current.get("status_code") != 200:
        return {"error": True, "response": f"Device group '{name}' not found"}
    existing_cron_jobs = current.get("reply", {}).get("cron_jobs", []) or []

    if mode == "add":
        new_cron_jobs = list(existing_cron_jobs)
        for cron_job in cron_jobs:
            if cron_job not in new_cron_jobs:
                new_cron_jobs.append(cron_job)
    else:
        new_cron_jobs = [c for c in existing_cron_jobs if c not in cron_jobs]

    result = write_comp.handleAsset("device_group", name, "update", {"cron_jobs": new_cron_jobs})
    if result.get("error"):
        return {"error": True, "response": result.get("response", "You do not have write access to this device group")}
    return {"error": False, "response": new_cron_jobs}


@router.post("/{name}/apps/add")
async def add_apps_to_device_group(
    name: str,
    req: AppListRequest,
    session: Session = Depends(verify_firebase_token),
):
    """
    Add apps to a device group.

    Parameters
    ----------
    name : str
        Device group name.
    req : AppListRequest
        `apps` to add.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.
    """
    cfg = config_store.get()
    try:
        result = _merge_device_group_apps(cfg, session, name, req.apps, "add")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "add failed")}
        return {"error": False, "response": f"Added {req.apps} to '{name}'"}
    except Exception as exc:
        logging.error(f"add_apps_to_dg {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}


@router.post("/{name}/apps/remove")
async def remove_apps_from_device_group(
    name: str,
    req: AppListRequest,
    session: Session = Depends(verify_firebase_token),
):
    """
    Remove apps from a device group.

    Parameters
    ----------
    name : str
        Device group name.
    req : AppListRequest
        `apps` to remove.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.
    """
    cfg = config_store.get()
    try:
        result = _merge_device_group_apps(cfg, session, name, req.apps, "remove")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "remove failed")}
        return {"error": False, "response": f"Removed {req.apps} from '{name}'"}
    except Exception as exc:
        logging.error(f"remove_apps_from_dg {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}


@router.post("/{name}/cron-jobs/add")
async def add_cron_jobs_to_device_group(
    name: str,
    req: CronJobListRequest,
    session: Session = Depends(verify_firebase_token),
):
    """
    Add cron jobs to a device group.

    Parameters
    ----------
    name : str
        Device group name.
    req : CronJobListRequest
        `cron_jobs` to add.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.
    """
    cfg = config_store.get()
    try:
        result = _merge_device_group_cron_jobs(cfg, session, name, req.cron_jobs, "add")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "add failed")}
        return {"error": False, "response": f"Added {req.cron_jobs} to '{name}'"}
    except Exception as exc:
        logging.error(f"add_cron_jobs_to_dg {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}


@router.post("/{name}/cron-jobs/remove")
async def remove_cron_jobs_from_device_group(
    name: str,
    req: CronJobListRequest,
    session: Session = Depends(verify_firebase_token),
):
    """
    Remove cron jobs from a device group.

    Parameters
    ----------
    name : str
        Device group name.
    req : CronJobListRequest
        `cron_jobs` to remove.
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        ``{"error": bool, "response": <message str>}``.
    """
    cfg = config_store.get()
    try:
        result = _merge_device_group_cron_jobs(cfg, session, name, req.cron_jobs, "remove")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "remove failed")}
        return {"error": False, "response": f"Removed {req.cron_jobs} from '{name}'"}
    except Exception as exc:
        logging.error(f"remove_cron_jobs_from_dg {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}


def _require_dg_access(cfg: dict, session: Session, name: str) -> None:
    """
    Raise 403 if `session` isn't admin and isn't granted device group `name`.

    Parameters
    ----------
    cfg : dict
        Current platform config.
    session : Session
        The authenticated caller.
    name : str
        Device group name.

    Raises
    ------
    HTTPException
        403 if not permitted.
    """
    if not session.is_admin and name not in nebula_auth.compute_permissions(cfg, session.username)["device_groups"]:
        raise HTTPException(status_code=403, detail=f"Not permitted for device group '{name}'")


def _batch_quote(value: str) -> str:
    """
    Quote `value` for safe use as a double-quoted argument in a Windows `.bat` file.

    Parameters
    ----------
    value : str
        The raw value to quote.

    Returns
    -------
    str
        `value` wrapped in double quotes, safe to embed in a `.bat`
        file's `docker run` invocation.

    Notes
    -----
    Uses cmd.exe's escaping rules, not shlex/POSIX. `%` must be
    doubled to avoid batch variable expansion (applies even inside
    double quotes); embedded `"` is escaped as `\\"` to match the
    standard Windows argv-parsing convention `docker.exe` (like most
    Windows CLI tools) follows. `& | < > ^` are left alone since
    cmd.exe's own metacharacter splitting doesn't apply inside a
    quoted argument.

    `download_worker_script_windows` now prefixes every invocation
    with `wsl`, so cmd.exe's own argv parsing runs first, then `wsl`
    hands the already-assembled string to the target distro's shell -
    not independently verified on a real WSL2 host that a value
    containing both cmd.exe- and shell-special characters (quotes,
    `$`, backticks) survives that second hop unchanged. Worth testing
    directly before relying on it for values that might contain any
    of those.
    """
    return '"' + value.replace("%", "%%").replace('"', '\\"') + '"'


@router.get("/{name}/worker-env", response_class=PlainTextResponse)
async def download_worker_env(
    name: str, gpu: bool = False, reporter: bool = False, check_in_time: int = 60,
    public_endpoints: bool = False,
    session: Session = Depends(verify_session_or_basic),
):
    """
    Native `gustavo worker up` env file for this device group, scoped to the caller's own Nebula identity.

    Parameters
    ----------
    name : str
        Device group name.
    gpu : bool, optional
        If `True`, adds `GPU_ENABLED=true` - only set this for a
        device group whose hardware actually has a GPU
        `nvidia-container-toolkit` can grant access to; the worker
        applies it to every container it launches on that device.
    reporter : bool, optional
        If `True`, emits `REPORTER_HOST`/`REPORTER_PORT`/
        `REPORTER_PROTOCOL` instead of `REDIS_HOST`/`REDIS_PORT`/
        `REDIS_AUTH_TOKEN`, switching worker status reporting to
        gustavo-reporter's REST API instead of direct Redis writes.
        Mutually exclusive with the Redis reporting fields - see
        `nebula_auth.build_worker_env`. Forced `True` server-side if the
        caller belongs to any `EXTERNAL_USER_GROUPS` group, regardless of
        what's passed here - `REDIS_AUTH_TOKEN` is a single shared,
        unscoped credential an external caller must never receive.
    check_in_time : int, optional
        `NEBULA_MANAGER_CHECK_IN_TIME` - how often (seconds) the
        worker polls the Nebula manager and reports status; the same
        loop tick drives both, there's no separate report-only timer.
        Defaults to 60.
    public_endpoints : bool, optional
        If `True`, uses `PUBLIC_MANAGER_HOST`/`PORT` (and
        `PUBLIC_REPORTER_HOST`/`PORT` if `reporter` is also set) instead
        of the internal LAN addresses - for a worker reaching this
        platform from outside (e.g. a Cloudflare Tunnel). See
        `nebula_auth.build_worker_env`. Defaults to `False`. Forced
        `True` server-side if the caller belongs to any
        `EXTERNAL_USER_GROUPS` group, regardless of what's passed here.
    session : Session
        The authenticated caller, via `verify_session_or_basic`.

    Returns
    -------
    str
        `key=value` lines, `text/plain`. Same shape as
        `/api/config/worker-download`, plus `DEVICE_GROUP` so the CLI
        invocation needs one less flag.

    Raises
    ------
    HTTPException
        403 if the caller isn't admin and isn't granted this device
        group.

    Notes
    -----
    Registry inclusion is not a caller-supplied choice - it's derived
    entirely from `PUBLIC_REGISTRY_ENABLED` and whether the caller is an
    external-group member, same as `nebula_auth.build_worker_env`.
    """
    cfg = config_store.get()
    _require_dg_access(cfg, session, name)
    username = session.username
    password = session.nebula_secret
    external = nebula_auth.is_external_user(cfg, username)
    public_endpoints = public_endpoints or external
    # REDIS_AUTH_TOKEN is a single shared, unscoped platform credential - an
    # external caller must never be able to reach the Redis branch below,
    # regardless of what they pass for `reporter`. See build_worker_env's
    # matching forced-reporter docstring.
    reporter = reporter or external
    auth_token = base64.b64encode(f"{username}:{password}".encode()).decode()
    manager_host = cfg.get("PUBLIC_MANAGER_HOST", "") if public_endpoints else cfg.get("MANAGER_HOST", "")
    manager_port = cfg.get("PUBLIC_MANAGER_PORT", "") if public_endpoints else cfg.get("MANAGER_PORT", "")
    lines = [
        f"DEVICE_GROUP={name}",
        f"MANAGER_HOST={manager_host}",
        f"MANAGER_PORT={manager_port}",
    ]
    if reporter:
        reporter_host = cfg.get("PUBLIC_REPORTER_HOST", "") if public_endpoints else cfg.get("REPORTER_HOST", "")
        reporter_port = cfg.get("PUBLIC_REPORTER_PORT", "") if public_endpoints else cfg.get("REPORTER_PORT", "")
        reporter_protocol = "https" if public_endpoints else "http"
        lines += [
            f"REPORTER_HOST={reporter_host}",
            f"REPORTER_PORT={reporter_port}",
            f"REPORTER_PROTOCOL={reporter_protocol}",
        ]
    else:
        lines += [
            f"REDIS_HOST={cfg.get('REDIS_HOST', '')}",
            f"REDIS_PORT={cfg.get('REDIS_PORT', '')}",
            f"REDIS_AUTH_TOKEN={cfg.get('REDIS_AUTH_TOKEN', '')}",
        ]
    if cfg.get("PUBLIC_REGISTRY_ENABLED"):
        lines += [
            f"REGISTRY_HOST={cfg.get('PUBLIC_REGISTRY_HOST', '')}",
            f"REGISTRY_PORT={cfg.get('PUBLIC_REGISTRY_PORT', '')}",
            f"REGISTRY_AUTH_USER={username}",
            f"REGISTRY_AUTH_PASSWORD={password}",
        ]
    elif not external:
        lines += [
            f"REGISTRY_HOST={cfg.get('REGISTRY_HOST', '')}",
            f"REGISTRY_PORT={cfg.get('REGISTRY_PORT', '')}",
            f"REGISTRY_AUTH_USER={username}",
            f"REGISTRY_AUTH_PASSWORD={password}",
        ]
    lines += [
        f"WORKER_NMODE={cfg.get('WORKER_NMODE', '')}",
        f"NEBULA_USERNAME={username}",
        f"NEBULA_PASSWORD={password}",
        f"NEBULA_AUTH_TOKEN={auth_token}",
        f"NEBULA_MANAGER_CHECK_IN_TIME={check_in_time}",
    ]
    if gpu:
        lines.append("GPU_ENABLED=true")
    return "\n".join(lines) + "\n"


@router.get("/{name}/worker-compose", response_class=PlainTextResponse)
async def download_worker_compose(
    name: str, gpu: bool = False, reporter: bool = False, check_in_time: int = 60,
    public_endpoints: bool = False,
    session: Session = Depends(verify_session_or_basic),
):
    """
    Self-contained `docker-compose.yml` for this device group's worker.

    Parameters
    ----------
    name : str
        Device group name.
    gpu : bool, optional
        If `True`, adds `GPU_ENABLED=true` - only for a device group
        whose hardware actually has a GPU.
    reporter : bool, optional
        If `True`, switches worker status reporting to
        gustavo-reporter's REST API instead of direct Redis writes -
        see `nebula_auth.build_worker_env`.
    check_in_time : int, optional
        `NEBULA_MANAGER_CHECK_IN_TIME` - how often (seconds) the
        worker polls the Nebula manager and reports status. Defaults
        to 60.
    public_endpoints : bool, optional
        If `True`, uses this platform's public Manager/Reporter
        addresses instead of the internal LAN ones - for a worker
        reaching this platform from outside (e.g. a Cloudflare
        Tunnel). See `nebula_auth.build_worker_env`. Defaults to
        `False`. Forced `True` server-side if the caller belongs to
        any `EXTERNAL_USER_GROUPS` group.
    session : Session
        The authenticated caller, via `verify_session_or_basic`.

    Returns
    -------
    str
        YAML `docker-compose.yml` text, every value baked in directly
        - no companion `.env` file needed.

    Raises
    ------
    HTTPException
        403 if the caller isn't admin and isn't granted this device
        group.

    Notes
    -----
    Independent of `worker-env`: changing/regenerating one has no
    effect on the other. Registry inclusion is derived, not
    caller-supplied - see `nebula_auth.build_worker_env`.
    """
    cfg = config_store.get()
    _require_dg_access(cfg, session, name)
    external = nebula_auth.is_external_user(cfg, session.username)
    env = nebula_auth.build_worker_env(
        cfg, session.username, session.nebula_secret, name,
        gpu_enabled=gpu, use_reporter=reporter, check_in_time=check_in_time,
        use_public_endpoints=public_endpoints or external, external=external,
    )
    service: dict = {
        "image": _WORKER_IMAGE,
        "container_name": f"worker_{name}",
        "restart": "unless-stopped",
    }
    if cfg.get("WORKER_NMODE") == "host":
        service["network_mode"] = "host"
    service["environment"] = env
    service["volumes"] = [
        "/var/run/docker.sock:/var/run/docker.sock",
        "/etc/gustavo-worker:/etc/gustavo-worker",
    ]
    compose = {"services": {"gustavo-worker": service}}
    # default_flow_style=False for block style; yaml.safe_dump handles quoting/
    # escaping of any value (quotes, $, backticks, ...) correctly on its own -
    # values here include admin-set secrets, which can contain anything.
    return yaml.safe_dump(compose, default_flow_style=False, sort_keys=False)


@router.get("/{name}/worker-script", response_class=PlainTextResponse)
async def download_worker_script(
    name: str, gpu: bool = False, reporter: bool = False, check_in_time: int = 60,
    public_endpoints: bool = False,
    session: Session = Depends(verify_session_or_basic),
):
    """
    Self-contained `docker run` launcher script for this device group's worker (macOS/Linux).

    Parameters
    ----------
    name : str
        Device group name.
    gpu : bool, optional
        If `True`, adds `GPU_ENABLED=true` - only for a device group
        whose hardware actually has a GPU.
    reporter : bool, optional
        If `True`, switches worker status reporting to
        gustavo-reporter's REST API instead of direct Redis writes -
        see `nebula_auth.build_worker_env`.
    check_in_time : int, optional
        `NEBULA_MANAGER_CHECK_IN_TIME` - how often (seconds) the
        worker polls the Nebula manager and reports status. Defaults
        to 60.
    public_endpoints : bool, optional
        If `True`, uses this platform's public Manager/Reporter
        addresses instead of the internal LAN ones - for a worker
        reaching this platform from outside (e.g. a Cloudflare
        Tunnel). See `nebula_auth.build_worker_env`. Defaults to
        `False`. Forced `True` server-side if the caller belongs to
        any `EXTERNAL_USER_GROUPS` group.
    session : Session
        The authenticated caller, via `verify_session_or_basic`.

    Returns
    -------
    str
        A `#!/bin/bash` script, `text/plain`. Uses `shlex.quote` (not
        naive f-string interpolation) since env values include
        admin-set secrets that can contain anything (quotes, `$`,
        backticks) - unescaped, that's a shell-injection risk in a
        script meant to be double-clicked and run, not just a
        formatting bug.

    Raises
    ------
    HTTPException
        403 if the caller isn't admin and isn't granted this device
        group.

    Notes
    -----
    Independent of both `worker-env` and `worker-compose`;
    downloading this needs nothing else. Registry inclusion is
    derived, not caller-supplied - see `nebula_auth.build_worker_env`.
    """
    cfg = config_store.get()
    _require_dg_access(cfg, session, name)
    external = nebula_auth.is_external_user(cfg, session.username)
    env = nebula_auth.build_worker_env(
        cfg, session.username, session.nebula_secret, name,
        gpu_enabled=gpu, use_reporter=reporter, check_in_time=check_in_time,
        use_public_endpoints=public_endpoints or external, external=external,
    )
    # shlex.quote, not naive f-string interpolation: these values include
    # admin-set secrets that can contain anything (quotes, $, backticks) -
    # unescaped, that's a shell-injection risk in a script meant to be
    # double-clicked and run, not just a formatting bug.
    env_flags = " \\\n  ".join(f"-e {key}={shlex.quote(value)}" for key, value in env.items())
    network_flag = "--network host \\\n  " if cfg.get("WORKER_NMODE") == "host" else ""
    script = (
        "#!/bin/bash\n"
        "set -e\n"
        f"docker rm -f {shlex.quote(f'worker_{name}')} 2>/dev/null || true\n"
        f"docker run -d --name {shlex.quote(f'worker_{name}')} --restart unless-stopped \\\n"
        f"  {network_flag}{env_flags} \\\n"
        "  -v /var/run/docker.sock:/var/run/docker.sock \\\n"
        "  -v /etc/gustavo-worker:/etc/gustavo-worker \\\n"
        f"  {_WORKER_IMAGE}\n"
    )
    return script


@router.get("/{name}/worker-script-windows", response_class=PlainTextResponse)
async def download_worker_script_windows(
    name: str, gpu: bool = False, reporter: bool = False, check_in_time: int = 60,
    public_endpoints: bool = False,
    session: Session = Depends(verify_session_or_basic),
):
    """
    Same as `worker-script`, as a double-click-able Windows `.bat` instead of a bash script.

    Requires WSL2 specifically (not WSL1), with a default Linux distro
    registered, Docker Desktop set to the WSL2 backend, and WSL
    integration enabled for that distro - all four, not just "WSL
    installed". Every `docker` invocation in the generated script is
    prefixed `wsl`, which forces it to run inside that distro's own
    Linux filesystem rather than native Windows - otherwise a bind
    mount like `/etc/gustavo-worker` resolves against Windows' own
    path rules instead of a real Linux `/etc`, silently breaking it.
    The script checks `wsl docker version` first and prints an
    actionable message instead of failing deep in a Docker error if
    any of those four prerequisites are missing.

    Parameters
    ----------
    name : str
        Device group name.
    gpu : bool, optional
        If `True`, adds `GPU_ENABLED=true` - only for a device group
        whose hardware actually has a GPU.
    reporter : bool, optional
        If `True`, switches worker status reporting to
        gustavo-reporter's REST API instead of direct Redis writes -
        see `nebula_auth.build_worker_env`.
    check_in_time : int, optional
        `NEBULA_MANAGER_CHECK_IN_TIME` - how often (seconds) the
        worker polls the Nebula manager and reports status. Defaults
        to 60.
    public_endpoints : bool, optional
        If `True`, uses this platform's public Manager/Reporter
        addresses instead of the internal LAN ones - for a worker
        reaching this platform from outside (e.g. a Cloudflare
        Tunnel). See `nebula_auth.build_worker_env`. Defaults to
        `False`. Forced `True` server-side if the caller belongs to
        any `EXTERNAL_USER_GROUPS` group.
    session : Session
        The authenticated caller, via `verify_session_or_basic`.

    Returns
    -------
    str
        A `@echo off` `.bat` script, `text/plain`.

    Raises
    ------
    HTTPException
        403 if the caller isn't admin and isn't granted this device
        group.

    Notes
    -----
    cmd.exe's syntax and quoting are different enough from bash (no
    `set -e`, `^` instead of `\\` for line continuation, its own
    escaping rules via `_batch_quote`) that it needs its own generator
    rather than reusing `download_worker_script`. Registry inclusion
    is derived, not caller-supplied - see `nebula_auth.build_worker_env`.
    """
    cfg = config_store.get()
    _require_dg_access(cfg, session, name)
    external = nebula_auth.is_external_user(cfg, session.username)
    env = nebula_auth.build_worker_env(
        cfg, session.username, session.nebula_secret, name,
        gpu_enabled=gpu, use_reporter=reporter, check_in_time=check_in_time,
        use_public_endpoints=public_endpoints or external, external=external,
    )
    container_name = _batch_quote(f"worker_{name}")
    args = [f"wsl docker run -d --name {container_name} --restart unless-stopped"]
    if cfg.get("WORKER_NMODE") == "host":
        args.append("--network host")
    args += [f"-e {key}={_batch_quote(value)}" for key, value in env.items()]
    args.append("-v /var/run/docker.sock:/var/run/docker.sock")
    args.append("-v /etc/gustavo-worker:/etc/gustavo-worker")
    args.append(_WORKER_IMAGE)
    run_command = " ^\n  ".join(args)
    script = (
        "@echo off\n"
        "wsl docker version >nul 2>&1\n"
        "if errorlevel 1 (\n"
        "    echo This worker requires WSL2, with a default Linux distro, Docker\n"
        "    echo Desktop set to the WSL2 backend, and WSL integration enabled for\n"
        "    echo that distro. See the docs for setup, then run this script again.\n"
        "    exit /b 1\n"
        ")\n"
        f"wsl docker rm -f {container_name} >nul 2>&1\n"
        f"{run_command}\n"
    )
    return script
