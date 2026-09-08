import sys, click, requests, json
from NebulaPythonSDK import Nebula
from .NebulaBase import NebulaBase
from gustavo.pages.config.Logging import setup_logging
setup_logging()
import logging
from urllib.parse import urlparse
from python_on_whales import docker as dockerow

class Composer(NebulaBase):
    """
    Creates, updates, and deletes user-deployed apps and device groups via the Nebula API.

    Inherits connection parameters from `NebulaBase`. Unlike `Manager`
    (which manages the platform's own services), `Composer` talks to
    the Nebula manager's REST API through `nebulaObj` (a
    `NebulaPythonSDK.Nebula` client) to manage what device groups run
    which apps.

    Notes
    -----
    Several methods here still call `sys.exit()` (see
    `checkLocalRepoImages`) or return an ``{"error": True, ...}`` dict
    rather than raising on every failure path - a REST-friendlier
    version would raise a real exception for every failure path, not
    just some, so callers never need to check both a return value and
    for an exception.
    """

    def __init__(self,mode = "CLI",params = None):
        """
        Populate connection attributes via `NebulaBase.__init__`, then construct `nebulaObj`.

        Parameters
        ----------
        mode : str, optional
            Passed through to `NebulaBase.__init__`. `"CLI"` (default)
            loads params from `GUSTAVO_CONFIG_FILE`; any other value
            reads from `params` instead.
        params : dict or None, optional
            Passed through to `NebulaBase.__init__` as `session_state`.

        Notes
        -----
        `NEBULA_PROTOCOL` defaults to `"http"` if it wasn't set by
        `NebulaBase.__init__`.
        """
        NebulaBase.__init__(self, mode = mode,session_state=params)
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
        Query the registry's `/v2` catalog/tag-list API for an image (and optionally a specific tag).

        Parameters
        ----------
        name : str
            Repository name to look up, or `"all"` to list the whole
            registry catalog instead.
        tag : str
            A specific tag to check for, or `"all"` to return every
            tag for `name`. Ignored when `name == "all"`.

        Returns
        -------
        dict
            ``{"error": bool, "response": ...}``. When `name == "all"`,
            `response` is the raw catalog JSON (`{"repositories": [...]}`)
            on success or `{"status": <code>}` on a non-200 response.
            Otherwise, `response` is the raw tag-list JSON when
            `tag == "all"`, a message string confirming `name:tag`
            exists, or a message string explaining why it doesn't
            (image not found, tag not found, unknown registry error).

        Raises
        ------
        SystemExit
            If `name != "all"` and the request to the registry itself
            fails (connection error, timeout, etc.) - not caught like
            the other failure paths here, which return an error dict
            instead.
        requests.exceptions.RequestException
            If `name == "all"` and the request fails - that branch
            doesn't wrap the call in a try/except at all, unlike the
            `name != "all"` branch.
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
            if response.status_code ==200:
                response_dict = json.loads(response.text)
                # print(response_dict)
                return {"error": False, "response": response_dict}
            else:
                return {"error": True, "response": {"status":response.status_code}}
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
            if response.status_code != 200:
                return {"error": True, "response": {"status": response.status_code}}
            response_dict = json.loads(response.text)

            if "errors" in response_dict.keys():
                error_msg = response_dict["errors"][0]
                if "code" in error_msg.keys() and error_msg["code"] == "NAME_UNKNOWN":
                    logging.error(f"{name} has not been in the local repository, add this to the syncer mapping list to pull from remote")
                    return {"error": True, "response": "{} has not been found in the local repository, add this to the syncer mapping list to pull from remote".format(
                                name
                            )}
                else:
                    logging.error(f"{error_msg}")
                # sys.exit()
                return {
                    "error": True,
                    "response": "{} has not been found in the local repository, add this to the syncer mapping list to pull from remote".format(
                        name
                    ),
                }
            elif "name" in response_dict.keys():
                # print(response_dict)
                if tag == "all":
                    # sys.exit()
                    return {"error": False, "response": response_dict}
                elif tag not in response_dict["tags"]:
                    logging.error(f"tag: {tag} not found among tag list {response_dict['tags']}")
                    # sys.exit()
                    return {
                        "error": True,
                        "response": "tag: "
                        + str(tag)
                        + " not found among tag list "
                        + str(response_dict["tags"]),
                    }
                else:
                    logging.info(f"{name}:{tag} have been found in local registry")
                    return {
                        "error": False,
                        "response": "{}:{} have been found in local registry".format(
                            name, tag
                        ),
                    }
            else:
                logging.error(f"Unknown error has occured")
                logging.error(f"{response_dict['errors'][0]}")
                # sys.exit()
                return {
                    "error": True,
                    "response": "unknown error has occured"
                    + str(response_dict["errors"][0]),
                }

    def checkImageExists(self, name):
        """
        Check whether a fully-qualified `registry:port/repo[:tag]` image reference exists in the local registry.

        Parameters
        ----------
        name : str
            Image reference including the `REGISTRY_IP:REGISTRY_PORT/`
            prefix, e.g. `"10.0.0.70:5000/myapp:latest"`. Defaults the
            tag to `"latest"` if none is given.

        Notes
        -----
        Delegates to `checkLocalRepoImages` but discards its return
        value - this method's result is only visible via the logging
        that happens inside `checkLocalRepoImages`.
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
        """
        Translate a raw Nebula API `reply` into a logged message and a `{"error", "response"}` dict.

        Parameters
        ----------
        reply : dict
            The raw Nebula SDK response, expected to have
            `"status_code"` and (on a 403) a `"reply"` dict.
        accept_code : int
            The HTTP status code that counts as success for this call
            (200 for create/delete, 202 for update - see `handleAsset`).
        moding : str
            The verb stem used in log/response messages, e.g.
            `"creat"`, `"updat"`, `"delet"` (a trailing `"e"` or
            `"ing"` is appended by the caller's phrasing).
        asset_type : str
            `"app"` or `"device_group"` - used only for message text.
        asset_name : str
            The asset's name - used only for message text.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `False` only if `reply["status_code"] == accept_code`;
            `True` for a 400 (bad params), a 403 (asset already
            exists / doesn't exist, or another 403 the SDK's `reply`
            doesn't explain), or any other status code.
        """
        # print(reply)
        # returnval = False
        if reply["status_code"] == accept_code:
            logging.info(f"{moding} ed nebula {asset_type} : {asset_name}")
            # returnval = True
            return {
                "error": False,
                "response": moding + "ed nebula " + asset_type + " : " + asset_name,
            }
        elif reply["status_code"] == 400:
            logging.error(f"error {moding}ing {asset_type} : {asset_name}, missing or incorrect parameters")
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
                    logging.error(f"error {moding}ing {asset_type} : {asset_type} already exists")
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
                    logging.error(f"error {moding}ing {asset_name} : {asset_type} dose not exist")
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
                logging.critical(f"error {moding}ing {asset_type} : {asset_type}, server replied with : {reply['reply']}")
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
            logging.error(f"Error {moding}ing {asset_type}: {asset_name}. Are you logged in? Did you send the correct parameters and app name?")
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
        Ask the Nebula manager to prune unused images on every device running `app`.

        Parameters
        ----------
        app : str
            Name of the app whose devices should have their images
            pruned.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``. `error` is
            `False` only if the Nebula API accepted the prune request
            (HTTP 202); `True` otherwise.
        """
        reply = self.nebulaObj.prune__device_group_images(app)
        if reply["status_code"] == 202:
            logging.warning(f"Pruning images on devices running app: {app}")
            return {
                "error": False,
                "response": "pruning images on devices running app: " + app,
            }
        else:
            logging.error(f"error pruning in? did you send the right app name?")
            return {
                "error": True,
                "response": "error pruning images on devices running app: " + app,
            }

    # ("device_group","bca","create",device_group_config)
    def handleAsset(self, asset_type, asset_name, mode, config=None):

        """
        Create, update, or delete an app or device group via the Nebula API.

        Parameters
        ----------
        asset_type : str
            `"app"` or `"device_group"`.
        asset_name : str
            The asset's name.
        mode : str
            `"create"`, `"update"`, or `"delete"` (case-insensitive).
        config : dict or None, optional
            The asset's configuration. Required for `"create"`/
            `"update"`; ignored for `"delete"`. For `asset_type="app"`,
            must contain `"docker_image"` - it's checked against the
            local registry (`checkImageExists`) before the Nebula
            call is made.

        Returns
        -------
        dict
            ``{"error": bool, "response": <message str>}``, produced
            by `printDiagnosticResponse` from the Nebula API's reply -
            or an earlier error dict if `config` is missing when
            required, `asset_type` is unrecognized, or `mode` is
            unrecognized.
        """

        # retval = False
        if config == None and (mode.lower() == "create" or mode.lower() == "update"):
            logging.error(f"Invalid config for {asset_type} : {asset_name}")
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
                logging.critical(f"Unknown asset type: {asset_type}")
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
                logging.critical(f"Unknown asset type: {asset_type}")
                return {"error": True, "response": "unknown asset type " + asset_type}
            moding = "updat"

        elif mode.lower() == "delete":
            accept_code = 200
            if asset_type == "app":
                reply = self.nebulaObj.delete_app(asset_name)

            elif asset_type == "device_group":
                reply = self.nebulaObj.delete_device_group(asset_name)

            else:
                logging.error(f"Unknown asset type: {asset_type}")
                return {"error": True, "response": "unknown asset type " + asset_type}
            moding = "delet"
        else:
            logging.error(f"unknown command {mode}")
            return {"error": True, "response": "unknown command " + mode}

        retval = self.printDiagnosticResponse(
            reply, accept_code, moding, asset_type, asset_name
        )

        return retval

    def handleDeviceGroup(self, app_list, mode, device_group="bca"):
        """
        Add or remove apps from a device group's app list.

        Fetches the device group's current app list, computes the new
        list by adding (`mode="update"`) or removing (`mode="delete"`)
        the apps named in `app_list`, then calls `handleAsset` to push
        the updated list.

        Parameters
        ----------
        app_list : str
            Comma-separated app names to add or remove.
        mode : str
            `"update"` to add the named apps (skipping ones already
            present), or `"delete"` to remove them.
        device_group : str, optional
            The device group to modify. Defaults to `"bca"`.

        Returns
        -------
        dict
            ``{"error": bool, "response": ...}``. On success,
            `response` is the device group's resulting app list
            (`list`). On failure, `response` is a message string -
            from `mode` being unrecognized, `handleAsset` failing to
            push the update, or the initial list-fetch failing.
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
                logging.critical(f"Unsupported mode: {mode}")
                return {"error": True, "response": "unsupported mode"}
            for app in new_app_list:
                if mode == "update" and app not in existing_app_list:
                    apps_to_be_modified = apps_to_be_modified + [app]
                if mode == "delete" and app in existing_app_list:
                    apps_to_be_modified.remove(app)

            device_group_config = dict({"apps": apps_to_be_modified})
            logging.info(f"Device Group Config: {device_group_config}")
            responseDG = self.handleAsset(
                "device_group", device_group, "update", device_group_config
            )

            if responseDG["error"]:
                return responseDG

            response = self.nebulaObj.list_device_group(device_group)

            self.printDiagnosticResponse(
                response, 200, "check", "app list for", device_group
            )
            logging.info(f"Apps: {response['reply']['apps']}")

            return {"error": False, "response": response["reply"]["apps"]}
        else:
            return success