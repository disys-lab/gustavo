"""
/api/backups — Redis and Registry backup management.

Handler methods are ported verbatim from gustavo/pages/5_Backups.py (no Streamlit imports).

GET    /api/backups/redis                       → list .rdb files
POST   /api/backups/redis/create                → BGSAVE → job_id
POST   /api/backups/redis/restore/{filename}    → stop/copy/start → job_id
DELETE /api/backups/redis/{filename}            → delete

GET    /api/backups/registry                       → list backup dirs
POST   /api/backups/registry/create                → copy docker/ dir → job_id
POST   /api/backups/registry/restore/{dirname}     → copy back → job_id
DELETE /api/backups/registry/{dirname}             → delete
"""
import datetime
import logging
import os
import shutil
import subprocess
import time

import docker
from fastapi import APIRouter, BackgroundTasks, Depends

from gustavo.api import config_store, background
from gustavo.api.auth import require_admin

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: get backup dirs from config
# ---------------------------------------------------------------------------

def _redis_bkp_dir() -> str:
    return config_store.get().get("REDIS_BKP_DIR", "/tmp/")


def _registry_bkp_dir() -> str:
    return config_store.get().get("REGISTRY_BKP_DIR", "/tmp/")


def _registry_live_path() -> str:
    """Return the host path to the live Docker registry data directory.

    Prefer the explicit REGISTRY_DATA_PATH setting. Fall back to
    {REGISTRY_BKP_DIR}/docker for backwards compatibility.
    """
    explicit = config_store.get().get("REGISTRY_DATA_PATH", "").strip()
    return explicit if explicit else os.path.join(_registry_bkp_dir(), "docker")


def _redis_auth_token() -> str:
    return config_store.get().get("REDIS_AUTH_TOKEN", "")


# ---------------------------------------------------------------------------
# Redis backup handlers (ported from BackupService in 5_Backups.py)
# ---------------------------------------------------------------------------

def _list_redis_backups_handler() -> dict:
    bkp_dir = _redis_bkp_dir()
    try:
        os.makedirs(bkp_dir, exist_ok=True)
        files = [f for f in os.listdir(bkp_dir) if f.startswith("redis_backup_") and f.endswith(".rdb")]
        backups = []
        for f in files:
            fp = os.path.join(bkp_dir, f)
            ts = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
            backups.append({"filename": f, "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S")})
        return {"error": False, "response": backups}
    except Exception as exc:
        logging.error(f"list_redis_backups: {exc}")
        return {"error": True, "response": str(exc)}


def _create_redis_backup_handler() -> dict:
    bkp_dir = _redis_bkp_dir()
    auth_token = _redis_auth_token()
    client = docker.from_env()
    try:
        redis_container = client.containers.get("redis")
        if not auth_token:
            return {"error": True, "response": "REDIS_AUTH_TOKEN not set"}
        redis_cli_command = f"redis-cli -a '{auth_token}' BGSAVE"
        exec_result = redis_container.exec_run(redis_cli_command)
        if exec_result.exit_code != 0:
            return {"error": True, "response": f"Redis BGSAVE failed: {exec_result.output.decode()}"}
        time.sleep(2)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        original_path = os.path.join(bkp_dir, "dump.rdb")
        backup_filename = f"redis_backup_{timestamp}.rdb"
        new_path = os.path.join(bkp_dir, backup_filename)
        if os.path.exists(original_path):
            os.rename(original_path, new_path)
            return {"error": False, "response": f"Redis backup created: {backup_filename}"}
        return {"error": True, "response": "Redis dump.rdb not found after BGSAVE."}
    except docker.errors.NotFound:
        return {"error": True, "response": "Redis container not found."}
    except docker.errors.APIError as exc:
        return {"error": True, "response": f"Docker API error: {exc}"}
    except Exception as exc:
        return {"error": True, "response": f"Unexpected error: {exc}"}


