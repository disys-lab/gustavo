from dotenv import load_dotenv
from pathlib import Path
import os, sys, click
from gustavo.pages.config.Logging import setup_logging
setup_logging()
import logging
class PathInvalid(Exception):
    """Raised when `GUSTAVO_CONFIG_FILE` points at a path that doesn't exist."""
    pass


class FileUndefined(Exception):
    """Raised when `mode="CLI"` is used but `GUSTAVO_CONFIG_FILE` isn't set in the environment."""
    pass


class NebulaBase:
    """
    Base configuration class holding platform connection parameters.

    Every other core class (`Manager`, `Composer`, `Cache`) subclasses
    this to inherit Redis/Registry/Manager/Nebula connection details,
    loaded either from a dotenv file (`mode="CLI"`) or a session-state
    dict passed in directly (the FastAPI backend's usage - see
    `gustavo.api.dependencies`).

    Attributes
    ----------
    nebulaObj : Nebula
        The Nebula object provided by the Nebula Python SDK. `None`
        until a subclass (e.g. `Composer`) constructs it.
    REGISTRY_IP : str
        Hostname or IP address of the Docker registry.
    REGISTRY_PORT : str
        Port number of the registry.
    REDIS_IP : str
        Hostname or IP address of Redis.
    REDIS_PORT : str
        Port number of the Redis DB.
    REDIS_AUTH_TOKEN : str
        Auth token for Redis.
    MANAGER_IP : str
        Hostname or IP address of the machine hosting the Nebula manager.
    MANAGER_PORT : str
        Port number of the Nebula manager.
    NEBULA_USERNAME : str
        Username for Nebula.
    NEBULA_PASSWORD : str
        Password for Nebula.
    NEBULA_AUTH_TOKEN : str
        Auth token for the Nebula API.
    NEBULA_PROTOCOL : str
        Protocol for communicating with Nebula - `"http"` or `"https"`.
    DOCKER_HOST : str
        Docker host address, e.g. `"unix:/var/run/docker.sock"`.
    DOCKER_HOST_SOCKET : str
        Socket path portion of `DOCKER_HOST`.
    WORKER_NMODE : str
        Worker network mode (e.g. `"bridge"`).
    CACHE_PREFIX : str
        Redis key prefix used by `Cache`. Set only in `mode="CLI"`.

    Notes
    -----
    `setNebulaParams` predates the FastAPI backend and still returns an
    ``{"error": True, "response": ...}`` dict on some failure paths
    instead of raising - a REST-friendlier version would raise a real
    exception for every failure path, not just some, so callers never
    need to check both a return value and for an exception.
    """

    def __init__(self,mode,session_state):
        """
        Populate connection attributes from a config file (`mode="CLI"`) or a session-state dict.

        Parameters
        ----------
        mode : str
            `"CLI"` loads `GUSTAVO_CONFIG_FILE` via `setNebulaParams`.
            Any other value (e.g. the FastAPI backend's usage) reads
            directly from `session_state` instead.
        session_state : dict or None
            Required (and must contain every attribute this class
            defines) when `mode` isn't `"CLI"`. Ignored when `mode` is
            `"CLI"`.

        Raises
        ------
        FileUndefined
            If `mode="CLI"` and `GUSTAVO_CONFIG_FILE` isn't set in the
            environment.
        PathInvalid
            If `mode="CLI"` and `GUSTAVO_CONFIG_FILE` points at a
            nonexistent file.

        Notes
        -----
        Originally called `sys.exit()` on failure; replaced with raising
        real exceptions so a REST caller (`gustavo.py`) can catch them
        and return ``{"error": True, "response": <reason>}`` instead of
        killing the process.
        """
        self.base_config = None

        self.REGISTRY_IP = None
        self.REGISTRY_PORT = None
        self.MANAGER_IP = None

        self.REDIS_IP = None
        self.REDIS_PORT = None
        self.REDIS_AUTH_TOKEN = None
        self.CACHE_PREFIX = None

        self.MANAGER_PORT = None
        self.NEBULA_USERNAME = None
        self.NEBULA_PASSWORD = None
        self.NEBULA_AUTH_TOKEN = None
        self.NEBULA_PROTOCOL = None

        self.DOCKER_HOST = None
        self.DOCKER_HOST_SOCKET = None

        self.WORKER_NMODE = None

        self.nebulaObj = None

        if mode == "CLI":
            self.base_config = None
            if "GUSTAVO_CONFIG_FILE" in os.environ:
                self.base_config = os.environ["GUSTAVO_CONFIG_FILE"]
                if not os.path.isfile(self.base_config):
                    logging.error(f"GUSTAVO_CONFIG_FILE: {self.base_config} path not valid")
                    raise PathInvalid
            else:
                logging.error(f"GUSTAVO_CONFIG_FILE not defined")
                raise FileUndefined

            self.setNebulaParams()

        else:
            if session_state:
                self.REGISTRY_IP = session_state["REGISTRY_HOST"]
                self.REGISTRY_PORT = session_state["REGISTRY_PORT"]
                self.MANAGER_IP = session_state["MANAGER_HOST"]

                self.REDIS_IP = session_state["REDIS_HOST"]
                self.REDIS_PORT = session_state["REDIS_PORT"]
                self.REDIS_AUTH_TOKEN = session_state["REDIS_AUTH_TOKEN"]


                self.MANAGER_PORT = session_state["MANAGER_PORT"]
                self.NEBULA_USERNAME = session_state["NEBULA_USERNAME"]
                self.NEBULA_PASSWORD = session_state["NEBULA_PASSWORD"]
                self.NEBULA_AUTH_TOKEN = session_state["NEBULA_AUTH_TOKEN"]
                self.NEBULA_PROTOCOL = session_state["NEBULA_PROTOCOL"]

                self.DOCKER_HOST = "unix:/var/run/docker.sock"
                if len(self.DOCKER_HOST.split(":")) == 2:
                    self.DOCKER_HOST_SOCKET = self.DOCKER_HOST.split(":")[1]
                else:
                    logging.error(f"ERROR: DOCKER_HOST={self.DOCKER_HOST_SOCKET} must be like unix:/var/run/docker.shok .... quitting")

                self.WORKER_NMODE = session_state["WORKER_NMODE"]
            else:
                logging.error(f"session_state undefined in NebulaBase")

    def setNebulaParams(self):
        """
        Populate connection attributes from environment variables (loaded from `GUSTAVO_CONFIG_FILE`).

        Called only when `mode="CLI"`; the `GUSTAVO_CONFIG_FILE` dotenv
        file has already been loaded into `os.environ` by the time this
        runs (see `__init__`).

        Returns
        -------
        dict or None
            ``{"error": True, "response": <reason>}`` if a required
            variable (`REDIS_HOST`, `REDIS_PORT`, `REDIS_AUTH_TOKEN`,
            `REGISTRY_HOST`, `REGISTRY_PORT`, `MANAGER_HOST`, or
            `MANAGER_PORT`) is missing - returns immediately on the
            first missing one, so later attributes may be left unset.
            `None` (implicitly) on success.
        """
        if "GUSTAVO_CONFIG_FILE" in os.environ:
            dotenv_path = Path(self.base_config)
            load_dotenv(dotenv_path=dotenv_path,override=True)

        if "CACHE_PREFIX" in os.environ.keys():
            self.CACHE_PREFIX = os.getenv("CACHE_PREFIX")
        else:
            self.CACHE_PREFIX = "gustavo-reports"

        if "REDIS_HOST" in os.environ.keys():
            self.REDIS_IP = os.getenv("REDIS_HOST")
        else:
            logging.error(f"REDIS_IP undefined in base_config file")
            # sys.exit()
            return {"error": True, "response": "REDIS_IP undefined in base_config file"}

        if "REDIS_PORT" in os.environ.keys():
            self.REDIS_PORT = int(os.getenv("REDIS_PORT"))
        else:
            logging.error(f"REDIS_PORT undefined in base_config file")
            # sys.exit()
            return {
                "error": True,
                "response": "REDIS_PORT undefined in base_config file",
            }

        if "REDIS_AUTH_TOKEN" in os.environ.keys():
            self.REDIS_AUTH_TOKEN = os.getenv("REDIS_AUTH_TOKEN")
        else:
            logging.error(f"REDIS_AUTH_TOKEN undefined in base_coonfig file")
            # sys.exit()
            return {
                "error": True,
                "response": "REDIS_AUTH_TOKEN undefined in base_config file",
            }

        if "REGISTRY_HOST" in os.environ.keys():
            self.REGISTRY_IP = os.getenv("REGISTRY_HOST")
        else:
            logging.error(f"REGISTER_HOST undefined in base_config file")
            # sys.exit()
            return {
                "error": True,
                "response": "REGISTRY_HOST undefined in base_config file",
            }

        if "REGISTRY_PORT" in os.environ.keys():
            self.REGISTRY_PORT = int(os.getenv("REGISTRY_PORT"))
        else:
            logging.error(f"REGISTER_PORT undefined in base_config file")
            # sys.exit()
            return {
                "error": True,
                "response": "REGISTRY_PORT undefined in base_config file",
            }

        if "MANAGER_HOST" in os.environ.keys():
            self.MANAGER_IP = os.getenv("MANAGER_HOST")
        else:
            logging.error(f"MANAGER_IP undefined in base_config file")
            # sys.exit()
            return {
                "error": True,
                "response": "MANAGER_IP undefined in base_config file",
            }

        if "MANAGER_PORT" in os.environ.keys():
            self.MANAGER_PORT = os.getenv("MANAGER_PORT")
        else:
            logging.error(f"MANAGER_PORT undefined in base_config file")
            # sys.exit()
            return {
                "error": True,
                "response": "MANAGER_PORT undefined in base_config file",
            }

        if "WORKER_NMODE" in os.environ.keys():
            self.WORKER_NMODE = os.getenv("WORKER_NMODE")
        else:
            self.WORKER_NMODE = "bridge"
            logging.error(f"WORKER_NMODE undefined in base_config file")

        if "NEBULA_USERNAME" in os.environ.keys():
            self.NEBULA_USERNAME = os.getenv("NEBULA_USERNAME")

        if "NEBULA_PASSWORD" in os.environ.keys():
            self.NEBULA_PASSWORD = os.getenv(
                "NEBULA_PASSWORD"
            )  # base64.b64decode(os.getenv("NEBULA_PASSWORD").encode('utf-8')).decode('utf-8')

        if "NEBULA_AUTH_TOKEN" in os.environ.keys():
            self.NEBULA_AUTH_TOKEN = os.getenv("NEBULA_AUTH_TOKEN")

        if "NEBULA_PROTOCOL" in os.environ.keys():
            self.NEBULA_PROTOCOL = os.getenv("NEBULA_PROTOCOL")

        if "DOCKER_HOST" in os.environ.keys():
            self.DOCKER_HOST = str(os.environ["DOCKER_HOST"])
        else:
            self.DOCKER_HOST = "unix:/var/run/docker.sock"

        if len(self.DOCKER_HOST.split(":")) == 2:
            self.DOCKER_HOST_SOCKET = self.DOCKER_HOST.split(":")[1]
        else:
            logging.error(f"ERROR: DOCKER_HOST={self.DOCKER_HOST_SOCKET} must be like unix:/var/run/docker.sock .... quitting")

        logging.info(f"{self.NEBULA_USERNAME}@{self.MANAGER_IP}:{self.MANAGER_PORT}")

        logging.warning(f"DOCKER_HOST: {self.DOCKER_HOST}")
