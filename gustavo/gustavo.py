import click
from gustavo.src.Composer import Composer
from gustavo.src.NebulaBase import FileUndefined
from gustavo.src.NebulaBase import PathInvalid
from gustavo.src.Cache import Cache
from gustavo.src.Cache import ErrorHandling
from gustavo.src.Manager import Manager
from gustavo.utils import *
from streamlit.web import cli
import os, pkg_resources

try:
    VERSION=pkg_resources.require("gustavo")[0].version
except Exception as e:
    VERSION="dev"


@click.version_option(version=VERSION)
@click.group(help="Manage gustavo from a simple CLI.")
def gustavo():
    pass


@click.version_option(version=VERSION)
@gustavo.group(help="Manage applications")
def apps():
    pass


@click.version_option(version=VERSION)
@gustavo.group(help="Manage device groups.")
def device_group():
    pass


@click.version_option(version=VERSION)
@gustavo.group(help="Administer the manager.")
def manager():
    pass


@click.version_option(version=VERSION)
@gustavo.group(help="Manage worker.")
def worker():
    pass


@click.version_option(version=VERSION)
@gustavo.group(help="Manage local registry.")
def registry():
    pass

@click.version_option(version=VERSION)
@gustavo.group(help="Prune images.")
def prune():
    pass


@click.version_option(version=VERSION)
@gustavo.group(help="Obtain status of various workers on the platform")
def cache():
    pass


@click.version_option(version=VERSION)
@gustavo.group(help="Utility commands")
def utils():
    pass

# @click.version_option(version=VERSION)
# @gustavo.group(help="Start the Gustavo GUI")
# def gui():
#     pass

@gustavo.command(
    help="Start the Gustavo GUI"
)
@click.option(
    "--port", "-p", help="specify port for serving GUI", prompt=True, default=8501
)
def gui(port):
    cwd = os.path.dirname(os.path.realpath(__file__))
    gui_runner_file = os.path.join(cwd,"Home.py")
    print(gui_runner_file)
    cli.main_run([gui_runner_file, "--server.headless", "true", "--server.port", int(port)])

@utils.command(
    help='specify JSON {"username": "...", "password": "..."}', name="syncer-auth-token"
)
@click.option(
    "--username", "-u", help="specify username for remote registry", prompt=True
)
@click.option(
    "--password",
    "-p",
    help="specify password for remote registry",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
)
def syncerAuthToken(username, password):
    syncerAuthTokens(username, password)


def syncerAuthTokens(username, password):
    raw_content = json.dumps({"username": username, "password": password})
    raw_content_bytes = raw_content.encode("ascii")
    base64_bytes = base64.b64encode(raw_content_bytes)
    click.echo(click.style("{}".format(str(base64_bytes.decode("utf-8")))))

    return {
        "error": False,
        "response": str("{}".format(str(base64_bytes.decode("utf-8")))),
    }


@cache.command(help="acquire vitals for devices", name="vitals")
@click.option("--device_group", "-d", help="specify device group", default="bca")
@click.option("--host", "-h", help="specify host id", default="all")
def getVitals(device_group, host):
    getsVitals(device_group, host)


def getsVitals(device_group, host):
    try:
        cache = Cache()
    except ErrorHandling:
        return {"error": True, "response": "Redis has some issue"}
    except Exception as e:
        return {"error": True, "response": e}
    res = cache.getAssetsForAll("vitals", device_group, host)
    return res


@cache.command(
    help="check container images on host and device_groups", name="containers"
)
@click.option("--device_group", "-d", help="specify device group", default="bca")
@click.option("--host", "-h", help="specify host id", default="all")
def getContainers(device_group, host):
    getsContainers(device_group, host)


def getsContainers(device_group, host):
    try:
        cache = Cache()
    except ErrorHandling:
        return {"error": True, "response": "Redis has some issue"}
    except Exception as e:
        return {"error": True, "response": e}
    responseCont = cache.getAssetsForAll("containers", device_group, host)

    return responseCont


@cache.command(help="fetch all hosts", name="hosts")
@click.option("--device_group", "-d", help="specify device group", default="bca")
@click.option("--host", "-h", help="specify host id", default="all")
def getHosts(device_group, host):
    getsHosts(device_group, host)


def getsHosts(device_group, host):
    try:
        cache = Cache()
    except ErrorHandling:
        return {"error": True, "response": "Redis has some issue"}
    except Exception as e:
        return {"error": True, "response": e}
    response = cache.getHosts(device_group, host)
    print(response["response"])
    return {"error": False, "response": response["response"]}

