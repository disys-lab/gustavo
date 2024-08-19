import click, os
from urllib.parse import urlparse
from dotenv import load_dotenv
from pathlib import Path
import requests
import docker
import time
from .NebulaBase import NebulaBase
from python_on_whales import docker as dockerow
import sys
from NebulaPythonSDK import Nebula


class Manager(NebulaBase):
    """
    Manager class inherits from NebulaBase and is responsible for handling all aspects of the manager, including
    the setup, configuration and tear down of the variety of manager services such as:
    * `registry`
    * `redis`
    * `mongo`
    * `manager`
    * `syncer`

    Attributes
    ----------
    DREGSY_CONFIG_FILE_PATH : string
        Config file for DREGSY which is the Syncer service being run on the manager

    DREGSY_MAPPING_FILE_PATH : string
        Mapping file that maps remote container images to the registry

    MONGO_IP : string
        Hostname or IP address of Mongo

    MONGO_PORT : string
        Port number of Mongo DB

    MONGO_USERNAME : string
        Username for accessing Mongo DB

    MONGO_PASSWORD : string
        Password for Mongo DB

    REGISTRY_IMAGE : string
        Docker image name to spin up

    SYNCER_IMAGE : string
        Docker image name to spin up

    REDIS_IMAGE : string
        Docker image name to spin up

    MONGO_IMAGE : string
        Docker image name to spin up

    MANAGER_IMAGE : string
        Docker image name to spin up

    MANAGER_NMODE: string
        Docker image network to spin up

    SYNCER_NMODE: string
        Docker image network to spin up

    TODO: Make setManagerParams() REST API-friendly, which means that instead of a sys.exit(), it needs to either
          throw an appropriate exception or return a status value or both.
          Good way to do it would be to throw an exception here and then catch it on gustavo.py

    """

    def __init__(self,mode="CLI",params = None):

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
        self.MONGO_IMAGE = None
        self.MANAGER_IMAGE = None

        self.MANAGER_NMODE = None
        self.SYNCER_NMODE = None

        self.service_list = "registry,redis,mongo,manager,syncer"

        if mode == "CLI":
            self.setManagerParams()

    def setManagerParams(self):
        """
        sets the class attributes from environment vars
        """
        if "DREGSY_CONFIG_FILE_PATH" in os.environ.keys():
            if os.path.isfile(os.environ["DREGSY_CONFIG_FILE_PATH"]):
                self.DREGSY_CONFIG_FILE_PATH = os.getenv("DREGSY_CONFIG_FILE_PATH")
            else:
                # raise Exception("DREGSY_CONFIG_FILE_PATH invalid")
                click.echo(click.style("DREGSY_CONFIG_FILE_PATH invalid", fg="red"))

                return {"error": True, "response": "DREGSY_CONFIG_FILE_PATH invalid"}
        else:
            # raise Exception("DREGSY_CONFIG_FILE_PATH undefined in base_config file")
            click.echo(
                click.style(
                    "DREGSY_CONFIG_FILE_PATH undefined in base_config file", fg="red"
                )
            )

            return {
                "error": True,
                "response": "DREGSY_CONFIG_FILE_PATH undefined in base_config file",
            }

        if "DREGSY_MAPPING_FILE_PATH" in os.environ.keys():
            if os.path.isfile(os.environ["DREGSY_MAPPING_FILE_PATH"]):
                self.DREGSY_MAPPING_FILE_PATH = os.getenv("DREGSY_MAPPING_FILE_PATH")
            else:
                # raise Exception("DREGSY_MAPPING_FILE_PATH invalid")
                click.echo(click.style("DREGSY_MAPPING_FILE_PATH invalid", fg="red"))

                return {"error": True, "response": "DREGSY_MAPPING_FILE_PATH invalid"}

        else:
            # raise Exception("DREGSY_MAPPING_FILE_PATH undefined in base_config file")
            click.echo(
                click.style(
                    "DREGSY_MAPPING_FILE_PATH undefined in base_config file", fg="red"
                )
            )

            return {
                "error": True,
                "response": "DREGSY_MAPPING_FILE_PATH undefined in base_config file",
            }

        if "MONGO_USERNAME" in os.environ.keys():
            self.MONGO_USERNAME = os.getenv("MONGO_USERNAME")
        else:
            # raise Exception("MONGO_USERNAME undefined in base_config file")
            click.echo(
                click.style("MONGO_USERNAME undefined in base_config file", fg="red")
            )

            return {
                "error": True,
                "response": "MONGO_USERNAME undefined in base_config file",
            }

        if "MONGO_PASSWORD" in os.environ.keys():
            self.MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
        else:
            # raise Exception("MONGO_PASSWORD undefined in base_config file")
            click.echo(
                click.style("MONGO_PASSWORD undefined in base_config file", fg="red")
            )

            return {
                "error": True,
                "response": "MONGO_PASSWORD undefined in base_config file",
            }

        if "MONGO_HOST" in os.environ.keys():
            self.MONGO_IP = os.getenv("MONGO_HOST")
        else:
            # raise Exception("MONGO_IP undefined in base_config file")
            click.echo(click.style("MONGO_IP undefined in base_config file", fg="red"))

            return {"error": True, "response": "MONGO_IP undefined in base_config file"}

        if "MONGO_PORT" in os.environ.keys():
            self.MONGO_PORT = int(os.getenv("MONGO_PORT"))
        else:
            # raise Exception("MONGO_PORT undefined in base_config file")
            click.echo(
                click.style("MONGO_PORT undefined in base_config file", fg="red")
            )

            return {
                "error": True,
                "response": "MONGO_PORT undefined in base_config file",
            }

        if "REGISTRY_IMAGE" in os.environ.keys():
            self.REGISTRY_IMAGE = os.getenv("REGISTRY_IMAGE")
        else:
            click.echo(
                click.style("REGISTRY_IMAGE undefined in base_config file", fg="red")
            )
            return {
                "error": True,
                "response": "REGISTRY_IMAGE undefined in base_config file",
            }

        if "SYNCER_IMAGE" in os.environ.keys():
            self.SYNCER_IMAGE = os.getenv("SYNCER_IMAGE")
        else:

            click.echo(
                click.style("SYNCER_IMAGE undefined in base_config file", fg="red")
            )

            return {
                "error": True,
                "response": "SYNCER_IMAGE undefined in base_config file",
            }
        if "REDIS_IMAGE" in os.environ.keys():
            self.REDIS_IMAGE = os.getenv("REDIS_IMAGE")
        else:

            click.echo(
                click.style("REDIS_IMAGE undefined in base_config file", fg="red")
            )

            return {
                "error": True,
                "response": "REDIS_IMAGE undefined in base_config file",
            }
        if "MONGO_IMAGE" in os.environ.keys():
            self.MONGO_IMAGE = os.getenv("MONGO_IMAGE")
        else:

            click.echo(
                click.style("MONGO_IMAGE undefined in base_config file", fg="red")
            )

            return {
                "error": True,
                "response": "MONGO_IMAGE undefined in base_config file",
            }
        if "MANAGER_IMAGE" in os.environ.keys():
            self.MANAGER_IMAGE = os.getenv("MANAGER_IMAGE")
        else:

            click.echo(
                click.style("MANAGER_IMAGE undefined in base_config file", fg="red")
            )

            return {
                "error": True,
                "response": "MANAGER_IMAGE undefined in base_config file",
            }

        if "MANAGER_NMODE" in os.environ.keys():
            self.MANAGER_NMODE = os.getenv("MANAGER_NMODE")
        else:
            self.MANAGER_NMODE = "bridge"
            click.echo(
                click.style("MANAGER_NMODE undefined in base_config file", fg="red")
            )

        if "SYNCER_NMODE" in os.environ.keys():
            self.SYNCER_NMODE = os.getenv("SYNCER_NMODE")
        else:
            self.SYNCER_NMODE = "bridge"

            click.echo(
                click.style("SYNCER_NMODE undefined in base_config file", fg="red")
            )

        return {"error": False, "response": "Manager Params set successfully"}

    def runRegistry(self, client):
        """
        Brings up the registry service

        Parameters
        ----------
        client : docker object
            The docker client object

        Raises
        ------
        docker.errors.ImageNotFound
            If the registry image is not found

        docker.errors.APIError
            If the docker API is unreachable

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the registry did not run
        If the key "error" is False it means that the registry ran successfully
            Based on success of the run registry command
        """

        if self.REGISTRY_IMAGE:

            # success = True
            dockerow.pull(self.REGISTRY_IMAGE)
            try:
                client.containers.run(
                    image=self.REGISTRY_IMAGE,
                    detach=True,
                    security_opt=["label=disable"],
                    ports={"5000": self.REGISTRY_PORT},
                    name="registry",
                    restart_policy={"Name": "always"},
                    volumes=[str(self.DOCKER_HOST_SOCKET) + ":/var/run/docker.sock:rw"],
                )
                # return {"error": False, "response": {"ipfs_bootnodes": redisRet}}
            except docker.errors.ImageNotFound as e:
                click.echo(click.style(e, fg="red"))
                click.echo(click.style("Registry image not found", fg="red"))
                # return False
                return {"error": True, "response": "Registry image not found"}
            except docker.errors.APIError as e:
                click.echo(click.style(e, fg="red"))
                click.echo(
                    click.style("Registry:Trouble reaching the docker API", fg="red")
                )
                # return False
                return {
                    "error": True,
                    "response": "Registry:Trouble reaching the docker API",
                }

            # return success
            return {"error": False, "response": "Registry ran successfully"}
        else:
            print("Registry Image Not defined in config files")
            return {
                "error": True,
                "response": "Registry Image Not defined in config files",
            }

    def runSyncer(self, client):
        """
        Brings up the syncer service

        Parameters
        ----------
        client : docker object
            The docker client object

        Raises
        ------
        docker.errors.ImageNotFound
            If the registry image is not found

        docker.errors.APIError
            If the docker API is unreachable

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the syncer did not run
        If the key "error" is False it means that the syncer ran successfully
            Based on success of the run syncer command
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
                click.echo(click.style(e, fg="red"))
                click.echo(click.style("Syncer (Dregsy) image not found", fg="red"))
                # return False
                return {"error": True, "response": "Syncer (Dregsy) image not found"}
            except docker.errors.APIError as e:
                click.echo(click.style(e, fg="red"))
                click.echo(
                    click.style("Syncer:Trouble reaching the docker API", fg="red")
                )
                # return False
                return {
                    "error": True,
                    "response": "Syncer:Trouble reaching the docker API",
                }

            # return success
            return {"error": False, "response": "Syncer run successfully"}
        else:
            print("Syncer Image Not defined in config files")
            return {
                "error": True,
                "response": "Syncer Image Not defined in config files",
            }

    def runRedis(self, client):
        """
        Brings up the Redis service

        Parameters
        ----------
        client : docker object
            The docker client object

        Raises
        ------
        docker.errors.ImageNotFound
            If the registry image is not found

        docker.errors.APIError
            If the docker API is unreachable

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the redis did not run
        If the key "error" is False it means that the redis ran successfully
            Based on success of the run redis command
        """

        if self.REDIS_IMAGE:
            # success = True
            dockerow.pull(self.REDIS_IMAGE)
            try:
                client.containers.run(
                    image=self.REDIS_IMAGE,
                    detach=True,
                    security_opt=["label=disable"],
                    name="redis",
                    ports={"6379": str(self.REDIS_PORT)},
                    restart_policy={"Name": "always"},
                    environment=["AUTH_TOKEN=" + str(self.REDIS_AUTH_TOKEN)],
                )
            except docker.errors.ImageNotFound as e:
                click.echo(click.style(e, fg="red"))
                click.echo(click.style("Redis image not found", fg="red"))
                # return False
                return {"error": True, "response": "Redis image not found"}
            except docker.errors.APIError as e:
                click.echo(click.style(e, fg="red"))
                click.echo(
                    click.style("Redis:Trouble reaching the docker API", fg="red")
                )
                # return False
                return {
                    "error": True,
                    "response": "Redis:Trouble reaching the docker API",
                }

            # return success
            return {"error": False, "response": "Redis run successfully"}
        else:
            print("Redis Image Not defined in config files")
            return {
                "error": True,
                "response": "Redis Image Not defined in config files",
            }

    def runMongo(self, client):
        """
        Brings up the Mongo service

        Parameters
        ----------
        client : docker object
            The docker client object

        Raises
        ------
        docker.errors.ImageNotFound
            If the registry image is not found

        docker.errors.APIError
            If the docker API is unreachable

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the mongo did not run
        If the key "error" is False it means that the mongo ran successfully
            Based on success of the run mongo command
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
                click.echo(click.style(e, fg="red"))
                click.echo(click.style("Mongo image not found", fg="red"))
                # return False
                return {"error": True, "response": "Mongo image not found"}
            except docker.errors.APIError as e:
                click.echo(click.style(e, fg="red"))
                click.echo(
                    click.style("Mongo:Trouble reaching the docker API", fg="red")
                )
                # return False
                return {
                    "error": True,
                    "response": "Mongo:Trouble reaching the docker API",
                }

            # return success
            return {"error": False, "response": "Mongo run successfully"}
        else:
            print("Mongo Image Not defined in config files")
            return {
                "error": True,
                "response": "Mongo Image Not defined in config files",
            }

    def runManager(self, client):
        """
        Brings up the Nebula Manager service

        Parameters
        ----------
        client : docker object
            The docker client object

        Raises
        ------
        docker.errors.ImageNotFound
            If the registry image is not found

        docker.errors.APIError
            If the docker API is unreachable

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the manager did not run
        If the key "error" is False it means that the manager ran successfully
            Based on success of the run manager command
        """

        if self.MANAGER_IMAGE:
            # success = True
            dockerow.pull(self.MANAGER_IMAGE)
            try:
                print("Spinning up Manager in " + self.MANAGER_NMODE + " network mode")
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
                        ],
                    )

            except docker.errors.ImageNotFound as e:
                click.echo(click.style(e, fg="red"))
                click.echo(click.style("Manager image not found", fg="red"))
                # return False
                return {"error": True, "response": "Manager image not found"}
            except docker.errors.APIError as e:
                click.echo(click.style(e, fg="red"))
                click.echo(
                    click.style("Manager:Trouble reaching the docker API", fg="red")
                )
                # return False
                return {
                    "error": True,
                    "response": "Manager:Trouble reaching the docker API",
                }

            # return success
            return {"error": False, "response": "Manager run successfully"}
        else:
            print("Manager Image Not defined in config files")
            return {
                "error": True,
                "response": "Manager Image Not defined in config files",
            }

    def checkManager(self):
        """
        Checks whether manager API is available

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the check manager did not run
        If the key "error" is False it means that the check manager ran successfully
            Based on success of the check manager command
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
                headers={"Authorization": "Basic " + self.NEBULA_AUTH_TOKEN},
            )
            if response.status_code == 200:
                click.echo(click.style("Manager Up", fg="green"))
                # return True
                return {"error": False, "response": "Manager up successfully"}
        except Exception as e:
            print("Unexpected error:", e)
            return {"error": True, "response": e}

        # return False

    def waitManager(self):
        """
        Keeps waiting until Nebula Manager API responds

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the wait manager did not run
        If the key "error" is False it means that the wait manager ran successfully
            Based on success of the wait manager command
        """
        managerUp = False
        response = None
        while not managerUp:
            time.sleep(3)
            click.echo(click.style("Waiting for manager to come alive..", fg="yellow"))
            response = self.checkManager()
            if not response["error"]:
                managerUp = True
            # managerUp = self.checkManager()
        # return True
        return {"error": False, "response": "Manager alive"}

    def run(self, service_name):
        """
        Wrapper function to invoke the corresponding run function based on a given service name. Options are :
        * `registry`
        * `redis`
        * `mongo`
        * `manager`
        * `syncer`
        * `all`

        Parameters
        ----------
        service_name : string
            Name of service to run

        TODO: return success status
        """

        fg = "green"

        client = docker.from_env()
        success = None
        if service_name == "registry":
            success = self.runRegistry(client)
            if not success["error"]:
                click.echo(click.style("Registry Up", fg="green"))
                return {
                    "error": False,
                    "response": "Registry Up",
                }
            else:
                return {
                    "error": True,
                    "response": "Registry Image Not defined in config files",
                }

        elif service_name == "redis":
            success = self.runRedis(client)
            if not success["error"]:
                click.echo(click.style("Redis Up", fg="green"))
                return {
                    "error": False,
                    "response": "Redis Up",
                }
            else:
                return {
                    "error": True,
                    "response": "Redis Image Not defined in config files",
                }
        elif service_name == "syncer":
            success = self.runSyncer(client)
            if not success["error"]:
                click.echo(click.style("Syncer Up", fg="green"))
                return {
                    "error": False,
                    "response": "Syncer Up",
                }
            else:
                return {
                    "error": True,
                    "response": "Syncer Image Not defined in config files",
                }
        elif service_name == "mongo":
            success = self.runMongo(client)
            if not success["error"]:
                click.echo(click.style("Mongo Up", fg="green"))
                return {
                    "error": False,
                    "response": "Mongo Up",
                }
            else:
                return {
                    "error": True,
                    "response": "Mongo Image Not defined in config files",
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
                    "response": "Manager Image Not defined in config files",
                }
        elif service_name == "all":
            success = self.runRegistry(client)
            if not success["error"]:
                click.echo(click.style("Registry Up", fg="green"))
            else:
                return {
                    "error": True,
                    "response": "Registry Image Not defined in config files",
                }

            success = self.runRedis(client)
            if not success["error"]:
                click.echo(click.style("Redis Up", fg="green"))
            else:
                return {
                    "error": True,
                    "response": "Redis Image Not defined in config files",
                }
            success = self.runSyncer(client)
            if not success["error"]:
                click.echo(click.style("Syncer Up", fg="green"))
            else:
                return {
                    "error": True,
                    "response": "Syncer Image Not defined in config files",
                }
            success = self.runMongo(client)
            if not success["error"]:
                click.echo(click.style("Mongo Up", fg="green"))
            else:
                return {
                    "error": True,
                    "response": "Mongo Image Not defined in config files",
                }
            success = self.runManager(client)
            if not success["error"]:
                click.echo(click.style("Manager Up", fg="green"))
            else:
                return {
                    "error": True,
                    "response": "Manager Image Not defined in config files",
                }
            self.waitManager()

            return {
                "error": False,
                "response": "All services brought up",
            }

        else:
            click.echo(click.style("service_name is not valid", fg="red"))
            return {
                "error": True,
                "response": "service_name is not valid",
            }

    def serviceStatus(self, service_name):
        client = docker.from_env()
        try:
            client.containers.get(service_name)
            return {"error": False, "response": "Container {} is running".format(service_name)}
        except docker.errors.NotFound:
            click.echo(click.style("Service {} does not exist".format(service_name), fg="red"))
            return {"error": True, "response": "Container {} does not exist".format(service_name)}
        except docker.errors.APIError:
            click.echo(click.style("Trouble reaching the docker API", fg="red"))
            return {"error": True, "response": "Trouble reaching the docker API"}

    def handleService(self, service_name, action):
        """
        Performs a given action on a given service name. The option for actions are:
        * `stop` : stop given service
        * `start` : start given service
        * `kill` : kill given service
        * `remove` : remove given service
        * `restart` : restart given service

        Parameters
        ----------
        service_name : string
            Name of service to run

        action : string
            Action to be taken

        Raises
        ------
        docker.errors.NotFound
            No container with the given service name has been found

        docker.errors.APIError
            If the docker API is unreachable

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the handle service did not run
        If the key "error" is False it means that the handle service ran successfully
            Based on success of the handle service command
        """

        if not isinstance(service_name, str):
            click.echo(click.style("service_name is not valid", fg="red"))

        client = docker.from_env()
        try:
            container_obj = client.containers.get(service_name)
        except docker.errors.NotFound:
            click.echo(click.style("No container called " + service_name, fg="red"))
            # return False
            return {"error": True, "response": "No container called"}

        except docker.errors.APIError:
            click.echo(click.style("Trouble reaching the docker API", fg="red"))
            # return False
            return {"error": True, "response": "Trouble reaching the docker API"}
        try:
            if action == "stop":
                click.echo(click.style("Stopping " + str(service_name), fg="yellow"))
                container_obj.stop()
                click.echo(
                    click.style("{} has been stopped".format(service_name), fg="green")
                )

            elif action == "start":
                click.echo(click.style("Starting " + str(service_name), fg="yellow"))
                container_obj.start()
                click.echo(
                    click.style("{} has been started".format(service_name), fg="green")
                )

            elif action == "kill":
                click.echo(click.style("Killing " + str(service_name), fg="yellow"))
                container_obj.kill()
                click.echo(
                    click.style("{} has been killed".format(service_name), fg="green")
                )

            elif action == "remove":
                click.echo(click.style("Removing " + str(service_name), fg="yellow"))
                container_obj.remove(force=True)
                click.echo(
                    click.style("{} has been removed".format(service_name), fg="green")
                )

            elif action == "restart":
                click.echo(click.style("Restarting " + str(service_name), fg="yellow"))
                container_obj.restart()
                click.echo(
                    click.style(
                        "{} has been restarted".format(service_name), fg="green"
                    )
                )

            else:
                click.echo(click.style("action is not valid", fg="red"))
                # return False
                return {"error": True, "response": "action is not valid"}

        except docker.errors.APIError:
            click.echo(click.style("Trouble reaching the docker API", fg="red"))
            # return False
            return {"error": True, "response": "Trouble reaching the docker API"}

        # return True
        return {"error": False, "response": "Service handled successfully"}
