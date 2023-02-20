from crypt import methods
import click
import yaml
import docker
from gustavo.src.Composer import Composer
from gustavo.src.Composer import Composer
from gustavo.src.NebulaBase import FileUndefined
from gustavo.src.NebulaBase import PathInvalid
from gustavo.src.Cache import Cache
from gustavo.src.Cache import ErrorHandling
from gustavo.src.Manager import Manager
from python_on_whales import docker as dockerow
import socket, sys
import base64
import json
from re import search


def readConfigFile(config_file):
    """
    Reads configuration file

    Parameters
    ----------
    config_file : string
        The config file to be read

    Returns
    -------

    app_config : dict
        The dict containing config variables.

    TODO : Make the calling consistent to REST-ify the function. Must return empty in case of failure or throw an
           exception.

    """
    try:
        stream = open(config_file, "r")
    except Exception as exception:
        click.echo(
            click.style(
                "failure opening file : {} with exception: {}".format(
                    config_file, exception
                ),
                fg="red",
            )
        )
        return {
            "error": True,
            "response": "failure opening file : {} with exception: {}".format(
                config_file, exception
            ),
        }
    try:
        app_config = yaml.safe_load(stream)
    except yaml.YAMLError as exception:
        click.echo(
            click.style(
                "failure opening file : {} with exception: {}".format(
                    config_file, exception
                ),
                fg="red",
            )
        )
        return {
            "error": True,
            "response": "failure opening file : {} with exception: {}".format(
                config_file, exception
            ),
        }

    return app_config


def handleMultipleApp(file, name, mode, fileType, device_groups=None):

    """
    Handles app creation and updation and forms a wrapper to "handleCreateApp"
    Parameters
    ----------
    file : string
        The config file to be read
    name : string
        The app name to be handled
    mode : string
        The mode of app creation, allowed modes are "create" and "update"
    device_groups = string
        Comma separated string list of device groups that app needs to be associated with
    """

    config_file = file
    result = {"error": True, "response": ""}
    intermediate = {}
    if fileType == "yaml" or fileType == "yml":
        app_config = readConfigFile(config_file)
    else:
        app_config = config_file

    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "BLOCKALYTICS_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {"error": True, "response": "BLOCKALYTICS_CONFIG_FILE not defined"}
    except Exception as e:
        return {"error": True, "response": e}

    if name == "all":
        app_list = app_config.keys()
    else:
        app_list = name.split(",")
    for app_name in app_list:
        if app_name in app_config.keys():
            if mode == "create":
                if device_groups == None or not isinstance(device_groups, str):
                    intermediate.update(
                        {
                            app_name: "error_app: "
                            + str(app_name)
                            + " device groups list: "
                            + str(device_groups)
                            + " invalid!"
                        }
                    )
                else:
                    # if device group is valid, then create the app
                    response = handleCreateApp(
                        bcmp, app_name, app_config, device_groups
                    )
                    result.update({"error": False})
                    intermediate.update(
                        {
                            app_name: str(response["error_app"]["response"])
                            + str(response["error_dg"]["response"])
                        }
                    )

            elif mode == "update":
                # update the app in case mode says update, this can simply be done by calling Composer.handleAsset
                response = bcmp.handleAsset(
                    "app", app_name, "update", app_config[app_name]
                )
                result.update({"error": False})
                intermediate.update({app_name: response["response"]})
            else:
                intermediate.update(
                    {
                        app_name: str(
                            "error_app: "
                            + str(app_name)
                            + " mode: "
                            + str(mode)
                            + " invalid!"
                        )
                    }
                )
        else:
            intermediate.update(
                {
                    app_name: str(
                        "error_app: "
                        + str(app_name)
                        + " could not be found in supplied config file",
                    )
                }
            )
    result["response"] = intermediate
    return result


