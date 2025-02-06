import yaml,time, sys,os
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
from gustavo.pages.config.SyncerConfig import SyncerConfig
sidebarInit()
from src.Manager import Manager

def load_css(file_name):
    """Load CSS from a file and inject into Streamlit."""
    with open(file_name) as f:
        css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

parent = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
css_url = os.path.join(parent,"styles","style.css")
load_css(css_url)

class ManagerService:
    def __init__(self):
        self.man = Manager(mode="streamlit")
        self.redis_conf = {"REDIS_HOST": "",
                      "REDIS_PORT": "",
                      "REDIS_AUTH_TOKEN": "",
                      "REDIS_IMAGE": ""
                      }
        st.session_state["Redis_status"] = "Unknown"
        self.mongo_conf = {
            "MONGO_HOST": "",
            "MONGO_PORT": "",
            "MONGO_USERNAME": "",
            "MONGO_PASSWORD":"",
            "MONGO_CERTIFICATE_FOLDER_PATH":""
        }
        st.session_state["Mongo_status"] = "Unknown"
        self.registry_conf = {
            "REGISTRY_HOST":"",
            "REGISTRY_PORT":"",
            "REGISTRY_IMAGE":""
        }
        st.session_state["Registry_status"] = "Unknown"
        self.syncer_conf = {
            "SYNCER_IMAGE": "",
            "DREGSY_CONFIG_FILE_PATH":"",
            "DREGSY_MAPPING_FILE_PATH":""
        }
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

    def status_circle(self, status):
        """Returns an HTML string that applies the correct CSS class based on the status."""
        css_class = "status-unknown"  # Default for Unknown
        if status == "Up":
            css_class = "status-up"
        elif status == "Down":
            css_class = "status-down"
        
        # Return the HTML that uses the CSS class for the circle
        return f'<span class="status-circle {css_class}"></span>'


    def statusUpdate(self):
        with st.container():
            redis, mongo, registry, manager, syncer = st.columns([50, 50, 50, 50, 50], gap="large")
            with redis:
                if st.session_state["Redis_status"] == "Up":
                    st.success("Up")
                else:
                    st.error("Down")

    def status_pill(self, status):
        if status == "Up":
            return '<div style="background-color: #9beba1; color: white; border-radius: 12px; padding: 5px 10px;">Up</div>'
        elif status == "Down":
            return '<div style="background-color: #f37e7a; color: white; border-radius: 12px; padding: 5px 10px;">Down</div>'
        else:
            return '<div style="background-color: #ffcc49; color: black; border-radius: 12px; padding: 5px 10px;">Unknown</div>'
    
    
    def obtainManagerConf(self):
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

        return [self.registry_conf]

    def obtainMongoConf(self):
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

        return [self.redis_conf]

    def serviceExpander(self, service_name, status_container):
        """Renders the expander for a given service, including status, launch, and remove buttons."""
        
        
        # Define the session key for service status at the top
        service_name_status = f'{service_name}_status'
        
        with st.expander(service_name, expanded=True):
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
                
            # Launch button logic
            with launch:
                launch_session_key = f'{service_name}_launch_clicked'
                if launch_session_key not in st.session_state:
                    st.session_state[launch_session_key] = False

                def set_launch_clicked():
                    st.session_state[launch_session_key] = not st.session_state[launch_session_key]

                st.button("Launch 🚀", on_click=set_launch_clicked, key=f"{service_name}_launch_button")

                if st.session_state[launch_session_key]:
                    with status_container:
                        status_container.write(f"Launching {service_name}...")
                        result = self.man.run(service_name.lower())
                        if not result["error"]:
                            st.session_state[service_name_status] = "Up"
                            status_container.markdown(f":green[{service_name} is Up]")
                        else:
                            st.session_state[service_name_status] = "Down"
                            # st.write(result["response"])
                            status_container.markdown(f":red[Error while launching {service_name}]")
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
                    st.session_state[remove_session_key] = False

    def statusButton(self, service_name, status_container, suffix=""):
        """Encapsulates the status button logic and status circle update, with a unique key suffix."""
        
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
            with status_container:

                # Check the service status
                result = self.man.serviceStatus(service_name.lower())
                if result["error"]:
                    st.session_state[service_name_status] = "Down"
                    # st.write(result["response"])
                    # status_container.markdown(f":red[{service_name} is not running 🚨]")  # Use markdown to format text in color
                else:
                    # st.section_state[service_name_status] = "Up"
                    # st.write(result["response"])
                    # status_container.markdown(f":green[{service_name} is running ✅]")

                    # Additional check for Manager API if it's the Manager service
                    if service_name == "Manager":
                        # st.write("Checking if Manager API is available")
                        
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
                                # st.write(result["response"])
                                # status_container.markdown(f":red[Manager API is not available 🚨]")
                            elif 'status' in result and result["status"] == "unknown":
                                st.session_state["Manager_status"] = "Unknown"
                                # status_container.markdown(f":orange[Manager API status is unknown ❓]")
                            else:
                                st.session_state["Manager_status"] = "Up"
                                # st.write(result["response"])
                                # status_container.markdown(f":green[Manager API Live! 🚀]")


                    else:
                        st.session_state[service_name_status] = "Up"
                        # status_container.markdown(f":green[{service_name} is running ✅]")

    def statusButtonTop(self):
        """Renders the top status buttons with individual boxes for each service."""
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
