"""
Thread-safe in-memory job store for long-running background tasks.

Usage:
    job_id = create_job()
    # In a background task:
    try:
        result = some_blocking_call()
        complete_job(job_id, result)
    except Exception as e:
        fail_job(job_id, str(e))

Clients poll GET /api/services/jobs/{job_id} until status is 'done' or 'error'.
"""
import threading
import uuid
from typing import Any

_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


def create_job(meta: dict | None = None) -> str:
    """Create a new job and return its ID."""
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "running",
            "result": None,
            "error": None,
            **(meta or {}),
        }
    return job_id


def complete_job(job_id: str, result: Any) -> None:
    """Mark a job as done with the given result."""
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["result"] = result


def fail_job(job_id: str, error: str) -> None:
    """Mark a job as failed with an error message."""
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = error


def get_job(job_id: str) -> dict | None:
    """Return the current state of a job, or None if not found."""
    with _lock:
        return dict(_jobs.get(job_id, {})) if job_id in _jobs else None


def run_in_background(fn, job_id: str, *args, **kwargs) -> None:
    """
    Execute *fn* in a daemon thread, updating *job_id* on completion.

    fn must return a dict with keys 'error' and 'response'.
    """
    def _worker():
        try:
            result = fn(*args, **kwargs)
            complete_job(job_id, result)
        except Exception as exc:
            fail_job(job_id, str(exc))

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
