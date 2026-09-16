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
    # When true, the registry container's port is published to 127.0.0.1 only
    # instead of 0.0.0.0 - only reachable from other processes on the same
    # host (e.g. an authenticated nginx proxy in front of it), not directly
    # from the network. Off by default to preserve existing behavior; turning
    # it on without also repointing anything that reads REGISTRY_HOST/PORT at
    # an authenticated front door breaks direct registry access entirely.
    "REGISTRY_BIND_LOCALHOST": False,
    # Port the raw registry container itself binds to. Empty by default,
    # meaning "same as REGISTRY_PORT" - correct whenever nothing sits in
    # front of the registry, since REGISTRY_PORT then points straight at the
    # raw container anyway. Must be set to a *different* port when a registry
    # proxy is in front of the registry (REGISTRY_PORT repointed at the
    # proxy) - otherwise the raw container and the proxy both try to bind the
    # same port and one fails to start.
    "REGISTRY_CONTAINER_PORT": "",
    # Syncer
    "SYNCER_IMAGE": "ghcr.io/disys-lab/dregsy:latest",
    "SYNCER_NMODE": "host",
    "DREGSY_CONFIG_FILE_PATH": "",
    "DREGSY_MAPPING_FILE_PATH": "",
    # Reporter
    "REPORTER_IMAGE": "ghcr.io/disys-lab/gustavo-reporter:latest",
    "REPORTER_HOST": _host_ip,
    "REPORTER_PORT": "8090",
    # Host/port reporter uses to reach gustavo's own API. Reporter runs as
    # its own separate container, so this must be gustavo's *host-published*
    # port, not gustavo's internal container port or FastAPI's 8000 (which
    # is bound to 127.0.0.1 inside gustavo's own container and unreachable
    # from any other container entirely). This repo's own docker-compose.yml
    # publishes gustavo as 3000:3000, but a real deployment's host port can
    # differ (e.g. cypress-ai uses 3002:3000, to avoid colliding with
    # another service already on host port 3000) - override this in Settings
    # to match whatever the actual deployment maps.
    "GUSTAVO_API_HOST": _host_ip,
    "GUSTAVO_API_PORT": "3002",
    # Public Facing Endpoints — the externally-reachable addresses for
    # Manager/Reporter/gustavo itself (e.g. behind a Cloudflare Tunnel),
    # separate from the internal LAN addresses above. Only used when a
    # worker-config download explicitly opts in (public_endpoints=true) -
    # every existing caller keeps using the internal *_HOST/*_PORT values
    # above unless PUBLIC_ENDPOINTS_ENABLED is also on. Protocol is always
    # https for these - a public tunnel entry always terminates TLS at the
    # edge, so there's no separate PUBLIC_*_PROTOCOL field.
    "PUBLIC_ENDPOINTS_ENABLED": False,
    "PUBLIC_MANAGER_HOST": "",
    "PUBLIC_MANAGER_PORT": "443",
    "PUBLIC_REPORTER_HOST": "",
    "PUBLIC_REPORTER_PORT": "443",
    "PUBLIC_GUSTAVO_HOST": "",
    "PUBLIC_GUSTAVO_PORT": "443",
    # Public registry access is a separate, stricter opt-in from the above -
    # off by default even when PUBLIC_ENDPOINTS_ENABLED is on. When enabled,
    # PUBLIC_REGISTRY_HOST/PORT becomes THE registry for every worker config
    # and the Registry tab alike, not just external-group users - a public
    # endpoint is reachable from anywhere, so there's no reason to keep
    # preferring the internal-only address once one exists. When disabled,
    # external-group users get no registry access at all; everyone else
    # keeps using the internal REGISTRY_HOST/PORT, unconditionally.
    "PUBLIC_REGISTRY_ENABLED": False,
    "PUBLIC_REGISTRY_HOST": "",
    "PUBLIC_REGISTRY_PORT": "443",
    # Nebula user-groups whose members are treated as "external" - their
    # worker configs and Registry tab access are governed entirely by the
    # PUBLIC_* settings above (mandatory, not optional), regardless of any
    # per-device-group checkbox state. Empty by default: nobody is external
    # until an admin explicitly assigns a group here.
    "EXTERNAL_USER_GROUPS": [],
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