@registry.command(help="check images on local registry", name="list")
@click.option("--name", "-n", help="image name to be checked", default="all")
@click.option("--tag", "-t", help="image tag to search", default="all")
def checkLocalRegistry(name, tag):
    checkLocalRegistries(name, tag)


def checkLocalRegistries(name, tag):
    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {"error": True, "response": "GUSTAVO_CONFIG_FILE not defined"}
    except Exception as e:
        return {"error": True, "response": e}
    response = bcmp.checkLocalRepoImages(name, tag)
    if response["error"]:
        return {"error": True, "response": "image not on local registry"}
    else:
        return response


@prune.command(help="prune unused images on a device_group", name="device_group")
@click.option(
    "--device_group", "-d", help="nebula device_group to prune images on", default="bca"
)
def prune_device_group(device_group):
    prune_device_groups(device_group)


def prune_device_groups(device_group):
    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {"error": True, "response": "GUSTAVO_CONFIG_FILE not defined"}
    except Exception as e:
        return {"error": True, "response": e}
    response = bcmp.prune_device_group_images(device_group)
    if response["error"]:
        return {"error": True, "response": "pruning not done"}
    else:
        return response


@apps.command(help="list all nebula apps", name="list")
def listApp():
    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {"error": True, "response": "GUSTAVO_CONFIG_FILE not defined"}
    except Exception as e:
        return {"error": True, "response": e}
    existing_app_list = bcmp.nebulaObj.list_apps()
    print(existing_app_list["reply"]["apps"])


@apps.command(help="create a new nebula app", name="create")
@click.option(
    "--name", "-n", help="name of the app to be created", prompt="what is the app name?"
)
@click.option(
    "--file",
    "-f",
    help="config file specifying app settings",
    prompt="what are the app settings?",
)
@click.option(
    "--device_groups",
    "-d",
    help="comma separated list of device groups to which the app is to be added",
    default="bca",
)
def createApp(name, file, device_groups):
    createApps(name, file, device_groups)


def createApps(name, file, device_groups, fileType="yml"):
    app_name = name
    config_file = file

    if fileType == "yaml" or fileType == "yml":
        if isinstance(app_name, str):
            app_config = readConfigFile(config_file)
            type(app_config)
        else:

            return {
                "error": True,
                "response": "APP_NAME_INVALID: enter a valid app name",
            }
    else:
        app_config = config_file

    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {"error": True, "response": "GUSTAVO_CONFIG_FILE not defined"}
    except Exception as e:
        return {"error": True, "response": e}

    response = handleCreateApp(bcmp, app_name, app_config, device_groups)

    return response


@apps.command(help="create a new nebula app", name="createm")
@click.option(
    "--file",
    "-f",
    help="config file specifying app settings",
    prompt="what are the app settings?",
)
@click.option(
    "--name",
    "-n",
    help="comma separated list of app names to be created",
    default="all",
)
@click.option(
    "--device_groups",
    "-d",
    help="comma separated list of device groups to which the app is to be added",
    default="bca",
)
def createAppMultiple(file, name, device_groups):
    createAppsMultiple(file, name, device_groups)


def createAppsMultiple(file, name, device_groups, fileType="yml"):
    response = handleMultipleApp(file, name, "create", fileType, device_groups)
    return response


@apps.command(help="update an existing nebula app", name="update")
@click.option(
    "--name", "-n", help="name of the app to be updated", prompt="what is the app name?"
)
@click.option(
    "--file",
    "-f",
    help="updated config file specifying app settings",
    prompt="what are the updated settings?",
)
def updateApp(name, file):

    updateApps(name, file)


def updateApps(name, file, fileType="yml"):

    app_name = name
    config_file = file

    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE not defined",
        }
    except Exception as e:
        return {"error": True, "response": e}

    if fileType == "yaml" or fileType == "yml":
        if isinstance(app_name, str):

            app_config = readConfigFile(config_file)
        else:
            return {
                "error": True,
                "response": "APP_NAME_INVALID: enter a valid app name",
            }
    else:

        app_config = config_file
    response = bcmp.handleAsset("app", app_name, "update", app_config[app_name])

    return {"error": False, "response": response}


@apps.command(help="update an existing nebula app", name="updatem")
@click.option(
    "--name",
    "-n",
    help="comma separated list of app names to be created",
    default="all",
)
@click.option(
    "--file",
    "-f",
    help="updated config file specifying app settings",
    prompt="what are the updated settings?",
)
def updateAppMultiple(name, file):

    updateAppsMultiple(name, file)


