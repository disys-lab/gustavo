"""
Reusable FastAPI Depends() helpers.

_build_manager(cfg) is the FastAPI equivalent of the Streamlit obtainManagerConf()
pattern — Manager with mode='streamlit' does NOT auto-populate Manager-specific
attributes, so we set them manually after init.
"""
from gustavo.src.Manager import Manager
from gustavo.src.Composer import Composer


def _build_manager(cfg: dict) -> Manager:
    """
    Instantiate Manager from config dict (the FastAPI replacement for
    Manager(mode='streamlit', params=st.session_state)).

    All attributes that are NOT populated by NebulaBase.__init__ in streamlit
    mode are set here, mirroring the obtain*Conf() methods in
    pages/1_Manager_Services.py.
    """
    man = Manager(mode="streamlit", params=cfg)

    # Manager service
    man.MANAGER_IMAGE = cfg.get("MANAGER_IMAGE")
    man.MANAGER_NMODE = cfg.get("MANAGER_NMODE", "bridge")
    man.CACHE_EXPIRE_TIME = cfg.get("CACHE_EXPIRE_TIME", "3600")

    # Redis
    man.REDIS_IMAGE = cfg.get("REDIS_IMAGE")
    man.REDIS_BKP_DIR = cfg.get("REDIS_BKP_DIR", "/tmp/")

    # MongoDB
    man.MONGO_IP = cfg.get("MONGO_HOST")
    man.MONGO_PORT = int(cfg.get("MONGO_PORT", 27017))
    man.MONGO_USERNAME = cfg.get("MONGO_USERNAME")
    man.MONGO_PASSWORD = cfg.get("MONGO_PASSWORD")
    man.MONGO_IMAGE = cfg.get("MONGO_IMAGE")
    man.MONGO_CERTIFICATE_FOLDER_PATH = cfg.get("MONGO_CERTIFICATE_FOLDER_PATH", "/tmp/")

    # Registry
    man.REGISTRY_IMAGE = cfg.get("REGISTRY_IMAGE")
    man.REGISTRY_BKP_DIR = cfg.get("REGISTRY_BKP_DIR", "/tmp/")

    # Syncer
    man.SYNCER_IMAGE = cfg.get("SYNCER_IMAGE")
    man.SYNCER_NMODE = cfg.get("SYNCER_NMODE", "host")
    man.DREGSY_CONFIG_FILE_PATH = cfg.get("DREGSY_CONFIG_FILE_PATH") or None
    man.DREGSY_MAPPING_FILE_PATH = cfg.get("DREGSY_MAPPING_FILE_PATH") or None

    # Disable blocking wait on manager startup
    man.wait_for_manager_enabled = False

    return man


def _build_composer(cfg: dict) -> Composer:
    """
    Instantiate Composer from config dict.
    Composer uses NebulaBase in streamlit mode, which reads from session_state dict.
    """
    return Composer(mode="streamlit", params=cfg)
