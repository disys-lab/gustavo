"""
/api/monitoring — Host vitals, container status, and SSE stream.

GET /api/monitoring/hosts       → Cache.getHosts()
GET /api/monitoring/vitals      → ?device_group=all&host=all
GET /api/monitoring/containers  → ?device_group=all&host=all
GET /api/monitoring/stream      → SSE, emits every 10 s

Open to any authenticated user, not just admins - non-admins see the
same shape of data an admin does, scoped to their own device-group
grants (ro or rw; viewing doesn't need rw). See
_permitted_device_groups/_scope_hosts_response/_scoped_asset_call.
"""
import ast
import asyncio
import json
import logging
import re
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from gustavo.api import config_store, nebula_auth
from gustavo.api.auth import verify_firebase_token
from gustavo.api.cache_shim import build_cache
from gustavo.api.session import Session

router = APIRouter()

SSE_INTERVAL_SECONDS = 10


def _get_hosts_sync(device_group: str = "all", host: str = "all") -> dict:
    """
    Blocking wrapper around `Cache.getHosts`, run via `run_in_executor` since `Cache` uses a sync Redis client.

    Parameters
    ----------
    device_group : str, optional
    host : str, optional

    Returns
    -------
    dict
        `Cache.getHosts`'s return shape, or
        ``{"error": True, "response": <str(exception)>}`` on failure.
    """
    try:
        cache = build_cache()
        return cache.getHosts(device_group, host)
    except Exception as exc:
        logging.error(f"getHosts failed: {exc}")
        return {"error": True, "response": str(exc)}


def _get_vitals_sync(device_group: str = "all", host: str = "all") -> dict:
    """
    Blocking wrapper around `Cache.getAssetsForAll("vitals", ...)`, run via `run_in_executor`.

    Parameters
    ----------
    device_group : str, optional
    host : str, optional

    Returns
    -------
    dict
        `Cache.getAssetsForAll`'s return shape, or
        ``{"error": True, "response": <str(exception)>}`` on failure.
    """
    try:
        cache = build_cache()
        return cache.getAssetsForAll("vitals", device_group, host)
    except Exception as exc:
        logging.error(f"getVitals failed: {exc}")
        return {"error": True, "response": str(exc)}


def _get_containers_sync(device_group: str = "all", host: str = "all") -> dict:
    """
    Blocking wrapper around `Cache.getAssetsForAll("containers", ...)`, run via `run_in_executor`.

    Parameters
    ----------
    device_group : str, optional
    host : str, optional

    Returns
    -------
    dict
        `Cache.getAssetsForAll`'s return shape, or
        ``{"error": True, "response": <str(exception)>}`` on failure.
    """
    try:
        cache = build_cache()
        return cache.getAssetsForAll("containers", device_group, host)
    except Exception as exc:
        logging.error(f"getContainers failed: {exc}")
        return {"error": True, "response": str(exc)}


def _permitted_device_groups(session: Session, cfg: dict) -> list[str] | None:
    """
    Which device groups `session` may view monitoring data for.

    Parameters
    ----------
    session : Session
    cfg : dict
        Current platform config.

    Returns
    -------
    list of str or None
        `None` means unrestricted (admin) - every device group.
        Otherwise, the caller's own device-group grants, `ro` or `rw`
        - viewing doesn't require `rw`.
    """
    if session.is_admin:
        return None
    return list(nebula_auth.compute_permissions(cfg, session.username)["device_groups"].keys())


def _scope_hosts_response(result: dict, permitted: list[str]) -> dict:
    """
    Narrow a `Cache.getHosts` result to `permitted` device groups.

    Parameters
    ----------
    result : dict
        `_get_hosts_sync`'s return value.
    permitted : list of str
        The caller's own device-group grants.

    Returns
    -------
    dict
        `result`, with its `response` narrowed in place. The dict
        shape (`{host: [device_group, ...]}`, both filters `"all"`)
        has each host's list filtered, dropping hosts left with none.
        The list shape (one filter specific, the other `"all"`) is
        filtered directly. The bool shape (neither `"all"`) is
        unreachable here - the caller already 403s an unpermitted
        specific device group before this runs.
    """
    response = result.get("response")
    if isinstance(response, dict):
        narrowed = {host: [dg for dg in dgs if dg in permitted] for host, dgs in response.items()}
        result["response"] = {host: dgs for host, dgs in narrowed.items() if dgs}
    elif isinstance(response, list):
        result["response"] = [dg for dg in response if dg in permitted]
    return result


