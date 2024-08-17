import yaml,time, sys,os,copy
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gui.Sidebar import Sidebar
from src.Composer import Composer


class AppHandler:
    def __init__(self):
        if "app_list" in st.session_state:
            self.app_list = st.session_state.app_list
        else:
            self.app_list = []
            st.session_state.app_list = []


    def process_uploaded_file(self,uploaded_file):
        app_config = yaml.load(uploaded_file,Loader=yaml.Loader)
        #app_config= temp_dict
        appkeys = list(app_config.keys())
        app_name = appkeys[0]
        st.session_state["create"]["app_name"] = app_name
        st.session_state["create"]["form_values"] = {
                                                        "image": app_config[app_name]["docker_image"],
                                                        "env_vars": self.setEnvVars(app_config[app_name]),#[{"key":"","value":""}],
                                                        "networks": "nebula",
                                                        "volumes": self.setVolumes(app_config[app_name]),#[{"from": "", "to": ""}],
                                                        "ports": self.setPorts(app_config[app_name]), #[{"from":" ","to":""}],
                                                        "running": True,
                                                        "rolling_restart": True,
                                                        "containers_per": {"server": 1},
                                                        "privileged": False,
                                                        "device_groups": ",".join(app_config[app_name]["devices"])
                                                    }
        #st.session_state[appkeys[0]] = app_config
        print(st.session_state["create"]["form_values"])
        return app_config

    def setPorts(self,app_config):
        if "starting_ports" not in app_config:
            return [{"from":"","to":""}]
        ports_dict_list = []
        ports_list = app_config["starting_ports"]
        try:
            for p in ports_list:
                fromp = p.keys()[0]
                top = p[fromp]
                ports_dict_list.append({"from":fromp, "to":top})
        except Exception:
            pass
        if len(ports_dict_list) == 0:
            ports_dict_list = [{"from":"","to":""}]
        return ports_dict_list

    def getPorts(self,edited_ports):
        port_list = [{p["from"]: p["to"]} for p in edited_ports]
        return port_list

    def setVolumes(self,app_config):
        if "volumes" not in app_config:
            return [{"from":"","to":""}]
        volume_dict_list = []
        volume_list = app_config["volumes"]
        try:
            for v in volume_list:
                v_split = v.split(":",1)
                volume_dict_list.append({"from":v_split[0],"to":v_split[1]})
        except Exception:
            pass
        if len(volume_dict_list) == 0:
            volume_dict_list = [{"from":"","to":""}]
        return volume_dict_list

    def getVolumes(self,edited_volumes):
        volume_list = [v["from"] + ":" + v["to"] for v in edited_volumes]
        return volume_list

    def getEnvVars(self,edited_env_vars):
        env_var_dict = {}
        try:
            for ev in edited_env_vars:
                env_var_dict[ev["key"]] = ev["value"]
        except Exception:
            pass
        return env_var_dict

    def setEnvVars(self,app_config):
        if "env_vars" not in app_config:
            return [{"key":"","value":""}]
        env_var_dict = app_config["env_vars"]
        edited_env_vars = [] #[{"key": "", "value": ""}]
        for key in env_var_dict:
            edited_env_vars.append({"key":key,"value":env_var_dict[key]})
        if len(edited_env_vars) == 0:
            edited_env_vars = [{"key":"","value":""}]
        return edited_env_vars

    def appExpander(self,name,form_name):
        if "visibility" not in st.session_state:
            st.session_state.visibility = "visible"
            st.session_state.disabled = False
            st.session_state.app_list = []

        if name not in st.session_state:
            st.session_state[name] = {}
            st.session_state[name]["app_name"] = ""
            st.session_state[name]["form_values"] = {
                                                        "image": "",
                                                        "env_vars": [{"key":"","value":""}],
                                                        "networks": "nebula",
                                                        "volumes": [{"from": "", "to": ""}],
                                                        "ports": [{"from":" ","to":""}],
                                                        "running": True,
                                                        "rolling_restart": True,
                                                        "containers_per": {"server": 1},
                                                        "privileged": False,
                                                        "device_groups": ""
                                                    }
            st.session_state[name]["config"] = {
                                        "docker_image": "",
                                        "env_vars": {},
                                        "networks": [],
                                        "volumes": [],
                                        "starting_ports": [],
                                        "running": True,
                                        "rolling_restart": True,
                                        "containers_per": {"server": 1},
                                        "privileged": False,
                                        "devices": []
                                        }

        app_expander = st.expander(form_name, expanded=False)

        name_key = "name_key_{}".format(name)
        image_key = "image_key_{}".format(name)
        network_key = "network_key_{}".format(name)
        dg_key = "dg_key_{}".format(name)
        env_key = "env_key_{}".format(name)
        vol_key = "vol_key_{}".format(name)
        port_key = "port_key_{}".format(name)

        name_col,image_col,networks_col, dg_col = app_expander.columns([50,50,50,50],gap="small")
        with name_col:
            app_name = st.text_input("App Name",st.session_state[name]["app_name"],key=name_key)
            st.session_state[name]["app_name"] = app_name
        with image_col:
            image = st.text_input("Container Image",st.session_state[name]["form_values"]["image"],key=image_key)
            st.session_state[name]["config"]["docker_image"] = image
        with networks_col:
            networks = st.text_input("Network",st.session_state[name]["form_values"]["networks"],key=network_key)
            st.session_state[name]["config"]["networks"] = [networks]
        with dg_col:
            device_groups = st.text_input("Device Group (leave blank for default)",st.session_state[name]["form_values"]["device_groups"],key=dg_key)
            st.session_state[name]["config"]["devices"] = [devices for devices in device_groups.split(",")]
        env_col, vol_col, port_col= app_expander.columns([50, 50, 50], gap="small")
        with env_col:
            st.write("Env Vars")
            edited_env_vars = st.data_editor(st.session_state[name]["form_values"]["env_vars"], use_container_width=True, num_rows="dynamic", disabled=False,
                                         key=env_key,)
            st.session_state[name]["config"]["env_vars"] = self.getEnvVars(edited_env_vars)
        with vol_col:

            st.write("Volumes")
            edited_volumes = st.data_editor(st.session_state[name]["form_values"]["volumes"], use_container_width=True, num_rows="dynamic", disabled=False,
                                         key=vol_key)  # column_order=("env_var", "value"),column_config=st.column_config.NumberColumn("Dollar values”, format=”$ %d"))
            st.session_state[name]["config"]["volumes"] = self.getVolumes(edited_volumes)

        with port_col:
            st.write("Ports")
            edited_ports = st.data_editor(st.session_state[name]["form_values"]["ports"], use_container_width=True, num_rows="dynamic", disabled=False,
                                        key=port_key)
            st.session_state[name]["config"]["starting_ports"] = self.getPorts(edited_ports)


        # if name == "create":
        #     st.session_state[app_name]
        #st.text(yaml.dump(st.session_state[name]))
        #st.text(st.session_state[name])
        return app_expander

    def refreshAppListForm(self):
        def delete_field(index):
            app_name = st.session_state.app_list[index]
            st.session_state.fields_size -= 1
            del st.session_state.fields[index]
            del st.session_state.deletes[index]
            del st.session_state.app_list[index]
            del st.session_state[app_name]
            st.session_state.latest_app_name = "create"


        def update_app(app_name):
            pass

        for i in range(st.session_state.fields_size):
            # self.app_list.append(st.session_state.latest_app_name)
            if i < len(self.app_list):
                app_expander = self.appExpander(self.app_list[i],
                                                self.app_list[i])  # st.expander(self.app_list[i],expanded=False)
                app_expander.text_input("Name".format(st.session_state.fields_size), key="{}_app".format(self.app_list[i]))
                updatecol, deletecol = app_expander.columns([50, 50], gap="large")
                updatecol.button("Update {}".format(self.app_list[i]), key=f"update{i}", on_click=update_app,
                                 args=(self.app_list[i],))
                st.session_state.fields.append(app_expander)
                st.session_state.deletes.append(
                    deletecol.button("❌ Delete {}".format(self.app_list[i]), key=f"delete{i}", on_click=delete_field,
                                     args=(i,)))

    def apps(self):
        st.header("Application Handler")

        if "fields_size" not in st.session_state:
            st.session_state.fields_size = len(self.app_list)
            st.session_state.fields = [app for app in self.app_list]
            st.session_state.deletes = []

        def add_field():
            st.session_state.fields_size += 1
            if "create" in st.session_state:
                app_name = st.session_state["create"]["app_name"]
                if app_name == "":
                    st.error("App Name is blank")
                if app_name in self.app_list:
                    st.error("App already exists")
                else:
                    st.session_state.app_list.append(app_name)
                    st.session_state.latest_app_name= app_name
                    st.session_state[app_name] = {}
                    st.session_state[app_name]["app_name"] = app_name
                    st.session_state[app_name]["form_values"] = copy.deepcopy(st.session_state["create"]["form_values"])
                    st.session_state[app_name]["config"] = copy.deepcopy(st.session_state["create"]["config"])
                    st.session_state.fields_size += 1
                    #refreshAppListForm()
                    #st.session_state.fields = [app for app in self.app_list]
            else:
                st.error("App creation error due to session state mismatch")

        self.refreshAppListForm()

        create_app_expander = self.appExpander("create","Create New App")
        load_config, save_config, download_config = create_app_expander.columns([50, 50, 50])
        with load_config:
            if 'load_config_clicked' not in st.session_state:
                st.session_state.load_config_clicked = False

            def set_load_config_clicked():
                st.session_state.load_config_clicked = not (st.session_state.load_config_clicked)

            st.button('Upload Configuration File', on_click=set_load_config_clicked)
            if st.session_state.load_config_clicked:
                uploaded_env_file = st.file_uploader("Upload Configuration File", type=[".yaml", ".yml"])
                if uploaded_env_file is not None:
                    app_config = self.process_uploaded_file(uploaded_env_file)
            #st.rerun()
                    #create_app_expander. = list(app_config.keys())[0]

        with save_config:
            st.button("Submit", on_click=add_field)
            #st.text(self.app_list)

        with download_config:
            if 'dn_config_clicked' not in st.session_state:
                st.session_state.dn_config_clicked = False

            def set_dn_config_clicked():
                st.session_state.dn_config_clicked = not (st.session_state.dn_config_clicked)

            # st.button('Upload Configuration File', on_click=set_dn_config_clicked)

            st.download_button(
                label="Download Configuration File",
                data="",  # self.save_params(),
                file_name='manager.env',
                mime='text',
                on_click=set_dn_config_clicked
            )

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

sb = Sidebar()
ah = AppHandler()
ah.apps()