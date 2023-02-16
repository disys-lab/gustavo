import sys, click, requests, json
from NebulaPythonSDK import Nebula
from .NebulaBase import NebulaBase
from urllib.parse import urlparse
from python_on_whales import docker as dockerow


class Composer(NebulaBase):
    """
    Creates a class Composer with NebulaBase as the base class.

    TODO: Make methods in this class REST API-friendly, which means that instead of a sys.exit(), it needs to either
          throw an appropriate exception or return a status value or both.
          Good way to do it would be to throw an exception here and then catch it on gustavo.py

    """

    def __init__(self):
        NebulaBase.__init__(self)

        if self.NEBULA_PROTOCOL:
            self.nebulaObj = Nebula(
                username=self.NEBULA_USERNAME,
                host=self.MANAGER_IP,
                port=self.MANAGER_PORT,
                token=self.NEBULA_AUTH_TOKEN,
                password=self.NEBULA_PASSWORD,
                protocol=self.NEBULA_PROTOCOL,
            )
        else:
            self.NEBULA_PROTOCOL = "http"
            self.nebulaObj = Nebula(
                username=self.NEBULA_USERNAME,
                host=self.MANAGER_IP,
                port=self.MANAGER_PORT,
                token=self.NEBULA_AUTH_TOKEN,
                password=self.NEBULA_PASSWORD,
            )

    def checkLocalRepoImages(self, name, tag):
        """
        Checks the existence of local images

        Parameters
        ----------

        name: string
            Name of the image

        tag: string
            The tag of the image

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the images were not found
        If the key "error" is False it means that the images were not found


        """
        if name == "all":
            url = urlparse(
                self.NEBULA_PROTOCOL
                + "://"
                + str(self.REGISTRY_IP)
                + ":"
                + str(self.REGISTRY_PORT)
                + "/v2/_catalog"
            )
            response = requests.get(url.geturl(), auth=None, verify=False)
            response_dict = json.loads(response.text)
            print(response_dict)
            return {"error": False, "response": response_dict}
        else:
            url = urlparse(
                self.NEBULA_PROTOCOL
                + "://"
                + str(self.REGISTRY_IP)
                + ":"
                + str(self.REGISTRY_PORT)
                + "/v2/"
                + str(name)
                + "/tags/list"
            )
            try:
                response = requests.get(url.geturl(), auth=None, verify=False)
            except requests.exceptions.RequestException as e:  # This is the correct syntax
                raise SystemExit(e)
            response_dict = json.loads(response.text)
            if "errors" in response_dict.keys():
                error_msg = response_dict["errors"][0]
                if "code" in error_msg.keys() and error_msg["code"] == "NAME_UNKNOWN":
                    click.echo(
                        click.style(
                            "{} has not been found in the local repository, add this to the syncer mapping list to pull from remote".format(
                                name
                            ),
                            fg="red",
                        )
                    )
                else:
                    click.echo(click.style(str(error_msg), fg="red"))
                # sys.exit()
                return {
                    "error": True,
                    "response": "{} has not been found in the local repository, add this to the syncer mapping list to pull from remote".format(
                        name
                    ),
                }
            elif "name" in response_dict.keys():
                print(response_dict)
                if tag == "all":
                    # sys.exit()
                    return {"error": True, "response": "tag cannot be all"}
                elif tag not in response_dict["tags"]:
                    click.echo(
                        click.style(
                            "tag: "
                            + str(tag)
                            + " not found among tag list "
                            + str(response_dict["tags"]),
                            fg="red",
                        )
                    )
                    # sys.exit()
                    return {
                        "error": True,
                        "response": "tag: "
                        + str(tag)
                        + " not found among tag list "
                        + str(response_dict["tags"]),
                    }
                else:
                    click.echo(
                        click.style(
                            "{}:{} have been found in local registry".format(name, tag),
                            fg="green",
                        )
                    )
                    return {
                        "error": False,
                        "response": "{}:{} have been found in local registry".format(
                            name, tag
                        ),
                    }
            else:
                click.echo(click.style("Unknown error has occured", fg="red"))
                click.echo(click.style(str(response_dict["errors"][0]), fg="red"))
                # sys.exit()
                return {
                    "error": True,
                    "response": "unknown error has occured"
                    + str(response_dict["errors"][0]),
                }

    def checkImageExists(self, name):
        """
        Check if image exists

        Parameters
        ----------

        name: string
            Name of the image to be checked
        """
        repository_name = name.split(
            str(self.REGISTRY_IP) + ":" + str(self.REGISTRY_PORT) + "/"
        )[1]
        if len(repository_name.split(":")) == 1:
            tag = "latest"
        else:
            tag = repository_name.split(":")[1]
        # http://10.0.0.70:5000/v2/ubuntu/tags/list
        self.checkLocalRepoImages(repository_name, tag)

    def printDiagnosticResponse(
        self, reply, accept_code, moding, asset_type, asset_name
    ):
        # Returns
        # -------
        # dictionary: {"error": True / False, "response": "Gives appropriate message depending on the kind of failure or a
        #              success message if everything is running"}
        #               If the key "error" is True it means that there is some error which is printed in printDiagnosticResponse
        #              If the key "error" is False it means that there is some error which is printed in printDiagnosticResponse
        # print(reply)
        # returnval = False
        if reply["status_code"] == accept_code:
            click.echo(
                click.style(
                    moding + "ed nebula " + asset_type + " : " + asset_name, fg="green"
                )
            )
            # returnval = True
            return {
                "error": False,
                "response": moding + "ed nebula " + asset_type + " : " + asset_name,
            }
        elif reply["status_code"] == 400:
            click.echo(
                click.style(
                    "error "
                    + moding
                    + "ing "
                    + asset_type
                    + " : "
                    + asset_name
                    + ", missing or incorrect parameters",
                    fg="red",
                )
            )
            return {
                "error": True,
                "response": "error "
                + moding
                + "ing "
                + asset_type
                + " : "
                + asset_name
                + ", missing or incorrect parameters",
            }
        elif reply["status_code"] == 403:
            if asset_type + "_exists" in reply["reply"].keys():
                if reply["reply"][asset_type + "_exists"]:
                    click.echo(
                        click.style(
                            "error "
                            + moding
                            + "ing "
                            + asset_type
                            + " : "
                            + asset_name
                            + ", "
                            + str(asset_type)
                            + " already exists",
                            fg="red",
                        )
                    )
                    return {
                        "error": True,
                        "response": "error "
                        + moding
                        + "ing "
                        + asset_type
                        + " : "
                        + asset_name
                        + ", "
                        + str(asset_type)
                        + " already exists",
                    }
                else:
                    click.echo(
                        click.style(
                            "error "
                            + moding
                            + "ing "
                            + asset_type
                            + " : "
                            + asset_name
                            + ", "
                            + str(asset_type)
                            + " does not exist",
                            fg="red",
                        )
                    )
                    return {
                        "error": True,
                        "response": "error "
                        + moding
                        + "ing "
                        + asset_type
                        + " : "
                        + asset_name
                        + ", "
                        + str(asset_type)
                        + " does not exist",
                    }
            else:
                click.echo(
                    click.style(
                        "error "
                        + moding
                        + "ing "
                        + asset_type
                        + " : "
                        + asset_name
                        + ", server replied with :"
                        + str(reply["reply"]),
                        fg="red",
                    )
                )
                return {
                    "error": True,
                    "response": "error "
                    + moding
                    + "ing "
                    + asset_type
                    + " : "
                    + asset_name
                    + ", server replied with :"
                    + str(reply["reply"]),
                }
        else:
            click.echo(
                click.style(
                    "error "
                    + moding
                    + "ing "
                    + asset_type
                    + " : "
                    + asset_name
                    + ", are you logged in? did you send the right params & app name?",
                    fg="red",
                )
            )
            return {
                "error": True,
                "response": "error "
                + moding
                + "ing "
                + asset_type
                + " : "
                + asset_name
                + ", are you logged in? did you send the right params & app name?",
            }
        # return returnval

    def prune_device_group_images(self, app):
        """
        Prunes the images on device group

        Parameters
        ----------

        app: string
            Name of the app whose images are to be pruned

        """
        reply = self.nebulaObj.prune__device_group_images(app)
        if reply["status_code"] == 202:
            click.echo(
                click.style(
                    "pruning images on devices running app: " + app, fg="yellow"
                )
            )
            return {
                "error": False,
                "response": "pruning images on devices running app: " + app,
            }
        else:
            click.echo(
                click.style(
                    "error pruning images on devices running app:"
                    + app
                    + ", are you logged in? did you sent the right app name?",
                    fg="red",
                )
            )
            return {
                "error": True,
                "response": "error pruning images on devices running app: " + app,
            }

    # ("device_group","bca","create",device_group_config)
    def handleAsset(self, asset_type, asset_name, mode, config=None):

        """
        Handles a generic asset either an app or a device group and performs the functions of create, update or delete.

        Parameters
        ----------

        asset_type : string
            Type of asset, legal values could be either an "app" or "device_group"

        asset_name: string
            The name of the asset

        mode : string
            The mode of handling, allowed values are "create", "update" and "delete"

        config : dict
            The configuration of the asset to be created or updated. Not applicable in case of delete.

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the handle asset did not run successfully
        If the key "error" is False it means that the handle asset did not run successfully
        """

        # retval = False
        if config == None and (mode.lower() == "create" or mode.lower() == "update"):
            click.echo(
                click.style(
                    "config is invlaid for " + asset_type + " : " + asset_name,
                    fg="green",
                )
            )
            return {
                "error": True,
                "response": "config is invlaid for " + asset_type + " : " + asset_name,
            }

        if mode.lower() == "create":
            accept_code = 200
            if asset_type == "app":
                self.checkImageExists(config["docker_image"])
                reply = self.nebulaObj.create_app(asset_name, config)

            elif asset_type == "device_group":
                reply = self.nebulaObj.create_device_group(asset_name, config)

            else:
                click.echo(click.style("unknown asset type " + asset_type, fg="red"))
                return {"error": True, "response": "unknown asset type " + asset_type}
            moding = "creat"

        elif mode.lower() == "update":
            accept_code = 202
            if asset_type == "app":
                self.checkImageExists(config["docker_image"])
                reply = self.nebulaObj.update_app(asset_name, config)

            elif asset_type == "device_group":
                reply = self.nebulaObj.update_device_group(asset_name, config)

            else:
                click.echo(click.style("unknown asset type " + asset_type, fg="red"))
                return {"error": True, "response": "unknown asset type " + asset_type}
            moding = "updat"

        elif mode.lower() == "delete":
            accept_code = 200
            if asset_type == "app":
                reply = self.nebulaObj.delete_app(asset_name)

            elif asset_type == "device_group":
                reply = self.nebulaObj.delete_device_group(asset_name)

            else:
                click.echo(click.style("unknown asset type " + asset_type, fg="red"))
                return {"error": True, "response": "unknown asset type " + asset_type}
            moding = "delet"
        else:
            click.echo(click.style("unknown command " + mode, fg="red"))
            return {"error": True, "response": "unknown command " + mode}

        retval = self.printDiagnosticResponse(
            reply, accept_code, moding, asset_type, asset_name
        )

        return retval

    def handleDeviceGroup(self, app_list, mode, device_group="bca"):
        """
        Handles aspects of the device group such as deleting, updating of apps

        Parameters
        ----------

        app_list : string
            Comma separated list of strings to be updated or deleted from the device group

        mode: string
            The mode i.e. update or delete

        device_group : string
            The device group name to be handled

        Returns
        -------
        dictionary : {"error": True/False, "response": "Gives appropriate message depending on the kind of failure or a
                     success message if everything is running"}
        If the key "error" is True it means that there is some error and the handle device group did not run successfully
        If the key "error" is False it means that the handle device group did run successfully
        """
        response = self.nebulaObj.list_device_group(device_group)
        success = self.printDiagnosticResponse(
            response, 200, "check", "app list for", device_group
        )
        if not success["error"]:
            new_app_list = app_list.split(",")
            existing_app_list = response["reply"]["apps"]
            apps_to_be_modified = existing_app_list
            if mode != "update" and mode != "delete":
                click.echo(click.style("unsupported mode " + mode, fg="red"))
                return {"error": True, "response": "unsupported mode"}
            for app in new_app_list:
                if mode == "update" and app not in existing_app_list:
                    apps_to_be_modified = apps_to_be_modified + [app]
                if mode == "delete" and app in existing_app_list:
                    apps_to_be_modified.remove(app)

            device_group_config = dict({"apps": apps_to_be_modified})
            print(device_group_config)
            self.handleAsset(
                "device_group", device_group, "update", device_group_config
            )
            response = self.nebulaObj.list_device_group(device_group)

            self.printDiagnosticResponse(
                response, 200, "check", "app list for", device_group
            )
            click.echo(response["reply"]["apps"])

            return {"error": False, "response": response["reply"]["apps"]}
