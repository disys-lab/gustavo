"""
/api/users — Nebula user + user_group (role) management.

Every db user's login credential is "username:secret" (see nebula_auth.py /
routers/auth.py), where secret is a random value Gustavo generates and
registers with Nebula as *both* that user's token and password — token for
ongoing per-user Bearer calls (apps.py/device_groups.py), password so login
itself can be verified via Nebula's identity-bound Basic auth. Nebula never
returns a usable plaintext secret from create_user/update_user, so Gustavo
captures it at generation time and shows it exactly once — the same
constraint that makes "forgot password" unnecessary: losing a credential
just means regenerating a new one, admin-driven or self-service.

GET    /api/users                        → list users with resolved groups/admin badge
POST   /api/users                        → create user, returns "username:secret" once
DELETE /api/users/{username}             → delete user (and drop from any groups)
POST   /api/users/{username}/regenerate-token → admin: rotate a user's credential
POST   /api/users/me/regenerate-token    → self-service: rotate my own credential
GET    /api/users/me/groups              → the names of groups I belong to (any authenticated user)

GET    /api/users/groups                 → list groups (roles) with full detail
POST   /api/users/groups                 → create a group
PUT    /api/users/groups/{name}          → update a group
DELETE /api/users/groups/{name}          → delete a group
"""
import logging
import re
import secrets as _secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from gustavo.api import config_store, nebula_auth
from gustavo.api.auth import require_admin, verify_firebase_token
from gustavo.api.dependencies import _build_composer
from gustavo.api.session import Session

router = APIRouter()

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class UserCreateRequest(BaseModel):
    username: str
    group: str | None = None


class GroupCreateRequest(BaseModel):
    name: str
    group_members: list[str] = []
    apps: dict[str, str] = {}
    device_groups: dict[str, str] = {}
    admin: bool = False
    pruning_allowed: bool = False
    cron_jobs: dict[str, str] = {}


class GroupUpdateRequest(BaseModel):
    group_members: list[str] | None = None
    apps: dict[str, str] | None = None
    device_groups: dict[str, str] | None = None
    admin: bool | None = None
    pruning_allowed: bool | None = None
    cron_jobs: dict[str, str] | None = None


def _new_secret() -> str:
    return _secrets.token_urlsafe(32)


def _credential(username: str, secret: str) -> str:
    return f"{username}:{secret}"


def _all_groups(comp) -> dict[str, dict]:
    """name -> group doc, for every user_group. Skips any that fail to fetch."""
    result = comp.nebulaObj.list_user_groups()
    if result.get("status_code") != 200:
        return {}
    groups = {}
    for name in result.get("reply", {}).get("user_groups", []):
        g = comp.nebulaObj.list_user_group(name)
        if g.get("status_code") == 200:
            groups[name] = g.get("reply", {})
    return groups