def updateAppsMultiple(name, file, fileType="yml"):
    response = handleMultipleApp(file, name, "update", fileType)

    return {"response": response}


@apps.command(help="delete an existing nebula app", name="delete")
@click.option(
    "--name", "-n", help="name of the app to be deleted", prompt="what is the app name?"
)
def deleteApp(name):
    deleteApps(name)


def deleteApps(name):
    app_name = name
    if isinstance(app_name, str):
        try:
            bcmp = Composer()
        except PathInvalid:
            return {
                "error": True,
                "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
            }
        except FileUndefined:
            return {"error": True, "response": "GUSTAVO_CONFIG_FILE not defined"}
        except Exception as e:
            return {"error": True, "response": e}

    else:
        return {"error": True, "response": "APP_NAME_INVALID: enter a valid app name"}

    response = bcmp.nebulaObj.list_device_groups()

    for device_group in response["reply"]["device_groups"]:

        response = bcmp.nebulaObj.list_device_group(device_group)

        bcmp.printDiagnosticResponse(
            response, 200, "check", "app list for", device_group
        )

        existing_app_list = response["reply"]["apps"]

        if app_name in existing_app_list:
            existing_app_list.remove(app_name)
            device_group_config = dict({"apps": existing_app_list})
            retval = bcmp.handleAsset(
                "device_group", device_group, "update", device_group_config
            )

            if retval:
                click.echo(
                    click.style(
                        "Deleted " + str(app_name) + " from device group" + str(),
                        fg="yellow",
                    )
                )

    retval = bcmp.handleAsset("app", app_name, "delete")

    if retval:
        return retval
    else:
        return {"error": True, "response": "delete app failed"}


@device_group.command(help="list all device groups", name="list")
@click.option(
    "--name", "-n", help="name of the device group to be listed", default="all"
)
def listDeviceGroup(name):
    listDeviceGroups(name)


def listDeviceGroups(name):
    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {"error": True, "response": "GUSTAVO_CONFIG_FILE not defined"}
    except Exception as e:
        return {"error": True, "response": e}
    if name == "all":
        existing_device_groups = bcmp.nebulaObj.list_device_groups()
    else:
        existing_device_groups = bcmp.nebulaObj.list_device_group(name)
    print(existing_device_groups["reply"])
    return existing_device_groups["reply"]


@device_group.command(help="create a new device group", name="create")
@click.option(
    "--name", "-n", help="name of the device group to be created", default="bca"
)
@click.option(
    "--apps",
    "-a",
    help="comma separated list of apps",
    prompt="what are the apps in this device group?",
)
def createDeviceGroup(apps, name):
    createDeviceGroups(apps, name)


def createDeviceGroups(apps, name):
    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {"error": True, "response": "GUSTAVO_CONFIG_FILE not defined"}
    except Exception as e:
        return {"error": True, "response": e}
    device_group_config = dict({"apps": [apps]})
    response = bcmp.handleAsset("device_group", name, "create", device_group_config)
    return response


@device_group.command(help="update a device group", name="update")
@click.option(
    "--name", "-n", help="name of the device group to be updated", default="bca"
)
@click.option(
    "--apps",
    "-a",
    help="comma separated list of apps",
    prompt="what are the apps you want to change in this device group?",
)
@click.option(
    "--add",
    "action",
    help="add the listed apps to device group",
    flag_value="update",
    default=True,
)
@click.option(
    "--remove",
    "action",
    help="remove the listed apps to device group",
    flag_value="delete",
)
def updateDeviceGroup(
    apps,
    action,
    name="bca",
):
    updateDeviceGroups(apps, action, name)


def updateDeviceGroups(
    apps,
    action,
    name="bca",
):

    try:
        bcmp = Composer()
    except PathInvalid:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
        }
    except FileUndefined:
        return {
            "error": True,
            "response": "GUSTAVO_CONFIG_FILE not defined",
        }
    except Exception as e:
        return {"error": True, "response": e}

    if isinstance(apps, str):

        app_list = apps.replace(" ", "")
        click.echo(
            click.style("The list of apps to be " + str(action) + " are:" + app_list)
        )

        response = bcmp.handleDeviceGroup(apps, action, name)
        if response["error"]:
            return {
                "error": True,
                "response": "device group not updated - APP_NAMES_INVALID: enter a valid app name",
            }
        else:
            return response
    else:
        click.echo(click.style("APP_NAMES_INVALID: enter a valid app name", fg="red"))
        return {
            "error": True,
            "response": "device group not updated - APP_NAMES_INVALID: enter a valid app name",
        }


