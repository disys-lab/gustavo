import streamlit as st
from urllib.error import URLError
import pandas as pd
# from pages.Sidebar import Sidebar
import yaml, os
import socket,os
from gustavo.src.Composer import Composer

def checkSocket(ip,port):
    timeout=5.0
    if "SOCKET_TIMEOUT" in os.environ.keys():
        timeout = float("SOCKET_TIMEOUT")
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    a_socket.settimeout(timeout)
    location = (ip, int(port))
    check = a_socket.connect_ex(location)

    return check

def checkRegistryStatus():
    if "REGISTRY_HOST" not in st.session_state.keys():
        st.error('REGISTRY_HOST undefined', icon="🚨")
        return False

    elif "REGISTRY_PORT" not in st.session_state.keys():
        st.error('REGISTRY_PORT undefined', icon="🚨")
        return False

    else:
        check = True
        with st.spinner(
                "Checking reachability of {}:{}".format(st.session_state.REGISTRY_HOST,
                                                        st.session_state.REGISTRY_PORT)):
            try:
                check = checkSocket(st.session_state.REGISTRY_HOST, st.session_state.REGISTRY_PORT)
            except Exception as e:
                st.error("Registry connection encountered an error {}".format(str(e)))
            if check:
                st.error(
                    "Unable to reach {}:{}".format(st.session_state.REGISTRY_HOST, st.session_state.REGISTRY_PORT),
                    icon="🚨")
        return not check

def refresh_registry():

    if "registry_dict_list" not in st.session_state:
        st.session_state.registry_dict_list = []
    if "registry_name_list" not in st.session_state:
        st.session_state.registry_name_list = []
    bcmp = Composer(mode="streamlit", params=st.session_state)

    try:
        r = bcmp.checkLocalRepoImages("all", "all")
        if not r["error"]:
            rep_name_list = r["response"]["repositories"]
            st.session_state.registry_name_list = rep_name_list
            rep_dict_list = []
            for rep in rep_name_list:
                r = bcmp.checkLocalRepoImages(rep, "all")
                if not r["error"]:
                    rep_dict_list.append(r["response"])
                else:
                    st.error(
                        "rep:{} registry@{}:{} responded with status {}".format(rep,st.session_state.REGISTRY_HOST,
                                                                st.session_state.REGISTRY_PORT,
                                                                r["response"]["status"]),
                        icon="🚨")
            st.session_state.registry_dict_list = rep_dict_list
        else:
            st.error(
                "registry@{}:{} responded with status {}".format(st.session_state.REGISTRY_HOST, st.session_state.REGISTRY_PORT,r["response"]["status"]),
                icon="🚨")
    except Exception as e:
        st.exception(e)


