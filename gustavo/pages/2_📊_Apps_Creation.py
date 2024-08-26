import yaml,time, sys,os,copy
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
sidebarInit()
from gustavo.src.Composer import Composer
from gustavo.pages.config.SyncerConfig import refresh_registry, checkRegistryStatus
from gustavo.utils import *


class AppHandler:
    def __init__(self):

        if "app_list" in st.session_state:
            self.app_list = st.session_state.app_list
        else:
            self.app_list = []
            st.session_state.app_list = []

        self.listAllApps()
        if "fields_size" not in st.session_state:
            st.session_state.fields_size = len(self.app_list)
            st.session_state.fields = [app for app in self.app_list]
            st.session_state.deletes = []


    def createApp(self,app_name,device_groups):
        if len(device_groups)==0:
            dg_str = "gustavodg1"
        else:
            dg_str = ",".join(device_groups)

        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        app_config = {app_name: st.session_state[app_name]["config"]}

        response = handleCreateApp(bcmp, app_name, app_config, dg_str)


        return response

    def updateApp(self,app_name):
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        app_config = st.session_state[app_name]["config"]
        response = bcmp.handleAsset("app", app_name, "update", app_config)

        return response

    def deleteApp(self,app_name):
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        response = bcmp.nebulaObj.list_device_groups()

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
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}
        response = bcmp.nebulaObj.list_device_groups()
        device_group_list = []
        if response["status_code"] == 200:
            device_group_list = response["reply"]["device_groups"]
        return device_group_list,bcmp

    def listDeviceGroups(self,app_name):
        dg_list = []
        device_group_list,bcmp = self.listAllDeviceGroups()
        for device_group in device_group_list:
            response = bcmp.nebulaObj.list_device_group(device_group)
            if response["status_code"] == 200:
                dg_app_list = response["reply"]["apps"]
                if app_name in dg_app_list:
                    dg_list.append(device_group)
        return dg_list

    def listAllApps(self):
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        response = bcmp.nebulaObj.list_apps()

        if response["status_code"] == 200:
            existing_app_list = response["reply"]["apps"]
            self.app_list = existing_app_list
            st.session_state.app_list = self.app_list
            for app_name in existing_app_list:
                app_response = bcmp.nebulaObj.list_app_info(app_name)
                if app_response["status_code"] == 200:
                    dg_list = self.listDeviceGroups(app_name)
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
                    st.session_state[app_name]["form_values"] = {
                        "image": app_response["reply"]["docker_image"],
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
        app_config = yaml.load(uploaded_file,Loader=yaml.Loader)
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
                                                        "privileged": False

                                                    }
        #st.session_state[appkeys[0]] = app_config
        print(st.session_state["create"]["form_values"])
        return app_config

    def setPorts(self,app_config):
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
        port_list = []
        for p in edited_ports:
            if p["from"] is not None and p["to"] is not None:
                if p["from"] != "" and p["to"] != "":
                    port_list.append({int(p["from"]):int(p["to"])})
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
        except Exception as e:
            st.exception("Exception occured while configuring volumes {}".format(str(e)))
        if len(volume_dict_list) == 0:
            volume_dict_list = [{"from":"","to":""}]
        return volume_dict_list

    def getVolumes(self,edited_volumes):
        volume_list = [] #[v["from"] + ":" + v["to"] for v in edited_volumes]
        for v in edited_volumes:
            if v["from"] is not None and v["to"] is not None:
                if v["from"] != "" and v["to"] != "":
                    volume_list.append(v["from"] + ":" + v["to"])
        return volume_list

    def getEnvVars(self,edited_env_vars):
        env_var_dict = {}
        for ev in edited_env_vars:
            if ev["key"] is not None and ev["value"] is not None:
                if ev["key"] !="" and ev["value"] != "":
                    env_var_dict[ev["key"]] = ev["value"]
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
                                                        "device_groups": []
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
                                        "device_groups": [],
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
        check = checkRegistryStatus()
        with name_col:
            app_name = st.text_input("App Name",st.session_state[name]["app_name"],key=name_key)
            st.session_state[name]["app_name"] = app_name


        with image_col:

            if check:
                refresh_registry()
            else:
                st.session_state.registry_name_list=[]
            image = st.selectbox(
                "Container Image",
                st.session_state.registry_name_list,
                disabled = not check,
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
                dg_list, _ = self.listAllDeviceGroups()
                dg_option_list = dg_list

            if not isinstance(dg_option_list,list):
                st.error("Could not decipher device groups, received: {}".format(dg_option_list))
                dg_option_list = []

            if "gustavodg1" not in dg_option_list:
                dg_option_list.append("gustavodg1")

            device_groups = st.multiselect("Device Group (leave blank for default)", options=dg_option_list,default=dg_option_list,
                                           key=dg_key,
                                          disabled=check)

            st.session_state[name]["config"]["device_groups"] = device_groups
            st.session_state[name]["form_values"]["device_groups"] = device_groups

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
            #print(st.session_state[name]["form_values"]["ports"])
            edited_ports = st.data_editor(st.session_state[name]["form_values"]["ports"], use_container_width=True, num_rows="dynamic", disabled=False,
                                        key=port_key)



            st.session_state[name]["config"]["starting_ports"] = self.getPorts(edited_ports)
            #st.session_state[name]["form_values"]["ports"] = edited_ports


        # if name == "create":
        #     st.session_state[app_name]
        #st.text(yaml.dump(st.session_state[name]))
        #st.text(st.session_state[name])
        return app_expander

    def refreshAppListForm(self):
        def delete_field(index):
            app_name = st.session_state.app_list[index]
            response = self.deleteApp(app_name)
            if response["error"]:
                st.error("Error deleting app {}, response was {}".format(app_name,response["response"]))
            else:
                st.session_state.fields_size -= 1
                del st.session_state.fields[index]
                del st.session_state.deletes[index]
                del st.session_state.app_list[index]
                del st.session_state[app_name]
                st.session_state.latest_app_name = "create"


        def update_app(app_name):

            response = self.updateApp(app_name)
            if response["error"]:
                st.error("Error updating app {}, response was {}".format(app_name,response["response"]))
            else:
                # need to convert from form values to config values for data editor
                if st.session_state[app_name]["app_name"] != app_name:
                    new_app_name = copy.deepcopy(st.session_state[app_name]["app_name"])
                    print(new_app_name)
                    app_index = st.session_state.app_list.index(app_name)
                    st.session_state.app_list[app_index] = new_app_name

                    st.session_state[new_app_name] = copy.deepcopy(st.session_state[app_name])

                    del st.session_state[app_name]

                    app_name = new_app_name

                st.session_state[app_name]["form_values"]["ports"] = self.setPorts(st.session_state[app_name]["config"])
                st.session_state[app_name]["form_values"]["volumes"] = self.setVolumes(
                    st.session_state[app_name]["config"])

                st.session_state[app_name]["form_values"]["env_vars"] = self.setEnvVars(
                    st.session_state[app_name]["config"])

        self.listAllApps()
        if "fields_size" not in st.session_state:
            st.session_state.fields_size = len(self.app_list)
            st.session_state.fields = [app for app in self.app_list]
            st.session_state.deletes = []

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
        st.header("Application Handler")

        if "fields_size" not in st.session_state:
            st.session_state.fields_size = len(self.app_list)
            st.session_state.fields = [app for app in self.app_list]
            st.session_state.deletes = []

        with st.container():
            def add_field():
                if "create" in st.session_state:

                    app_name = st.session_state["create"]["app_name"]
                    if app_name == "":
                        st.error("App Name is blank")
                    elif app_name in self.app_list:
                        st.error("App already exists")
                    else:
                        st.session_state.app_list.append(app_name)
                        st.session_state.latest_app_name= app_name
                        st.session_state[app_name] = {}
                        st.session_state[app_name]["app_name"] = app_name
                        st.session_state[app_name]["form_values"] = copy.deepcopy(st.session_state["create"]["form_values"])
                        st.session_state[app_name]["config"] = copy.deepcopy(st.session_state["create"]["config"])

                        #need to convert from form values to config values for data editor

                        st.session_state[app_name]["form_values"]["ports"] = self.setPorts(st.session_state[app_name]["config"])
                        st.session_state[app_name]["form_values"]["volumes"] = self.setVolumes(st.session_state[app_name]["config"])

                        st.session_state[app_name]["form_values"]["env_vars"] = self.setEnvVars(st.session_state[app_name]["config"])

                        response = self.createApp(app_name,st.session_state[app_name]["config"]["device_groups"])

                        if response["error"]:
                            st.error("Error creating app name {}, response: {}".format(app_name,response["response"]))
                            del st.session_state[app_name]
                        else:
                            st.session_state.fields_size += 1
                        #refreshAppListForm()
                        #st.session_state.fields = [app for app in self.app_list]
                else:
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
                        app_config = self.process_uploaded_file(uploaded_env_file)

            with save_config:
                st.button("Submit", on_click=add_field)


ah = AppHandler()
ah.apps()