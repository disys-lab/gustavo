import click, os
from urllib.parse import urlparse
from dotenv import load_dotenv
from pathlib import Path
import requests
import docker
import time
import logging
from .NebulaBase import NebulaBase
from gustavo.pages.config.Logging import setup_logging
setup_logging()
import logging
from python_on_whales import docker as dockerow
import sys
from NebulaPythonSDK import Nebula
import datetime
import shutil

"""
Manages the Docker Compose-adjacent lifecycle of the platform's own
services (registry, Redis, Mongo, Nebula manager, syncer) - starting,
stopping, and health-checking the containers `gustavo` itself depends
on, as distinct from `Composer`, which manages user-deployed apps.
"""

class Manager(NebulaBase):
    """
    Brings up, tears down, and checks the health of the platform's own services.

    Inherits connection parameters from `NebulaBase`. The services
    managed here are:

    * `registry`
    * `redis`
    * `mongo`
    * `manager`
    * `syncer`

    Attributes
    ----------
    DREGSY_CONFIG_FILE_PATH : str
        Path to the Dregsy config file (the syncer service).
    DREGSY_MAPPING_FILE_PATH : str
        Path to the Dregsy image-mapping file.
    MONGO_IP : str
        Hostname or IP address of Mongo.
    MONGO_PORT : str
        Port number of Mongo.
    MONGO_USERNAME : str
        Username for Mongo.
    MONGO_PASSWORD : str
        Password for Mongo.
    REGISTRY_IMAGE : str
        Docker image to run for the registry service.
    REGISTRY_BKP_DIR : str
        Host directory bind-mounted as the registry's data volume.
        Defaults to `"/tmp/"` if unset or invalid.
    REGISTRY_BIND_LOCALHOST : bool
        If `True`, bind the registry port to `127.0.0.1` only.
    REGISTRY_CONTAINER_PORT : str
        Container-side port for the registry; falls back to
        `REGISTRY_PORT` if unset.
    SYNCER_IMAGE : str
        Docker image to run for the syncer (Dregsy) service.
    SYNCER_NMODE : str
        Docker network mode for the syncer container. Defaults to
        `"bridge"`.
    REDIS_IMAGE : str
        Docker image to run for Redis.
    REDIS_BKP_DIR : str
        Host directory bind-mounted as Redis's data volume. Defaults
        to `"/tmp/"` if unset or invalid.
    MONGO_IMAGE : str
        Docker image to run for Mongo.
    MANAGER_IMAGE : str
        Docker image to run for the Nebula manager.
    MANAGER_NMODE : str
        Docker network mode for the manager container. Defaults to
        `"bridge"`.
    service_list : str
        Comma-separated list of the service names this class manages.

    Notes
    -----
    `setManagerParams` predates the FastAPI backend and still returns
    an ``{"error": True, "response": ...}`` dict on failure instead of
    raising - a REST-friendlier version would throw a real exception
    here and let the caller (`gustavo.py`) catch it, rather than
    requiring every caller to check a return value.
    """

    def __init__(self,mode="CLI",params = None):
        """
        Populate connection attributes via `NebulaBase.__init__`, then load Manager-specific service params.

        Parameters
        ----------
        mode : str, optional
            `"CLI"` (default) also calls `setManagerParams` to load
            service image/config settings from the environment. Any
            other value skips that call, leaving those attributes
            `None` (matches `NebulaBase`'s FastAPI-backend usage,
            which doesn't need them).
        params : dict or None, optional
            Passed through to `NebulaBase.__init__` as `session_state`.
        """

        NebulaBase.__init__(self,mode=mode,session_state=params)

        self.DREGSY_CONFIG_FILE_PATH = None
        self.DREGSY_MAPPING_FILE_PATH = None

        self.MONGO_IP = None
        self.MONGO_PORT = None
        self.MONGO_USERNAME = None
        self.MONGO_PASSWORD = None

        self.REGISTRY_IMAGE = None
        self.SYNCER_IMAGE = None
        self.REDIS_IMAGE = None
        self.REDIS_BKP_DIR = "/tmp/"
        self.REGISTRY_BKP_DIR = "/tmp/"  # Added Registry Backup Directory
        self.REGISTRY_BIND_LOCALHOST = False
        self.REGISTRY_CONTAINER_PORT = None
        self.MONGO_IMAGE = None
        self.MANAGER_IMAGE = None

        self.MANAGER_NMODE = None
        self.SYNCER_NMODE = None

        self.service_list = "registry,redis,mongo,manager,syncer"

        if mode == "CLI":
            self.setManagerParams()

    def setManagerParams(self):
        """
        Populate Manager-specific attributes from environment variables.

        Called only when `mode="CLI"` (see `__init__`); the dotenv
        file has already been loaded into `os.environ` by
        `NebulaBase.setNebulaParams` by the time this runs.

        Returns
        -------
        dict
            ``{"error": True, "response": <reason>}`` if a required
            variable is missing or invalid - returns immediately on
            the first such variable, so later attributes may be left
            unset. ``{"error": False, "response": "Manager Params set
            successfully"}`` on success.
        """
        if "DREGSY_CONFIG_FILE_PATH" in os.environ.keys():
            if os.path.isfile(os.environ["DREGSY_CONFIG_FILE_PATH"]):
                self.DREGSY_CONFIG_FILE_PATH = os.getenv("DREGSY_CONFIG_FILE_PATH")
            else:
                logging.error(f"DREGSY_CONFIG_FILE_PATH invalid")

                return {"error": True, "response": "DREGSY_CONFIG_FILE_PATH invalid"}
        else:
            logging.error(f"DREGSY_CONFIG_PATH undefined in base_config file")

            return {
                "error": True,
                "response": "DREGSY_CONFIG_FILE_PATH undefined in base_config file",
            }

        if "DREGSY_MAPPING_FILE_PATH" in os.environ.keys():
            if os.path.isfile(os.environ["DREGSY_MAPPING_FILE_PATH"]):
                self.DREGSY_MAPPING_FILE_PATH = os.getenv("DREGSY_MAPPING_FILE_PATH")
            else:
                logging.error(f"DREGSY_MAPPING_PATH invalid")

                return {"error": True, "response": "DREGSY_MAPPING_FILE_PATH invalid"}

        else:
            logging.error(f"DREGSY_MAPPING_FILE_PATH undefined in base_config file")

            return {
                "error": True,
                "response": "DREGSY_MAPPING_FILE_PATH undefined in base_config file",
            }

        if "MONGO_USERNAME" in os.environ.keys():
            self.MONGO_USERNAME = os.getenv("MONGO_USERNAME")
        else:
            logging.error(f"MONGO_USERNAME undefined in base_config file")

            return {
                "error": True,
                "response": "MONGO_USERNAME undefined in base_config file",
            }

        if "MONGO_PASSWORD" in os.environ.keys():
            self.MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
        else:
            logging.error(f"MONGO_PASSOWRD undefined in base_config file")

            return {
                "error": True,
                "response": "MONGO_PASSWORD undefined in base_config file",
            }

        if "MONGO_HOST" in os.environ.keys():
            self.MONGO_IP = os.getenv("MONGO_HOST")
        else:
            logging.error(f"MONGO_IP undefined in base_config file")

            return {"error": True, "response": "MONGO_IP undefined in base_config file"}

        if "MONGO_PORT" in os.environ.keys():
            self.MONGO_PORT = int(os.getenv("MONGO_PORT"))
        else:
            logging.error(f"MONGO_PORT undefined in base_config file")

            return {
                "error": True,
                "response": "MONGO_PORT undefined in base_config file",
            }

        if "REGISTRY_IMAGE" in os.environ.keys():
            self.REGISTRY_IMAGE = os.getenv("REGISTRY_IMAGE")
        else:
            logging.error(f"REGISTER_IMAGE undefined in base_config file")
            return {
                "error": True,
                "response": "REGISTRY_IMAGE undefined in base_config file",
            }

        if "REGISTRY_BKP_DIR" in os.environ.keys():  # Added Registry Backup Directory
            REGISTRY_BKP_DIR = os.getenv("REGISTRY_BKP_DIR")
            if not (os.path.exists(REGISTRY_BKP_DIR) and os.path.isdir(REGISTRY_BKP_DIR)):
                logging.error(f"{REGISTRY_BKP_DIR} does not exist, defaulting to /tmp/")
                REGISTRY_BKP_DIR = "/tmp/"
            self.REGISTRY_BKP_DIR = REGISTRY_BKP_DIR
        else:
            self.REGISTRY_BKP_DIR = "/tmp/"
            logging.error(f"REGISTRY_BKP_DIR undefined in os.environ, defaulting to {self.REGISTRY_BKP_DIR}")

        if "REGISTRY_BIND_LOCALHOST" in os.environ.keys():
            self.REGISTRY_BIND_LOCALHOST = os.getenv("REGISTRY_BIND_LOCALHOST").lower() in ("1", "true", "yes", "on")
        else:
            self.REGISTRY_BIND_LOCALHOST = False

        if "REGISTRY_CONTAINER_PORT" in os.environ.keys() and os.getenv("REGISTRY_CONTAINER_PORT"):
            self.REGISTRY_CONTAINER_PORT = os.getenv("REGISTRY_CONTAINER_PORT")
        else:
            self.REGISTRY_CONTAINER_PORT = self.REGISTRY_PORT

        if "SYNCER_IMAGE" in os.environ.keys():
            self.SYNCER_IMAGE = os.getenv("SYNCER_IMAGE")
        else:
            logging.error("SYNCER_IMAGE undefined in bse_config file")

            return {
                "error": True,
                "response": "SYNCER_IMAGE undefined in base_config file",
            }
        if "REDIS_IMAGE" in os.environ.keys():
            self.REDIS_IMAGE = os.getenv("REDIS_IMAGE")
        else:
            logging.error(f"REDIS_IMAGE undefined in base_config file")

            return {
                "error": True,
                "response": "REDIS_IMAGE undefined in base_config file",
            }

        if "REDIS_BKP_DIR" in os.environ.keys():
            REDIS_BKP_DIR = os.getenv("REDIS_BKP_DIR")
            if not (os.path.exists(REDIS_BKP_DIR) and os.path.isdir(REDIS_BKP_DIR)):
                logging.error(f"{REDIS_BKP_DIR} does not exist, defaulting to /tmp/")
                REDIS_BKP_DIR = "/tmp/"
            self.REDIS_BKP_DIR = REDIS_BKP_DIR
        else:
            self.REDIS_BKP_DIR = "/tmp/"
            logging.error(f"REDIS_BKP_DIR undefined in os.environ, defaulting to {self.REDIS_BKP_DIR}")



        if "MONGO_IMAGE" in os.environ.keys():
            self.MONGO_IMAGE = os.getenv("MONGO_IMAGE")
        else:
            logging.error(f"MONGO_IMAGE undefined in base_config file")

            return {
                "error": True,
                "response": "MONGO_IMAGE undefined in base_config file",
            }
        if "MANAGER_IMAGE" in os.environ.keys():
            self.MANAGER_IMAGE = os.getenv("MANAGER_IMAGE")
        else:
            logging.error(f"MANAGER_IMAGE undefined in base_config file")

            return {
                "error": True,
                "response": "MANAGER_IMAGE undefined in base_config file",
            }

        if "MANAGER_NMODE" in os.environ.keys():
            self.MANAGER_NMODE = os.getenv("MANAGER_NMODE")
        else:
            self.MANAGER_NMODE = "bridge"
            logging.error(f"MANAGER_NMODE undefined in base_config file")

        if "SYNCER_NMODE" in os.environ.keys():
            self.SYNCER_NMODE = os.getenv("SYNCER_NMODE")
        else:
            self.SYNCER_NMODE = "bridge"
            logging.error(f"SYNCE_NMODE undefined in base_config file")

        return {"error": False, "response": "Manager Params set successfully"}

    def runRegistry(self, client):
        """
        Bring up the registry container via `client`.

        Also creates `REGISTRY_BKP_DIR` if it doesn't exist.

        Parameters
        ----------
        client : docker.DockerClient
            The Docker client to run the container with.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `True` if `REGISTRY_IMAGE` isn't configured, the backup
            directory couldn't be created, the image can't be pulled,
            or the Docker API errors; `False` on success. `response`
            describes which.
        """

        if self.REGISTRY_IMAGE:

            # success = True
            dockerow.pull(self.REGISTRY_IMAGE)
            if not os.path.exists(self.REGISTRY_BKP_DIR):
                try:
                    os.makedirs(self.REGISTRY_BKP_DIR,exist_ok=True)
                except Exception as e:
                    logging.error(f"{e}")
                    logging.error(f"Could not create directory: {self.REGISTRY_BKP_DIR} ")
                    return {"error": False, "response": f"Could not create directory: {self.REGISTRY_BKP_DIR} "}

            try:
                registry_bind_port = self.REGISTRY_CONTAINER_PORT or self.REGISTRY_PORT
                registry_port_binding = (
                    {"5000": ("127.0.0.1", registry_bind_port)}
                    if self.REGISTRY_BIND_LOCALHOST
                    else {"5000": registry_bind_port}
                )
                client.containers.run(
                    image=self.REGISTRY_IMAGE,
                    detach=True,
                    security_opt=["label=disable"],
                    ports=registry_port_binding,
                    name="registry",
                    restart_policy={"Name": "always"},
                    volumes=[
                        str(self.DOCKER_HOST_SOCKET) + ":/var/run/docker.sock:rw",
                        f"{self.REGISTRY_BKP_DIR}:/var/lib/registry:rw"  # Mounted registry data volume
                    ],
                    # volumes=[str(self.DOCKER_HOST_SOCKET) + ":/var/run/docker.sock:rw"],
                )
                # return {"error": False, "response": {"ipfs_bootnodes": redisRet}}
            except docker.errors.ImageNotFound as e:
                logging.error(f"ERROR: {e}")
                logging.error(f"Register image not found")
                return {"error": True, "response": "Registry image not found"}
            except docker.errors.APIError as e:
                logging.error(f"ERROR: {e}")
                logging.error(f"Register:Troble reaching the docker API")
                return {
                    "error": True,
                    "response": "Registry:Trouble reaching the docker API, exception:{}".format(str(e)),
                }
            return {"error": False, "response": "Registry ran successfully"}
        else:
            logging.error(f"Register Image Not defined in config files")
            return {
                "error": True,
                "response": "Registry Image Not defined in config files",
            }

    def runSyncer(self, client):
        """
        Bring up the syncer (Dregsy) container via `client`.

        Uses `network_mode="host"` when `SYNCER_NMODE == "host"`, else
        the Docker default.

        Parameters
        ----------
        client : docker.DockerClient
            The Docker client to run the container with.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `True` if `SYNCER_IMAGE` isn't configured, the image can't
            be pulled, or the Docker API errors; `False` on success.
            `response` describes which.
        """

        if self.SYNCER_IMAGE:
            # success = True
            dockerow.pull(self.SYNCER_IMAGE)
            try:

                if self.SYNCER_NMODE == "host":
                    client.containers.run(
                        image=self.SYNCER_IMAGE,
                        detach=True,
                        security_opt=["label=disable"],
                        name="syncer",
                        network_mode=self.SYNCER_NMODE,
                        restart_policy={"Name": "always"},
                        volumes=[
                            self.DREGSY_CONFIG_FILE_PATH + ":/config.yaml",
                            self.DREGSY_MAPPING_FILE_PATH + ":/mappings_list.yaml",
                        ],
                    )
                else:
                    client.containers.run(
                        image=self.SYNCER_IMAGE,
                        detach=True,
                        security_opt=["label=disable"],
                        name="syncer",
                        restart_policy={"Name": "always"},
                        volumes=[
                            self.DREGSY_CONFIG_FILE_PATH + ":/config.yaml",
                            self.DREGSY_MAPPING_FILE_PATH + ":/mappings_list.yaml",
                        ],
                    )
            except docker.errors.ImageNotFound as e:
                logging.error(f"{e}")
                logging.error("Syncer (Dregsy) image not found ")
                return {"error": True, "response": "Syncer (Dregsy) image not found"}
            except docker.errors.APIError as e:
                logging.error(f"{e}")
                logging.error(f"Syncer:Troble reaching the docker API")
                return {
                    "error": True,
                    "response": "Syncer:Trouble reaching the docker API, exception:{}".format(str(e)),
                }
            return {"error": False, "response": "Syncer run successfully"}
        else:
            logging.error(f"Syncer Image defined in config files")
            return {
                "error": True,
                "response": "Syncer Image Not defined in config files",
            }

    def runRedis(self, client):
        """
        Bring up the Redis container via `client`.

        Also creates `REDIS_BKP_DIR` if it doesn't exist. Passes
        `REDIS_AUTH_TOKEN` in as `--requirepass` via the `REDIS_ARGS`
        environment variable.

        Parameters
        ----------
        client : docker.DockerClient
            The Docker client to run the container with.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `True` if `REDIS_IMAGE` isn't configured, the backup
            directory couldn't be created, the image can't be pulled,
            or the Docker API errors; `False` on success. `response`
            describes which.
        """

        if self.REDIS_IMAGE:
            # success = True
            dockerow.pull(self.REDIS_IMAGE)
            if not os.path.exists(self.REDIS_BKP_DIR):
                try:
                    os.makedirs(self.REDIS_BKP_DIR,exist_ok=True)
                except Exception as e:
                    logging.error(f"{e}")
                    logging.error(f"Could not create directory: {self.REDIS_BKP_DIR} ")
                    return {"error": False, "response": f"Could not create directory: {self.REDIS_BKP_DIR} "}
            try:

                print(f"REDIS_ARGS= --requirepass {str(self.REDIS_AUTH_TOKEN)}")
                client.containers.run(
                    image=self.REDIS_IMAGE,
                    detach=True,
                    security_opt=["label=disable"],
                    name="redis",
                    ports={"6379": str(self.REDIS_PORT)},
                    restart_policy={"Name": "always"},
                    volumes = {f"{self.REDIS_BKP_DIR}": {'bind': '/data/', 'mode': 'rw'}},
                    environment=[f"REDIS_ARGS=--requirepass {str(self.REDIS_AUTH_TOKEN)}"],
                )
            except docker.errors.ImageNotFound as e:
                logging.error(f"{e}")
                logging.error(f"Redis image not found")
                return {"error": True, "response": "Redis image not found"}
            except docker.errors.APIError as e:
                logging.error(f"{e}")
                logging.error(f"Redis:Troble reaching the docker API")
                return {
                    "error": True,
                    "response": "Redis:Trouble reaching the docker API, exception:{}".format(str(e)),
                }
            return {"error": False, "response": "Redis run successfully"}
        else:
            logging.error(f"Redis Image Not defined in config files")
            return {
                "error": True,
                "response": "Redis Image Not defined in config files",
            }

    def runMongo(self, client):
        """
        Bring up the Mongo container via `client`, seeded with `MONGO_USERNAME`/`MONGO_PASSWORD` as the root user.

        Parameters
        ----------
        client : docker.DockerClient
            The Docker client to run the container with.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `True` if `MONGO_IMAGE` isn't configured, the image can't
            be pulled, or the Docker API errors; `False` on success.
            `response` describes which.
        """

        if self.MONGO_IMAGE:
            # success = True
            dockerow.pull(self.MONGO_IMAGE)
            try:
                client.containers.run(
                    image=self.MONGO_IMAGE,
                    detach=True,
                    security_opt=["label=disable"],
                    name="mongo",
                    hostname="mongo",
                    ports={"27017": self.MONGO_PORT},
                    restart_policy={"Name": "always"},
                    environment=[
                        "MONGO_INITDB_ROOT_USERNAME=" + str(self.MONGO_USERNAME),
                        "MONGO_INITDB_ROOT_PASSWORD=" + str(self.MONGO_PASSWORD),
                    ],
                )
            except docker.errors.ImageNotFound as e:
                logging.error(f"{e}")
                logging.error(f"Mongo image not found")
                # return False
                return {"error": True, "response": "Mongo image not found"}
            except docker.errors.APIError as e:
                logging.error(f"{e}")
                logging.error(f"Mongo:Trouble reaching the docker API")
                # return False
                return {
                    "error": True,
                    "response": "Mongo:Trouble reaching the docker API, exception:{}".format(str(e)),
                }

            # return success
            return {"error": False, "response": "Mongo run successfully"}
        else:
            logging.error(f"Mongo Image Not defined in config files")
            return {
                "error": True,
                "response": "Mongo Image Not defined in config files",
            }

    def runManager(self, client):
        """
        Bring up the Nebula manager container via `client`, wired to Mongo/Redis and Nebula auth.

        Uses `network_mode="host"` when `MANAGER_NMODE == "host"`
        (no port binding needed), else publishes `MANAGER_PORT`.

        Parameters
        ----------
        client : docker.DockerClient
            The Docker client to run the container with.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `True` if `MANAGER_IMAGE` isn't configured, the image
            can't be pulled, or the Docker API errors; `False` on
            success. `response` describes which.
        """

        if self.MANAGER_IMAGE:
            # success = True
            dockerow.pull(self.MANAGER_IMAGE)

            try:
                logging.info(f"Spinning up Manager in {self.MANAGER_NMODE} network mode")
                if self.MANAGER_NMODE == "host":
                    client.containers.run(
                        image=self.MANAGER_IMAGE,
                        detach=True,
                        security_opt=["label=disable"],
                        name="manager",
                        network_mode=self.MANAGER_NMODE,
                        hostname="manager",
                        restart_policy={"Name": "always"},
                        environment=[
                            "MONGO_URL=mongodb://"
                            + str(self.MONGO_USERNAME)
                            + ":"
                            + str(self.MONGO_PASSWORD)
                            + "@"
                            + str(self.MONGO_IP)
                            + ":"
                            + str(self.MONGO_PORT)
                            + "/nebula?authSource=admin",
                            # "MONGO_URL=mongodb://nebula:nebula@10.0.0.70:27017/nebula?authSource=admin",
                            "SCHEMA_NAME=nebula",
                            "BASIC_AUTH_USER=" + str(self.NEBULA_USERNAME),
                            "BASIC_AUTH_PASSWORD=" + str(self.NEBULA_PASSWORD),
                            "AUTH_TOKEN=" + str(self.NEBULA_AUTH_TOKEN),
                            "REDIS_HOST=" + str(self.REDIS_IP),
                            "REDIS_PORT=" + str(self.REDIS_PORT),
                            "REDIS_AUTH_TOKEN=" + str(self.REDIS_AUTH_TOKEN)
                        ],
                    )
                else:
                    client.containers.run(
                        image=self.MANAGER_IMAGE,
                        detach=True,
                        security_opt=["label=disable"],
                        name="manager",
                        hostname="manager",
                        ports={"80": self.MANAGER_PORT},
                        restart_policy={"Name": "always"},
                        sysctls={"net.ipv4.conf.all.forwarding":"1"},
                        environment=[
                            "MONGO_URL=mongodb://"
                            + str(self.MONGO_USERNAME)
                            + ":"
                            + str(self.MONGO_PASSWORD)
                            + "@"
                            + str(self.MONGO_IP)
                            + ":"
                            + str(self.MONGO_PORT)
                            + "/nebula?authSource=admin",
                            # "MONGO_URL=mongodb://nebula:nebula@10.0.0.70:27017/nebula?authSource=admin",
                            "SCHEMA_NAME=nebula",
                            "BASIC_AUTH_USER=" + str(self.NEBULA_USERNAME),
                            "BASIC_AUTH_PASSWORD=" + str(self.NEBULA_PASSWORD),
                            "AUTH_TOKEN=" + str(self.NEBULA_AUTH_TOKEN),
                            "REDIS_HOST=" + str(self.REDIS_IP),
                            "REDIS_PORT=" + str(self.REDIS_PORT),
                            "REDIS_AUTH_TOKEN=" + str(self.REDIS_AUTH_TOKEN)
                        ],
                    )

            except docker.errors.ImageNotFound as e:
                logging.error(f"{e}")
                logging.error("Manager image not found")
                # return False
                return {"error": True, "response": "Manager image not found"}
            except docker.errors.APIError as e:
                logging.error(f"{e}")
                logging.error(f"Manager:Troble reaching the docker API")
                # return False
                return {
                    "error": True,
                    "response": "Manager:Trouble reaching the docker API, exception:{}".format(str(e)),
                }

            # return success
            return {"error": False, "response": "Manager run successfully"}
        else:
            logging.error(f"Manager Image Not defined in config files")
            return {
                "error": True,
                "response": "Manager Image Not defined in config files",
            }

    def checkManager(self):
        """
        Check whether the Nebula manager's `/api/v2/status` endpoint responds with HTTP 200.

        Defaults `NEBULA_PROTOCOL` to `"http"` if unset.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `False` only if the status endpoint returns HTTP 200;
            `True` on any other status code, or if the request itself
            raises (connection refused, timeout, etc.).
        """

        # nebulaObj = Nebula(username=self.NEBULA_USERNAME, host=self.MANAGER_IP, port=self.MANAGER_PORT,
        #                         token=self.NEBULA_AUTH_TOKEN, password=self.NEBULA_PASSWORD)
        # response = nebulaObj.check_api()
        
        if not self.NEBULA_PROTOCOL:
            self.NEBULA_PROTOCOL = "http"
        url = urlparse(
            self.NEBULA_PROTOCOL
            + "://"
            + str(self.MANAGER_IP)
            + ":"
            + str(self.MANAGER_PORT)
            + "/api/v2/status"
        )
        try:
            response = requests.get(
                url.geturl(),
                headers={"Authorization": "Basic " + str(self.NEBULA_AUTH_TOKEN)},
            )
            if response.status_code == 200:
                logging.info(f"Manager Up")
                # return True
                return {"error": False, "response": "Manager up successfully"}
            else:
                click.echo(click.style("Manager Up", fg="red"))
                # return True
                return {"error": True, "response": "Manager not reachable"}
        except Exception as e:
            logging.error(f"Unexpected error {e}")
            return {"error": True, "response": e}

        # return False

    def waitManager(self):
        """
        Block, polling `checkManager` every 3 seconds, until the Nebula manager responds.

        Returns
        -------
        dict
            ``{"error": False, "response": "Manager alive"}``. Always
            this value - the loop never exits any other way (no
            timeout or retry limit).
        """
        managerUp = False
        response = None
        while not managerUp:
            time.sleep(3)
            logging.warning(f"Waiting for manager to come alive..")
            response = self.checkManager()
            if not response["error"]:
                managerUp = True
            # managerUp = self.checkManager()
        # return True
        return {"error": False, "response": "Manager alive"}

    def run(self, service_name):
        """
        Dispatch to the `run<Service>` method matching `service_name`.

        Parameters
        ----------
        service_name : str
            One of `"registry"`, `"redis"`, `"mongo"`, `"manager"`,
            `"syncer"`, or `"all"` (brings up all five in that order,
            stopping at the first failure; if `"manager"` succeeds,
            also calls `waitManager`).

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `True` if `service_name` is unrecognized or the
            corresponding `run<Service>` call failed; `False` on
            success.
        """

        fg = "green"

        client = docker.from_env()
        success = None
        if service_name == "registry":
            success = self.runRegistry(client)
            if not success["error"]:
                logging.info(f"Register Up")
                return {
                    "error": False,
                    "response": "Registry Up",
                }
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }

        elif service_name == "redis":
            success = self.runRedis(client)
            if not success["error"]:
                logging.info(f"Redis Up")
                return {
                    "error": False,
                    "response": "Redis Up",
                }
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }
        elif service_name == "syncer":
            success = self.runSyncer(client)
            if not success["error"]:
                logging.info(f"Syncer Up")
                return {
                    "error": False,
                    "response": "Syncer Up",
                }
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }
        elif service_name == "mongo":
            success = self.runMongo(client)
            if not success["error"]:
                logging.info(f"Mongo Up")
                return {
                    "error": False,
                    "response": "Mongo Up",
                }
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }
        elif service_name == "manager":
            success = self.runManager(client)
            if not success["error"]:
                self.waitManager()
                return {
                    "error": False,
                    "response": "Manager running",
                }
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }
        elif service_name == "all":
            success = self.runRegistry(client)
            if not success["error"]:
                logging.info(f"Registry Up")
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }

            success = self.runRedis(client)
            if not success["error"]:
                logging.info(f"Redis Up")
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }
            success = self.runSyncer(client)
            if not success["error"]:
                logging.info("Syncer Up")
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }
            success = self.runMongo(client)
            if not success["error"]:
                logging.info(f"Mongo Up")
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }
            success = self.runManager(client)
            if not success["error"]:
                logging.info(f"Manager Up")
            else:
                return {
                    "error": True,
                    "response": success["response"],
                }
            self.waitManager()

            return {
                "error": False,
                "response": "All services brought up",
            }

        else:
            logging.error(f"service_name is not valid")
            return {
                "error": True,
                "response": "service_name is not valid",
            }

    def serviceStatus(self, service_name):
        """
        Check whether a container named `service_name` exists (running or not).

        Parameters
        ----------
        service_name : str
            Docker container name to look up.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `False` if the container exists (regardless of its
            running state); `True` if it doesn't exist or the Docker
            API errors.
        """
        client = docker.from_env()
        try:
            client.containers.get(service_name)
            return {"error": False, "response": "Container {} is running".format(service_name)}
        except docker.errors.NotFound:
            logging.error(f"Service {service_name} does not exist")
            return {"error": True, "response": "Container {} does not exist".format(service_name)}
        except docker.errors.APIError:
            logging.error(f"Trouble reaching the docker API")
            return {"error": True, "response": "Trouble reaching the docker API"}

    def handleService(self, service_name, action):
        """
        Look up a container by name and perform a lifecycle action on it.

        Parameters
        ----------
        service_name : str
            Docker container name to act on.
        action : str
            One of `"stop"`, `"start"`, `"kill"`, `"remove"` (force),
            or `"restart"`.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `True` if the container doesn't exist, `action` isn't
            recognized, or the Docker API errors; `False` on success.
        """

        if not isinstance(service_name, str):
            logging.error(f"service_name is not valid")

        client = docker.from_env()
        try:
            container_obj = client.containers.get(service_name)
        except docker.errors.NotFound:
            logging.error(f"No container called {service_name}")
            # return False
            return {"error": True, "response": "No container called"}

        except docker.errors.APIError:
            logging.error(f"Troble reaching the docker API")
            # return False
            return {"error": True, "response": "Trouble reaching the docker API"}
        try:
            if action == "stop":
                logging.warning(f"Stopping {service_name}")
                container_obj.stop()
                logging.info(f"{service_name} has been stopped")

            elif action == "start":
                logging.warning(f"Starting {service_name}")
                container_obj.start()
                logging.info(f"{service_name} has been started")

            elif action == "kill":
                logging.warning(f"Killing {service_name}")
                container_obj.kill()
                logging.info(f"{service_name} has been killed")

            elif action == "remove":
                logging.warning(f"Removing {service_name}")
                container_obj.remove(force=True)
                logging.info(f"{service_name} has been removed")

            elif action == "restart":
                logging.warning(f"Restarting {service_name}")
                container_obj.restart()
                logging.info(f"{service_name} has been restarted")

            else:
                logging.error(f"action is not valid")
                # return False
                return {"error": True, "response": "action is not valid"}

        except docker.errors.APIError:
            logging.error("Trouble reaching the docker API")
            # return False
            return {"error": True, "response": "Trouble reaching the docker API"}

        # return True
        return {"error": False, "response": "Service handled successfully"}

