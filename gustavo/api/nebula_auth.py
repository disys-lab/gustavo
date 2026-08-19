"""
Bridges Gustavo sessions to Nebula's own user/user_group RBAC.

Nebula (see nebula-orchestrator/manager/manager.py) already has real
multi-user auth: a `users` collection (db users, token or password based)
and a `user_groups` collection (group_members + apps/device_groups ro-rw
maps + admin flag — a group *is* a role). Gustavo doesn't keep a competing
copy of any of this; these helpers just read/verify against Nebula directly,
using the platform admin composer for anything that needs elevated access
(listing all groups, etc.) and a per-user composer for verifying a specific
user's own token.
"""
import requests

from gustavo.api.dependencies import _build_composer, _build_composer_for


class ManagerUnreachable(Exception):
    """The Nebula Manager API could not be reached at all."""


def verify_db_user_token(cfg: dict, secret: str) -> bool:
    """
    Check whether `secret` is a valid Nebula token for some db user, by
    calling the Manager's /status with it as a Bearer token. Raises
    ManagerUnreachable if the Manager can't be contacted at all (distinct
    from an invalid/unrecognized token, which just returns False).

    Nebula's 401 response body is plain text ("Unauthorized Access"), not
    JSON, but the SDK's check_api() always calls response.json() — so an
    invalid token raises requests.exceptions.JSONDecodeError (a
    RequestException subclass) here, not a clean non-200 status. Only
    genuine connectivity failures should be treated as "Manager down";
    anything else reachable-but-unparseable means the credential was wrong.
    """
    comp = _build_composer_for(cfg, token=secret)
    try:
        result = comp.nebulaObj.check_api()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise ManagerUnreachable(str(exc)) from exc
    except requests.exceptions.RequestException:
        return False
    return result.get("status_code") == 200


def compute_permissions(cfg: dict, username: str) -> dict:
    """
    Mirrors Nebula's own mongo_list_user_permissions: the union of
    apps/device_groups/cron_jobs/admin/pruning_allowed across every
    user_group `username` belongs to. Always uses the platform admin
    composer — listing/reading every group is an admin-only operation on
    the Nebula side.
    """
    permissions = {"apps": {}, "device_groups": {}, "admin": False, "pruning_allowed": False, "cron_jobs": {}}
    comp = _build_composer(cfg)

    try:
        groups_result = comp.nebulaObj.list_user_groups()
    except requests.exceptions.RequestException:
        # Fail closed: if Nebula can't be reached, a non-admin sees no grants
        # rather than the request crashing.
        return permissions
    if groups_result.get("status_code") != 200:
        return permissions

    group_names = groups_result.get("reply", {}).get("user_groups", [])
    for group_name in group_names:
        try:
            group_result = comp.nebulaObj.list_user_group(group_name)
        except requests.exceptions.RequestException:
            continue
        if group_result.get("status_code") != 200:
            continue
        group = group_result.get("reply", {})
        if username not in (group.get("group_members") or []):
            continue
        if group.get("admin") is True:
            permissions["admin"] = True
        if group.get("pruning_allowed") is True:
            permissions["pruning_allowed"] = True
        permissions["apps"] = {**permissions["apps"], **(group.get("apps") or {})}
        permissions["device_groups"] = {**permissions["device_groups"], **(group.get("device_groups") or {})}
        permissions["cron_jobs"] = {**permissions["cron_jobs"], **(group.get("cron_jobs") or {})}

    return permissions


def user_groups(cfg: dict, username: str) -> list[str]:
    """Names of every user_group `username` is a member of."""
    comp = _build_composer(cfg)
    try:
        groups_result = comp.nebulaObj.list_user_groups()
    except requests.exceptions.RequestException:
        return []
    if groups_result.get("status_code") != 200:
        return []

    names = []
    for group_name in groups_result.get("reply", {}).get("user_groups", []):
        try:
            group_result = comp.nebulaObj.list_user_group(group_name)
        except requests.exceptions.RequestException:
            continue
        if group_result.get("status_code") != 200:
            continue
        if username in (group_result.get("reply", {}).get("group_members") or []):
            names.append(group_name)
    return names
