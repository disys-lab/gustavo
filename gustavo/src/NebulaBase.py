from dotenv import load_dotenv
from pathlib import Path
import os, sys, click
from gustavo.pages.config.Logging import setup_logging
setup_logging()
import logging
class PathInvalid(Exception):
    pass


class FileUndefined(Exception):
    pass


class NebulaBase:
    """
    NebulaBase class holds the configuration parameters as defined in the GUSTAVO_CONFIG_FILE

    Attributes
    ----------

    nebulaObj : nebula object
        The nebula object provided by the Nebula Python API

    REGISTRY_IP : string
        Hostname or IP address of Registry

    REGISTRY_PORT : string
        Port number of Registry

    REDIS_IP : string
        Hostname or IP address of Redis

    REDIS_PORT : string
        Port number of Redis DB

    REDIS_AUTH_TOKEN : string
        Auth token for Redis

    MANAGER_IP : string
        Hostname or IP address of the machine where the Manager is hosted

    NEBULA_USERNAME : string
        Username for Nebula

    NEBULA_PASSWORD : string
        Password for Nebula

    NEBULA_AUTH_TOKEN : string
        Auth token for the Nebula API

    NEBULA_PROTOCOL : string
        Protocol for communicating with Nebula, http or https

    DOCKER_HOST : string
        Docker Hostname

    DOCKER_HOST_SOCKET : string
        Socket for Docker Client

    WORKER_NMODE: string
        Worker network mode

    TODO: Make setNebulaParams() REST API-friendly, which means that instead of a sys.exit(), it needs to either
          throw an appropriate exception or return a status value or both.
          Good way to do it would be to throw an exception here and then catch it on gustavo.py

    """

    def __init__(self,mode,session_state):
        """
        Inorder to make NebulaBase rest friendly replaced sys.exit() with raising exceptions which will get excepted
        in gustavo.py and eventually return a dictionary there {"error": True, "response": reason for error}
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
        Sets the Nebula Params for all the class attributes
        Inorder to make NebulaBase rest friendly replaced sys.exit(); return a dictionary there
        {"error": True, "response": reason for error}
        """
        if "GUSTAVO_CONFIG_FILE" in os.environ:
            dotenv_path = Path(self.base_config)
            load_dotenv(dotenv_path=dotenv_path)

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
