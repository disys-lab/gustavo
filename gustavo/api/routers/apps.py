"""
/api/apps — Nebula application CRUD + registry images + YAML import/export.

GET    /api/apps                     → list all apps
GET    /api/apps/registry/images     → list registry images
POST   /api/apps/yaml/parse          → parse uploaded YAML, return config dict
GET    /api/apps/{name}              → get single app config
POST   /api/apps                     → create app
PUT    /api/apps/{name}              → update app
DELETE /api/apps/{name}              → delete app (removes from all DGs first)
GET    /api/apps/{name}/yaml         → export app config as YAML text
"""
import logging
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from gustavo.api import config_store
from gustavo.api.auth import verify_firebase_token
from gustavo.api.dependencies import _build_composer

router = APIRouter()


def _handleAsset_with_image_fallback(comp, asset_type: str, name: str, mode: str, config: dict) -> dict:
    """Call comp.handleAsset, but if checkImageExists raises IndexError (image is not from
    the local registry), fall back to calling the SDK method directly so the operation
    still completes."""
    try:
        return comp.handleAsset(asset_type, name, mode, config)
    except IndexError:
        logging.warning(
            f"handleAsset '{mode}' for '{name}': checkImageExists failed (image not in local registry), "
            "falling back to direct SDK call"
        )
        if mode == "create":
            reply = comp.nebulaObj.create_app(name, config)
            if reply.get("status_code") == 200:
                return {"error": False, "response": f"created app: {name}"}
        elif mode == "update":
            reply = comp.nebulaObj.update_app(name, config)
            if reply.get("status_code") == 202:
                return {"error": False, "response": f"updated app: {name}"}
        else:
            return {"error": True, "response": f"image not in local registry and mode '{mode}' has no fallback"}
        return {"error": True, "response": f"SDK {mode} failed (status {reply.get('status_code')}): {reply.get('reply')}"}


class AppCreateRequest(BaseModel):
    name: str
    config: dict[str, Any]
    device_groups: list[str] = []


class AppUpdateRequest(BaseModel):
    config: dict[str, Any]
    device_groups: list[str] | None = None


# Note: /registry/images, /yaml/parse and /defaults are fixed paths — declare them BEFORE /{name}
@router.get("/defaults")
async def get_app_defaults(_token=Depends(verify_firebase_token)):
    """Return default env vars for new app creation with real (unmasked) values.
    Values are read directly from config_store so secrets are never exposed to the browser."""
    cfg = config_store.get()
    keygen_public_key = "06ede5b6f133fc291d1b7bb195a105756f8aa484bdba8a0d6ef8d5ea1f26a1bc"
    return {
        "error": False,
        "response": {
            "env_vars": {
                "REDIS_DB_HOST":     cfg.get("REDIS_HOST", ""),
                "REDIS_DB_PORT":     cfg.get("REDIS_PORT", ""),
                "REDIS_DB_PWD":      cfg.get("REDIS_AUTH_TOKEN", ""),
                "MANAGER_HOST":      cfg.get("MANAGER_HOST", ""),
                "MANAGER_PORT":      cfg.get("MANAGER_PORT", ""),
                "NEBULA_AUTH_TOKEN": cfg.get("NEBULA_AUTH_TOKEN", ""),
                "MANAGER_AUTH":      cfg.get("NEBULA_AUTH_TOKEN", ""),
                "SLEEP_SECS":        "600",
                "KEYGEN_PUBLIC_KEY": keygen_public_key,
            }
        },
    }


@router.get("/registry/images")
async def list_registry_images(_token=Depends(verify_firebase_token)):
    """Return all images in the local registry, each with its list of tags.

    Makes direct HTTP requests to the Docker registry v2 API so we can
    return verbose diagnostic info independent of the Composer abstraction.
    """
    import requests as _requests

    cfg = config_store.get()
    protocol = cfg.get("NEBULA_PROTOCOL", "http")
    host = cfg.get("REGISTRY_HOST", "")
    port = cfg.get("REGISTRY_PORT", "5000")
    registry_url = f"{protocol}://{host}:{port}"

    try:
        catalog_url = f"{registry_url}/v2/_catalog"
        r = _requests.get(catalog_url, auth=None, verify=False, timeout=10)
        raw_text = r.text
        try:
            raw_json = r.json()
        except Exception:
            raw_json = None

        if r.status_code != 200:
            return {"error": True, "response": {
                "message": f"Registry returned HTTP {r.status_code}",
                "registry_url": registry_url,
                "catalog_url": catalog_url,
                "raw_response": raw_text,
            }}

        repos = raw_json.get("repositories", []) if raw_json else []
        images = []
        for repo in repos:
            tags_url = f"{registry_url}/v2/{repo}/tags/list"
            tr = _requests.get(tags_url, auth=None, verify=False, timeout=10)
            tags = tr.json().get("tags", []) or [] if tr.status_code == 200 else []
            images.append({"name": repo, "tags": tags})

        return {"error": False, "response": {
            "images": images,
            "registry_url": registry_url,
            "catalog_url": catalog_url,
            "raw_catalog": raw_json,
        }}
    except Exception as exc:
        logging.error(f"registry images failed: {exc}")
        return {"error": True, "response": {
            "message": str(exc),
            "registry_url": registry_url,
        }}