@router.get("")
async def list_users(_session=Depends(require_admin)):
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        users_result = comp.nebulaObj.list_users()
        if users_result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to list users (status {users_result.get('status_code')})"}
        usernames = users_result.get("reply", {}).get("users", [])

        groups = _all_groups(comp)
        users = []
        for username in usernames:
            member_of = [name for name, g in groups.items() if username in (g.get("group_members") or [])]
            is_admin = any(groups[name].get("admin") is True for name in member_of)
            users.append({"username": username, "groups": member_of, "is_admin": is_admin})
        return {"error": False, "response": {"users": users}}
    except Exception as exc:
        logging.error(f"list_users failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("")
async def create_user(req: UserCreateRequest, _session=Depends(require_admin)):
    if not _USERNAME_RE.match(req.username):
        return {"error": True, "response": "Usernames may only contain letters, digits, hyphens, and underscores"}

    cfg = config_store.get()
    comp = _build_composer(cfg)
    secret = _new_secret()
    try:
        # Both fields get the same secret: token is used for ongoing per-user
        # Bearer calls (apps.py/device_groups.py), password is what makes
        # login's Basic-auth check identity-bound (see nebula_auth.py).
        result = comp.nebulaObj.create_user(req.username, {"token": secret, "password": secret})
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to create user (status {result.get('status_code')}): {result.get('reply')}"}

        if req.group:
            group_result = comp.nebulaObj.list_user_group(req.group)
            if group_result.get("status_code") != 200:
                return {
                    "error": False,
                    "response": {
                        "username": req.username,
                        "credential": _credential(req.username, secret),
                        "warning": f"User created but group '{req.group}' was not found",
                    },
                }
            members = list(group_result.get("reply", {}).get("group_members") or [])
            if req.username not in members:
                members.append(req.username)
            comp.nebulaObj.update_user_group(req.group, {"group_members": members})

        return {"error": False, "response": {"username": req.username, "credential": _credential(req.username, secret)}}
    except Exception as exc:
        logging.error(f"create_user failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.delete("/{username}")
async def delete_user(username: str, _session=Depends(require_admin)):
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        # Drop from any groups first so no stale membership references remain.
        for name, group in _all_groups(comp).items():
            members = group.get("group_members") or []
            if username in members:
                comp.nebulaObj.update_user_group(name, {"group_members": [m for m in members if m != username]})

        result = comp.nebulaObj.delete_user(username)
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to delete user (status {result.get('status_code')})"}
        return {"error": False, "response": f"User '{username}' deleted"}
    except Exception as exc:
        logging.error(f"delete_user {username} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("/me/regenerate-token")
async def regenerate_my_token(session: Session = Depends(verify_firebase_token)):
    """Self-service credential rotation — no admin required, no old-secret confirmation
    needed since the caller is already authenticated via their current session.

    Declared BEFORE /{username}/regenerate-token: FastAPI matches path routes
    in declaration order, and a dynamic /{username}/... segment would
    otherwise swallow the literal "me" path first.
    """
    if session.user_type != "db":
        return {"error": True, "response": "This account type doesn't have a Nebula token to regenerate"}
    cfg = config_store.get()
    comp = _build_composer(cfg)
    secret = _new_secret()
    try:
        result = comp.nebulaObj.update_user(session.username, {"token": secret, "password": secret})
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to regenerate token (status {result.get('status_code')})"}
        return {"error": False, "response": {"username": session.username, "credential": _credential(session.username, secret)}}
    except Exception as exc:
        logging.error(f"regenerate_my_token for {session.username} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("/{username}/regenerate-token")
async def regenerate_token(username: str, _session=Depends(require_admin)):
    cfg = config_store.get()
    comp = _build_composer(cfg)
    secret = _new_secret()
    try:
        result = comp.nebulaObj.update_user(username, {"token": secret, "password": secret})
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to regenerate token (status {result.get('status_code')})"}
        return {"error": False, "response": {"username": username, "credential": _credential(username, secret)}}
    except Exception as exc:
        logging.error(f"regenerate_token {username} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.get("/me/groups")
async def my_groups(session: Session = Depends(verify_firebase_token)):
    """Which groups the caller belongs to — used by the Apps page to decide
    whether a non-admin needs to pick an owner_group when creating an app."""
    if session.is_admin:
        return {"error": False, "response": {"groups": []}}
    cfg = config_store.get()
    return {"error": False, "response": {"groups": nebula_auth.user_groups(cfg, session.username)}}


@router.get("/groups")
async def list_groups(_session=Depends(require_admin)):
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        groups = _all_groups(comp)
        return {"error": False, "response": {"groups": [{"name": name, **doc} for name, doc in groups.items()]}}
    except Exception as exc:
        logging.error(f"list_groups failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.post("/groups")
async def create_group(req: GroupCreateRequest, _session=Depends(require_admin)):
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.nebulaObj.create_user_group(
            req.name,
            {
                "group_members": req.group_members,
                "apps": req.apps,
                "device_groups": req.device_groups,
                "admin": req.admin,
                "pruning_allowed": req.pruning_allowed,
                "cron_jobs": req.cron_jobs,
            },
        )
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to create group (status {result.get('status_code')}): {result.get('reply')}"}
        return {"error": False, "response": f"Group '{req.name}' created"}
    except Exception as exc:
        logging.error(f"create_group failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.put("/groups/{name}")
async def update_group(name: str, req: GroupUpdateRequest, _session=Depends(require_admin)):
    cfg = config_store.get()
    comp = _build_composer(cfg)
    partial = {k: v for k, v in req.model_dump().items() if v is not None}
    if not partial:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        result = comp.nebulaObj.update_user_group(name, partial)
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to update group (status {result.get('status_code')})"}
        return {"error": False, "response": f"Group '{name}' updated"}
    except Exception as exc:
        logging.error(f"update_group {name} failed: {exc}")
        return {"error": True, "response": str(exc)}


@router.delete("/groups/{name}")
async def delete_group(name: str, _session=Depends(require_admin)):
    cfg = config_store.get()
    comp = _build_composer(cfg)
    try:
        result = comp.nebulaObj.delete_user_group(name)
        if result.get("status_code") != 200:
            return {"error": True, "response": f"Failed to delete group (status {result.get('status_code')})"}
        return {"error": False, "response": f"Group '{name}' deleted"}
    except Exception as exc:
        logging.error(f"delete_group {name} failed: {exc}")
        return {"error": True, "response": str(exc)}
