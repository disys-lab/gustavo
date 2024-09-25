import yaml, time, sys, os, copy
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
sidebarInit()
from src.Composer import Composer

def load_css(file_name):
    """Load CSS from a file and inject into Streamlit."""
    with open(file_name) as f:
        css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css("gustavo/pages/styles/style.css")

       
class DGHandler:
    def __init__(self):
        """Initialize session state variables."""
        if "app_list" in st.session_state:
            self.app_list = st.session_state.app_list
        else :
            self.app_list = []
            st.session_state.app_list = [] # This should be populated with actual data from the backend
        if 'decive_groups' in st.session_state:
            self.device_group = st.section_state.device_group
        else:
            st.session_state.device_groups = []
        self.allDGApps()
        # if 'device_groups' not in st.session_state:
        #     st.session_state.device_groups = [{'name': 'Device Group 1', 'apps': []}]

    def updateDeviceGroup(self, group_name, apps):
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            st.error(f"Error initializing Composer: {e}")
            return

        group_config = {"apps": apps}
        response = bcmp.handleAsset("device_group", group_name, "update", group_config)

        if response:
            st.success(f"Device group '{group_name}' updated successfully.")
        else:
            st.error(f"Failed to update device group '{group_name}'.")

    def deleteDeviceGroup(self, group_name):
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            st.error(f"Error initializing Composer: {e}")
            return

        response = bcmp.handleAsset("device_group", group_name, "delete")

        if response:
            st.success(f"Device group '{group_name}' deleted successfully.")
        else:
            st.error(f"Failed to delete device group '{group_name}'.")

    def createDeviceGroup(self, group_name, apps):
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            st.error(f"Error initializing Composer: {e}")
            return

        group_config = {"apps": apps}
        response = bcmp.handleAsset("device_group", group_name, "create", group_config)

        if response:
            st.success(f"Device group '{group_name}' created successfully.")
        else:
            st.error(f"Failed to create device group '{group_name}'.")
            
    def allDGApps(self):
        """Fetch device groups and their apps from the backend."""
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            st.error(f"Error initializing Composer: {e}")
            return

        # Fetch all device groups from the backend
        response = bcmp.nebulaObj.list_device_groups()

        if response["status_code"] == 200:
            # Populate the device groups and apps in session state
            st.session_state.device_groups = []
            for group_name in response["reply"]["device_groups"]:
                group_response = bcmp.nebulaObj.list_device_group(group_name)
                if group_response["status_code"] == 200:
                    apps = group_response["reply"]["apps"]
                    st.session_state.device_groups.append({"name": group_name, "apps": apps})
                else:
                    st.error(f"Failed to retrieve apps for device group '{group_name}': {group_response}")
        else:
            st.error(f"Failed to retrieve device groups: {response}")

    def dgs(self):
        st.title("Manage Device Groups and Apps")

        for i in range(len(st.session_state.device_groups)):
            group_info = st.session_state.device_groups[i]
            group_name = group_info['name']
            apps = group_info['apps']

            with st.expander(f"{group_name}"):
                # Show only the dropdown for selecting apps
                selected_apps = st.multiselect(
                    f"Select apps for {group_name}",
                    options=st.session_state.app_list,  # This should be fetched from the backend as well
                    default=apps,
                    key=f"app_multiselect_{i}"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Update {group_name}", key=f"update_button_{i}"):
                        self.updateDeviceGroup(group_name, selected_apps)
                with col2:
                    if st.button(f"Delete {group_name}", key=f"delete_button_{i}"):
                        self.deleteDeviceGroup(group_name)
                        st.session_state.device_groups.pop(i)
                        return  # Avoid further execution after deletion

        # New Device Group Section as an Expander
        with st.expander("Create New Device Group"):
            new_group_name = st.text_input("New Device Group Name", key="new_group_name")
            selected_apps = st.multiselect(
                "Select apps for new device group",
                options=st.session_state.app_list,
                key="new_group_apps"
            )

            if st.button("Create New Device Group"):
                if new_group_name:
                    self.createDeviceGroup(new_group_name, selected_apps)
                    st.session_state.device_groups.append({"name": new_group_name, "apps": selected_apps})
                    st.success(f"Device group '{new_group_name}' created successfully!")
                else:
                    st.error("Please enter a name for the new device group.")

    

# Initialize the Device Group Handler and execute the logic
dh = DGHandler()
dh.dgs()