@router.post("/yaml/parse")
async def parse_yaml(
    file: UploadFile = File(...),
    _token=Depends(verify_firebase_token),
):
    """Upload a YAML app config file and return the parsed dict."""
    try:
        content = await file.read()
        parsed = yaml.safe_load(content)
        return {"error": False, "response": parsed}
    except Exception as exc:
        logging.error(f"YAML parse failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.get("")
async def list_apps(_token=Depends(verify_firebase_token)):
    """List all apps from Nebula."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.nebulaObj.list_apps()
        if result.get("status_code") == 200:
            return {"error": False, "response": result.get("reply", {})}
        return {"error": True, "response": f"Failed to list apps (status {result.get('status_code')})"}
    except Exception as exc:
        logging.error(f"list_apps failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.get("/{name}/yaml", response_class=PlainTextResponse)
async def export_app_yaml(name: str, _token=Depends(verify_firebase_token)):
    """Export a single app's config as YAML text (reuses list_app_info, no extra SDK call)."""
    cfg = config_store.get()
    try:
        comp = _build_composer(cfg)
        result = comp.nebulaObj.list_app_info(name)
        if result.get("status_code") != 200:
            raise HTTPException(status_code=404, detail=f"App '{name}' not found")
        return yaml.dump(result.get("reply", {}), default_flow_style=False)
    except HTTPException:
        raise
    except Exception as exc:
        logging.error(f"export yaml for {name} failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{name}")
async def get_app(name: str, _token=Depends(verify_firebase_token)):
    """Get a single app config."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.nebulaObj.list_app_info(name)
        if result.get("status_code") == 200:
            return {"error": False, "response": result.get("reply", {})}
        return {"error": True, "response": f"App '{name}' not found (status {result.get('status_code')})"}
    except Exception as exc:
        logging.error(f"get_app {name} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("")
async def create_app(req: AppCreateRequest, _token=Depends(verify_firebase_token)):
    """Create a new Nebula app and optionally assign it to device groups."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        config = dict(req.config)
        env_vars = dict(config.get("env_vars") or {})
        env_vars["APP_ID"] = req.name
        config["env_vars"] = env_vars
        result = _handleAsset_with_image_fallback(comp, "app", req.name, "create", config)
        if result.get("error"):
            return {"error": True, "response": result.get("response", "create failed")}

        # Assign to device groups via handleDeviceGroup (mirrors Streamlit pattern)
        errors = []
        for dg in req.device_groups:
            dg_result = comp.handleDeviceGroup(req.name, "update", dg)
            if dg_result.get("error"):
                errors.append(f"Failed to add {req.name} to {dg}: {dg_result.get('response', '')}")

        response = f"App '{req.name}' created successfully"
        if errors:
            response += f"; warnings: {'; '.join(errors)}"
        return {"error": False, "response": response}
    except Exception as exc:
        logging.error(f"create_app failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.put("/{name}")
async def update_app(name: str, req: AppUpdateRequest, _token=Depends(verify_firebase_token)):
    """Update an existing app's config (mirrors Streamlit updateApp exactly)."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        config = dict(req.config)
        # Nebula requires APP_ID in env_vars — Streamlit always injected this.
        env_vars = dict(config.get("env_vars") or {})
        env_vars["APP_ID"] = name
        config["env_vars"] = env_vars
        result = _handleAsset_with_image_fallback(comp, "app", name, "update", config)
        logging.info(f"update_app '{name}' handleAsset result: {result}")
        if not result.get("error"):
            return {"error": False, "response": f"App '{name}' updated successfully"}
        return {"error": True, "response": result.get("response", "update failed")}
    except Exception as exc:
        logging.error(f"update_app {name} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.delete("/{name}")
async def delete_app(name: str, _token=Depends(verify_firebase_token)):
    """Delete an app. Removes it from all device groups first (mirrors Streamlit deleteApp)."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        # Remove from all device groups first via handleDeviceGroup (mirrors Streamlit deleteApp)
        dgs_result = comp.nebulaObj.list_device_groups()
        if dgs_result.get("status_code") == 200:
            for dg in dgs_result.get("reply", {}).get("device_groups", []):
                try:
                    comp.handleDeviceGroup(name, "delete", dg)
                except Exception:
                    pass

        result = comp.handleAsset("app", name, "delete")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "delete failed")}
        return {"error": False, "response": f"App '{name}' deleted"}
    except Exception as exc:
        logging.error(f"delete_app {name} failed: {exc}")
        return {"error": True, "response": str(exc)}
