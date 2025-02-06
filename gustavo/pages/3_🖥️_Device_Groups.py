import yaml, time, sys, os, copy
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
sidebarInit()
from gustavo.src.Composer import Composer

def load_css(file_name):
    """Load CSS from a file and inject into Streamlit."""
    with open(file_name) as f:
        css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

parent = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
css_url = os.path.join(parent,"styles","style.css")
load_css(css_url)


class DGHandler:
    def __init__(self):
        """Initialize session state variables."""
        if "app_list" not in st.session_state:
            st.session_state.app_list = []

        if "device_groups" not in st.session_state:
            st.session_state.device_groups = []

        if "create_dg" not in st.session_state:
            st.session_state["create_dg"] = {
                "group_name": "",
                "selected_apps": []
            }

        self.listAllDeviceGroups()  # ✅ Ensures device groups load at startup

    def createDeviceGroup(self, group_name, apps):
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        group_config = {"apps": apps}
        response = bcmp.handleAsset("device_group", group_name, "create", group_config)

        return response

    def updateDeviceGroup(self, group_name, apps):
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        group_config = {"apps": apps}
        response = bcmp.handleAsset("device_group", group_name, "update", group_config)

        return response

    def deleteDeviceGroup(self, group_name, index):
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        # Fetch device group details before deletion
        response = bcmp.nebulaObj.list_device_group(group_name)
        
        # Log response
        bcmp.printDiagnosticResponse(response, 200, "check", "device group details", group_name)

        # Proceed with deletion
        retval = bcmp.handleAsset("device_group", group_name, "delete")

        if retval:
            # Remove from UI immediately
            del st.session_state.device_groups[index]  
            st.rerun()  # Force UI refresh for instant update

        return retval if retval else {"error": True, "response": f"Failed to delete device group '{group_name}'"}

    def listAllDeviceGroups(self):
        """Fetch device groups and their apps from the backend."""
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        response = bcmp.nebulaObj.list_device_groups()
        device_group_list = []

        if response["status_code"] == 200:
            for group_name in response["reply"]["device_groups"]:
                group_response = bcmp.nebulaObj.list_device_group(group_name)
                if group_response["status_code"] == 200:
                    apps = group_response["reply"]["apps"]
                    device_group_list.append({"name": group_name, "apps": apps})

        # ✅ Ensure session state is updated
        st.session_state.device_groups = device_group_list

        return {"error": False, "response": device_group_list}

    def deviceGroups(self):
        st.header("Device Group Handler")

        if not st.session_state.device_groups:
            st.warning("No device groups found. Try refreshing!")

        with st.container():
            def add_group():
                group_name = st.session_state["create_dg"]["group_name"]
                selected_apps = st.session_state["create_dg"]["selected_apps"]

                if not group_name:
                    st.error("Device Group Name is blank")
                    return

                elif any(dg["name"] == group_name for dg in st.session_state.device_groups):
                    st.error("Device Group already exists")
                    return
                else :
                    st.session_state.device_groups.append(group_name)
                    st.session_state.latest_group_name= group_name
                    st.session_state[group_name] = {}
                    st.session_state[group_name]["group_name"] = group_name

                    response = self.createDeviceGroup(group_name, selected_apps)

                    if response["error"]:
                        st.error(f"Error creating device group '{group_name}': {response['response']}")
                    else:
                        st.session_state.device_groups.append({"name": group_name, "apps": selected_apps})
                        # st.success(f"Device group '{group_name}' created successfully!")
                
            for i, group_info in enumerate(st.session_state.device_groups):
                group_name = group_info["name"]
                apps = group_info["apps"]

                with st.expander(f"{group_name}", expanded=False):
                    selected_apps = st.multiselect(
                        f"Select apps for {group_name}",
                        options=st.session_state.app_list,
                        default=apps,
                        key=f"app_multiselect_{i}"
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Update {group_name}", key=f"update_button_{i}"):
                            self.updateDeviceGroup(group_name, selected_apps)
                    with col2:
                        if st.button(f"Delete {group_name}", key=f"delete_button_{i}"):
                            self.deleteDeviceGroup(group_name, i)
                            st.session_state.device_groups.pop(i)  # ✅ Remove from UI
                            return  # ✅ Prevent further execution after deletion

            # self.refreshDeviceGroupList()

            create_dg_expander = st.expander("Create New Device Group", expanded=False)

            group_name_key = "create_dg_group_name"
            app_multiselect_key = "create_dg_group_apps"

            group_name = create_dg_expander.text_input(
                "Device Group Name", 
                st.session_state["create_dg"]["group_name"], 
                key=group_name_key
            )

            selected_apps = create_dg_expander.multiselect(
                "Select apps for new device group",
                options=st.session_state.app_list,
                key="new_group_apps"
            )

            st.session_state["create_dg"]["group_name"] = group_name
            st.session_state["create_dg"]["selected_apps"] = selected_apps

            create_dg_expander.button("Create", on_click=add_group)


dh = DGHandler()
dh.deviceGroups()