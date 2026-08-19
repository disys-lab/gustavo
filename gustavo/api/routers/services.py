"""
/api/services — Manager service lifecycle endpoints.

GET  /api/services                      → all 5 services + status (any authenticated user)
GET  /api/services/{svc}/status         → Manager.serviceStatus(svc) (any authenticated user)
POST /api/services/{svc}/run            → background task → returns job_id (admin-only)
POST /api/services/{svc}/action         → body: {action: stop|start|kill|remove|restart} (admin-only)
GET  /api/services/jobs/{job_id}        → poll result of background run (admin-only)

Valid {svc}: redis, mongo, registry, syncer, manager, all
"""
import asyncio
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from gustavo.api import config_store, background
from gustavo.api.auth import require_admin, verify_firebase_token
from gustavo.api.dependencies import _build_manager

router = APIRouter()

VALID_SERVICES = {"redis", "mongo", "registry", "syncer", "manager", "all"}


class ActionRequest(BaseModel):
    action: str  # stop | start | kill | remove | restart


def _get_status_for(man, svc: str) -> dict:
    try:
        return man.serviceStatus(svc)
    except Exception as exc:
        return {"error": True, "response": str(exc)}


@router.get("")
async def list_services(_session=Depends(verify_firebase_token)):
    """Return status for all 5 services. Read-only, open to any authenticated
    user (launch/stop/restart/remove stay admin-only, below).

    Docker calls are blocking, so we run them in a single background thread
    (sequential, same Manager instance) to avoid blocking the event loop.
    """
    cfg = config_store.get()
    services = ["redis", "mongo", "registry", "syncer", "manager"]

    def _all_statuses() -> dict:
        man = _build_manager(cfg)
        result = {}
        for svc in services:
            result[svc] = _get_status_for(man, svc)
            logging.info(f"serviceStatus({svc}): {result[svc]}")
        return result

    try:
        result = await asyncio.wait_for(asyncio.to_thread(_all_statuses), timeout=25.0)
    except asyncio.TimeoutError:
        logging.warning("list_services: timed out after 25s")
        result = {svc: {"error": True, "response": "status check timed out"} for svc in services}
    except Exception as exc:
        logging.error(f"list_services failed: {exc}")
        result = {svc: {"error": True, "response": str(exc)} for svc in services}

    return {"error": False, "response": result}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, _session=Depends(require_admin)):
    """Poll the result of a background run/restore job."""
    job = background.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"error": False, "response": job}


@router.get("/{svc}/status")
async def service_status(svc: str, _session=Depends(verify_firebase_token)):
    """Check status of a single service. Read-only, open to any authenticated user."""
    if svc not in VALID_SERVICES:
        return {"error": True, "response": f"Unknown service: {svc}"}
    cfg = config_store.get()
    man = _build_manager(cfg)
    return _get_status_for(man, svc)


@router.post("/{svc}/run")
async def run_service(
    svc: str,
    bg: BackgroundTasks,
    _session=Depends(require_admin),
):
    """
    Launch a service (long-running). Returns a job_id immediately.
    Poll GET /api/services/jobs/{job_id} for the result.
    """
    if svc not in VALID_SERVICES:
        return {"error": True, "response": f"Unknown service: {svc}"}

    cfg = config_store.get()
    job_id = background.create_job({"service": svc, "action": "run"})

    def _run():
        man = _build_manager(cfg)
        return man.run(svc)

    background.run_in_background(_run, job_id)
    return {"error": False, "response": {"job_id": job_id, "status": "running"}}


@router.post("/{svc}/action")
async def service_action(
    svc: str,
    req: ActionRequest,
    _session=Depends(require_admin),
):
    """
    Perform a lifecycle action on a service.
    action: stop | start | kill | remove | restart
    """
    if svc not in VALID_SERVICES:
        return {"error": True, "response": f"Unknown service: {svc}"}

    valid_actions = {"stop", "start", "kill", "remove", "restart"}
    if req.action not in valid_actions:
        return {"error": True, "response": f"Unknown action: {req.action}. Valid: {valid_actions}"}

    cfg = config_store.get()
    man = _build_manager(cfg)
    try:
        result = man.handleService(svc, req.action)
        return result
    except Exception as exc:
        logging.error(f"service action {req.action} on {svc} failed: {exc}")
        return {"error": True, "response": str(exc)}
