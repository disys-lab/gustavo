"""
Cache CLI-mode bridge.

Cache.__init__ hardcodes mode='CLI', which forces NebulaBase to read from
GUSTAVO_CONFIG_FILE.  config_store.update() always keeps that env-file fresh.
This module provides a single helper that ensures the env var is set before
constructing Cache().
"""
import os
from gustavo.api import config_store


def build_cache():
    """
    Return a fully-initialised Cache() instance using the current config.

    Raises whatever Cache / NebulaBase raise on misconfiguration.
    """
    env_path = config_store.ENV_SHIM_PATH

    # Always call load() — it re-writes the env shim file unconditionally.
    # Using get() is NOT sufficient: get() returns the in-memory dict without
    # touching the file, so if /tmp/gustavo_api.env was cleaned up (container
    # restart, OS tmpwatch, uvicorn --reload) the file would be gone while the
    # env var still points at it, causing NebulaBase to raise PathInvalid.
    config_store.load()
    os.environ["GUSTAVO_CONFIG_FILE"] = str(env_path)

    # Import here to avoid circular imports at module load time.
    from gustavo.src.Cache import Cache
    return Cache()
