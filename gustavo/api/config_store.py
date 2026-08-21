"""
YAML-backed config singleton — replaces st.session_state for FastAPI.

On startup: load() reads /etc/gustavo/platform.yaml (or GUSTAVO_API_CONFIG env var).
Routes call get() to obtain the current dict; POST /api/config calls update() to persist.
"""
import os
import socket
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(os.environ.get("GUSTAVO_API_CONFIG", "/etc/gustavo/platform.yaml"))
ENV_SHIM_PATH = Path("/tmp/gustavo_api.env")

try:
    _host_ip = socket.gethostbyname(socket.gethostname())
except Exception:
    _host_ip = "127.0.0.1"

DEFAULTS: dict[str, Any] = {
    # Manager
    "MANAGER_HOST": _host_ip,
    "MANAGER_PORT": "8080",
    "MANAGER_NMODE": "bridge",
    "MANAGER_IMAGE": "ghcr.io/disys-lab/gustavo-manager:latest",
    "CACHE_EXPIRE_TIME": "120",
    # Nebula credentials
    "NEBULA_USERNAME": "nebula",
    "NEBULA_PASSWORD": "nebula",
    "NEBULA_AUTH_TOKEN": "bmVidWxhOm5lYnVsYQ==",
    "NEBULA_PROTOCOL": "http",
    # Registry
    "REGISTRY_HOST": _host_ip,
    "REGISTRY_PORT": "5001",
    "REGISTRY_IP_DISABLED": True,
    "REGISTRY_IMAGE": "registry:2",
    "REGISTRY_BKP_DIR": "/tmp/",
    "REGISTRY_DATA_PATH": "",  # Host path to live registry data dir (e.g. /data/registry/docker)
    # Syncer
    "SYNCER_IMAGE": "ghcr.io/disys-lab/dregsy:latest",
    "SYNCER_NMODE": "host",
    "DREGSY_CONFIG_FILE_PATH": "",
    "DREGSY_MAPPING_FILE_PATH": "",
    # Redis
    "REDIS_HOST": _host_ip,
    "REDIS_PORT": "6379",
    "REDIS_IP_DISABLED": True,
    "REDIS_AUTH_TOKEN": "e87052bfcc0b65b2d0603ad4baa8d8ced7aa929b6698a568d2ce53dfd2dc04bcs",
    "REDIS_IMAGE": "redis/redis-stack:7.4.0-v1",
    "REDIS_BKP_DIR": "/tmp/",
    # MongoDB
    "MONGO_HOST": _host_ip,
    "MONGO_PORT": "27017",
    "MONGO_IP_DISABLED": True,
    "MONGO_USERNAME": "nebula",
    "MONGO_PASSWORD": "nebula",
    "MONGO_CERTIFICATE_FOLDER_PATH": "/tmp/",
    "MONGO_IMAGE": "mongo:4.0.19",
    "MONGO_BKP_DIR": "/tmp/",
    # Worker / misc
    "WORKER_NMODE": "host",
}

_SENSITIVE_KEYS = {"NEBULA_PASSWORD", "NEBULA_AUTH_TOKEN", "REDIS_AUTH_TOKEN", "MONGO_PASSWORD"}

# Keys that, when set as container environment variables, always win over
# platform.yaml/DEFAULTS. This keeps the break-glass admin login
# (auth.py, compared directly against os.environ) from ever diverging from
# what _build_manager/_build_composer actually use to talk to Nebula.
_ENV_OVERRIDE_KEYS = ("NEBULA_USERNAME", "NEBULA_PASSWORD")

_config: dict[str, Any] = {}


def _apply_env_overrides(cfg: dict[str, Any]) -> None:
    for key in _ENV_OVERRIDE_KEYS:
        value = os.environ.get(key)
        if value:
            cfg[key] = value


def load() -> dict[str, Any]:
    """Read YAML from disk, merge with DEFAULTS, and return the result."""
    global _config
    merged = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open() as f:
                on_disk = yaml.safe_load(f) or {}
            merged.update({k: v for k, v in on_disk.items() if v is not None})
        except Exception as exc:
            import logging
            logging.error(f"config_store: failed to load {CONFIG_PATH}: {exc}")
    _apply_env_overrides(merged)
    _config = merged
    _write_env_shim()
    return _config


def get() -> dict[str, Any]:
    """Return the current in-memory config (loads lazily if not yet initialised)."""
    if not _config:
        load()
    return _config


def update(partial: dict[str, Any]) -> dict[str, Any]:
    """Merge *partial* into the config, persist to YAML and refresh the env shim."""
    global _config
    if not _config:
        load()
    _config.update(partial)
    _apply_env_overrides(_config)
    _persist()
    _write_env_shim()
    return _config


def masked() -> dict[str, Any]:
    """Return the config with sensitive values replaced by '***'."""
    return {k: ("***" if k in _SENSITIVE_KEYS else v) for k, v in get().items()}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _persist() -> None:
    """Write the current config to CONFIG_PATH as YAML."""
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w") as f:
            yaml.safe_dump(_config, f, default_flow_style=False)
    except Exception as exc:
        import logging
        logging.error(f"config_store: failed to write {CONFIG_PATH}: {exc}")


def _write_env_shim() -> None:
    """
    Write all config keys as KEY=VALUE lines to ENV_SHIM_PATH so that
    Cache() (which hardcodes mode='CLI') can pick them up via GUSTAVO_CONFIG_FILE.
    """
    try:
        lines = [f"{k}={v}" for k, v in _config.items() if not isinstance(v, bool)]
        # Boolean flags: write as 1/0 strings
        for k, v in _config.items():
            if isinstance(v, bool):
                lines.append(f"{k}={'true' if v else 'false'}")
        ENV_SHIM_PATH.write_text("\n".join(lines) + "\n")
        os.environ["GUSTAVO_CONFIG_FILE"] = str(ENV_SHIM_PATH)
    except Exception as exc:
        import logging
        logging.error(f"config_store: failed to write env shim: {exc}")
