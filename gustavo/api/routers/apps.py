"""
/api/apps — Nebula application CRUD + registry images + YAML import/export.

GET    /api/apps                     → list all apps (filtered to the caller's grants for non-admins)
GET    /api/apps/registry/images     → list registry images
POST   /api/apps/yaml/parse          → parse uploaded YAML, return config dict
GET    /api/apps/{name}              → get single app config
POST   /api/apps                     → create app (non-admins: auto-granted rw on their own group)
PUT    /api/apps/{name}              → update app (non-admins: enforced by Nebula's own rw check)
DELETE /api/apps/{name}              → delete app (removes from all DGs first)
GET    /api/apps/{name}/yaml         → export app config as YAML text

Permission model: Nebula's per-resource GET checks are exact-match (rw does
NOT imply ro), so single-resource reads always go through the admin composer
with a Python-side permission check here. Writes (create/update/delete) for
non-admins go through a Composer built with that user's own Nebula token, so
Nebula's own rw check is the real enforcement boundary — see
gustavo/api/dependencies.py::_build_composer_for and gustavo/api/nebula_auth.py.
"""
import logging
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from gustavo.api import config_store, nebula_auth
from gustavo.api.auth import verify_firebase_token
from gustavo.api.dependencies import _build_composer, _build_composer_for
from gustavo.api.session import Session

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
    # Only consulted for non-admin callers who belong to more than one
    # user_group — picks which group gets granted rw on the new app.
    owner_group: str | None = None


class AppUpdateRequest(BaseModel):
    config: dict[str, Any]
    device_groups: list[str] | None = None


# Note: /registry/images, /yaml/parse and /defaults are fixed paths — declare them BEFORE /{name}
@router.get("/defaults")
async def get_app_defaults(_token=Depends(verify_firebase_token)):
    """Return default env vars for new app creation with real (unmasked) values.
    Values are read directly from config_store so secrets are never exposed to
    the browser.

    Deliberately does NOT include NEBULA_AUTH_TOKEN/MANAGER_AUTH: env_vars get
    baked into a real container environment variable wherever the app is
    deployed (see docs/cli/apps.md's env_vars format), and base64 is encoding,
    not encryption - anyone with docker/shell access on that device group's
    machine can trivially recover it. Auto-filling either a shared platform
    secret or (worse) the creating user's own personal Nebula credential means
    that credential lands in plaintext on whatever remote hardware the app
    happens to be assigned to, which may not be a machine the creator
    controls or trusts. An app that genuinely needs to call back into the
    Manager should have its creator deliberately supply a credential scoped
    for that purpose, not have one silently defaulted in."""
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
async def list_apps(session: Session = Depends(verify_firebase_token)):
    """List all apps from Nebula, filtered to the caller's grants if not an admin."""
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.nebulaObj.list_apps()
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to list apps (status {result.get('status_code')})"}
        reply = result.get("reply", {})
        if not session.is_admin:
            perms = nebula_auth.compute_permissions(cfg, session.username)
            reply = {**reply, "apps": [a for a in reply.get("apps", []) if a in perms["apps"]]}
        return {"error": False, "response": reply}
    except Exception as exc:
        logging.error(f"list_apps failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.get("/{name}/yaml", response_class=PlainTextResponse)
async def export_app_yaml(name: str, session: Session = Depends(verify_firebase_token)):
    """Export a single app's config as YAML text (reuses list_app_info, no extra SDK call)."""
    cfg = config_store.get()
    if not session.is_admin and name not in nebula_auth.compute_permissions(cfg, session.username)["apps"]:
        raise HTTPException(status_code=403, detail=f"Not permitted for app '{name}'")
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
async def get_app(name: str, session: Session = Depends(verify_firebase_token)):
    """Get a single app config."""
    cfg = config_store.get()
    if not session.is_admin and name not in nebula_auth.compute_permissions(cfg, session.username)["apps"]:
        raise HTTPException(status_code=403, detail=f"Not permitted for app '{name}'")
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
async def create_app(req: AppCreateRequest, session: Session = Depends(verify_firebase_token)):
    """Create a new Nebula app and optionally assign it to device groups.

    Nebula's own create_app check is rw-gated against the app name, which
    can't exist in anyone's group yet — so this always creates via the
    admin composer. For non-admins, we then immediately grant their own
    group rw on the new app name so Nebula's own checks govern it from here on.
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

        if owner_group:
            try:
                group_result = comp.nebulaObj.list_user_group(owner_group)
                existing_apps = group_result.get("reply", {}).get("apps", {}) if group_result.get("status_code") == 200 else {}
                comp.nebulaObj.update_user_group(owner_group, {"apps": {**existing_apps, req.name: "rw"}})
            except Exception as exc:
                logging.error(f"granting '{owner_group}' rw on '{req.name}' failed: {exc}")
                errors.append(f"App created but failed to grant access to group '{owner_group}': {exc}")

        response = f"App '{req.name}' created successfully"
        if errors:
            response += f"; warnings: {'; '.join(errors)}"
        return {"error": False, "response": response}
    except Exception as exc:
        logging.error(f"create_app failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.put("/{name}")
async def update_app(name: str, req: AppUpdateRequest, session: Session = Depends(verify_firebase_token)):
    """Update an existing app's config (mirrors Streamlit updateApp exactly).

    Non-admins go through a Composer authenticated as their own Nebula
    token — Nebula's own rw check is the real gate here, not anything
    Gustavo decides locally.
    """
    cfg = config_store.get()
    comp = _build_composer(cfg) if session.is_admin else _build_composer_for(cfg, token=session.nebula_secret)
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
        return {"error": True, "response": result.get("response", "You do not have write access to this app")}
    except Exception as exc:
        logging.error(f"update_app {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}


@router.delete("/{name}")
async def delete_app(name: str, session: Session = Depends(verify_firebase_token)):
    """Delete an app. Removes it from all device groups first (mirrors Streamlit deleteApp).

    The device-group cleanup is best-effort and always runs as the admin
    composer (it's just removing an association, not a security boundary).
    The actual delete, for non-admins, runs as their own Nebula token so
    Nebula's own rw check is the real gate.
    """
    cfg = config_store.get()
    admin_comp = _build_composer(cfg)
    comp = admin_comp if session.is_admin else _build_composer_for(cfg, token=session.nebula_secret)
    try:
        dgs_result = admin_comp.nebulaObj.list_device_groups()
        if dgs_result.get("status_code") == 200:
            for dg in dgs_result.get("reply", {}).get("device_groups", []):
                try:
                    admin_comp.handleDeviceGroup(name, "delete", dg)
                except Exception:
                    pass

        result = comp.handleAsset("app", name, "delete")
        if result.get("error"):
            return {"error": True, "response": result.get("response", "You do not have write access to this app")}
        return {"error": False, "response": f"App '{name}' deleted"}
    except Exception as exc:
        logging.error(f"delete_app {name} failed: {exc}")
        return {"error": True, "response": nebula_auth.friendly_write_error(exc)}