class SyncerConfig:
    def __init__(self):
        self.hosts_list = {}

        if "REGISTRY_IP" not in st.session_state:
            REGISTRY_IP = "127.0.0.1"
        else:
            REGISTRY_IP = st.session_state["REGISTRY_HOST"]

        if "REGISTRY_PORT" not in st.session_state:
            REGISTRY_PORT = "5000"
        else:
            REGISTRY_PORT = st.session_state["REGISTRY_PORT"]

        self.dregsy_conf = {'relay': 'skopeo',
                   'skopeo': {'binary': 'skopeo', 'certs-dir': '/etc/skopeo/certs.d'},
                   'docker': {'dockerhost': 'unix:///var/run/docker.sock', 'api-version': 1.24},
                   'tasks': [{'name': 'task1', 'interval': 30, 'verbose': True, 'source': {'registry': 'registry.hub.docker.com', 'auth': ''},
                              'target': {'registry': '{}:{}'.format(REGISTRY_IP,REGISTRY_PORT), 'skip-tls-verify': True}, 'mappings_file': '/mappings_list.yaml'}]}
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

    def save_mappings_list(self,key,filepathkey=None):

        # self.mappings_list = st.session_state.mappings_list
        yaml_map_list = ""
        if key in st.session_state.keys():
            yaml_map_list = yaml.dump(st.session_state[key],default_flow_style=None, sort_keys=False)

        if filepathkey in st.session_state.keys() and yaml_map_list != "":
            map_file = os.path.expanduser(st.session_state[filepathkey])
            with open(map_file, "w") as text_file:
                text_file.write(yaml_map_list)

        return yaml_map_list

    def save_params(self,key,filepathkey=None):
        # self.mappings_list = st.session_state.mappings_list
        yaml_map_list = ""
        if key in st.session_state.keys():
            yaml_map_list = yaml.dump(st.session_state[key])

        if filepathkey in st.session_state.keys() and yaml_map_list != "":
            print(st.session_state[filepathkey])
            with open(os.path.expanduser(st.session_state[filepathkey]), "w") as text_file:
                text_file.write(yaml_map_list)

        return yaml_map_list

    def process_uploaded_file(self,uploaded_file,key):
        temp_hosts_dict = yaml.load(uploaded_file,Loader=yaml.Loader)
        print(temp_hosts_dict)
        self.mappings_list= temp_hosts_dict
        st.session_state[key] = temp_hosts_dict

    def syncerMappings(self):
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

                st.button('Upload Configuration 📤', on_click=set_syncer_load_config_clicked,key="syncer_map_load_button_widget_key")
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

                check = True
                if os.path.isdir(os.path.dir(os.path.expanduser(st.session_state.DREGSY_MAPPING_FILE_PATH))):
                    check = False
                st.button("Save Configuration 💾", on_click=set_syncer_save_config_clicked, key="syncer_map_save_button_widget_key",disabled = check)

                if st.session_state.syncer_save_config_clicked:
                    global_platform_env_file_str = self.save_mappings_list("mappings_list","DREGSY_MAPPING_FILE_PATH")
                    st.session_state.syncer_save_config_clicked = False

            with download_config:
                # print(global_platform_env_file_str)
                st.download_button(
                    label="Download Configuration ⬇️",
                    data=self.save_mappings_list("mappings_list"),
                    file_name='mappings_list.yaml',
                    mime='text',
                    key="syncer_map_download_button_widget_key"
                )

            #TODO: mixing data types makes the column uneditable.
            #TODO: we have lists with strings, thats why right now num rows are fixed as opposed to dynamic
            mapping_list = st.data_editor(st.session_state["mappings_list"]["mappings"]
                                            , num_rows="fixed", use_container_width=True,
                                        key="MAPPINGS_CONFIG_EDITOR")

            st.session_state["mappings_list"]["mappings"] = mapping_list

    def syncerConfigs(self):



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

                check = True
                if os.path.isdir(os.path.dir(os.path.expanduser(st.session_state.DREGSY_CONFIG_FILE_PATH))):
                    check = False

                st.button("Save Configuration 💾", on_click=set_syncer_task_save_config_clicked,key="SYNCER_TASK_SAVE",disabled=check)


                if st.session_state.syncer_task_save_config_clicked:
                    global_platform_env_file_str = self.save_params("dregsy_conf","DREGSY_CONFIG_FILE_PATH")
                    st.session_state.syncer_task_save_config_clicked = False

            with download_config:
                # print(global_platform_env_file_str)
                st.download_button(
                    label="Download Configuration ⬇️",
                    data=self.save_params("dregsy_conf"),
                    file_name='dregsy_conf.yaml',
                    mime='text',
                    key="syncer_task_download_button_widget_key"
                )

            if "REGISTRY_HOST" not in st.session_state:
                REGISTRY_IP = "127.0.0.1"
            else:
                REGISTRY_IP = st.session_state["REGISTRY_HOST"]

            if "REGISTRY_PORT" not in st.session_state:
                REGISTRY_PORT = "5000"
            else:
                REGISTRY_PORT = st.session_state["REGISTRY_PORT"]

            # if "dregsy_conf" in st.session_state.keys():
            st.session_state["dregsy_conf"]["tasks"][0]["target"]["registry"] = '{}:{}'.format(REGISTRY_IP,
                                                                                               REGISTRY_PORT)
            st.session_state["dregsy_vars"] = self.getTaskConfig(st.session_state["dregsy_conf"])

            st.session_state["dregsy_vars"] = self.getTaskConfig(st.session_state["dregsy_conf"])
            task_conf = st.data_editor(st.session_state["dregsy_vars"],
                                     num_rows="fixed", use_container_width=True,
                                     key="TASKS_CONFIG_EDITOR")

            st.session_state["dregsy_vars"] = task_conf
            st.session_state["dregsy_conf"] = self.setTaskConfig(task_conf,st.session_state["dregsy_conf"])

    def syncer(self):
        self.syncerMappings()
        self.syncerConfigs()