async def _scoped_asset_call(sync_fn, device_group: str, host: str, session: Session, cfg: dict) -> dict:
    """
    Run `sync_fn` (`_get_vitals_sync` or `_get_containers_sync`), scoped to `session`'s own device groups.

    Parameters
    ----------
    sync_fn : callable
        `_get_vitals_sync` or `_get_containers_sync`.
    device_group, host : str
    session : Session
    cfg : dict
        Current platform config.

    Returns
    -------
    dict
        `sync_fn`'s own return shape.

    Raises
    ------
    HTTPException
        403 if `device_group` is a specific value the caller isn't
        granted on.

    Notes
    -----
    `Cache.getAssetsForAll("all", ...)` returns only the *first*
    matching host it finds scanning every cached device group - not
    filterable after the fact, since a "no data matches" result and a
    real match are both `error: False` and only distinguishable by
    sniffing the response string. So for a non-admin's `device_group
    == "all"`, this calls `sync_fn` once per permitted device group
    instead (real per-group semantics, already well-defined), keeping
    the first real match - the same "first match wins" behavior an
    admin's `"all"` query already has, just restricted to the
    caller's own groups instead of every cached one.
    """
    loop = asyncio.get_event_loop()
    permitted = _permitted_device_groups(session, cfg)

    if permitted is None or device_group != "all":
        if permitted is not None and device_group not in permitted:
            raise HTTPException(status_code=403, detail=f"Not permitted for device group '{device_group}'")
        return await loop.run_in_executor(None, sync_fn, device_group, host)

    for dg in permitted:
        result = await loop.run_in_executor(None, sync_fn, dg, host)
        if not result.get("error") and "at time:" in str(result.get("response", "")):
            return result
    return {"error": False, "response": "No data matches the query for your device groups"}


@router.get("/hosts")
async def get_hosts(
    device_group: str = Query("all"),
    host: str = Query("all"),
    session: Session = Depends(verify_firebase_token),
):
    """
    Which hosts and/or device groups currently exist in the cache.

    Parameters
    ----------
    device_group : str, optional
        A device group name, or `"all"` (default).
    host : str, optional
        A host name, or `"all"` (default).
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        `Cache.getHosts`'s return shape, narrowed to the caller's own
        device-group grants if not admin.

    Raises
    ------
    HTTPException
        403 if `device_group` is a specific value the caller isn't
        granted on.
    """
    cfg = config_store.get()
    permitted = _permitted_device_groups(session, cfg)
    if permitted is not None and device_group != "all" and device_group not in permitted:
        raise HTTPException(status_code=403, detail=f"Not permitted for device group '{device_group}'")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _get_hosts_sync, device_group, host)
    if permitted is not None:
        result = _scope_hosts_response(result, permitted)
    return result


@router.get("/vitals")
async def get_vitals(
    device_group: str = Query("all"),
    host: str = Query("all"),
    session: Session = Depends(verify_firebase_token),
):
    """
    Cached CPU/memory/disk vitals for a device group/host filter.

    Parameters
    ----------
    device_group : str, optional
        A device group name, or `"all"` (default).
    host : str, optional
        A host name, or `"all"` (default).
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        `Cache.getAssetsForAll`'s return shape, scoped to the
        caller's own device-group grants if not admin - see
        `_scoped_asset_call`.
    """
    return await _scoped_asset_call(_get_vitals_sync, device_group, host, session, config_store.get())