def handleCreateApp(bcmp, app_name, app_config, device_groups):
    """
    Handles app creation based on app name, device group and the app configuration provided. This method wraps around the
    methods "handleAsset" and "handleDeviceGroup" from the Composer class.

    Parameters
    ----------
    bcmp : Composer
        The Composer object
    app_name : string
        The app name to be created
    app_config : dict
        The dictionary containing configurations
    device_groups : string
        A comma separated list of strings

    """
    if not isinstance(device_groups, str):
        return {
            "error": True,
            "response": "error_app: "
            + str(app_name)
            + " device groups list: "
            + str(device_groups)
            + " invalid!",
        }
    if app_name not in app_config.keys():
        return {
            "error": True,
            "response": "error_app: " + str(app_name) + " not found in config list ",
        }

    appRes = bcmp.handleAsset("app", app_name, "create", app_config[app_name])

    # get list of device groups already present
    response = bcmp.nebulaObj.list_device_groups()

    device_group_list = device_groups.split(",")
    for device_group in device_group_list:

        if device_group not in response["reply"]["device_groups"]:
            # if device group does not exist, create a device group, with app_name as the only app
            responseDG = bcmp.handleAsset(
                "device_group", device_group, "create", {"apps": [app_name]}
            )

        else:
            # else update the device group by adding app_name as one of the apps in the device group
            responseDG = bcmp.handleDeviceGroup(
                app_name, "update", device_group=device_group
            )

    return {"error_app": appRes, "error_dg": responseDG}


def createWorker(name, device_group, image, prefix, expire_time):

    """
    Creates a worker container for a specific device group, image, a prefix and an expire time

    Parameters
    ----------

    name : string
        The name of the worker to be created

    device_group : string
        The device group to be associated with the worker

    image : string
        The container image that needs to be used for the worker

    prefix : string
        Prefix for cache entries, the topic used to identify cache entries in redis, default is "nebula-reports"

    expire_time : string
        The expire time for cache content on redis

    """

    if not isinstance(name, str):
        click.echo(
            click.style(
                "DEVICE_GROUP_NAME_INVALID: enter a valid device group name", fg="red"
            )
        )
        return {
            "error": True,
            "response": "DEVICE_GROUP_NAME_INVALID: enter a valid device group name",
        }
    dockerow.pull(image)

    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "BLOCKALYTICS_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {"error": True, "response": "BLOCKALYTICS_CONFIG_FILE not defined"}
    except Exception as e:
        return {"error": True, "response": e}

    client = docker.from_env()

    if not search("_" + device_group, name):
        name = name + "_" + device_group

    try:
        print("Spinning up Worker in " + bcmp.WORKER_NMODE + " network mode")
        if bcmp.WORKER_NMODE == "host":

            client.containers.run(
                image=image,
                detach=True,
                security_opt=["label=disable"],
                network_mode=bcmp.WORKER_NMODE,
                environment=[
                    "DEVICE_GROUP=" + str(device_group),
                    #"HOST_MACHINE_IP=" + str(local_ip),
                    "REDIS_HOST=" + str(bcmp.REDIS_IP),
                    "REDIS_PORT=" + str(bcmp.REDIS_PORT),
                    "REDIS_AUTH_TOKEN=" + str(bcmp.REDIS_AUTH_TOKEN),
                    "REDIS_EXPIRE_TIME=" + str(expire_time),
                    "REDIS_KEY_PREFIX=" + str(prefix),
                    "REGISTRY_HOST=http://"
                    + str(bcmp.REGISTRY_IP)
                    + ":"
                    + str(bcmp.REGISTRY_PORT)
                    + "/",
                    "MAX_RESTART_WAIT_IN_SECONDS=0",
                    "NEBULA_MANAGER_AUTH_USER=" + str(bcmp.NEBULA_USERNAME),
                    "NEBULA_MANAGER_AUTH_PASSWORD=" + str(bcmp.NEBULA_PASSWORD),
                    "NEBULA_MANAGER_HOST=" + str(bcmp.MANAGER_IP),
                    "NEBULA_MANAGER_PORT=" + str(bcmp.MANAGER_PORT),
                    "NEBULA_MANAGER_PROTOCOL=" + str(bcmp.NEBULA_PROTOCOL),
                    "NEBULA_MANAGER_CHECK_IN_TIME=5",
                ],
                name=name,
                restart_policy={"Name": "always"},
                volumes=[str(bcmp.DOCKER_HOST_SOCKET) + ":/var/run/docker.sock:rw"],
            )
        else:
            client.containers.run(
                image=image,
                detach=True,
                security_opt=["label=disable"],
                environment=[
                    "DEVICE_GROUP=" + str(device_group),
                    #"HOST_MACHINE_IP=" + str(local_ip),
                    "REDIS_HOST=" + str(bcmp.REDIS_IP),
                    "REDIS_PORT=" + str(bcmp.REDIS_PORT),
                    "REDIS_AUTH_TOKEN=" + str(bcmp.REDIS_AUTH_TOKEN),
                    "REDIS_EXPIRE_TIME=" + str(expire_time),
                    "REDIS_KEY_PREFIX=" + str(prefix),
                    "REGISTRY_HOST=http://"
                    + str(bcmp.REGISTRY_IP)
                    + ":"
                    + str(bcmp.REGISTRY_PORT)
                    + "/",
                    "MAX_RESTART_WAIT_IN_SECONDS=0",
                    "NEBULA_MANAGER_AUTH_USER=" + str(bcmp.NEBULA_USERNAME),
                    "NEBULA_MANAGER_AUTH_PASSWORD=" + str(bcmp.NEBULA_PASSWORD),
                    "NEBULA_MANAGER_HOST=" + str(bcmp.MANAGER_IP),
                    "NEBULA_MANAGER_PORT=" + str(bcmp.MANAGER_PORT),
                    "NEBULA_MANAGER_PROTOCOL=" + str(bcmp.NEBULA_PROTOCOL),
                    "NEBULA_MANAGER_CHECK_IN_TIME=5",
                ],
                name=name,
                restart_policy={"Name": "always"},
                volumes=[str(bcmp.DOCKER_HOST_SOCKET) + ":/var/run/docker.sock:rw"],
            )
        click.echo(click.style("Worker Up", fg="green"))
        return {"error": False, "response": "Worker Up"}
    except Exception as e:
        click.echo(click.style(e, fg="red"))
        return {"error": True, "response": e}


