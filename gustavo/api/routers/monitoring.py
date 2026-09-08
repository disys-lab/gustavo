"""
/api/monitoring — Host vitals, container status, and SSE stream.

GET /api/monitoring/hosts       → Cache.getHosts()
GET /api/monitoring/vitals      → ?device_group=all&host=all
GET /api/monitoring/containers  → ?device_group=all&host=all
GET /api/monitoring/stream      → SSE, emits every 10 s
"""
import ast
import asyncio
import json
import logging
import re
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from sse_starlette.sse import EventSourceResponse

from gustavo.api import config_store
from gustavo.api.auth import require_admin
from gustavo.api.cache_shim import build_cache

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


@router.get("/hosts")
async def get_hosts(
    device_group: str = Query("all"),
    host: str = Query("all"),
    _session=Depends(require_admin),
):
    """
    Which hosts and/or device groups currently exist in the cache. Admin-only.

    Parameters
    ----------
    device_group : str, optional
        A device group name, or `"all"` (default).
    host : str, optional
        A host name, or `"all"` (default).

    Returns
    -------
    dict
        `Cache.getHosts`'s return shape.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _get_hosts_sync, device_group, host)
    return result


@router.get("/vitals")
async def get_vitals(
    device_group: str = Query("all"),
    host: str = Query("all"),
    _session=Depends(require_admin),
):
    """
    Cached CPU/memory/disk vitals for a device group/host filter. Admin-only.

    Parameters
    ----------
    device_group : str, optional
        A device group name, or `"all"` (default).
    host : str, optional
        A host name, or `"all"` (default).

    Returns
    -------
    dict
        `Cache.getAssetsForAll`'s return shape.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _get_vitals_sync, device_group, host)
    return result


@router.get("/containers")
async def get_containers(
    device_group: str = Query("all"),
    host: str = Query("all"),
    _session=Depends(require_admin),
):
    """
    Cached container status for a device group/host filter. Admin-only.

    Parameters
    ----------
    device_group : str, optional
        A device group name, or `"all"` (default).
    host : str, optional
        A host name, or `"all"` (default).

    Returns
    -------
    dict
        `Cache.getAssetsForAll`'s return shape.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _get_containers_sync, device_group, host)
    return result


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
) -> AsyncGenerator[dict, None]:
    """
    Yield monitoring snapshots as SSE events every `SSE_INTERVAL_SECONDS`, forever.

    Parameters
    ----------
    device_group : str
        A device group name, or `"all"`.
    host : str
        A host name, or `"all"`.

    Yields
    ------
    dict
        ``{"event": "monitoring", "data": <JSON str of {"vitals":
        ..., "containers": [...]}>}`` each tick, or ``{"event":
        "error", "data": <JSON str of {"error": ...}>}`` if fetching
        that tick's snapshot raised.
    """
    loop = asyncio.get_event_loop()
    while True:
        try:
            vitals_raw = await loop.run_in_executor(None, _get_vitals_sync, device_group, host)
            containers_raw = await loop.run_in_executor(None, _get_containers_sync, device_group, host)
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
    _session=Depends(require_admin),
):
    """
    Server-Sent Events endpoint. Emits monitoring snapshots every `SSE_INTERVAL_SECONDS`. Admin-only.

    Parameters
    ----------
    device_group : str, optional
        A device group name, or `"all"` (default).
    host : str, optional
        A host name, or `"all"` (default).

    Returns
    -------
    EventSourceResponse
        `text/event-stream`, backed by `_monitoring_event_generator`.

    Notes
    -----
    Browsers can't set `Authorization` headers on `EventSource`, so
    the browser never calls this directly - the Next.js proxy route
    (`app/api/monitoring/stream/route.ts`) reads the `gustavo_token`
    cookie and forwards it here as a real `Authorization: Bearer`
    header.
    """
    return EventSourceResponse(
        _monitoring_event_generator(device_group, host),
        media_type="text/event-stream",
    )
