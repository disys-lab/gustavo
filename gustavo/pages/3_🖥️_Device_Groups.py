import yaml, time, sys, os, copy
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
sidebarInit()
from gustavo.src.Composer import Composer
from gustavo.pages.config.Logging import setup_logging
setup_logging()
import logging
from streamlit.runtime.scriptrunner.exceptions import RerunException
from gustavo.pages.config.loadCss import load_css
load_css()

class DGHandler:
    """
    The `DGHandler` class provides a UI and logic wrapper for managing device groups in a Streamlit application.
    It interacts with a backend through the `Composer` class and manages session state updates and UI feedback
    via spinners and tooltips.

    Features:
    - List all device groups
    - Create a new group with selected apps
    - Update or delete existing groups
    - Provide real-time feedback with visual spinners and status tooltips
    - Dynamically reflect changes in the Streamlit interface using session state and reruns
    """
    def __init__(self):
        """
        Initializes session state variables needed for group creation and tracking device groups.

        Logic:
        - Initializes:
            - `app_list`: list of available apps for selection
            - `device_groups`: current state of all known device groups
            - `create_dg`: dict holding in-progress group creation inputs (name and selected apps)
        - Also sets placeholders for error and logging containers in the UI
        """
        self.error_container = None
        self.log_placeholder = None

        if "app_list" not in st.session_state:
            st.session_state.app_list = []

        if "device_groups" not in st.session_state:
            st.session_state.device_groups = []

        if "create_dg" not in st.session_state:
            st.session_state["create_dg"] = {
                "group_name": "",
                "selected_apps": []
            }


    def handleTask(self, label, action_fn, result_container_key="action_result_placeholder"):
        """
        Wraps an asynchronous or time-consuming operation with a loading spinner and tooltip feedback.

        Args:
            label (str): Message shown while the spinner is active
            action_fn (Callable): A function to call (e.g. create or update operation)
            result_container_key (str): A key to store the result in Streamlit's session state

        Logic:
        - Shows a loading spinner with the given label
        - Executes `action_fn()`
        - Determines message to display based on result (success, failure, or error)
        - Renders tooltip HTML near the mouse cursor
        - Updates the result in session state for traceability

        Returns:
            dict: Result returned by `action_fn()`
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


    def createDeviceGroup(self, group_name, apps):
        """
        Creates a device group with the specified name and selected apps.

        Args:
            group_name (str): Name for the new device group
            apps (list): List of apps to include in the group

        Logic:
        - Instantiates a `Composer` with session state context
        - Prepares a group configuration dictionary
        - Sends a `create` request using the Composer’s asset handling API

        Returns:
            dict: Response from the Composer service (with error flag and message)
        """
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        group_config = {"apps": apps}
        response = bcmp.handleAsset("device_group", group_name, "create", group_config)

        return response

    def updateDeviceGroup(self, group_name, apps):
        """
        Updates an existing device group by replacing its associated apps.

        Args:
            group_name (str): Existing group name to update
            apps (list): New app list for the group

        Returns:
            dict: Response from Composer’s update API
        """
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
        except Exception as e:
            return {"error": True, "response": e}

        group_config = {"apps": apps}
        response = bcmp.handleAsset("device_group", group_name, "update", group_config)

        return response

    def deleteDeviceGroup(self, group_name, index):
        """
        Deletes the specified device group from both backend and Streamlit state.

        Args:
            group_name (str): The name of the group to delete
            index (int): Index in session state's `device_groups` list for removal

        Logic:
        - Fetches device group details (for diagnostic logging)
        - Calls `handleAsset(..., "delete")` on Composer
        - If successful:
            - Removes group from session state
            - Calls `st.rerun()` to refresh UI immediately

        Returns:
            dict: Response object indicating success or failure
        """
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
        """
        Retrieves all device groups from the backend and updates Streamlit session state.

        Logic:
        - Calls `list_device_groups()` from the Composer API
        - For each returned group:
            - Calls `list_device_group()` to get its apps
            - Adds result to `session_state.device_groups`

        Returns:
            dict: {error: bool, response: device_group_list}
        """
        try:
            bcmp = Composer(mode="streamlit", params=st.session_state)
            response = bcmp.nebulaObj.list_device_groups()
        except Exception as e:
            return {"error": True, "response": e}


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
        """
        Main method that renders the full device group management UI in Streamlit.

        Logic:
        1. Loads all existing device groups
        2. Displays warning if none are found
        3. For each group:
            - Shows an expander block
            - Lets the user update app selection or delete the group
        4. Provides a UI section to create a new device group
            - Validates name and uniqueness
            - Shows app selector
            - Uses `add_group()` function to create the group
        5. Uses `handleTask()` to wrap each operation with spinner/tooltip feedback

        UI Structure:
        - Header and error containers
        - List of expanders for each group
        - Expander for creating new group
        """
        st.header("Device Group Handler")
        self.error_container = st.container()
        self.log_placeholder = st.empty()

        try:
            self.listAllDeviceGroups()  # ✅ Ensures device groups load at startup
        except Exception as e:
            with self.error_container:
                st.error(f"Error listing device groups, exception {e}")
        if not st.session_state.device_groups:
            with self.error_container:
                st.warning("No device groups found. Try refreshing!")

        with st.container():
            def add_group():
                group_name = st.session_state["create_dg"]["group_name"]
                selected_apps = st.session_state["create_dg"]["selected_apps"]

                if not group_name:
                    with self.error_container:
                        st.error("Device Group Name is blank")
                    return

                elif any(dg["name"] == group_name for dg in st.session_state.device_groups):
                    with self.error_container:
                        st.error("Device Group already exists")
                    return
                else :
                    #st.session_state.device_groups.append(group_name)
                    st.session_state.latest_group_name= group_name
                    st.session_state[group_name] = {}
                    st.session_state[group_name]["group_name"] = group_name
                    try:
                        response = self.handleTask(
                        label=f"Creating {group_name}...",
                        action_fn=lambda: self.createDeviceGroup(group_name, selected_apps),
                        result_container_key=f"{group_name}_create_result"
                    )
                        # response = self.createDeviceGroup(group_name, selected_apps)
                        if response["error"]:
                            with self.error_container:
                                st.error(f"Error creating device group '{group_name}': {response['response']}")
                        else:
                            st.session_state.device_groups.append({"name": group_name, "apps": selected_apps})
                    except Exception as e:
                        with self.error_container:
                            st.error(f"Error creating device group {group_name}, exception {e}")
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
                            try:
                                self.handleTask(
                                label=f"Updating {group_name}...",
                                action_fn=lambda: self.updateDeviceGroup(group_name, selected_apps),
                                result_container_key=f"{group_name}_update_result"
                            )

                                # self.updateDeviceGroup(group_name, selected_apps)
                            except Exception as e:
                                with self.error_container:
                                    st.error(f"Error updating device group {group_name}, exception {e}")
                    with col2:
                        if st.button(f"Delete {group_name}", key=f"delete_button_{i}"):
                            try:
                                self.handleTask(
                                label=f"Deleting {group_name}...",
                                action_fn=lambda: self.deleteDeviceGroup(group_name, i),
                                result_container_key=f"{group_name}_delete_result"
                            )
                                return  # (Still keep this return after spinner because rerun will happen)
                                # ✅ Prevent further execution after deletion
                            except RerunException:
                                raise
                            except Exception as e:
                                with self.error_container:
                                    st.error(f"Error deleting device group {group_name}, exception {e}")

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