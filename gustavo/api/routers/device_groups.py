"""
/api/device-groups — Nebula device group CRUD + app membership.

GET    /api/device-groups                          → list all (with app membership)
POST   /api/device-groups                          → create
GET    /api/device-groups/{name}                   → get single
PUT    /api/device-groups/{name}                   → update
DELETE /api/device-groups/{name}                   → delete
POST   /api/device-groups/{name}/apps/add          → body: {apps: []}
POST   /api/device-groups/{name}/apps/remove       → body: {apps: []}
"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from gustavo.api import config_store, nebula_auth
from gustavo.api.auth import verify_firebase_token
from gustavo.api.dependencies import _build_composer, _build_composer_for
from gustavo.api.session import Session

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