def _restore_redis_backup_handler(filename: str) -> dict:
    bkp_dir = _redis_bkp_dir()
    client = docker.from_env()
    backup_file_path = os.path.join(bkp_dir, filename)
    redis_data_path = os.path.join(bkp_dir, "dump.rdb")
    if not os.path.exists(backup_file_path):
        return {"error": True, "response": f"Redis backup file not found: {filename}"}
    try:
        try:
            redis_container = client.containers.get("redis")
            redis_container.stop()
        except docker.errors.NotFound:
            pass
        except docker.errors.APIError as exc:
            return {"error": True, "response": f"Docker API error stopping Redis: {exc}"}
        if os.path.exists(redis_data_path):
            os.remove(redis_data_path)
        shutil.copyfile(backup_file_path, redis_data_path)
        try:
            redis_container = client.containers.get("redis")
            redis_container.start()
            return {"error": False, "response": f"Redis restored from {filename} and restarted."}
        except docker.errors.NotFound:
            return {"error": True, "response": "Redis container not found after stop; restore file placed."}
        except docker.errors.APIError as exc:
            return {"error": True, "response": f"Docker API error starting Redis: {exc}"}
    except Exception as exc:
        return {"error": True, "response": f"Unexpected error during Redis restore: {exc}"}


def _delete_redis_backup_handler(filename: str) -> dict:
    bkp_dir = _redis_bkp_dir()
    backup_path = os.path.join(bkp_dir, filename)
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
            return {"error": False, "response": f"Redis backup deleted: {filename}"}
        return {"error": True, "response": f"Redis backup not found: {filename}"}
    except Exception as exc:
        return {"error": True, "response": str(exc)}


# ---------------------------------------------------------------------------
# Registry backup handlers (ported from BackupService in 5_Backups.py)
# ---------------------------------------------------------------------------

def _list_registry_backups_handler() -> dict:
    bkp_dir = _registry_bkp_dir()
    try:
        os.makedirs(bkp_dir, exist_ok=True)
        dirs = [
            d for d in os.listdir(bkp_dir)
            if os.path.isdir(os.path.join(bkp_dir, d)) and d.startswith("registry_backup_")
        ]
        backups = []
        for d in dirs:
            dp = os.path.join(bkp_dir, d)
            ts = datetime.datetime.fromtimestamp(os.path.getmtime(dp))
            backups.append({"filename": d, "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S")})
        return {"error": False, "response": backups}
    except Exception as exc:
        logging.error(f"list_registry_backups: {exc}")
        return {"error": True, "response": str(exc)}


def _create_registry_backup_handler() -> dict:
    bkp_dir = _registry_bkp_dir()
    live_path = _registry_live_path()
    client = docker.from_env()
    try:
        client.containers.get("registry")  # verify it exists
        if not os.path.exists(live_path):
            return {
                "error": True,
                "response": (
                    f"Registry data path not found: {live_path}. "
                    "Set REGISTRY_DATA_PATH in Settings to the host path of your registry data directory."
                ),
            }
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dirname = f"registry_backup_{timestamp}"
        backup_path = os.path.join(bkp_dir, backup_dirname)
        os.makedirs(backup_path, exist_ok=True)
        result = subprocess.run(["cp", "-r", live_path, backup_path], capture_output=True, text=True)
        if result.returncode == 0:
            return {"error": False, "response": f"Registry backup created: {backup_dirname}"}
        if os.path.exists(backup_path) and not os.listdir(backup_path):
            os.rmdir(backup_path)
        return {"error": True, "response": f"Registry backup failed: {result.stderr}"}
    except docker.errors.NotFound:
        return {"error": True, "response": "Registry container not found."}
    except docker.errors.APIError as exc:
        return {"error": True, "response": f"Docker API error: {exc}"}
    except Exception as exc:
        return {"error": True, "response": f"Unexpected error: {exc}"}


