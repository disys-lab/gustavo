from dotenv import load_dotenv
from pathlib import Path
import os, sys, click


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
                    # raise Exception("GUSTAVO_CONFIG_FILE: {} path not valid".format(self.base_config))
                    click.echo(
                        click.style(
                            "GUSTAVO_CONFIG_FILE: {} path not valid".format(
                                self.base_config
                            ),
                            fg="red",
                        )
                    )
                    # sys.exit()
                    # return {"error": True, "response": "GUSTAVO_CONFIG_FILE: {} path not valid"}
                    raise PathInvalid
            else:
                # raise Exception("GUSTAVO_CONFIG_FILE not defined")
                click.echo(click.style("GUSTAVO_CONFIG_FILE not defined", fg="red"))
                # sys.exit()
                # return {"error": True, "response": "GUSTAVO_CONFIG_FILE not defined"}
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
                self.CACHE_PREFIX = session_state["REDIS_PORT"]

                self.MANAGER_PORT = session_state["MANAGER_PORT"]
                self.NEBULA_USERNAME = session_state["NEBULA_USERNAME"]
                self.NEBULA_PASSWORD = session_state["NEBULA_PASSWORD"]
                self.NEBULA_AUTH_TOKEN = session_state["NEBULA_AUTH_TOKEN"]
                self.NEBULA_PROTOCOL = session_state["NEBULA_PROTOCOL"]

                self.DOCKER_HOST = "unix:/var/run/docker.sock"
                if len(self.DOCKER_HOST.split(":")) == 2:
                    self.DOCKER_HOST_SOCKET = self.DOCKER_HOST.split(":")[1]
                else:
                    click.echo(
                        click.style(
                            "ERROR: DOCKER_HOST={} must be like unix:/var/run/docker.sock .... quitting".format(
                                self.DOCKER_HOST_SOCKET
                            ),
                            fg="red",
                        )
                    )

                self.WORKER_NMODE = session_state["WORKER_NMODE"]
            else:
                click.echo(
                    click.style("session_state undefined in NebulaBase", fg="red")
                )

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
            self.CACHE_PREFIX = "nebula-reports"

        if "REDIS_HOST" in os.environ.keys():
            self.REDIS_IP = os.getenv("REDIS_HOST")
        else:
            # raise Exception("REDIS_IP undefined in base_config file")
            click.echo(click.style("REDIS_IP undefined in base_config file", fg="red"))
            # sys.exit()
            return {"error": True, "response": "REDIS_IP undefined in base_config file"}

        if "REDIS_PORT" in os.environ.keys():
            self.REDIS_PORT = int(os.getenv("REDIS_PORT"))
        else:
            # raise Exception("REDIS_PORT undefined in base_config file")
            click.echo(
                click.style("REDIS_PORT undefined in base_config file", fg="red")
            )
            # sys.exit()
            return {
                "error": True,
                "response": "REDIS_PORT undefined in base_config file",
            }

        if "REDIS_AUTH_TOKEN" in os.environ.keys():
            self.REDIS_AUTH_TOKEN = os.getenv("REDIS_AUTH_TOKEN")
        else:
            # raise Exception("REDIS_AUTH_TOKEN undefined in base_config file")
            click.echo(
                click.style("REDIS_AUTH_TOKEN undefined in base_config file", fg="red")
            )
            # sys.exit()
            return {
                "error": True,
                "response": "REDIS_AUTH_TOKEN undefined in base_config file",
            }

        if "REGISTRY_HOST" in os.environ.keys():
            self.REGISTRY_IP = os.getenv("REGISTRY_HOST")
        else:
            click.echo(
                click.style("REGISTRY_HOST undefined in base_config file", fg="red")
            )
            # sys.exit()
            return {
                "error": True,
                "response": "REGISTRY_HOST undefined in base_config file",
            }

        if "REGISTRY_PORT" in os.environ.keys():
            self.REGISTRY_PORT = int(os.getenv("REGISTRY_PORT"))
        else:
            # raise Exception("REGISTRY_PORT undefined in base_config file")
            click.echo(
                click.style("REGISTRY_PORT undefined in base_config file", fg="red")
            )
            # sys.exit()
            return {
                "error": True,
                "response": "REGISTRY_PORT undefined in base_config file",
            }

        if "MANAGER_HOST" in os.environ.keys():
            self.MANAGER_IP = os.getenv("MANAGER_HOST")
        else:
            # raise Exception("MANAGER_IP undefined in base_config file")
            click.echo(
                click.style("MANAGER_IP undefined in base_config file", fg="red")
            )
            # sys.exit()
            return {
                "error": True,
                "response": "MANAGER_IP undefined in base_config file",
            }

        if "MANAGER_PORT" in os.environ.keys():
            self.MANAGER_PORT = os.getenv("MANAGER_PORT")
        else:
            # raise Exception("MANAGER_PORT undefined in base_config file")

            click.echo(
                click.style("MANAGER_PORT undefined in base_config file", fg="red")
            )
            # sys.exit()
            return {
                "error": True,
                "response": "MANAGER_PORT undefined in base_config file",
            }

        if "WORKER_NMODE" in os.environ.keys():
            self.WORKER_NMODE = os.getenv("WORKER_NMODE")
        else:
            self.WORKER_NMODE = "bridge"

            click.echo(
                click.style("WORKER_NMODE undefined in base_config file", fg="red")
            )

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
            click.echo(
                click.style(
                    "ERROR: DOCKER_HOST={} must be like unix:/var/run/docker.sock .... quitting".format(
                        self.DOCKER_HOST_SOCKET
                    ),
                    fg="red",
                )
            )

        print(self.NEBULA_USERNAME + "@" + self.MANAGER_IP + ":" + self.MANAGER_PORT)

        click.echo(click.style("DOCKER_HOST:{}".format(self.DOCKER_HOST), fg="yellow"))
