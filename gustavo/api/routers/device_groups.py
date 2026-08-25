"""
/api/device-groups — Nebula device group CRUD + app membership.

GET    /api/device-groups                          → list all (with app membership)
POST   /api/device-groups                          → create
GET    /api/device-groups/{name}                   → get single
PUT    /api/device-groups/{name}                   → update
DELETE /api/device-groups/{name}                   → delete
POST   /api/device-groups/{name}/apps/add          → body: {apps: []}
POST   /api/device-groups/{name}/apps/remove       → body: {apps: []}
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


@router.get("")
async def list_device_groups(session: Session = Depends(verify_firebase_token)):
    """List all device groups with their app membership (mirrors DGHandler.listAllDeviceGroups).
    Filtered to the caller's grants if not an admin (Nebula's own list endpoint is unfiltered)."""
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
            if group_result.get("status_code") == 200:
                apps = group_result.get("reply", {}).get("apps", []) or []
            groups.append({"name": group_name, "apps": apps})

        return {"error": False, "response": {"device_groups": groups}}
    except Exception as exc:
        logging.error(f"list_device_groups failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("")
async def create_device_group(req: DeviceGroupCreateRequest, session: Session = Depends(verify_firebase_token)):
    """Create a new device group (mirrors DGHandler.createDeviceGroup).

    Nebula's own create_device_group check is rw-gated against the group
    name, which can't exist in anyone's grants yet — so this always creates
    via the admin composer. For non-admins, we then immediately grant their
    own group rw on the new device group so Nebula's own checks govern it
    from here on (mirrors create_app in apps.py).
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
    """Get a device group's config (mirrors list_device_group SDK call)."""
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
    """Update a device group's app list (mirrors DGHandler.updateDeviceGroup).
    Non-admins go through a Composer authenticated as their own Nebula
    token — Nebula's own rw check is the real gate, same as apps.py."""
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
    """Delete a device group (mirrors DGHandler.deleteDeviceGroup — diagnostic fetch first).
    The diagnostic fetch always runs as admin (read-only, not a security
    boundary); the actual delete, for non-admins, runs as their own token."""
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
    Shared implementation for apps/add and apps/remove. Composer.handleDeviceGroup
    (gustavo/src/Composer.py) bundles a read-before, write, and read-after into
    one call — but the read is ro-gated on Nebula's side, and a non-admin's
    grant on a device group is typically rw only. Since Nebula's permission
    check is exact-match (rw does NOT imply ro), running the whole bundled
    call through a per-user token 403s on the internal read even when the
    actual write would have been allowed. So: read the current app list via
    the admin composer (never a security boundary — reads are already
    Python-filtered elsewhere), then perform only the write through the
    caller's own composer, so Nebula's own rw check is what actually gates it.
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