@router.get("/containers")
async def get_containers(
    device_group: str = Query("all"),
    host: str = Query("all"),
    session: Session = Depends(verify_firebase_token),
):
    """
    Cached container status for a device group/host filter.

    Parameters
    ----------
    device_group : str, optional
        A device group name, or `"all"` (default).
    host : str, optional
        A host name, or `"all"` (default).
    session : Session
        The authenticated caller.

    Returns
    -------
    dict
        `Cache.getAssetsForAll`'s return shape, scoped to the
        caller's own device-group grants if not admin - see
        `_scoped_asset_call`.
    """
    return await _scoped_asset_call(_get_containers_sync, device_group, host, session, config_store.get())


def _extract_vitals(vitals_result: dict) -> dict:
    """
    Parse `Cache.getIndividualVitals`'s summary string (via `getAssetsForAll`) into structured metrics.

    Parameters
    ----------
    vitals_result : dict
        `_get_vitals_sync`'s return value - the nested shape
        ``{"error": bool, "response": {"error": bool, "response":
        "<string>"}}``, where the inner string looks like
        `"host@ip at time:TIMESTAMP\\t mem:{'total':...}\\t
        disk:{...}\\tcpu_cores:N\\tcpu_percent:X.X"`.

    Returns
    -------
    dict
        ``{"host": str, "timestamp": int, "cpu_percent": float,
        "cpu_cores": int, "memory_mb": dict, "disk_mb": dict}``, with
        any field missing from the input's regex matches simply
        absent (not defaulted). `{}` if the input isn't parseable at
        all.
    """
    try:
        inner = vitals_result.get("response", {})
        raw = inner.get("response", "") if isinstance(inner, dict) else str(inner)
        if not isinstance(raw, str) or not raw.strip():
            return {}

        result: dict = {}

        m = re.match(r"^(\S+)\s*at time:(\d+)", raw)
        if m:
            result["host"] = m.group(1)
            result["timestamp"] = int(m.group(2))

        m = re.search(r"cpu_percent:([\d.]+)", raw)
        if m:
            result["cpu_percent"] = float(m.group(1))

        m = re.search(r"cpu_cores:(\d+)", raw)
        if m:
            result["cpu_cores"] = int(m.group(1))

        m = re.search(r"mem:\{([^}]+)\}", raw)
        if m:
            pairs = re.findall(r"'(\w+)':\s*(\d+)", m.group(1))
            result["memory_mb"] = {k: int(v) for k, v in pairs}

        m = re.search(r"disk:\{([^}]+)\}", raw)
        if m:
            pairs = re.findall(r"'(\w+)':\s*(\d+)", m.group(1))
            result["disk_mb"] = {k: int(v) for k, v in pairs}

        return result
    except Exception as exc:
        logging.warning(f"_extract_vitals parse error: {exc}")
        return {}


def _extract_containers(containers_result: dict) -> list:
    """
    Parse `Cache.getIndividualContainers`'s summary string (via `getAssetsForAll`) into simplified per-container metrics.

    Parameters
    ----------
    containers_result : dict
        `_get_containers_sync`'s return value - the nested shape
        ``{"error": bool, "response": {"error": bool, "response":
        "<string>"}}``, where the inner string ends with
        `"containers:[{<docker stats dict>}, ...]"`.

    Returns
    -------
    list of dict
        One entry per container: ``{"name": str, "cpu_percent":
        float, "memory_mb": float, "memory_limit_mb": float,
        "memory_percent": float}``, computed from each raw Docker
        stats dict via the standard Docker CPU%/memory% formulas.
        `[]` if the input isn't parseable at all; a given container's
        cpu/memory fields default to `0.0` if that container's stats
        dict is missing the keys the formula needs.
    """
    try:
        inner = containers_result.get("response", {})
        raw = inner.get("response", "") if isinstance(inner, dict) else str(inner)
        if not isinstance(raw, str) or not raw.strip():
            return []

        m = re.search(r"containers:\[(.+)\]$", raw, re.DOTALL)
        if not m:
            return []

        containers = ast.literal_eval(f"[{m.group(1)}]")
        result = []
        for c in containers:
            name = c.get("name", "unknown").lstrip("/")

            # Docker CPU% formula
            cpu_pct = 0.0
            try:
                cd = (c["cpu_stats"]["cpu_usage"]["total_usage"]
                      - c["precpu_stats"]["cpu_usage"]["total_usage"])
                sd = (c["cpu_stats"]["system_cpu_usage"]
                      - c["precpu_stats"]["system_cpu_usage"])
                nc = c["cpu_stats"].get("online_cpus", 1)
                if sd > 0:
                    cpu_pct = (cd / sd) * nc * 100.0
            except Exception:
                pass

            mem_mb = mem_limit_mb = mem_pct = 0.0
            try:
                mem_mb = c["memory_stats"]["usage"] / 1024 / 1024
                mem_limit_mb = c["memory_stats"]["limit"] / 1024 / 1024
                if mem_limit_mb > 0:
                    mem_pct = mem_mb / mem_limit_mb * 100
            except Exception:
                pass

            result.append({
                "name": name,
                "cpu_percent": round(cpu_pct, 2),
                "memory_mb": round(mem_mb, 1),
                "memory_limit_mb": round(mem_limit_mb, 1),
                "memory_percent": round(mem_pct, 2),
            })
        return result
    except Exception as exc:
        logging.warning(f"_extract_containers parse error: {exc}")
        return []


