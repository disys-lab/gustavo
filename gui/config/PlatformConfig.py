import streamlit as st
from urllib.error import URLError
import pandas as pd

class PlatformConfig:
    def __init__(self):

        self.platform_config = {
                            "REGISTRY_HOST":"172.31.18.128",
                            "REGISTRY_PORT":"5000",
                            "REGISTRY_IMAGE":"registry:2",
                            "SYNCER_IMAGE":"blockalytics/dregsy:latest",
                            "SYNCER_NMODE":"host",
                            "REDIS_HOST":"172.31.18.128",
                            "REDIS_PORT":"6379",
                            "REDIS_AUTH_TOKEN":"e87052bfcc0b65b2d0603ad4baa8d8ced7aa929b6698a568d2ce53dfd2dc04bcs",
                            "REDIS_IMAGE":"blockalytics/redis",
                            "MANAGER_HOST":"172.31.18.128",
                            "MANAGER_PORT":"80",
                            "CACHE_EXPIRE_TIME":"3600",
                            "MANAGER_IMAGE":"blockalytics/manager:2.6.3",
                            "MANAGER_NMODE":"host",
                            "MONGO_HOST":"172.31.18.128",
                            "MONGO_PORT":"27017",
                            "MONGO_USERNAME":"nebula",
                            "MONGO_PASSWORD":"nebula",
                            "MONGO_CERTIFICATE_FOLDER_PATH":"/tmp/",
                            "MONGO_IMAGE":"mongo:4.0.19",
                            "NEBULA_USERNAME":"nebula",
                            "NEBULA_PASSWORD":"nebula",
                            "NEBULA_AUTH_TOKEN":"e87052bfcc0b65b2d0603ad4baa8d8ced7aa929b6698a568d2ce53dfd2dc04bcs",
                        }

        self.platform_config_keys = self.platform_config.keys()

        self.global_platform_env_file_str=""

        if "visibility" not in st.session_state:
            st.session_state.visibility = "visible"
            st.session_state.disabled = False

            st.session_state.MANAGER_HOST = "172.31.18.128"
            st.session_state.MANAGER_PORT = "80"

            st.session_state.REGISTRY_HOST = "172.31.18.128"
            st.session_state.REGISTRY_PORT = "5000"
            #
            # DREGSY_CONFIG_FILE_PATH=/home/ubuntu/workshop_demo/dregsy_conf.yml
            # DREGSY_MAPPING_FILE_PATH=/home/ubuntu/workshop_demo/mappings_list.yml

            st.session_state.REDIS_HOST = "172.31.18.128"
            st.session_state.REDIS_PORT = "6379"
            st.session_state.REDIS_AUTH_TOKEN = "e87052bfcc0b65b2d0603ad4baa8d8ced7aa929b6698a568d2ce53dfd2dc04bcs"
            # st.session_state.REDIS_EXPIRE_TIME=10
            # st.session_state.REDIS_KEY_PREFIX="nebula-reports"

            st.session_state.CACHE_EXPIRE_TIME = "120"

            st.session_state.MONGO_HOST = "172.31.18.128"
            st.session_state.MONGO_PORT = "27017"
            st.session_state.MONGO_USERNAME = "nebula"
            st.session_state.MONGO_PASSWORD = "nebula"
            st.session_state.MONGO_CERTIFICATE_FOLDER_PATH = "/tmp/"

            st.session_state.NEBULA_USERNAME = "nebula"
            st.session_state.NEBULA_PASSWORD = "nebula"
            st.session_state.NEBULA_AUTH_TOKEN = "bmVidWxhOm5lYnVsYQ=="

            # KEYGEN_ADD_ACC_ID=34b683d0-6121-4a5a-ac92-ee6320611484
            # KEYGEN_USER_ID=0cf72126-2151-4f14-a960-bd72d33f5716
            # KEYGEN_USER_TOKEN=user-5881c1fac7b8e6242a0c2b4558d89d03f78f08dff96980d7a4fc72980b7c53eav3
            # KEYGEN_PUBLIC_KEY=06ede5b6f133fc291d1b7bb195a105756f8aa484bdba8a0d6ef8d5ea1f26a1bc

            # docker image details

            st.session_state.REGISTRY_IMAGE = "registry:2"
            st.session_state.SYNCER_IMAGE = "blockalytics/dregsy:latest"
            st.session_state.REDIS_IMAGE = "blockalytics/redis"
            st.session_state.MONGO_IMAGE = "mongo:4.0.19"
            st.session_state.MANAGER_IMAGE = "blockalytics/manager:2.6.3"

            # network mode
            st.session_state.MANAGER_NMODE = "host"
            st.session_state.WORKER_NMODE = "host"
            st.session_state.SYNCER_NMODE = "host"

    def textChange(self,key):
        self.platform_config[key]=st.session_state[key]

    def save_params(self):
        file_str=""
        for config_var in self.platform_config.keys():
            file_str=file_str+"{}={}\n".format(config_var,st.session_state[config_var])
            self.platform_config[config_var] = st.session_state[config_var]
        return file_str

    def process_uploaded_file(self,uploaded_file):
        env_vars = []
        # with open(uploaded_file, encoding='utf8') as f:
        for line in uploaded_file:
                if line.startswith(b'#') or not line.strip():
                    continue
                key, value = line.strip().split(b'=', 1)
                env_vars.append({'name': key.decode("utf8"), 'value': value.decode("utf8")})  # Save to a list
                st.session_state[key.decode("utf8")] = value.decode("utf8")

    def platform(self):
       # st.subheader("Platform Configuration")
       # st.divider()
       with st.container():
        load_config, save_config, download_config = st.columns([50,50,50])
        with load_config:
            if 'load_config_clicked' not in st.session_state:
                st.session_state.load_config_clicked = False

            def set_load_config_clicked():
                st.session_state.load_config_clicked = not(st.session_state.load_config_clicked)

            st.button('Upload Configuration File', on_click=set_load_config_clicked)
            if st.session_state.load_config_clicked:
                uploaded_env_file = st.file_uploader("Upload Configuration File", type=".env")
                if uploaded_env_file is not None:
                    process_uploaded_file(uploaded_env_file)

        with save_config:
            if 'save_config_clicked' not in st.session_state:
                st.session_state.save_config_clicked = False

            def set_save_config_clicked():
                st.session_state.save_config_clicked = True #not(st.session_state.save_config_clicked)

            st.button("Save Configuration", on_click=set_save_config_clicked)
            if st.session_state.save_config_clicked:
                global_platform_env_file_str = self.save_params()
                st.session_state.save_config_clicked = False

        with download_config:
            #print(global_platform_env_file_str)
            st.download_button(
                label="Download Configuration File",
                data=self.save_params(),
                file_name='manager.env',
                mime='text',
            )

       manager_col, mongo_col, redis_col, registry_col = st.columns(4)

       with manager_col:
         # st.checkbox("Disable text input widget", key="enabled")
         st.subheader("Manager")
         st.text_input(
          "Manager IP",
          st.session_state.MANAGER_HOST,
          key="MANAGER_HOST",
         )
         self.platform_config["MANAGER_PORT"]=st.text_input(
             "Manager Port",
             st.session_state.MANAGER_PORT,
             key="MANAGER_PORT",
         )
         self.platform_config["CACHE_EXPIRE_TIME"]=st.text_input(
             "Manager Cache Expire Time",
             3600,
             key="CACHE_EXPIRE_TIME",
         )
         self.platform_config["MANAGER_IMAGE"]=st.text_input(
             "Manager Container Image",
             st.session_state.MANAGER_IMAGE,
             key="MANAGER_IMAGE",
         )
         self.platform_config["MANAGER_NMODE"]=st.radio(
             "Select Manager Network Mode", horizontal=True,
             key="MANAGER_NMODE",
             options=["host", "bridge"],
         )
         self.platform_config["NEBULA_USERNAME"]=st.text_input(
             "Nebula Username",
             st.session_state.NEBULA_USERNAME,
             key="NEBULA_USERNAME",
         )
         self.platform_config["NEBULA_PASSWORD"]=st.text_input(
             "Nebula Password",
             st.session_state.NEBULA_PASSWORD,
             key="NEBULA_PASSWORD",
             type="password"
         )
         self.platform_config["NEBULA_AUTH_TOKEN"]=st.text_input(
             "Nebula Auth Token",
             st.session_state.NEBULA_AUTH_TOKEN,
             key="NEBULA_AUTH_TOKEN",
             type="password"
         )

       with registry_col:
        st.subheader("Registry")
        registry_eq_manager = st.toggle('Same as Manager IP',value=True,key="REGISTRY_EQ_MANAGER")
        registry_ip = self.platform_config["MANAGER_HOST"]
        if registry_eq_manager:
           registry_ip_disabled = True
        else:
           registry_ip_disabled = False
        self.platform_config["REGISTRY_HOST"]=st.text_input(
            "Registry Host",
            registry_ip,
            disabled=registry_ip_disabled,
            key="REGISTRY_HOST",
        )
        self.platform_config["REGISTRY_PORT"]=st.text_input(
            "Registry Port",
            st.session_state.REGISTRY_PORT,
            key="REGISTRY_PORT",
        )
        self.platform_config["REGISTRY_IMAGE"]=st.text_input(
            "Registry Container Image",
            st.session_state.REGISTRY_IMAGE,
            key="REGISTRY_IMAGE",
        )
        self.platform_config["SYNCER_IMAGE"]=st.text_input(
            "Syncer Container Image",
            st.session_state.SYNCER_IMAGE,
            key="SYNCER_IMAGE",
        )

       with mongo_col:
        st.subheader("Mongo")
        mongo_eq_manager = st.toggle('Same as Manager IP',key="MONGO_EQ_MANAGER",value=True)
        if mongo_eq_manager:
           mongo_ip = self.platform_config["MANAGER_HOST"]
           mongo_ip_disabled = True
        else:
           mongo_ip = ""
           mongo_ip_disabled = False

        self.platform_config["MONGO_HOST"]=st.text_input(
           "Mongo IP",
           mongo_ip,
           disabled=mongo_ip_disabled,
           key="MONGO_HOST",
        )
        self.platform_config["MONGO_PORT"]=st.text_input(
            "Mongo Port",
            st.session_state.MONGO_PORT,
            key="MONGO_PORT",
        )
        self.platform_config["MONGO_CERTIFICATE_FOLDER_PATH"]=st.text_input(
            "Mongo Certificate Folder Path",
            st.session_state.MONGO_CERTIFICATE_FOLDER_PATH,
            key="MONGO_CERTIFICATE_FOLDER_PATH",
        )
        self.platform_config["MONGO_USERNAME"]=st.text_input(
            "Mongo Username",
            st.session_state.MONGO_USERNAME,
            key="MONGO_USERNAME",
        )
        self.platform_config["MONGO_PASSWORD"]=st.text_input(
            "Mongo Password",
            st.session_state.MONGO_PASSWORD,
            key="MONGO_PASSWORD",
            type="password"
        )
        self.platform_config["MONGO_IMAGE"]=st.text_input(
            "Mongo Container Image",
            st.session_state.MONGO_IMAGE,
            key="MONGO_IMAGE",
        )

       with redis_col:
        st.subheader("Redis")
        redis_eq_manager = st.toggle('Same as Manager IP',value=True,key="REDIS_EQ_MANAGER")
        if redis_eq_manager:
            redis_ip = self.platform_config["MANAGER_HOST"]
            redis_ip_disabled = True
        else:
            redis_ip = self.platform_config["MANAGER_HOST"]
            redis_ip_disabled = False

        self.platform_config["REDIS_HOST"]=st.text_input(
           "Redis IP",
           redis_ip,
           disabled=redis_ip_disabled,
           key="REDIS_HOST",
        )
        self.platform_config["REDIS_PORT"]=st.text_input(
            "Redis Port",
            st.session_state.REDIS_PORT,
            key="REDIS_PORT",
        )
        self.platform_config["REDIS_AUTH_TOKEN"]=st.text_input(
            "Redis Auth Token",
            st.session_state.REDIS_AUTH_TOKEN,
            key="REDIS_AUTH_TOKEN",
            type="password"
        )
        self.platform_config["REDIS_IMAGE"]=st.text_input(
            "Redis Container Image",
            st.session_state.REDIS_IMAGE,
            key="REDIS_IMAGE",
        )

#