@router.post("/{name}/apps/add")
async def add_apps_to_device_group(
    name: str,
    req: AppListRequest,
    session: Session = Depends(verify_firebase_token),
):
    """Add apps to a device group (mirrors Streamlit: handleDeviceGroup with mode='update')."""
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
    """Remove apps from a device group (mirrors Streamlit: handleDeviceGroup with mode='delete')."""
    cfg = config_store.get()
    try:
        result = _merge_device_group_apps(cfg, session, name, req.apps, "remove")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "remove failed")}
        return {"error": False, "response": f"Removed {req.apps} from '{name}'"}
    except Exception as exc:
        logging.error(f"remove_apps_from_dg {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}


def _require_dg_access(cfg: dict, session: Session, name: str) -> None:
    if not session.is_admin and name not in nebula_auth.compute_permissions(cfg, session.username)["device_groups"]:
        raise HTTPException(status_code=403, detail=f"Not permitted for device group '{name}'")


def _batch_quote(value: str) -> str:
    """Quote a value for safe use as a double-quoted argument in a Windows
    .bat file — cmd.exe's escaping rules, not shlex/POSIX. % must be doubled
    to avoid batch variable expansion (applies even inside double quotes);
    embedded " is escaped as \\" to match the standard Windows argv-parsing
    convention docker.exe (like most Windows CLI tools) follows. & | < > ^
    are left alone since cmd.exe's own metacharacter splitting doesn't apply
    inside a quoted argument."""
    return '"' + value.replace("%", "%%").replace('"', '\\"') + '"'


@router.get("/{name}/worker-env", response_class=PlainTextResponse)
async def download_worker_env(name: str, session: Session = Depends(verify_session_or_basic)):
    """Native `gustavo worker up` env file for this device group, scoped to the
    caller's own Nebula identity — same shape as /api/config/worker-download,
    plus DEVICE_GROUP so the CLI invocation needs one less flag."""
    cfg = config_store.get()
    _require_dg_access(cfg, session, name)
    username = session.username
    password = session.nebula_secret
    auth_token = base64.b64encode(f"{username}:{password}".encode()).decode()
    lines = [
        f"DEVICE_GROUP={name}",
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
    return "\n".join(lines) + "\n"


@router.get("/{name}/worker-compose", response_class=PlainTextResponse)
async def download_worker_compose(name: str, session: Session = Depends(verify_session_or_basic)):
    """Self-contained docker-compose.yml for this device group's worker — every
    value baked in directly, no companion .env file. Independent of worker-env:
    changing/regenerating one has no effect on the other."""
    cfg = config_store.get()
    _require_dg_access(cfg, session, name)
    env = nebula_auth.build_worker_env(cfg, session.username, session.nebula_secret, name)
    service: dict = {
        "image": _WORKER_IMAGE,
        "container_name": f"worker_{name}",
        "restart": "unless-stopped",
    }
    if cfg.get("WORKER_NMODE") == "host":
        service["network_mode"] = "host"
    service["environment"] = env
    service["volumes"] = ["/var/run/docker.sock:/var/run/docker.sock"]
    compose = {"services": {"gustavo-worker": service}}
    # default_flow_style=False for block style; yaml.safe_dump handles quoting/
    # escaping of any value (quotes, $, backticks, ...) correctly on its own -
    # values here include admin-set secrets, which can contain anything.
    return yaml.safe_dump(compose, default_flow_style=False, sort_keys=False)


@router.get("/{name}/worker-script", response_class=PlainTextResponse)
async def download_worker_script(name: str, session: Session = Depends(verify_session_or_basic)):
    """Self-contained launcher script for this device group's worker — a single
    `docker run` invocation with every value baked in directly. Independent of
    both worker-env and worker-compose; downloading this needs nothing else."""
    cfg = config_store.get()
    _require_dg_access(cfg, session, name)
    env = nebula_auth.build_worker_env(cfg, session.username, session.nebula_secret, name)
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
        f"  {_WORKER_IMAGE}\n"
    )
    return script


@router.get("/{name}/worker-script-windows", response_class=PlainTextResponse)
async def download_worker_script_windows(name: str, session: Session = Depends(verify_session_or_basic)):
    """Same as worker-script, as a double-click-able Windows .bat instead of
    a bash script — cmd.exe's syntax and quoting are different enough (no
    set -e, ^ instead of \\ for line continuation, its own escaping rules)
    that it needs its own generator rather than reusing the bash one."""
    cfg = config_store.get()
    _require_dg_access(cfg, session, name)
    env = nebula_auth.build_worker_env(cfg, session.username, session.nebula_secret, name)
    container_name = _batch_quote(f"worker_{name}")
    args = [f"docker run -d --name {container_name} --restart unless-stopped"]
    if cfg.get("WORKER_NMODE") == "host":
        args.append("--network host")
    args += [f"-e {key}={_batch_quote(value)}" for key, value in env.items()]
    args.append("-v /var/run/docker.sock:/var/run/docker.sock")
    args.append(_WORKER_IMAGE)
    run_command = " ^\n  ".join(args)
    script = (
        "@echo off\n"
        f"docker rm -f {container_name} >nul 2>&1\n"
        f"{run_command}\n"
    )
    return script
