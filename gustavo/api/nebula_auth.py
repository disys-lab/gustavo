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


def friendly_write_error(exc: Exception) -> str:
    """
    Translate a per-user Composer write failure (update/delete on an app or
    device group) into a message clean enough to show a user.

    Same footgun as verify_db_user_credentials: Nebula's 401/403 responses
    have a plain-text body, not JSON, but the SDK always calls
    response.json() regardless of status code. So when a per-user token is
    invalid or has been regenerated out from under an open session, the
    failure surfaces here as requests.exceptions.JSONDecodeError (a
    RequestException subclass) rather than a clean non-200 status — without
    this translation, the raw parser error ("Expecting value: line 1 column
    1 (char 0)") leaks straight to the user instead of an actionable message.
    """
    if isinstance(exc, requests.exceptions.RequestException):
        return "Your credential is no longer valid — please log in again."
    return str(exc)


def verify_db_user_credentials(cfg: dict, username: str, password: str) -> bool:
    """
    Check whether (username, password) is a valid Nebula Basic-auth pair, by
    calling the Manager's /status with it. Raises ManagerUnreachable if the
    Manager can't be contacted at all (distinct from a wrong/unrecognized
    pair, which just returns False).

    Deliberately Basic auth, not Bearer: Nebula's Basic-auth check looks up
    `username` specifically and compares `password` against that user's own
    stored hash, so a mismatched pair genuinely fails. Bearer verification
    has no claimed-username concept at all — it just scans every user's
    token for any match — so it can't be used here without letting someone
    pair a valid secret with a different (more privileged) claimed username
    and have Gustavo believe the claim.

    Nebula's 401 response body is plain text ("Unauthorized Access"), not
    JSON, but the SDK's check_api() always calls response.json() — so a
    wrong pair raises requests.exceptions.JSONDecodeError (a
    RequestException subclass) here, not a clean non-200 status. Only
    genuine connectivity failures should be treated as "Manager down";
    anything else reachable-but-unparseable means the credentials were wrong.
    """
    comp = _build_composer_for(cfg, username=username, password=password)
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


def resolve_owner_group(cfg: dict, username: str, owner_group: str | None) -> tuple[str | None, str | None]:
    """
    For a non-admin creating a new app or device group: which of their
    groups should be granted rw on it? Returns (group_name, error_message)
    — exactly one is set. Shared by apps.py and device_groups.py, since
    both need identical zero/one/many-groups resolution.
    """
    groups = user_groups(cfg, username)
    if not groups:
        return None, "You are not a member of any group — ask an admin to add you to one before creating resources."
    if owner_group:
        if owner_group not in groups:
            return None, f"You are not a member of group '{owner_group}'"
        return owner_group, None
    if len(groups) > 1:
        return None, f"You belong to multiple groups ({', '.join(groups)}) — specify owner_group."
    return groups[0], None


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