def removeWorker(name):
    """
    Removes the given worker

    Parameters
    ----------
    name: string
        The name of the worker to remove
    """
    client = docker.from_env()
    try:
        container_obj = client.containers.get(name)
    except docker.errors.NotFound:
        click.echo(
            click.style("No worker container called {} found".format(name), fg="red")
        )
        return {"error": True, "response": "No worker container found"}
    except docker.errors.APIError:
        click.echo(click.style("Trouble reaching the docker API", fg="red"))
        return {"error": True, "response": "Trouble reaching the docker API"}

    try:
        container_obj.stop()
    except docker.errors.APIError:
        click.echo(click.style("Trouble reaching the docker API", fg="red"))
        return {"error": True, "response": "Trouble reaching the docker API"}

    try:
        container_obj.remove()
    except docker.errors.APIError:
        click.echo(click.style("Trouble reaching the docker API", fg="red"))
        return {"error": True, "response": "Trouble reaching the docker API"}

    click.echo(
        click.style("Worker named: {} has been brought down".format(name), fg="yellow")
    )
    return {"error": False, "response": "Worker has been brought down"}


def handleManagerServices(service, action):
    """
    Handles manager services by calling Manager.handleService

    Parameters
    ----------

    service : string
        Comma separated list of services to be handled

    action : string
        Action to be taken on the set of services. For the allowable actions refer to Manager.handleServices

    """
    man = Manager()
    if service == "all":
        service = man.service_list
    service_list = service.split(",")
    for svc in service_list:
        if not click.confirm(
            "About to perform action : "
            + str(action)
            + " on service : "
            + str(svc)
            + ", do you want to continue?",
            abort=True,
        ):
            continue
        response = man.handleService(svc, action)

    return response