@device_group.command(help="delete a device group", name="delete")
@click.option(
    "--name", "-n", help="name of the device group to be deleted", default="bca"
)
def deleteDeviceGroup(name="bca"):
    deleteDeviceGroups(name)


def deleteDeviceGroups(name="bca"):
    device_group = name
    if isinstance(device_group, str):
        try:
            bcmp = Composer()
        except PathInvalid:
            return {
                "error": True,
                "response": "GUSTAVO_CONFIG_FILE: {} path not valid",
            }
        except FileUndefined:
            return {"error": True, "response": "GUSTAVO_CONFIG_FILE not defined"}
        except Exception as e:
            return {"error": True, "response": e}

        retval = bcmp.handleAsset("device_group", device_group, "delete")

        if retval["error"] == "False":
            click.echo(click.style("Deleted " + str(device_group), fg="green"))

        return retval
    else:

        return {
            "error": True,
            "response": "DEVICE_GROUP_INVALID: enter a valid device_group name",
        }

@worker.command(help="create a worker", name="up")
@click.option("--name", "-n", help="name of the worker container", default="worker")
@click.option(
    "--device_group",
    "-d",
    help="name of the device group that the worker belongs to",
    default="bca",
)
@click.option(
    "--image",
    "-i",
    help="name of the docker image to be used for worker",
    default="homert2admin/worker:latest",
)
@click.option(
    "--prefix", "-p", help="prefix for reporting logs", default="nebula-reports"
)
@click.option(
    "--expire-time",
    "-e",
    help="expiration time for keeping logs in redis cache",
    default="10",
)
def workerUp(name, device_group, image, prefix, expire_time):
    createWorker(name, device_group, image, prefix, expire_time)


@worker.command(help="remove a worker", name="remove")
@click.option("--name", "-n", help="name of the worker container", default="worker_bca")
def workerDn(name):
    removeWorker(name)


@worker.command(help="recreate a worker", name="recreate")
@click.option("--name", "-n", help="name of the worker container", default="worker_bca")
@click.option(
    "--device_group",
    "-d",
    help="name of the device group that the worker belongs to",
    default="bca",
)
@click.option(
    "--image",
    "-i",
    help="name of the docker image to be used for worker",
    default="homert2admin/worker:latest",
)
@click.option(
    "--prefix", "-p", help="prefix for reporting logs", default="nebula-reports"
)
@click.option(
    "--expire-time",
    "-e",
    help="expiration time for keeping logs in redis cache",
    default="10",
)
def recreateWorker(name, device_group, image, prefix, expire_time):
    removeWorker(name)
    createWorker(name, device_group, image, prefix, expire_time)


@manager.command(help="check manager services", name="check")
def checkManager():
    man = Manager()
    man.checkManager()


@manager.command(help="bring up manager services", name="up")
@click.option(
    "--service",
    "-s",
    help="comma separated list of service names to bring up",
    default="all",
)
def createManagerServices(service):
    man = Manager()
    service_list = service.split(",")
    for service in service_list:
        man.run(service)


@manager.command(help="stop manager services", name="stop")
@click.option(
    "--service",
    "-s",
    help="comma separated list of service names to stop",
    default="all",
)
def stopManagerServices(service):
    handleManagerServices(service, "stop")


@manager.command(help="start manager services", name="start")
@click.option(
    "--service",
    "-s",
    help="comma separated list of service names to start",
    default="all",
)
def startManagerServices(service):
    handleManagerServices(service, "start")


@manager.command(help="kill manager services", name="kill")
@click.option(
    "--service",
    "-s",
    help="comma separated list of service names to kill",
    default="all",
)
def killManagerServices(service):
    handleManagerServices(service, "kill")


@manager.command(help="remove manager services", name="remove")
@click.option(
    "--service",
    "-s",
    help="comma separated list of service names to remove",
    default="all",
)
def removeManagerServices(service):
    handleManagerServices(service, "remove")


@manager.command(help="restart manager services", name="restart")
@click.option(
    "--service",
    "-s",
    help="comma separated list of service names to remove",
    default="all",
)
def restartManagerServices(service):
    handleManagerServices(service, "restart")


if __name__ == "__main__":
    gustavo()