async def _monitoring_event_generator(
    device_group: str,
    host: str,
    session: Session,
    cfg: dict,
) -> AsyncGenerator[dict, None]:
    """
    Yield monitoring snapshots as SSE events every `SSE_INTERVAL_SECONDS`, forever.

    Parameters
    ----------
    device_group : str
        A device group name, or `"all"`.
    host : str
        A host name, or `"all"`.
    session : Session
        The authenticated caller - scoping is resolved once here, not
        re-checked per tick, since it doesn't change within the
        lifetime of one SSE connection.
    cfg : dict
        Current platform config.

    Yields
    ------
    dict
        ``{"event": "monitoring", "data": <JSON str of {"vitals":
        ..., "containers": [...]}>}`` each tick, or ``{"event":
        "error", "data": <JSON str of {"error": ...}>}`` if fetching
        that tick's snapshot raised.
    """
    while True:
        try:
            vitals_raw = await _scoped_asset_call(_get_vitals_sync, device_group, host, session, cfg)
            containers_raw = await _scoped_asset_call(_get_containers_sync, device_group, host, session, cfg)
            payload = json.dumps({
                "vitals": _extract_vitals(vitals_raw),
                "containers": _extract_containers(containers_raw),
            })
            yield {"event": "monitoring", "data": payload}
        except Exception as exc:
            logging.error(f"SSE monitoring error: {exc}")
            yield {"event": "error", "data": json.dumps({"error": str(exc)})}
        await asyncio.sleep(SSE_INTERVAL_SECONDS)


@router.get("/stream")
async def monitoring_stream(
    device_group: str = Query("all"),
    host: str = Query("all"),
    session: Session = Depends(verify_firebase_token),
):
    """
    Server-Sent Events endpoint. Emits monitoring snapshots every `SSE_INTERVAL_SECONDS`.

    Parameters
    ----------
    device_group : str, optional
        A device group name, or `"all"` (default).
    host : str, optional
        A host name, or `"all"` (default).
    session : Session
        The authenticated caller.

    Returns
    -------
    EventSourceResponse
        `text/event-stream`, backed by `_monitoring_event_generator`.

    Raises
    ------
    HTTPException
        403 if `device_group` is a specific value the caller isn't
        granted on.

    Notes
    -----
    Browsers can't set `Authorization` headers on `EventSource`, so
    the browser never calls this directly - the Next.js proxy route
    (`app/api/monitoring/stream/route.ts`) reads the `gustavo_token`
    cookie and forwards it here as a real `Authorization: Bearer`
    header.
    """
    cfg = config_store.get()
    permitted = _permitted_device_groups(session, cfg)
    if permitted is not None and device_group != "all" and device_group not in permitted:
        raise HTTPException(status_code=403, detail=f"Not permitted for device group '{device_group}'")

    return EventSourceResponse(
        _monitoring_event_generator(device_group, host, session, cfg),
        media_type="text/event-stream",
    )
