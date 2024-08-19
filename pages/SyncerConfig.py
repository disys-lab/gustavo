import streamlit as st
from urllib.error import URLError
import pandas as pd
from pages.Sidebar import Sidebar
import yaml

class SyncerConfig:
    def __init__(self):
        self.hosts_list = {}
        self.dregsy_conf = {'relay': 'skopeo',
                   'skopeo': {'binary': 'skopeo', 'certs-dir': '/etc/skopeo/certs.d'},
                   'docker': {'dockerhost': 'unix:///var/run/docker.sock', 'api-version': 1.24},
                   'tasks': [{'name': 'task1', 'interval': 30, 'verbose': True, 'source': {'registry': 'registry.hub.docker.com', 'auth': ''},
                              'target': {'registry': '172.31.17.1:5000', 'skip-tls-verify': True}, 'mappings_file': '/mappings_list.yaml'}]}
        self.mappings_list = {'mappings': [{'from': 'homert2admin/environment_algorithm1', 'to': 'environment_algorithm1', 'tags': ['latest']}, {'from': 'homert2admin/eclss_algorithm3', 'to': 'eclss_algorithm3', 'tags': ['latest']}, {'from': 'homert2admin/eclss_algorithm2', 'to': 'eclss_algorithm2', 'tags': ['latest']}, {'from': 'homert2admin/eclss_algorithm1', 'to': 'eclss_algorithm1', 'tags': ['latest']}, {'from': 'homert2admin/eps_algorithm1', 'to': 'eps_algorithm1', 'tags': ['latest']}, {'from': 'homert2admin/robotics_algorithm1', 'to': 'robotics_algorithm1', 'tags': ['latest']}]}

        if "visibility" not in st.session_state:
            st.session_state.visibility = "visible"
            st.session_state.disabled = False
        if "dregsy_vars" not in st.session_state.keys():
            st.session_state["dregsy_vars"] = self.getTaskConfig(self.dregsy_conf)
        if "dregsy_conf" not in st.session_state.keys():
            st.session_state["dregsy_conf"] = self.dregsy_conf
        if "mappings_list" not in st.session_state.keys():
            st.session_state["mappings_list"] = self.mappings_list

    def getTaskConfig(self,task_dict):
        task_config = [{"Name": task_dict["tasks"][0]["name"],
            "Interval": task_dict["tasks"][0]["interval"],
            "Source Registry": task_dict["tasks"][0]["source"]["registry"],
            "Source Auth": task_dict["tasks"][0]["source"]["auth"],
            "Target Registry": task_dict["tasks"][0]["target"]["registry"],
            "Target Skip TLS": task_dict["tasks"][0]["target"]["skip-tls-verify"]
            }]
        return task_config

    def setTaskConfig(self,task_config,task_dict):
        task_dict["tasks"][0]["name"] = task_config[0]["Name"]
        task_dict["tasks"][0]["interval"] = task_config[0]["Interval"]
        task_dict["tasks"][0]["source"]["registry"] = task_config[0]["Source Registry"]
        task_dict["tasks"][0]["source"]["auth"] = task_config[0]["Source Auth"]
        task_dict["tasks"][0]["target"]["registry"] = task_config[0]["Target Registry"]
        task_dict["tasks"][0]["target"]["skip-tls-verify"] = task_config[0]["Target Skip TLS"]

        return task_dict

    def save_mappings_list(self,key):
        # self.mappings_list = st.session_state.mappings_list
        yaml_map_list = ""
        if key in st.session_state.keys():
            yaml_map_list = yaml.dump(st.session_state[key],default_flow_style=None, sort_keys=False)

        return yaml_map_list

    def save_params(self,key):
        # self.mappings_list = st.session_state.mappings_list
        yaml_map_list = ""
        if key in st.session_state.keys():
            yaml_map_list = yaml.dump(st.session_state[key])
        return yaml_map_list

    def process_uploaded_file(self,uploaded_file,key):
        temp_hosts_dict = yaml.load(uploaded_file,Loader=yaml.Loader)
        print(temp_hosts_dict)
        self.mappings_list= temp_hosts_dict
        st.session_state[key] = temp_hosts_dict

    def syncer(self):
        #st.header("Syncer Configuration")
        # st.divider()
        with st.container():
            st.subheader("Syncer Mappings")
            load_config, save_config, download_config = st.columns([50, 50, 50], gap="large")
            with load_config:
                if 'syncer_load_config_clicked' not in st.session_state:
                    st.session_state.syncer_load_config_clicked = False

                def set_syncer_load_config_clicked():
                    st.session_state.syncer_load_config_clicked = not (st.session_state.syncer_load_config_clicked)

                st.button('Upload Configuration 📤', on_click=set_syncer_load_config_clicked)
                if st.session_state.syncer_load_config_clicked:
                    uploaded_env_file = st.file_uploader("Upload Configuration File", type=[".yaml",".yml"],key="SYNCER_MAPPINGS_UPLOAD")
                    if uploaded_env_file is not None:
                        self.process_uploaded_file(uploaded_env_file,"mappings_list")
                        #self.edited_df.update(temp_df)

            with save_config:
                if 'syncer_save_config_clicked' not in st.session_state:
                    st.session_state.syncer_save_config_clicked = False

                def set_syncer_save_config_clicked():
                    st.session_state.syncer_save_config_clicked = True  # not(st.session_state.save_config_clicked)

                st.button("Save Configuration 💾", on_click=set_syncer_save_config_clicked)
                if st.session_state.syncer_save_config_clicked:
                    global_platform_env_file_str = self.save_mappings_list("mappings_list")
                    st.session_state.syncer_save_config_clicked = False

            with download_config:
                # print(global_platform_env_file_str)
                st.download_button(
                    label="Download Configuration ⬇️",
                    data=self.save_mappings_list("mappings_list"),
                    file_name='mappings_list.yaml',
                    mime='text',
                )

            #TODO: mixing data types makes the column uneditable.
            #TODO: we have lists with strings, thats why right now num rows are fixed as opposed to dynamic
            mapping_list = st.data_editor(st.session_state["mappings_list"]["mappings"]
                                            , num_rows="fixed", use_container_width=True,
                                        key="MAPPINGS_CONFIG_EDITOR")

            st.session_state["mappings_list"]["mappings"] = mapping_list

        with st.container():
            st.subheader("Syncer Task")
            load_config, save_config, download_config = st.columns([50, 50, 50], gap="large")
            with load_config:
                if 'syncer_task_load_config_clicked' not in st.session_state:
                    st.session_state.syncer_task_load_config_clicked = False

                def set_syncer_task_load_config_clicked():
                    st.session_state.syncer_task_load_config_clicked = not (st.session_state.syncer_task_load_config_clicked)

                st.button('Upload Configuration 📤', on_click=set_syncer_task_load_config_clicked,key="SYNCER_TASK_UPLOAD")
                if st.session_state.syncer_task_load_config_clicked:
                    uploaded_env_file = st.file_uploader("Upload Configuration File", type=[".yaml", ".yml"],key="SYNCER_TASK_FILE_UPLOADER")
                    if uploaded_env_file is not None:
                        self.process_uploaded_file(uploaded_env_file,"dregsy_conf")
                        # self.edited_df.update(temp_df)

            with save_config:
                if 'syncer_task_save_config_clicked' not in st.session_state:
                    st.session_state.syncer_task_save_config_clicked = False

                def set_syncer_task_save_config_clicked():
                    st.session_state.syncer_task_save_config_clicked = True  # not(st.session_state.save_config_clicked)

                st.button("Save Configuration 💾", on_click=set_syncer_task_save_config_clicked,key="SYNCER_TASK_SAVE")
                if st.session_state.syncer_task_save_config_clicked:
                    global_platform_env_file_str = self.save_params("dregsy_conf")
                    st.session_state.syncer_task_save_config_clicked = False

            with download_config:
                # print(global_platform_env_file_str)
                st.download_button(
                    label="Download Configuration ⬇️",
                    data=self.save_params("dregsy_conf"),
                    file_name='dregsy_conf.yaml',
                    mime='text',
                )
            task_conf = st.data_editor(st.session_state["dregsy_vars"],
                                     num_rows="fixed", use_container_width=True,
                                     key="TASKS_CONFIG_EDITOR")

            st.session_state["dregsy_vars"] = task_conf
            #print(st.session_state["dregsy_conf"])
            st.session_state["dregsy_conf"] = self.setTaskConfig(task_conf,st.session_state["dregsy_conf"])

# st.set_page_config(
#
#     layout="wide",
#     initial_sidebar_state="expanded"
#
# )

sb = Sidebar()
sy = SyncerConfig()
sy.syncer()
#