def _restore_registry_backup_handler(dirname: str) -> dict:
    bkp_dir = _registry_bkp_dir()
    live_path = _registry_live_path()
    data_name = os.path.basename(live_path.rstrip("/"))
    live_parent = os.path.dirname(live_path.rstrip("/"))

    backup_dir = os.path.join(bkp_dir, dirname)
    if not os.path.exists(backup_dir) or not os.path.isdir(backup_dir):
        return {"error": True, "response": f"Registry backup directory not found: {dirname}"}

    # The backup dir contains a copy of the live data dir (named data_name)
    backed_up_data = os.path.join(backup_dir, data_name)
    restore_src = backed_up_data if os.path.exists(backed_up_data) else backup_dir
    restore_dst = os.path.join(live_parent, data_name) if os.path.exists(backed_up_data) else live_path

    client = docker.from_env()
    try:
        try:
            registry_container = client.containers.get("registry")
            registry_container.stop()
        except docker.errors.NotFound:
            pass
        except docker.errors.APIError as exc:
            return {"error": True, "response": f"Docker API error stopping Registry: {exc}"}

        if os.path.exists(restore_dst):
            shutil.rmtree(restore_dst)
        shutil.copytree(restore_src, restore_dst)

        try:
            registry_container = client.containers.get("registry")
            registry_container.start()
            return {"error": False, "response": f"Registry restored from {dirname} and restarted."}
        except docker.errors.NotFound:
            return {"error": True, "response": "Registry container not found after stop; files restored."}
        except docker.errors.APIError as exc:
            return {"error": True, "response": f"Docker API error starting Registry: {exc}"}
    except Exception as exc:
        return {"error": True, "response": f"Unexpected error during Registry restore: {exc}"}


def _delete_registry_backup_handler(dirname: str) -> dict:
    bkp_dir = _registry_bkp_dir()
    backup_path = os.path.join(bkp_dir, dirname)
    try:
        if os.path.exists(backup_path) and os.path.isdir(backup_path):
            shutil.rmtree(backup_path)
            return {"error": False, "response": f"Registry backup deleted: {dirname}"}
        return {"error": True, "response": f"Registry backup directory not found: {dirname}"}
    except Exception as exc:
        return {"error": True, "response": str(exc)}


# ---------------------------------------------------------------------------
# Redis routes
# ---------------------------------------------------------------------------

@router.get("/redis")
async def list_redis_backups(_session=Depends(require_admin)):
    return _list_redis_backups_handler()


@router.post("/redis/create")
async def create_redis_backup(_session=Depends(require_admin)):
    job_id = background.create_job({"type": "redis_backup", "action": "create"})
    background.run_in_background(_create_redis_backup_handler, job_id)
    return {"error": False, "response": {"job_id": job_id, "status": "running"}}


@router.post("/redis/restore/{filename}")
async def restore_redis_backup(filename: str, _session=Depends(require_admin)):
    job_id = background.create_job({"type": "redis_backup", "action": "restore", "filename": filename})
    background.run_in_background(_restore_redis_backup_handler, job_id, filename)
    return {"error": False, "response": {"job_id": job_id, "status": "running"}}


@router.delete("/redis/{filename}")
async def delete_redis_backup(filename: str, _session=Depends(require_admin)):
    return _delete_redis_backup_handler(filename)


# ---------------------------------------------------------------------------
# Registry routes
# ---------------------------------------------------------------------------

@router.get("/registry")
async def list_registry_backups(_session=Depends(require_admin)):
    return _list_registry_backups_handler()


@router.post("/registry/create")
async def create_registry_backup(_session=Depends(require_admin)):
    job_id = background.create_job({"type": "registry_backup", "action": "create"})
    background.run_in_background(_create_registry_backup_handler, job_id)
    return {"error": False, "response": {"job_id": job_id, "status": "running"}}


@router.post("/registry/restore/{dirname}")
async def restore_registry_backup(dirname: str, _session=Depends(require_admin)):
    job_id = background.create_job({"type": "registry_backup", "action": "restore", "dirname": dirname})
    background.run_in_background(_restore_registry_backup_handler, job_id, dirname)
    return {"error": False, "response": {"job_id": job_id, "status": "running"}}


@router.delete("/registry/{dirname}")
async def delete_registry_backup(dirname: str, _session=Depends(require_admin)):
    return _delete_registry_backup_handler(dirname)
