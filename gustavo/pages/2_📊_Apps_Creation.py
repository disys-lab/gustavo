import yaml,time, sys,os,copy
import streamlit as st
import socket, logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
from gustavo.pages.config.Logging import setup_logging
setup_logging()
import logging
sidebarInit()
from gustavo.src.Composer import Composer
from gustavo.src.Manager import Manager
from gustavo.pages.config.SyncerConfig import refresh_registry, checkRegistryStatus
from gustavo.utils import *
from gustavo.pages.config.loadCss import load_css
load_css()

class AppHandler:
    """
    The `AppHandler` class is responsible for rendering and managing application lifecycle operations 
    within a Streamlit-based interface, leveraging Gustavo’s Composer, Manager, and registry services.

    Core Responsibilities:
    - List all apps and their configurations from Nebula
    - Render dynamic UI to create, update, or delete apps
    - Manage form-based app configurations (env vars, volumes, ports)
    - Sync app states with associated device groups
    - Handle YAML upload/download for app configurations
    - Display tooltip-based feedback for operations

    Session State:
    - Dynamically reads/writes app configs under session keys (e.g., `st.session_state["myapp"]`)
    - Maintains auxiliary keys like `app_list`, `fields_size`, `deletes`, `create`, etc.

    Dependencies:
    - Requires `Composer` and `Manager` objects for backend communication
    - Uses helper functions for transforming and validating YAML and UI data

    UI Components:
    - Main app handler UI (`apps()`)
    - Per-app expander UI (`appExpander()`)
    - Feedback containers (`error_container`, `log_placeholder`)
    """
    def __init__(self):
        """
    Initializes the `AppHandler` class and sets up session state for managing applications.

    Purpose:
    - Prepares app listing context (`app_list`)
    - Initializes default fields and field counters for the app management UI

    Logic:
    - If "app_list" is missing in session state, initializes it as an empty list
    - If "fields_size" is not present, sets it based on `app_list` length and 
      initializes fields and delete button tracking structures

    Returns:
        None
    """
        self.error_container = None
        self.log_placeholder = None
        if "app_list" in st.session_state:
            self.app_list = st.session_state.app_list
        else:
            self.app_list = []
            st.session_state.app_list = []

        if "fields_size" not in st.session_state:
            st.session_state.fields_size = len(self.app_list)
            st.session_state.fields = [app for app in self.app_list]
            st.session_state.deletes = []

    def handleTask(self, label, action_fn, result_container_key="action_result_placeholder"):
        """
    Wraps an operation with a spinner and shows mouse-based tooltip feedback in Streamlit.

    Purpose:
    - Enhance UX with progress spinners and tooltip status messages
    - Track result state via a unique session state key

    Args:
        label (str): Label shown inside the Streamlit spinner
        action_fn (Callable): A function representing the action to be performed (create/update/delete)
        result_container_key (str): Unique session key to store the result

    Logic:
    - Runs the action function inside a Streamlit spinner
    - Based on result:
        - Displays success/failure tooltip message
        - Saves response in session state for traceability

    Returns:
        dict: Result of the invoked action (with `error` and `response` keys)
    """
        if result_container_key not in st.session_state:
            st.session_state[result_container_key] = ""

        with st.spinner(label):
            result = action_fn()

        if result is None:
            message = "No response received ❌"
            color_class = "tooltip-text"
        elif result.get("error"):
            message = result.get("response", "Something went wrong ❌")
            color_class = "tooltip-text"
        else:
            message = result.get("response", "Success ✅")
            color_class = "tooltip-text"

        tooltip_html = f"""
        <div class="mouse-tooltip">
            <span class="{color_class}">{message}</span>
        </div>
        """
        st.markdown(tooltip_html, unsafe_allow_html=True)
        st.session_state[result_container_key] = result
        return result


    def createApp(self,app_name,device_groups):
        """
    Creates a new application with configuration based on form inputs and device group bindings.

    Purpose:
    - Aggregate form values (env vars, ports, volumes) into a valid config
    - Assign default device group if none is selected
    - Submit creation request to Composer

    Args:
        app_name (str): Name of the application to be created
        device_groups (list): List of device groups to associate with the app

    Logic:
    - If no device group is selected, default to `gustavodg1`
    - Use `getEnvVars`, `getVolumes`, and `getPorts` to process inputs
    - Compose final config with `APP_ID` set
    - Call `handleCreateApp()` to initiate creation

    Returns:
        dict: Response object containing `error` and `response` keys
    """
        if len(device_groups)==0:
            dg_str = "gustavodg1"
        else:
            dg_str = ",".join(device_groups)

        bcmp = Composer(mode="streamlit", params=st.session_state)

        st.session_state[app_name]["config"]["env_vars"] = self.getEnvVars(st.session_state[app_name]["form_values"]["env_vars"])
        st.session_state[app_name]["config"]["volumes"] = self.getVolumes(st.session_state[app_name]["form_values"]["volumes"])
        st.session_state[app_name]["config"]["starting_ports"] = self.getPorts(st.session_state[app_name]["form_values"]["ports"])
        st.session_state[app_name]["config"]["env_vars"]["APP_ID"] = app_name

        app_config = {app_name: st.session_state[app_name]["config"]}

        response = handleCreateApp(bcmp, app_name, app_config, dg_str)

        return response

    def updateApp(self,app_name):
        """
        Updates an existing app by re-submitting its configuration to the backend.

        Purpose:
        - Convert edited form inputs into backend-compatible format
        - Submit update via Composer

        Args:
            app_name (str): Name of the application to update

        Logic:
        - Transform UI data (env vars, volumes, ports) to backend format
        - Set the `APP_ID` in the env vars
        - Submit updated configuration via `Composer.handleAsset(...)`

        Returns:
            dict: Backend response object with status info
        """
        # print(st.session_state.edited_env_vars)
        # st.session_state[app_name]["config"]["env_vars"] = self.getEnvVars(st.session_state.edited_env_vars)
        # print(st.session_state[app_name]["config"]["env_vars"])
        bcmp = Composer(mode="streamlit", params=st.session_state)

        st.session_state[app_name]["config"]["env_vars"] = self.getEnvVars(st.session_state[app_name]["form_values"]["env_vars"])
        st.session_state[app_name]["config"]["volumes"] = self.getVolumes(st.session_state[app_name]["form_values"]["volumes"])
        st.session_state[app_name]["config"]["starting_ports"] = self.getPorts(st.session_state[app_name]["form_values"]["ports"])

        app_config = st.session_state[app_name]["config"]
        st.session_state[app_name]["config"]["env_vars"]["APP_ID"] = app_name
        response = bcmp.handleAsset("app", app_name, "update", app_config)

        return response

    def deleteApp(self,app_name):
        """
        Deletes an application from both the backend and all associated device groups.

        Purpose:
        - Ensure app is removed from every device group before full deletion
        - Clean up app references from UI state

        Args:
            app_name (str): Name of the application to delete

        Logic:
        - Use Composer to list all device groups
        - For each group, remove the app and submit an updated config
        - After cleanup, delete the app using `handleAsset("app", ..., "delete")`

        Returns:
            dict: Result of the deletion (success/failure)
        """
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
            response = bcmp.nebulaObj.list_device_groups()
        except Exception as e:
            return {"error": True, "response": f"error occured listing device_groups, please check Nebula object"}

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

    def listAllDeviceGroups(self):
        """
        Retrieves all existing device groups from the backend using the Manager and Composer services.

        Purpose:
        - Validate backend Manager connection
        - Fetch a list of all registered device groups via Nebula

        Logic:
        - Calls `Manager.checkManager()` to verify backend health
        - Instantiates a `Composer` object and calls `nebulaObj.list_device_groups()`
        - Returns the list of group names and the Composer instance

        Returns:
            dict: 
                {
                    "error": bool, 
                    "response": {
                        "device_group_list": list of device group names,
                        "bcmp": Composer instance
                    } or str (error message)
                }
        """
        manager_reply = Manager(mode="streamlit",params=st.session_state).checkManager()

        if manager_reply.get("error", True):
            reply = manager_reply.get("response", "manager not accessible")
            return {"error": True, "response": f"error occured listing device groups, please check manager connection"}

        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
            response = bcmp.nebulaObj.list_device_groups()
        except Exception as e:
            return {"error": True, "response": f"error occured listing device groups, please check Nebula object"}

        #device_group_list = []
        #bcmp = None
        if response["status_code"] == 200:
            device_group_list = response["reply"]["device_groups"]
            return {"error": False, "response": {"device_group_list":device_group_list,"bcmp":bcmp}}
        else:
            return {"error": True, "response": f"error occured listing device groups, Nebula object creation failed"}
        #return device_group_list,bcmp

    def listDeviceGroups(self,app_name):
        """
        Lists all device groups associated with a given app.

        Purpose:
        - Determine which device groups currently contain the specified app

        Args:
            app_name (str): Application name to search for within device groups

        Logic:
        - Fetch all device groups using `listAllDeviceGroups()`
        - For each group, call `nebulaObj.list_device_group()` to get its app list
        - If the app appears in a group, add that group to the results

        Returns:
            dict: {
                "error": bool,
                "response": list of device group names containing the app or an error message
            }
        """
        dg_list = []

        #device_group_list,bcmp = self.listAllDeviceGroups()
        listdg_reply = self.listAllDeviceGroups()
        listdg_fail = listdg_reply.get("error",True)
        listdg_response = listdg_reply.get("response", {})
        if listdg_fail:
            return {"error": True, "response": f"error occured while listing device_group {listdg_response}"}

        device_group_list = listdg_response.get("device_group_list",[])
        bcmp = listdg_response.get("bcmp",None)

        for device_group in device_group_list:
            try:
                response = bcmp.nebulaObj.list_device_group(device_group)
            except Exception as e:
                return {"error": True, "response": f"error occured while listing device_group {device_group}, exception {e}"}

            if response["status_code"] == 200:
                dg_app_list = response["reply"]["apps"]
                if app_name in dg_app_list:
                    dg_list.append(device_group)

        return {"error":False,"response":dg_list}

    def listAllApps(self):
        """
        Retrieves all existing apps and their configurations from the backend, and updates session state.

        Purpose:
        - Load complete app metadata for all apps managed by Nebula
        - Build Streamlit-compatible form values for each app
        - Store configuration under individual `st.session_state[app_name]`

        Logic:
        - Calls `Manager.checkManager()` to confirm backend health
        - Uses `Composer.nebulaObj.list_apps()` to get list of app names
        - For each app:
            - Fetches config using `list_app_info`
            - Calls `listDeviceGroups(app_name)` to find group bindings
            - Constructs config and form values for rendering in Streamlit UI

        Updates:
            - `st.session_state.app_list`: list of all app names
            - `st.session_state[app_name]`: stores both form-friendly and backend-ready config for each app

        Returns:
            dict: {
                "error": bool,
                "response": list of app names or error message
            }
        """
        manager_reply = Manager(mode="streamlit",params=st.session_state).checkManager()

        if manager_reply.get("error",True):
            reply = manager_reply.get("response","manager not accessible")
            logging.error(reply)
            return {"error": True, "response": f"error occured listing apps, please check manager connection"}

        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
            response = bcmp.nebulaObj.list_apps()
        except Exception as e:
            return {"error": True, "response": f"error occured listing apps, please check MongoDB connection"}

        if response["status_code"] == 200:
            existing_app_list = response["reply"]["apps"]
            self.app_list = existing_app_list
            st.session_state.app_list = self.app_list
            for app_name in existing_app_list:

                try:
                    app_response = bcmp.nebulaObj.list_app_info(app_name)
                except Exception as e:
                    return {"error": True, "response": f"error occured while listing app {app_name}"}

                if app_response["status_code"] == 200:
                    listdg_reply = self.listDeviceGroups(app_name)
                    listdg_fail = listdg_reply.get("error",True)
                    if listdg_fail:
                        logging.error(f"failed to list device groups, error {listdg_reply}")
                        continue
                    else:
                        dg_list = listdg_reply.get("response")

                    if app_name not in st.session_state:
                        st.session_state[app_name] = {}
                    st.session_state[app_name]["app_name"] = app_name
                    st.session_state[app_name]["config"] = {
                                        "docker_image": app_response["reply"]["docker_image"],
                                        "env_vars": app_response["reply"]["env_vars"],
                                        "networks": app_response["reply"]["networks"],
                                        "volumes": app_response["reply"]["volumes"],
                                        "starting_ports": app_response["reply"]["starting_ports"],
                                        "running": app_response["reply"]["running"],
                                        "rolling_restart": app_response["reply"]["rolling_restart"],
                                        "containers_per": app_response["reply"]["containers_per"],
                                        "privileged": app_response["reply"]["privileged"],
                                        "device_groups": dg_list,
                                        "devices": app_response["reply"]["devices"]
                                        }
                    docker_image = app_response["reply"]["docker_image"]
                    image = docker_image.split("/")[-1]

                    st.session_state[app_name]["form_values"] = {
                        "image": image,
                        "env_vars": self.setEnvVars(app_response["reply"]["env_vars"]),
                        "networks": ",".join(app_response["reply"]["networks"]),
                        "volumes": self.setVolumes(app_response["reply"]["volumes"]),
                        "ports": self.setVolumes(app_response["reply"]["starting_ports"]),
                        "running": True,
                        "rolling_restart": True,
                        "containers_per": {"server": 1},
                        "privileged": False,
                        "device_groups": dg_list
                    }

            return {"error": False, "response": self.app_list}
        else:
            return {"error":True, "response": response}

    def process_uploaded_file(self,uploaded_file):
        """
        Loads an uploaded YAML file and parses it into the internal app configuration format.

        Purpose:
        - Allow users to import an app config via drag-and-drop or file upload
        - Populate session state under `"create"` key for further editing or submission

        Args:
            uploaded_file (BytesIO): A YAML file object uploaded by the user

        Logic:
        - Parses YAML using PyYAML
        - Extracts the first app name and config block
        - Stores config and transformed form values in `st.session_state["create"]`

        Returns:
            dict: Parsed app configuration
        """
        app_config = yaml.load(uploaded_file,Loader=yaml.Loader)
        appkeys = list(app_config.keys())
        app_name = appkeys[0]
        st.session_state["create"]["app_name"] = app_name

        st.session_state["create"]["form_values"] = {
                                                        "image": app_config[app_name]["docker_image"],
                                                        "env_vars": self.setEnvVars(app_config[app_name]),
                                                        "networks": "nebula",
                                                        "volumes": self.setVolumes(app_config[app_name]),
                                                        "ports": self.setPorts(app_config[app_name]),
                                                        "running": True,
                                                        "rolling_restart": True,
                                                        "containers_per": {"server": 1},
                                                        "privileged": False
                                                    }

        st.session_state["create"]["config"] = app_config[app_name]

        #st.session_state[appkeys[0]] = app_config
        # print(st.session_state["create"]["form_values"])
        logging.info(f"{st.session_state['create']['form_values']}")
        return app_config

    def setPorts(self,app_config):
        """
        Transforms raw port dictionary list into editable dicts for Streamlit data editor.

        Purpose:
        - Prepare port configuration (from backend format) for display/edit in UI

        Args:
            app_config (dict): App configuration containing `starting_ports`

        Logic:
        - If `starting_ports` is empty or not present, return a blank row
        - Each port mapping `{from: to}` is converted to a dict with `from` and `to` keys

        Returns:
            list[dict]: List of editable port rows (e.g., [{"from": "8000", "to": "80"}])
        """
        if "starting_ports" not in app_config:
            return [{"from":"","to":""}]
        ports_dict_list = []
        ports_list = app_config["starting_ports"]
        if len(ports_list) == 0:
            ports_dict_list = [{"from":"","to":""}]
        else:
            try:
                for p in ports_list:
                    fromp = list(p.keys())[0]
                    top = p[fromp]
                    ports_dict_list.append({"from":fromp, "to":top})
            except Exception as e:
                st.exception("Exception occured while configuring ports {}".format(str(e)))
                ports_dict_list = [{"from":"","to":""}]

        return ports_dict_list

    def getPorts(self,edited_ports):
        """
        Converts edited port input from UI into backend-compatible format.

        Purpose:
        - Clean and validate port input data for submission

        Args:
            edited_ports (list[dict]): UI-formatted list of port maps (with 'from' and 'to' keys)

        Logic:
        - Filters out incomplete/invalid entries
        - Converts to format: [{from_port: to_port}]

        Returns:
            list[dict]: List of validated port mappings for backend
        """
        port_list = []
        for p in edited_ports:
            if p["from"] is not None and p["to"] is not None:
                if p["from"] != "" and p["to"] != "":
                    port_list.append({int(p["from"]):int(p["to"])})
        return port_list

    def setVolumes(self,app_config):
        """
        Converts the 'volumes' list from backend format into editable dict format for the UI.

        Purpose:
        - Prepare volume mount paths for user editing in Streamlit's data editor

        Args:
            app_config (dict): Configuration containing a `volumes` key (list of "src:dest" strings)

        Logic:
        - If no volumes are present, returns a default empty row
        - Splits each string like "/host:/container" into a dict with "from" and "to"

        Returns:
            list[dict]: Volume entries formatted as [{"from": "/host", "to": "/container"}, ...]
        """
        if "volumes" not in app_config:
            return [{"from":"","to":""}]
        volume_dict_list = []
        volume_list = app_config["volumes"]
        try:
            for v in volume_list:
                v_split = v.split(":",1)
                volume_dict_list.append({"from":v_split[0],"to":v_split[1]})
        except Exception as e:
            st.exception("Exception occured while configuring volumes {}".format(str(e)))
        if len(volume_dict_list) == 0:
            volume_dict_list = [{"from":"","to":""}]
        return volume_dict_list

    def getVolumes(self,edited_volumes):
        """
        Converts edited volume mappings from UI back into backend format.

        Purpose:
        - Transform user-edited volume data into "host:container" strings

        Args:
            edited_volumes (list[dict]): List of dicts with keys "from" and "to"

        Logic:
        - Filters out incomplete/empty mappings
        - Joins valid entries as strings: "from:to"

        Returns:
            list[str]: List of volume mount strings (e.g., ["/data:/mnt/data"])
        """
        volume_list = [] #[v["from"] + ":" + v["to"] for v in edited_volumes]
        for v in edited_volumes:
            if v["from"] is not None and v["to"] is not None:
                if v["from"] != "" and v["to"] != "":
                    volume_list.append(v["from"] + ":" + v["to"])
        return volume_list

    def getEnvVars(self,edited_env_vars):
        """
        Transforms a dictionary of environment variables into an editable list for Streamlit.

        Purpose:
        - Convert a dict like {"KEY": "VALUE"} into a list of {"key": ..., "value": ...} for UI

        Args:
            app_config (dict): Configuration containing `env_vars` key

        Logic:
        - Iterates over the dict and creates a list of dicts
        - Provides a blank row if no env vars exist

        Returns:
            list[dict]: [{"key": "ENV_KEY", "value": "ENV_VALUE"}, ...]
        """
        env_var_dict = {}
        for ev in edited_env_vars:
            if ev["key"] is not None:
                if ev["key"] !="":
                    env_var_dict[ev["key"]] = ev["value"]
        return env_var_dict

    def setEnvVars(self,app_config):
        """
        Converts edited environment variables from UI format back to a dictionary.

        Purpose:
        - Clean and filter env var inputs from the UI before submission

        Args:
            edited_env_vars (list[dict]): List of dicts with "key" and "value" entries

        Logic:
        - Filters out entries with empty keys
        - Returns a dictionary of {key: value}

        Returns:
            dict: Final environment variable dictionary
        """
        if "env_vars" not in app_config:
            return [{"key":"","value":""}]
        env_var_dict = app_config["env_vars"]
        # print(env_var_dict)
        edited_env_vars = [] #[{"key": "", "value": ""}]
        for key in env_var_dict:
            edited_env_vars.append({"key":key,"value":env_var_dict[key]})
        if len(edited_env_vars) == 0:
            edited_env_vars = [{"key":"","value":""}]
        return edited_env_vars

    def getLatestEnvVars(self):
        """
        Collects the latest environment values from session state, used to auto-fill new app creation forms.

        Purpose:
        - Construct default `env_vars` based on infrastructure variables (e.g., Redis, Manager, Auth)

        Logic:
        - Reads known session keys (`REDIS_HOST`, `MANAGER_PORT`, etc.)
        - Fills in default env vars including constants like `SLEEP_SECS` and a hardcoded public key

        Returns:
            dict: {
                "env_vars": {
                    "REDIS_DB_HOST": "...",
                    "NEBULA_AUTH_TOKEN": "...",
                    "REDIS_DB_PWD": "...",
                    "MANAGER_HOST": "...",
                    "MANAGER_PORT": "...",
                    "NEBULA_AUTH_TOKEN": "...",
                    "MANAGER_AUTH": "...",
                    "SLEEP_SECS": "...",
                    "KEYGEN_PUBLIC_KEY":"..."
                }
            }
        """
        redis_host = st.session_state["REDIS_HOST"] if "REDIS_HOST" in st.session_state else ""
        redis_port = st.session_state["REDIS_PORT"] if "REDIS_PORT" in st.session_state else ""
        redis_auth_token = st.session_state["REDIS_AUTH_TOKEN"] if "REDIS_AUTH_TOKEN" in st.session_state else ""
        manager_host = st.session_state["MANAGER_HOST"] if "MANAGER_HOST" in st.session_state else ""
        manager_port = st.session_state["MANAGER_PORT"] if "MANAGER_PORT" in st.session_state else ""
        nebula_auth_token = st.session_state["NEBULA_AUTH_TOKEN"] if "NEBULA_AUTH_TOKEN" in st.session_state else ""

        env_vars = {"env_vars": {"REDIS_DB_HOST": redis_host,
                                 "REDIS_DB_PORT": redis_port,
                                 "REDIS_DB_PWD": redis_auth_token,
                                 "MANAGER_HOST": manager_host,
                                 "MANAGER_PORT": manager_port,
                                 "NEBULA_AUTH_TOKEN": nebula_auth_token,
                                 "MANAGER_AUTH": nebula_auth_token,
                                 "SLEEP_SECS": "600",
                                 "KEYGEN_PUBLIC_KEY": "06ede5b6f133fc291d1b7bb195a105756f8aa484bdba8a0d6ef8d5ea1f26a1bc",
                                 }}

        return env_vars

    def appExpander(self,name,form_name):
        """
        Renders an expandable Streamlit form to view or configure an app.

        Purpose:
        - Central method for creating or editing an app
        - Supports form-based configuration: name, image, network, device groups, env vars, volumes, ports

        Args:
            name (str): Session key for this app (e.g., "create", or the app name)
            form_name (str): Title shown on the expander block

        Logic:
        - Initializes form state if missing
        - Pulls default values from session or registry
        - Renders inputs: App name, image (selectbox), network, device groups, editable tables for env vars, volumes, ports
        - Disables device group selection for existing apps

        Returns:
            Streamlit expander object (reference for interaction or layout)
        """
        if "visibility" not in st.session_state:
            st.session_state.visibility = "visible"
            st.session_state.disabled = False
            st.session_state.app_list = []

        if name not in st.session_state:
            try:
                hostname = socket.gethostname()
                netwIPAddr = socket.gethostbyname(hostname)
            except Exception as e:
                netwIPAddr = "127.0.0.1"

            env_vars = self.getLatestEnvVars()

            st.session_state["edited_env_vars"] = self.setEnvVars(env_vars)

            st.session_state[name] = {}
            st.session_state[name]["app_name"] = ""
            st.session_state[name]["form_values"] = {
                                                        "image": "",
                                                        "env_vars": self.setEnvVars(env_vars),
                                                        #"env_vars": [{"key":"","value":""}],
                                                        "networks": "nebula",
                                                        "volumes": [{"from": "", "to": ""}],
                                                        "ports": [{"from":" ","to":""}],
                                                        "running": True,
                                                        "rolling_restart": True,
                                                        "containers_per": {"server": 1},
                                                        "privileged": False,
                                                        "device_groups": []
                                                    }
            st.session_state[name]["config"] = {
                                        "docker_image": "",
                                        "env_vars": env_vars["env_vars"],
                                        "networks": [],
                                        "volumes": [],
                                        "starting_ports": [],
                                        "running": True,
                                        "rolling_restart": True,
                                        "containers_per": {"server": 1},
                                        "privileged": False,
                                        "device_groups": [],
                                        "devices": []
                                        }

        elif name == "create":
            existing_env_vars = st.session_state[name]["config"].get("env_vars",{})
            env_vars = self.getLatestEnvVars()
            env_vars["env_vars"] = env_vars["env_vars"] | existing_env_vars

            st.session_state[name]["form_values"]["env_vars"] = self.setEnvVars(env_vars)
            st.session_state[name]["config"]["env_vars"] = env_vars["env_vars"]


        app_expander = st.expander(form_name, expanded=False)

        name_key = "name_key_{}".format(name)
        image_key = "image_key_{}".format(name)
        network_key = "network_key_{}".format(name)
        dg_key = "dg_key_{}".format(name)
        env_key = "env_key_{}".format(name)
        vol_key = "vol_key_{}".format(name)
        port_key = "port_key_{}".format(name)

        name_col,image_col,networks_col, dg_col = app_expander.columns([50,50,50,50],gap="small")
        try:
            check = checkRegistryStatus(self.error_container)
        except Exception as e:
            with self.error_container:
                st.error(f"Trouble Checking Registry Exception: {e}")
            check = False

        with name_col:
            app_name = st.text_input("App Name",st.session_state[name]["app_name"],key=name_key)
            st.session_state[name]["app_name"] = app_name

        with image_col:

            if check:
                refresh_registry()
            else:
                st.session_state.registry_name_list=[]
            preselected_idx = 0
            if name != "create":
                try:
                    preselected_idx = st.session_state.registry_name_list.index(st.session_state[name]["form_values"]["image"])
                except Exception as e:
                    with self.error_container:
                        st.warning("{} not found in existing registry list, exception {}".format(st.session_state[name]["form_values"]["image"],e))

            image = st.selectbox(
                "Container Image",
                st.session_state.registry_name_list,
                disabled = not check,
                index=preselected_idx,
                key=image_key
            )
            if check:
                st.session_state[name]["config"]["docker_image"] = "{}:{}/{}".format(st.session_state.REGISTRY_HOST,st.session_state.REGISTRY_PORT,image)
                st.session_state[name]["form_values"]["image"] = image

            else:
                st.session_state[name]["config"]["docker_image"] = ""
                st.session_state[name]["form_values"]["image"] = ""

        with networks_col:
            networks = st.text_input("Network",st.session_state[name]["form_values"]["networks"],key=network_key)
            st.session_state[name]["config"]["networks"] = [networks]
            st.session_state[name]["form_values"]["networks"] = networks

        with dg_col:

            check = True
            if name !="create":
                dg_option_list = st.session_state[name]["form_values"]["device_groups"]

            else:
                check = False
                try:
                    #dg_list, _ = self.listAllDeviceGroups()
                    listdg_reply = self.listAllDeviceGroups()
                    listdg_fail = listdg_reply.get("error", True)
                    listdg_response = listdg_reply.get("response", {})
                    if listdg_fail:
                        with self.error_container:
                            st.error(f"Error listing device groups, exception {listdg_response}")
                        dg_list = []
                    else:
                        dg_list = listdg_response.get("device_group_list",[])
                except Exception as e:
                    with self.error_container:
                        st.error(f"Error listing device groups, exception {e}")
                    dg_list = []

                dg_option_list = dg_list

            if not isinstance(dg_option_list,list):
                with self.error_container:
                    st.error("Could not decipher device groups, received: {}".format(dg_option_list))
                dg_option_list = []

            if name == "create":
                if "gustavodg1" not in dg_option_list:
                    dg_option_list.append("gustavodg1")

            device_groups = st.multiselect("Device Group (leave blank for default)", options=dg_option_list,default=dg_option_list,
                                           key=dg_key,
                                          disabled=check)

            st.session_state[name]["config"]["device_groups"] = device_groups
            st.session_state[name]["form_values"]["device_groups"] = device_groups

        with app_expander.container():
            st.write("Env Vars")

            edited_env_vars = st.data_editor(self.setEnvVars(st.session_state[name]["config"]),
                                             use_container_width=True,
                                             num_rows="dynamic", disabled=False,
                                             key=env_key, )

            st.session_state[name]["form_values"]["env_vars"] = edited_env_vars

        vol_col, port_col= app_expander.columns([ 50, 50], gap="small")

        with vol_col:

            st.write("Volumes")
            edited_volumes = st.data_editor(self.setVolumes(st.session_state[name]["config"]), use_container_width=True, num_rows="dynamic", disabled=False,
                                         key=vol_key)
            # st.session_state[name]["config"]["volumes"] = self.getVolumes(edited_volumes)
            st.session_state[name]["form_values"]["volumes"] = edited_volumes


        with port_col:
            st.write("Ports")
            edited_ports = st.data_editor(self.setPorts(st.session_state[name]["config"]), use_container_width=True, num_rows="dynamic", disabled=False,
                                        key=port_key)
            st.session_state[name]["form_values"]["ports"] = edited_ports


            #st.session_state[name]["config"]["starting_ports"] = self.getPorts(edited_ports)

        return app_expander

    def refreshAppListForm(self):
        """
        Refreshes the entire list of app forms, rendering UI components for each existing app.

        Purpose:
        - Sync current apps from the backend
        - Display update/delete buttons and YAML download for each app
        - Regenerate `fields`, `deletes`, and `fields_size` session entries

        Logic:
        - Calls `listAllApps()` to refresh `app_list` and configurations
        - Initializes `fields_size`, `fields`, and `deletes`
        - For each app in `app_list`:
            - Calls `appExpander()` to render its config editor
            - Adds Update, Download, and Delete buttons with appropriate callbacks:
                - `update_app(app_name)` updates app config
                - `delete_field(index)` deletes the app and updates state

        UI Elements:
        - App expanders (editable form)
        - YAML config download buttons
        - Inline delete buttons with `❌` icons

        Returns:
            None
        """
        def delete_field(index):
            """
            Deletes the app at the specified index from both the backend and local session state.

            Purpose:
            - Allow users to delete an app from the UI with a single button click
            - Updates the UI and session state immediately upon deletion

            Args:
                index (int): Index of the app in `st.session_state.app_list`

            Logic:
            - Gets the app name from the list using the index
            - Calls `handleTask()` to show spinner and call `deleteApp()`
            - If deletion succeeds:
                - Decrements `fields_size`
                - Removes corresponding entries from `fields`, `deletes`, and `app_list`
                - Deletes the app's config from session state
                - Resets `latest_app_name` to "create"
            - If deletion fails:
                - Shows an error in `error_container`

            Returns:
                None
            """

            app_name = st.session_state.app_list[index]
            try:
                response = self.handleTask(f"Deleting {app_name}...",lambda: self.deleteApp(app_name),f"{app_name}_delete_result")
                if response["error"]:
                    with self.error_container:
                        st.error("Error deleting app {}, response was {}".format(app_name,response["response"]))
                else:
                    st.session_state.fields_size -= 1
                    del st.session_state.fields[index]
                    del st.session_state.deletes[index]
                    del st.session_state.app_list[index]
                    del st.session_state[app_name]
                    st.session_state.latest_app_name = "create"
            except Exception as e:
                with self.error_container:
                    st.error(f"Error deleting app {app_name} exception:{e}")


        def update_app(app_name):
            """
            Updates the configuration of an app based on current form values.

            Purpose:
            - Allow users to submit updates to an app's config directly from the UI

            Args:
                app_name (str): Name of the app being updated

            Logic:
            - Calls `handleTask()` to invoke `updateApp()` and wrap the operation in a spinner
            - If the app's name was changed in the form:
                - Updates the session state and `app_list` to reflect the new name
                - Copies the configuration to the new name and deletes the old one
            - Syncs form values (`env_vars`, `volumes`, `ports`) from updated config to UI

            Error Handling:
            - Shows exception messages in the error container if update fails

            Returns:
                None
            """
            try:

                response = self.handleTask(f"Updating {app_name}...", lambda: self.updateApp(app_name), f"{app_name}_update_result")

                if response["error"]:
                    st.error("Error updating app {}, response was {}".format(app_name,response["response"]))
                else:
                    # need to convert from form values to config values for data editor
                    if st.session_state[app_name]["app_name"] != app_name:
                        new_app_name = copy.deepcopy(st.session_state[app_name]["app_name"])
                        # print(new_app_name)
                        logging.info(f"{new_app_name}")
                        app_index = st.session_state.app_list.index(app_name)
                        st.session_state.app_list[app_index] = new_app_name

                        st.session_state[new_app_name] = copy.deepcopy(st.session_state[app_name])

                        del st.session_state[app_name]

                        app_name = new_app_name

                    st.session_state[app_name]["form_values"]["ports"] = self.setPorts(st.session_state[app_name]["config"])
                    st.session_state[app_name]["form_values"]["volumes"] = self.setVolumes(st.session_state[app_name]["config"])
                    st.session_state[app_name]["form_values"]["env_vars"] = self.setEnvVars(st.session_state[app_name]["config"])

            except Exception as e:
                with self.error_container:
                    st.error(f"Error updating app {app_name}, exception :{e}")

        try:
            listapps_reply = self.listAllApps()
            listapps_fail = listapps_reply.get("error",True)
            listapps_response = listapps_reply.get("response","failure listing apps")
            if listapps_fail:
                with self.error_container:
                    st.error(f"Error listing existing apps, exception {listapps_response}")
            else:
                self.app_list =  listapps_response

        except Exception as e:
            with self.error_container:
                st.error(f"Error listing existing apps, exception {e}")

        st.session_state.fields_size = len(self.app_list)
        st.session_state.fields = [app for app in self.app_list]

        if "fields_size" not in st.session_state:
            st.session_state.deletes = []

        #print(st.session_state.fields_size,self.app_list)
        for i in range(st.session_state.fields_size):

            if i < len(self.app_list):
                app_expander = self.appExpander(self.app_list[i],
                                                self.app_list[i])
                updatecol, downloadcol, deletecol = app_expander.columns([50, 50, 50], gap="large")
                updatecol.button("Update {}".format(self.app_list[i]), key=f"update{i}", on_click=update_app,
                                 args=(self.app_list[i],))
                with downloadcol:

                    app_name = self.app_list[i]

                    app_dict = {app_name : st.session_state[app_name]["config"]}
                    app_config = yaml.dump(app_dict, default_flow_style=False, sort_keys=False)


                    st.download_button(
                        label="Download App Config",
                        key=f"app{i}_config_dn_button",
                        data=app_config,
                        file_name="{}_config.yaml".format(app_name),
                        mime='text',
                        # on_click=set_dn_config_clicked
                    )
                st.session_state.fields.append(app_expander)
                st.session_state.deletes.append(
                    deletecol.button("❌ Delete {}".format(self.app_list[i]), key=f"delete{i}", on_click=delete_field,
                                     args=(i,)))

    def apps(self):
        """
        Top-level UI method that renders the complete Application Handler page in Streamlit.

        Purpose:
        - Provides a unified interface for creating, viewing, editing, and deleting apps

        Logic:
        - Calls `listAllApps()` on startup to populate the app list
        - Initializes session structures if not present
        - Renders:
            - List of existing apps via `refreshAppListForm()`
            - Expander for new app creation (`appExpander("create", ...)`)
                - Includes Upload (YAML) and Submit (Create) buttons
                - Supports pre-filling form using `process_uploaded_file()`
                - Submits via `add_field()` which validates and invokes `createApp()`

        UI Components:
        - Header: "Application Handler"
        - Error container (Streamlit container)
        - Create New App expander:
            - YAML upload
            - Submit button (calls `add_field`)
        - Existing apps listed with:
            - Update button
            - Download config
            - Delete button

        Returns:
            None
        """

        st.header("Application Handler")

        self.error_container = st.container()
        self.log_placeholder = st.empty()

        try:
            listapps_reply = self.listAllApps()
            listapps_fail = listapps_reply.get("error", True)
            listapps_response = listapps_reply.get("response", "failure listing apps")
            if listapps_fail:
                with self.error_container:
                    st.error(f"Error listing existing apps, exception {listapps_response}")

        except Exception as e:
            with self.error_container:
                st.error(f"Error listing all apps, exception :{e}")

        if "fields_size" not in st.session_state:
            st.session_state.fields_size = len(self.app_list)
            st.session_state.fields = [app for app in self.app_list]
            st.session_state.deletes = []

        with st.container():
            def add_field():
                if "create" in st.session_state:

                    app_name = st.session_state["create"]["app_name"]
                    if app_name == "":
                        with self.error_container:
                            st.error("App Name is blank")
                    elif app_name in self.app_list:
                        with self.error_container:
                            st.error("App already exists")
                    else:
                        st.session_state.app_list.append(app_name)
                        st.session_state.latest_app_name= app_name
                        st.session_state[app_name] = {}
                        st.session_state[app_name]["app_name"] = app_name
                        st.session_state[app_name]["form_values"] = copy.deepcopy(st.session_state["create"]["form_values"])
                        st.session_state[app_name]["config"] = copy.deepcopy(st.session_state["create"]["config"])

                        #need to convert from form values to config values for data editor
                        st.session_state[app_name]["config"]["env_vars"] = self.getEnvVars(st.session_state[app_name]["form_values"]["env_vars"])
                        st.session_state[app_name]["config"]["volumes"] = self.getVolumes(st.session_state[app_name]["form_values"]["volumes"])
                        st.session_state[app_name]["config"]["starting_ports"] = self.getPorts(st.session_state[app_name]["form_values"]["ports"])

                        # st.session_state[app_name]["form_values"]["ports"] = self.setPorts(st.session_state[app_name]["config"])
                        # st.session_state[app_name]["form_values"]["volumes"] = self.setVolumes(st.session_state[app_name]["config"])
                        # st.session_state[app_name]["form_values"]["env_vars"] = self.setEnvVars(st.session_state[app_name]["config"])

                        try:
                            response = self.handleTask( f"Creating {app_name}...", lambda: self.createApp(app_name, st.session_state[app_name]["config"]["device_groups"]), f"{app_name}_create_result")

                            if response["error"]:
                                with self.error_container:
                                    st.error("Error creating app {}, response: {}".format(app_name,response["response"]))
                                del st.session_state[app_name]
                                st.session_state.app_list.pop(st.session_state.fields_size)
                            else:
                                st.session_state.fields_size += 1
                        except Exception as e:
                            del st.session_state[app_name]
                            st.session_state.app_list.pop(st.session_state.fields_size)
                            with self.error_container:
                                st.error(f"Error creating app {app_name}, exception : {e}")

                else:
                    with self.error_container:
                        st.error("App creation error due to session state mismatch")

            self.refreshAppListForm()

            create_app_expander = self.appExpander("create","Create New App")
            load_config, save_config = create_app_expander.columns([50, 50])
            with load_config:
                if 'load_config_clicked' not in st.session_state:
                    st.session_state.load_config_clicked = False

                def set_load_config_clicked():
                    st.session_state.load_config_clicked = not (st.session_state.load_config_clicked)

                st.button('Upload Configuration File', on_click=set_load_config_clicked)
                if st.session_state.load_config_clicked:
                    uploaded_env_file = st.file_uploader("Upload Configuration File", type=[".yaml", ".yml"])
                    if uploaded_env_file is not None:
                        app_config = self.handleTask("Processing config...", lambda: self.process_uploaded_file(uploaded_env_file), "config_upload_result")

            with save_config:
                st.button("Submit", on_click=add_field)


ah = AppHandler()
ah.apps()
