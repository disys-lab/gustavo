import yaml,time, sys,os
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
from gustavo.pages.config.SyncerConfig import SyncerConfig
sidebarInit()
from src.Manager import Manager
from gustavo.pages.config.Logging import setup_logging
setup_logging()
import logging
from gustavo.pages.config.loadCss import load_css
load_css()

class ManagerService:
    """
    The `ManagerService` class provides a Streamlit-based interface to control and monitor backend services 
    such as Redis, Mongo, Registry, Syncer, and Manager.

    Core Responsibilities:
    - Retrieve configurations from Streamlit session state
    - Render UI forms and status displays for each service
    - Support service lifecycle operations: status check, launch, remove
    - Display interactive feedback using tooltips and status pills

    Backend Dependencies:
    - Interfaces with the `Manager` class to execute service operations
    - Relies on accurate session state setup for all configuration variables

    UI Elements:
    - Top-level service status indicators (`statusButtonTop`)
    - Detailed control panels per service (`serviceExpander`)
    - Async feedback via `handleTask` spinners and tooltips

    Supported Services:
    - Redis
    - Mongo
    - Registry
    - Syncer
    - Manager
    """
    def __init__(self):
        """
        Initializes the `ManagerService` interface and pre-loads configuration structures for all services.

        Purpose:
        - Prepares internal data structures to hold service configurations
        - Initializes status values in Streamlit session state
        - Instantiates the `Manager` controller object with session context

        Logic:
        - Sets empty/default values for Redis, Mongo, Registry, Syncer, and Manager configuration dictionaries
        - Adds session state status entries for all services (`"Redis_status"`, etc.)
        - Prepares default Redis backup directory

        Returns:
            None
        """
        self.man = Manager(mode="streamlit", params=st.session_state)
        self.redis_conf = {"REDIS_HOST": "",
                      "REDIS_PORT": "",
                      "REDIS_AUTH_TOKEN": "",
                      "REDIS_IMAGE": "",
                      "REDIS_BKP_DIR": "/tmp/"
                      }
        if "Redis_status" not in st.session_state.keys():
            st.session_state["Redis_status"] = "Unknown"
        self.mongo_conf = {
            "MONGO_HOST": "",
            "MONGO_PORT": "",
            "MONGO_USERNAME": "",
            "MONGO_PASSWORD":"",
            "MONGO_CERTIFICATE_FOLDER_PATH":""
        }
        if "Mongo_status" not in st.session_state.keys():
            st.session_state["Mongo_status"] = "Unknown"
        self.registry_conf = {
            "REGISTRY_HOST":"",
            "REGISTRY_PORT":"",
            "REGISTRY_IMAGE":"",
            "REGISTRY_BKP_DIR": "/tmp/"
        }
        if "Registry_status" not in st.session_state.keys():
            st.session_state["Registry_status"] = "Unknown"
        self.syncer_conf = {
            "SYNCER_IMAGE": "",
            "DREGSY_CONFIG_FILE_PATH":"",
            "DREGSY_MAPPING_FILE_PATH":""
        }
        if "Syncer_status" not in st.session_state.keys():
            st.session_state["Syncer_status"] = "Unknown"
        self.manager_conf = {
            "MANAGER_HOST": "",
            "MANAGER_PORT": "",
            "NEBULA_USERNAME": "",
            "NEBULA_PASSWORD":"",
            "NEBULA_AUTH_TOKEN":"",
            "MANAGER_NMODE":"",
            "CACHE_EXPIRE_TIME":"",
            "MANAGER_IMAGE":""
        }
        st.session_state["Manager_status"] = "Unknown"

    def handleTask(self, label, action_fn, result_container_key="action_result_placeholder"):
        """
        Executes a task with spinner feedback and tooltip messaging in the UI.

        Purpose:
        - Show a loading spinner during long operations (launch/remove/status)
        - Display a tooltip message based on the task result
        - Store the result in session state for traceability

        Args:
            label (str): Spinner message during execution
            action_fn (Callable): The task to run (typically a lambda or method call)
            result_container_key (str): Session key for saving the result

        Returns:
            dict: Task result with keys `error` and `response`
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

    def status_pill(self, status):
        """
        Returns a styled HTML badge (pill) for the current status of a service.

        Purpose:
        - Provide visual feedback of service status (Up, Down, Unknown)

        Args:
            status (str): One of "Up", "Down", or "Unknown"

        Returns:
            str: HTML markup string for the status badge
        """
        if status == "Up":
            return '<div style="background-color: #9beba1; color: white; border-radius: 12px; padding: 5px 10px;">Up</div>'
        elif status == "Down":
            return '<div style="background-color: #f37e7a; color: white; border-radius: 12px; padding: 5px 10px;">Down</div>'
        else:
            return '<div style="background-color: #ffcc49; color: black; border-radius: 12px; padding: 5px 10px;">Unknown</div>'

    def obtainManagerConf(self):
        """
        Retrieves and stores Manager service configuration from session state.

        Purpose:
        - Populate `self.manager_conf` with manager-related fields
        - Update the `Manager` instance's attributes accordingly

        Logic:
        - For each expected manager configuration key (e.g., MANAGER_HOST, NEBULA_AUTH_TOKEN, etc.):
            - Check if it exists in `st.session_state`
            - If yes: assign value to both the internal `manager_conf` and `self.man`
            - If not: set "Undefined" or an empty string

        Side Effects:
        - Disables `wait_for_manager_enabled` for the `Manager` instance

        Returns:
            list[dict]: A single-element list containing the updated `manager_conf` dictionary
        """
        if "MANAGER_HOST" not in st.session_state.keys():
            self.manager_conf["MANAGER_HOST"] = "Undefined"
        else:
            self.manager_conf["MANAGER_HOST"] = st.session_state.MANAGER_HOST
            self.man.MANAGER_IP=st.session_state.MANAGER_HOST

        if "MANAGER_PORT" not in st.session_state.keys():
            self.manager_conf["MANAGER_PORT"] = "Undefined"
        else:
            self.manager_conf["MANAGER_PORT"] = st.session_state.MANAGER_PORT
            self.man.MANAGER_PORT = st.session_state.MANAGER_PORT

        if "NEBULA_AUTH_TOKEN" not in st.session_state.keys():
            self.manager_conf["NEBULA_AUTH_TOKEN"] = "Undefined"
        else:
            self.manager_conf["NEBULA_AUTH_TOKEN"] = ""
            self.man.NEBULA_AUTH_TOKEN = st.session_state.NEBULA_AUTH_TOKEN

        if "NEBULA_USERNAME" not in st.session_state.keys():
            self.manager_conf["NEBULA_USERNAME"] = "Undefined"
        else:
            self.manager_conf["NEBULA_USERNAME"] = st.session_state.NEBULA_USERNAME
            self.man.NEBULA_USERNAME = st.session_state.NEBULA_USERNAME

        if "NEBULA_PASSWORD" not in st.session_state.keys():
            self.manager_conf["NEBULA_PASSWORD"] = "Undefined"
        else:
            self.manager_conf["NEBULA_PASSWORD"] = ""
            self.man.NEBULA_PASSWORD = st.session_state.NEBULA_PASSWORD

        if "MANAGER_IMAGE" not in st.session_state.keys():
            self.manager_conf["MANAGER_IMAGE"] = "Undefined"
        else:
            self.manager_conf["MANAGER_IMAGE"] = st.session_state.MANAGER_IMAGE
            self.man.MANAGER_IMAGE = st.session_state.MANAGER_IMAGE
        
        if "MANAGER_NMODE" not in st.session_state.keys():
            self.manager_conf["MANAGER_NMODE"] = "Undefined"
        else:
            self.manager_conf["MANAGER_NMODE"] = st.session_state.MANAGER_NMODE
            self.man.MANAGER_NMODE = st.session_state.MANAGER_NMODE
        
        if "CACHE_EXPIRE_TIME" not in st.session_state.keys():
            self.manager_conf["CACHE_EXPIRE_TIME"] = "Undefined"
        else:
            self.manager_conf["CACHE_EXPIRE_TIME"] = st.session_state.CACHE_EXPIRE_TIME
            self.man.CACHE_EXPIRE_TIME = st.session_state.CACHE_EXPIRE_TIME
        self.man.wait_for_manager_enabled = False
        return [self.manager_conf]
    
    def obtainSyncerConf(self):
        """
        Retrieves and stores Syncer service configuration from session state.

        Purpose:
        - Populate `self.syncer_conf` with values like SYNCER_IMAGE and config/mapping file paths
        - Update the same values in the `Manager` instance

        Logic:
        - Checks for each expected session key (e.g., SYNCER_IMAGE, DREGSY_CONFIG_FILE_PATH)
        - Populates internal and external configuration values with the current session state

        Returns:
            list[dict]: A single-element list containing the `syncer_conf` dictionary
        """
        if "SYNCER_IMAGE" not in st.session_state.keys():
            self.syncer_conf["SYNCER_IMAGE"] = "Undefined"
        else:
            self.syncer_conf["SYNCER_IMAGE"] = st.session_state.SYNCER_IMAGE
            self.man.SYNCER_IMAGE = st.session_state.SYNCER_IMAGE

        if "DREGSY_CONFIG_FILE_PATH" not in st.session_state.keys():
            self.syncer_conf["DREGSY_CONFIG_FILE_PATH"] = "Undefined"
        else:
            self.syncer_conf["DREGSY_CONFIG_FILE_PATH"] = st.session_state.DREGSY_CONFIG_FILE_PATH
            self.man.DREGSY_CONFIG_FILE_PATH = st.session_state.DREGSY_CONFIG_FILE_PATH

        if "DREGSY_MAPPING_FILE_PATH" not in st.session_state.keys():
            self.syncer_conf["DREGSY_MAPPING_FILE_PATH"] = "Undefined"
        else:
            self.syncer_conf["DREGSY_MAPPING_FILE_PATH"] = st.session_state.DREGSY_MAPPING_FILE_PATH
            self.man.DREGSY_MAPPING_FILE_PATH = st.session_state.DREGSY_MAPPING_FILE_PATH

        return [self.syncer_conf]
    
    def obtainRegistryConf(self):
        """
        Retrieves and stores Registry service configuration from session state.

        Purpose:
        - Load and store registry IP, port, and image information
        - Propagate this information to the associated `Manager` instance

        Logic:
        - Checks and assigns REGISTRY_HOST, REGISTRY_PORT, and REGISTRY_IMAGE
        - Defaults to "Undefined" if any key is missing

        Returns:
            list[dict]: A single-element list with `registry_conf` values
        """
        if "REGISTRY_HOST" not in st.session_state.keys():
            self.registry_conf["REGISTRY_HOST"] = "Undefined"
        else:
            self.registry_conf["REGISTRY_HOST"] = st.session_state.REGISTRY_HOST
            self.man.REGISTRY_IP=st.session_state.REGISTRY_HOST

        if "REGISTRY_PORT" not in st.session_state.keys():
            self.registry_conf["REGISTRY_PORT"] = "Undefined"
        else:
            self.registry_conf["REGISTRY_PORT"] = st.session_state.REGISTRY_PORT
            self.man.REGISTRY_PORT = st.session_state.REGISTRY_PORT
        
        if "REGISTRY_IMAGE" not in st.session_state.keys():
            self.registry_conf["REGISTRY_IMAGE"] = "Undefined"
        else:
            self.registry_conf["REGISTRY_IMAGE"] = st.session_state.REGISTRY_IMAGE
            self.man.REGISTRY_IMAGE = st.session_state.REGISTRY_IMAGE

        if "REGISTRY_BKP_DIR" not in st.session_state.keys():
            self.registry_conf["REGISTRY_BKP_DIR"] = "/tmp/"
        else:
            REGISTRY_BKP_DIR = st.session_state.REGISTRY_BKP_DIR
            if not (os.path.exists(REGISTRY_BKP_DIR) and os.path.isdir(REGISTRY_BKP_DIR)):
                logging.error(f"{REGISTRY_BKP_DIR} does not exist, defaulting to /tmp/")
                st.toast(f"{REGISTRY_BKP_DIR} does not exist, defaulting to /tmp/")
                REGISTRY_BKP_DIR = "/tmp/"

            #self.REDIS_BKP_DIR = REDIS_BKP_DIR
            self.registry_conf["REGISTRY_BKP_DIR"] = REGISTRY_BKP_DIR
            self.man.REGISTRY_BKP_DIR = st.session_state.REGISTRY_BKP_DIR

        return [self.registry_conf]

    def obtainMongoConf(self):
        """
        Retrieves and stores MongoDB service configuration from session state.

        Purpose:
        - Read and assign all required MongoDB parameters (host, port, user, pass, cert path, image)
        - Mirror values to the corresponding `Manager` attributes

        Logic:
        - Uses `st.session_state` to populate `self.mongo_conf`
        - Assigns to both internal dictionary and `self.man` attributes

        Returns:
            list[dict]: A single-element list with the MongoDB configuration
        """
        if "MONGO_HOST" not in st.session_state.keys():
            self.mongo_conf["MONGO_HOST"] = "Undefined"
        else:
            self.mongo_conf["MONGO_HOST"] = st.session_state.MONGO_HOST
            self.man.MONGO_IP=st.session_state.MONGO_HOST

        if "MONGO_PORT" not in st.session_state.keys():
            self.mongo_conf["MONGO_PORT"] = "Undefined"
        else:
            self.mongo_conf["MONGO_PORT"] = st.session_state.MONGO_PORT
            self.man.MONGO_PORT = st.session_state.MONGO_PORT

        if "MONGO_USERNAME" not in st.session_state.keys():
            self.mongo_conf["MONGO_USERNAME"] = "Undefined"
        else:
            self.mongo_conf["MONGO_USERNAME"] = st.session_state.MONGO_USERNAME
            self.man.MONGO_USERNAME = st.session_state.MONGO_USERNAME

        if "MONGO_PASSWORD" not in st.session_state.keys():
            self.mongo_conf["MONGO_PASSWORD"] = "Undefined"
        else:
            self.mongo_conf["MONGO_PASSWORD"] = ""
            self.man.MONGO_PASSWORD = st.session_state.MONGO_PASSWORD

        if "MONGO_CERTIFICATE_FOLDER_PATH" not in st.session_state.keys():
            self.mongo_conf["MONGO_CERTIFICATE_FOLDER_PATH"] = "Undefined"
        else:
            self.mongo_conf["MONGO_CERTIFICATE_FOLDER_PATH"] = st.session_state.MONGO_CERTIFICATE_FOLDER_PATH
            self.man.MONGO_CERTIFICATE_FOLDER_PATH = st.session_state.MONGO_CERTIFICATE_FOLDER_PATH

        if "MONGO_IMAGE" not in st.session_state.keys():
            self.mongo_conf["MONGO_IMAGE"] = "Undefined"
        else:
            self.mongo_conf["MONGO_IMAGE"] = st.session_state.MONGO_IMAGE
            self.man.MONGO_IMAGE = st.session_state.MONGO_IMAGE

        return [self.mongo_conf]

    def obtainRedisConf(self):
        """
        Retrieves and stores Redis service configuration from session state, with validation.

        Purpose:
        - Gather Redis host, port, token, image, and backup directory
        - Validate backup directory path
        - Sync values to the `Manager` instance

        Logic:
        - Checks all expected Redis keys
        - Validates `REDIS_BKP_DIR` using `os.path.exists()` and falls back to `/tmp/` if invalid
        - Logs fallback conditions for visibility

        Returns:
            list[dict]: A single-element list with Redis configuration
        """
        if "REDIS_HOST" not in st.session_state.keys():
            self.redis_conf["REDIS_HOST"] = "Undefined"
        else:
            self.redis_conf["REDIS_HOST"] = st.session_state.REDIS_HOST
            self.man.REDIS_IP=st.session_state.REDIS_HOST

        if "REDIS_PORT" not in st.session_state.keys():
            self.redis_conf["REDIS_PORT"] = "Undefined"
        else:
            self.redis_conf["REDIS_PORT"] = st.session_state.REDIS_PORT
            self.man.REDIS_PORT = st.session_state.REDIS_PORT

        if "REDIS_AUTH_TOKEN" not in st.session_state.keys():
            self.redis_conf["REDIS_AUTH_TOKEN"] = "Undefined"
        else:
            self.redis_conf["REDIS_AUTH_TOKEN"] = st.session_state.REDIS_AUTH_TOKEN
            self.man.REDIS_AUTH_TOKEN = st.session_state.REDIS_AUTH_TOKEN

        if "REDIS_IMAGE" not in st.session_state.keys():
            self.redis_conf["REDIS_IMAGE"] = "Undefined"
        else:
            self.redis_conf["REDIS_IMAGE"] = st.session_state.REDIS_IMAGE
            self.man.REDIS_IMAGE = st.session_state.REDIS_IMAGE

        if "REDIS_BKP_DIR" not in st.session_state.keys():
            self.redis_conf["REDIS_BKP_DIR"] = "/tmp/"
        else:
            REDIS_BKP_DIR = st.session_state.REDIS_BKP_DIR
            if not (os.path.exists(REDIS_BKP_DIR) and os.path.isdir(REDIS_BKP_DIR)):
                logging.error(f"{REDIS_BKP_DIR} does not exist, defaulting to /tmp/")
                st.toast(f"{REDIS_BKP_DIR} does not exist, defaulting to /tmp/")
                REDIS_BKP_DIR = "/tmp/"

            #self.REDIS_BKP_DIR = REDIS_BKP_DIR
            self.redis_conf["REDIS_BKP_DIR"] = REDIS_BKP_DIR
            self.man.REDIS_BKP_DIR = st.session_state.REDIS_BKP_DIR

        return [self.redis_conf]

    def serviceExpander(self, service_name, status_container):
        """
        Renders an interactive UI panel (expander) for managing a specific service.

        Purpose:
        - Display service configuration
        - Provide buttons for checking status, launching, and removing the service
        - Dynamically update configuration paths (for Syncer)

        Args:
            service_name (str): Name of the service to render (e.g., "Redis", "Mongo")
            status_container (st.status): Streamlit status context used for feedback

        Logic:
        - Determines which `obtain...Conf()` method to call based on service_name
        - For Syncer:
            - Displays editable text inputs for config and mapping file paths
            - Validates paths and calls `syncerConfigs()` and `syncerMappings()`
        - Renders:
            - Read-only config table using `st.data_editor()`
            - Status, Launch 🚀, and Remove 🛑 buttons
        - Each button triggers corresponding logic via `handleTask()` with wrapped actions

        Returns:
            Renders the expander for a given service, including status, launch, and remove buttons."""
        # Define the session key for service status at the top
        service_name_status = f'{service_name}_status'
        
        with st.expander(service_name, expanded=False):
            service_name_status = '{}_status'.format(service_name)
            data_editor_widget_key = service_name + "_" + "data_editor"
            status_button_widget_key = service_name + "_" + "status_button"
            launch_button_widget_key = service_name + "_" + "launch_button"
            remove_button_widget_key = service_name + "_" + "remove_button"
            
            # Determine the configuration for each service
            if service_name == "Manager":
                conf = self.obtainManagerConf()
            elif service_name == "Redis":
                conf = self.obtainRedisConf()
            elif service_name == "Mongo":
                conf = self.obtainMongoConf()
            elif service_name == "Registry":
                conf = self.obtainRegistryConf()
            elif service_name == "Syncer":
                sy = SyncerConfig()
                conf = self.obtainSyncerConf()

                #config_file_path, mapping_file_path = st.columns([50, 50], gap="large")
                if "DREGSY_CONFIG_FILE_PATH" in st.session_state.keys():
                    self.syncer_conf["DREGSY_CONFIG_FILE_PATH"] = st.session_state.DREGSY_CONFIG_FILE_PATH

                if "DREGSY_MAPPING_FILE_PATH" in st.session_state.keys():
                    self.syncer_conf["DREGSY_MAPPING_FILE_PATH"] = st.session_state.DREGSY_MAPPING_FILE_PATH

                with st.container():
                    st.session_state.DREGSY_CONFIG_FILE_PATH = st.text_input("SYNCER_CONFIG_PATH",
                                                                                self.syncer_conf["DREGSY_CONFIG_FILE_PATH"],
                                                                key="SYNCER_CONFIG_PATH_WIDGET_KEY")
                    self.syncer_conf["DREGSY_CONFIG_FILE_PATH"] = st.session_state.DREGSY_CONFIG_FILE_PATH
                    if os.path.exists(os.path.dirname(os.path.expanduser(self.syncer_conf["DREGSY_CONFIG_FILE_PATH"]))):
                        st.success("Valid DREGSY_CONFIG_FILE_PATH")
                        st.session_state.DREGSY_CONFIG_FILE_PATH = os.path.expanduser(self.syncer_conf["DREGSY_CONFIG_FILE_PATH"])
                    else:
                        st.error("Invalid DREGSY_CONFIG_FILE_PATH")

                    sy.syncerConfigs()

                with st.container():
                    st.session_state.DREGSY_MAPPING_FILE_PATH = st.text_input("SYNCER_MAPPING_PATH",
                                                                              self.syncer_conf["DREGSY_MAPPING_FILE_PATH"],
                                                                             key="SYNCER_MAPPING_PATH_WIDGET_KEY")
                    self.syncer_conf["DREGSY_MAPPING_FILE_PATH"] = st.session_state.DREGSY_MAPPING_FILE_PATH
                    if os.path.exists(
                            os.path.dirname(os.path.expanduser(self.syncer_conf["DREGSY_MAPPING_FILE_PATH"]))):
                        st.success("Valid DREGSY_MAPPING_FILE_PATH")
                        st.session_state.DREGSY_MAPPING_FILE_PATH = os.path.expanduser(self.syncer_conf["DREGSY_MAPPING_FILE_PATH"])
                    else:
                        st.error(
                            "Invalid DREGSY_MAPPING_FILE_PATH {}".format(self.syncer_conf["DREGSY_MAPPING_FILE_PATH"]))

                    sy.syncerMappings()

                conf = self.obtainSyncerConf()

            # Display the configuration for the service
            st.data_editor(conf, disabled=True, num_rows="fixed", use_container_width=True, key=f"{service_name}_data_editor")

            # circle, status, launch, kill = st.columns([1, 50, 50, 50], gap="large")
            status, launch, kill = st.columns([50, 50, 50], gap="large")
            status_session_key = '{}_status_clicked'.format(service_name)
            launch_session_key = '{}_launch_clicked'.format(service_name)
            remove_session_key = '{}_remove_clicked'.format(service_name)

            # Status button logic
            with status:
                self.statusButton(service_name, status_container, suffix="")
                
            # Update the status pill at the top of the expander
            with launch:
                launch_session_key = f'{service_name}_launch_clicked'
                if launch_session_key not in st.session_state:
                    st.session_state[launch_session_key] = False

                def set_launch_clicked():
                    st.session_state[launch_session_key] = not st.session_state[launch_session_key]

                st.button("Launch 🚀", on_click=set_launch_clicked, key=f"{service_name}_launch_button")

                if st.session_state[launch_session_key]:
                    def launch_action():
                        with status_container:
                            status_container.write(f"Launching {service_name}...")
                            result = self.man.run(service_name.lower())
                            if not result["error"]:
                                st.session_state[service_name_status] = "Up"
                                status_container.markdown(f":green[{service_name} is Up]")
                            else:
                                st.session_state[service_name_status] = "Down"
                                status_container.markdown(f":red[Error while launching {service_name}]")
                            return result  # ✅ Add this line
                    self.handleTask(f"Launching {service_name}...", launch_action, f"{service_name}_launch_result")
                    st.session_state[launch_session_key] = False

            # Remove button logic
            with kill:
                remove_session_key = f'{service_name}_remove_clicked'
                if remove_session_key not in st.session_state:
                    st.session_state[remove_session_key] = False

                def set_kill_clicked():
                    st.session_state[remove_session_key] = not st.session_state[remove_session_key]

                st.button("Remove 🛑", on_click=set_kill_clicked, key=f"{service_name}_remove_button")

                if st.session_state[remove_session_key]:
                    def remove_action():
                        with status_container:
                            status_container.write(f"Removing {service_name}...")
                            result = self.man.handleService(service_name.lower(), "remove")
                            if not result["error"]:
                                st.session_state[service_name_status] = "Down"
                                st.write(result["response"])
                                status_container.markdown(f":green[{service_name} is brought down]")
                            elif "error" in result.keys():
                                st.write(result["response"])
                                status_container.markdown(f":red[Error encountered while removing {service_name}]")
                            return result
                    self.handleTask(f"Removing {service_name}...", remove_action, f"{service_name}_remove_result")
                    st.session_state[remove_session_key] = False

    def statusButton(self, service_name, status_container, suffix=""):
        """
        Displays and manages the "Status" button for a given service.

        Purpose:
        - Allow user to manually check if a service is currently running
        - Update the status pill in session state

        Args:
            service_name (str): Name of the service (e.g., "Mongo", "Manager")
            status_container (st.container): UI placeholder for writing status updates
            suffix (str): Optional suffix to distinguish button keys (used in top bar vs. expander)

        Logic:
        - Defines a `status_action()` to call `self.man.serviceStatus(...)`
        - For Manager:
            - Performs additional health check via `checkManager()` API
        - Updates corresponding `..._status` session state field
        - Wraps the operation in `handleTask()` for spinner and tooltip feedback

        Returns:
            None
        """ 
        # Ensure that the service name status is correctly initialized in session_state
        service_name_status = f'{service_name}_status'
        status_button_widget_key = f"{service_name}_status_button_{suffix}"  # Add suffix to make the key unique
        status_session_key = f"{service_name}_status_clicked_{suffix}"  # Also make the session key unique

        if status_session_key not in st.session_state:
            st.session_state[status_session_key] = False

        # Define the function to toggle status session state
        def set_status_clicked():
            st.session_state[status_session_key] = not st.session_state[status_session_key]
            
        # Create the Status button
        st.button(f'Status {suffix} 📈', on_click=set_status_clicked, key=status_button_widget_key)
        
        # If the status button is clicked
        if st.session_state[status_session_key]:
            def status_action():
                with status_container:

                    # Check the service status
                    result = self.man.serviceStatus(service_name.lower())
                    if result["error"]:
                        st.session_state[service_name_status] = "Down"
                        
                    else:
                        # Additional check for Manager API if it's the Manager service
                        if service_name == "Manager":
                            # Safely fetch the configuration from session state with defaults
                            manager_host = st.session_state.get("MANAGER_HOST", None)
                            manager_port = st.session_state.get("MANAGER_PORT", None)
                            auth_token = st.session_state.get("NEBULA_AUTH_TOKEN", "")

                            # Ensure the host and port are not None before proceeding
                            if manager_host is None or manager_port is None or not auth_token:
                                st.session_state[service_name_status] ="Up"
                                # status_container.markdown(f":red[Manager configuration is incomplete 🚨]")
                            else:
                                # Safeguard the token and host before assigning to self.man
                                self.man.MANAGER_IP = manager_host
                                self.man.MANAGER_PORT = manager_port
                                self.man.NEBULA_AUTH_TOKEN = auth_token if auth_token else ""

                                # Now proceed to check the Manager API
                                result = self.man.checkManager()
                                if result["error"]:
                                    st.session_state["Manager_status"] = "Down"
                                elif 'status' in result and result["status"] == "unknown":
                                    st.session_state["Manager_status"] = "Unknown"
                                    # status_container.markdown(f":orange[Manager API status is unknown ❓]")
                                else:
                                    st.session_state["Manager_status"] = "Up"
                        else:
                            st.session_state[service_name_status] = "Up"
                            # status_container.markdown(f":green[{service_name} is running ✅]")
                        return result
            self.handleTask(f"Checking {service_name} status...", status_action, f"{service_name}_status_result")

    def statusButtonTop(self):
        """
        Renders a row of top-level status indicators and buttons for all services.

        Purpose:
        - Provide quick access to status check buttons at the top of the page
        - Visually indicate current service states with colored pills

        Logic:
        - Creates 5 columns for: Redis, Mongo, Registry, Syncer, Manager
        - For each service:
            - Displays status pill using `status_pill(...)`
            - Adds button via `statusButton(...)` with suffix to keep keys unique
            - Refreshes the pill after status is updated

        Returns:
            None
        """
        # Create columns for each button box
        cols = st.columns([1, 1, 1, 1, 1])  # Adjust the column proportions as needed
        services = ["Redis", "Mongo", "Registry", "Syncer", "Manager"]

        # Iterate over each service to create a button and a status box
        for i, service in enumerate(services):
            with cols[i]:
                with st.container():  # Create a separate box for each service
                    # Define the status variable for each service
                    service_name_status = f'{service}_status'

                    # Create an empty container to dynamically update the status pill
                    status_pill_placeholder = st.empty()

                    # Display the initial status pill for each service at the top
                    status_pill_placeholder.markdown(
                        f"{self.status_pill(st.session_state[service_name_status])}",
                        unsafe_allow_html=True
                    )

                    # Status button logic for each service
                    status_container = st.empty()  # Placeholder for status updates
                    self.statusButton(service, status_container, suffix=service)

                    # After the status check, update the status pill again dynamically
                    status_pill_placeholder.markdown(
                        f"{self.status_pill(st.session_state[service_name_status])}",
                        unsafe_allow_html=True
                    )

    def manager(self):
        """
        Main UI method that renders the entire Manager Services dashboard.

        Purpose:
        - Display service lifecycle controls and configurations for all system services

        Logic:
        - Renders a header ("Manager Services")
        - Creates a status container for feedback
        - Calls `statusButtonTop()` to show top-row service pills and status buttons
        - Renders detailed service expanders for:
            - Redis
            - Mongo
            - Registry
            - Syncer
            - Manager

        Returns:
            None
        """
        # Header for the detailed services
        st.header("Manager Services")

        # Create the status container for the services
        status_container = st.status("Manager Services", expanded=False, state="complete")
        # with st.expander("Manager Services Status", expanded=False):
        self.statusButtonTop()
        # Call the serviceExpander for each service
        with st.container():
            self.serviceExpander("Redis", status_container)
            self.serviceExpander("Mongo", status_container)
            self.serviceExpander("Registry", status_container)
            self.serviceExpander("Syncer", status_container)
            self.serviceExpander("Manager", status_container)

mn = ManagerService()
mn.manager()
