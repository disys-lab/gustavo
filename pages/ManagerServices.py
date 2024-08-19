import yaml,time, sys,os
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
# from pages.Sidebar import Sidebar
from src.Manager import Manager

parent = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
logo_url = os.path.join(parent,"images","gustavo_bw.png")
st.logo(logo_url)

with st.sidebar:
    st.text("Gustavo Admin Tool")

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

    def statusUpdate(self):
        with st.container():
            redis, mongo, registry, manager, syncer = st.columns([50, 50, 50, 50, 50], gap="large")
            with redis:
                if st.session_state["Redis_status"] == "Up":
                    st.success("Up")
                else:
                    st.error("Down")

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
            if os.path.isfile(self.syncer_conf["DREGSY_CONFIG_FILE_PATH"]):
                st.success("Valid DREGSY_CONFIG_FILE_PATH")
                st.session_state.DREGSY_CONFIG_FILE_PATH = st.session_state.DREGSY_CONFIG_FILE_PATH
            else:
                st.error("Invalid DREGSY_CONFIG_FILE_PATH")

        if "DREGSY_MAPPING_FILE_PATH" not in st.session_state.keys():
            self.syncer_conf["DREGSY_MAPPING_FILE_PATH"] = "Undefined"
        else:
            self.syncer_conf["DREGSY_MAPPING_FILE_PATH"] = st.session_state.DREGSY_MAPPING_FILE_PATH
            self.man.DREGSY_MAPPING_FILE_PATH = st.session_state.DREGSY_MAPPING_FILE_PATH
            if os.path.isfile(self.syncer_conf["DREGSY_MAPPING_FILE_PATH"]):
                st.success("Valid DREGSY_MAPPING_FILE_PATH")
                st.session_state.DREGSY_MAPPING_FILE_PATH = self.syncer_conf["DREGSY_MAPPING_FILE_PATH"]
            else:
                st.error("Invalid DREGSY_MAPPING_FILE_PATH {}".format(self.syncer_conf["DREGSY_MAPPING_FILE_PATH"]))

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

    def serviceExpander(self,service_name,status_container):
        with st.expander(service_name, expanded=True):
            data_editor_widget_key = service_name+"_"+"data_editor"
            status_button_widget_key = service_name+"_"+"status_button"
            launch_button_widget_key = service_name + "_" + "launch_button"
            remove_button_widget_key = service_name + "_" + "remove_button"
            service_name_status = '{}_status'.format(service_name)
            if service_name == "Manager":
                conf = self.obtainManagerConf()
            if service_name == "Redis":
                conf = self.obtainRedisConf()
            if service_name == "Mongo":
                conf = self.obtainMongoConf()
            if service_name == "Registry":
                conf = self.obtainRegistryConf()
            if service_name == "Syncer":
                config_file_path, mapping_file_path = st.columns([50, 50], gap="large")
                if "DREGSY_CONFIG_FILE_PATH" in st.session_state.keys():
                    self.syncer_conf["DREGSY_CONFIG_FILE_PATH"] = st.session_state.DREGSY_CONFIG_FILE_PATH

                if "DREGSY_MAPPING_FILE_PATH" in st.session_state.keys():
                    self.syncer_conf["DREGSY_MAPPING_FILE_PATH"] = st.session_state.DREGSY_MAPPING_FILE_PATH

                with config_file_path:
                    st.session_state.DREGSY_CONFIG_FILE_PATH = st.text_input("SYNCER_CONFIG_PATH",
                                                                                self.syncer_conf["DREGSY_CONFIG_FILE_PATH"],
                                                                key="SYNCER_CONFIG_PATH_WIDGET_KEY")

                with mapping_file_path:
                    st.session_state.DREGSY_MAPPING_FILE_PATH = st.text_input("SYNCER_MAPPING_PATH",
                                                                              self.syncer_conf["DREGSY_MAPPING_FILE_PATH"],
                                                                             key="SYNCER_MAPPING_PATH_WIDGET_KEY")
                conf = self.obtainSyncerConf()
            st.data_editor(conf, disabled=True, num_rows="fixed", use_container_width=True, key=data_editor_widget_key)

            status, launch, kill = st.columns([50, 50, 50], gap="large")
            status_session_key = '{}_status_clicked'.format(service_name)
            launch_session_key = '{}_launch_clicked'.format(service_name)
            remove_session_key = '{}_remove_clicked'.format(service_name)

            with status:
                if status_session_key not in st.session_state:
                    st.session_state[status_session_key] = False

                def set_redis_status_clicked():
                    st.session_state[status_session_key] = not (st.session_state[status_session_key])

                st.button('Status 📈', on_click=set_redis_status_clicked,key=status_button_widget_key)
                if st.session_state[status_session_key]:
                    with status_container:
                        status_container.update(label="Checking {} Status".format(service_name), expanded=True, state="running")
                        st.write("Checking for {} Container".format(service_name))
                        result = self.man.serviceStatus(service_name.lower())
                        if result["error"]:
                            st.session_state[service_name_status] = "Down"
                            st.write(result["response"])
                            status_container.update(label=":red[{} is not running]".format(service_name),
                                                    expanded=True, state="error")
                        else:
                            st.write(result["response"])
                            status_container.update(label=":green[{} is running]".format(service_name), expanded=True,
                                                    state="complete")

                            if service_name == "Manager":
                                st.write("Checking if Manager API is available")
                                result = self.man.checkManager()
                                if result["error"]:
                                    st.session_state[service_name_status] = "Down"
                                    st.write(result["response"])
                                    status_container.update(label=":red[{} API is not available]".format(service_name),
                                                            expanded=True, state="error")
                                else:
                                    st.session_state[service_name_status] = "Up"
                                    st.write(result["response"])
                                    status_container.update(label=":green[{} API Live!]".format(service_name),
                                                            expanded=True,
                                                            state="complete")
                            else:
                                st.session_state[service_name_status] = "Up"
                    st.session_state[status_session_key] = False

            with launch:
                if launch_session_key not in st.session_state:
                    st.session_state[launch_session_key] = False

                def set_redis_launch_clicked():
                    st.session_state[launch_session_key] = not (st.session_state[launch_session_key])

                st.button("Launch 🚀", on_click=set_redis_launch_clicked,key=launch_button_widget_key)
                if st.session_state[launch_session_key]:
                    with status_container:
                        status_container.update(label="Launching {}".format(service_name), expanded=True, state="running")
                        result = self.man.run(service_name.lower())
                        if not result["error"]:
                            st.session_state[service_name_status] = "Up"
                            print(service_name_status)
                            status_container.update(label=":green[{} is Up]".format(service_name), expanded=True,
                                                    state="complete")

                        # elif :
                        #     st.session_state[service_name_status] = "Down"
                        #     st.write(result["response"])
                        #     status_container.update(label=":red[Errors encountered while launching {}]".format(service_name),
                        #                             expanded=True, state="error")
                        else:
                            st.session_state[service_name_status] = "Down"
                            st.write(result["response"])
                            status_container.update(
                                label=":red[Unhandled Exception error encountered while launching {}]".format(service_name),
                                expanded=True,
                                state="complete")
                    st.session_state[launch_session_key] = False
            with kill:
                if remove_session_key not in st.session_state:
                    st.session_state[remove_session_key] = False

                def set_redis_kill_clicked():
                    st.session_state[remove_session_key] = not (st.session_state[remove_session_key])

                st.button("Remove 🛑", on_click=set_redis_kill_clicked,key=remove_button_widget_key)
                if st.session_state[remove_session_key]:
                    with status_container:
                        status_container.update(label="Removing {}".format(service_name), expanded=True, state="running")
                        # st.write("")
                        # time.sleep(2)
                        result = self.man.handleService(service_name.lower(), "remove")
                        if not result["error"]:
                            st.session_state[service_name_status] = "Down"
                            st.write(result["response"])
                            status_container.update(label=":green[{} is brought down]".format(service_name), expanded=True,
                                                    state="complete")
                        elif "error" in result.keys():
                            st.write(result["response"])
                            status_container.update(label=":red[Errors encountered while killing {}]".format(service_name),
                                                    expanded=True, state="error")
                        else:
                            st.write(result["response"])
                            status_container.update(
                                label=":red[Unhandled Exception error encountered while launching {}]".format(service_name),
                                expanded=True,
                                state="complete")
                    st.session_state[remove_session_key] = False

    def manager(self):
        st.header("Manager Services")



        status_container = st.status("Manager Services", expanded=False, state="complete")
        with st.container():
            self.serviceExpander("Redis",status_container)
            self.serviceExpander("Mongo",status_container)
            self.serviceExpander("Registry", status_container)
            self.serviceExpander("Syncer", status_container)
            self.serviceExpander("Manager",status_container)

# st.set_page_config(
#     layout="wide",
#     initial_sidebar_state="expanded"
# )
#
# sb = Sidebar()
mn = ManagerService()
mn.manager()
