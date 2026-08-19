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
from gustavo.api.auth import require_admin, verify_firebase_token
from gustavo.api.dependencies import _build_composer
from gustavo.api.session import Session

router = APIRouter()


class DeviceGroupCreateRequest(BaseModel):
    name: str
    apps: list[str] = []


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
async def create_device_group(req: DeviceGroupCreateRequest, _session=Depends(require_admin)):
    """Create a new device group (mirrors DGHandler.createDeviceGroup)."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.handleAsset("device_group", req.name, "create", {"apps": req.apps})
        if result.get("error"):
            return {"error": True, "response": result.get("response", "create failed")}
        return {"error": False, "response": f"Device group '{req.name}' created"}
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
    _session=Depends(require_admin),
):
    """Update a device group's app list (mirrors DGHandler.updateDeviceGroup)."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.handleAsset("device_group", name, "update", {"apps": req.apps})
        if result.get("error"):
            return {"error": True, "response": result.get("response", "update failed")}
        return {"error": False, "response": f"Device group '{name}' updated"}
    except Exception as exc:
        logging.error(f"update_device_group {name} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.delete("/{name}")
async def delete_device_group(name: str, _session=Depends(require_admin)):
    """Delete a device group (mirrors DGHandler.deleteDeviceGroup — diagnostic fetch first)."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        # Diagnostic fetch before delete (mirrors Streamlit pattern)
        diag = comp.nebulaObj.list_device_group(name)
        logging.info(f"delete_device_group diagnostic for '{name}': status={diag.get('status_code')} reply={diag.get('reply')}")

        result = comp.handleAsset("device_group", name, "delete")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "delete failed")}
        return {"error": False, "response": f"Device group '{name}' deleted"}
    except Exception as exc:
        logging.error(f"delete_device_group {name} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("/{name}/apps/add")
async def add_apps_to_device_group(
    name: str,
    req: AppListRequest,
    _session=Depends(require_admin),
):
    """Add apps to a device group (mirrors Streamlit: handleDeviceGroup with mode='update')."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.handleDeviceGroup(",".join(req.apps), "update", name)
        if result.get("error"):
            return {"error": True, "response": result.get("response", "add failed")}
        return {"error": False, "response": f"Added {req.apps} to '{name}'"}
    except Exception as exc:
        logging.error(f"add_apps_to_dg {name} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("/{name}/apps/remove")
async def remove_apps_from_device_group(
    name: str,
    req: AppListRequest,
    _session=Depends(require_admin),
):
    """Remove apps from a device group (mirrors Streamlit: handleDeviceGroup with mode='delete')."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.handleDeviceGroup(",".join(req.apps), "delete", name)
        if result.get("error"):
            return {"error": True, "response": result.get("response", "remove failed")}
        return {"error": False, "response": f"Removed {req.apps} from '{name}'"}
    except Exception as exc:
        logging.error(f"remove_apps_from_dg {name} failed: {exc}")
        return {"error": True, "response": str(exc)}
