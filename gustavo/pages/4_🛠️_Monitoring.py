from dotenv import load_dotenv
import redis
import os
import pickle
import streamlit as st
import pandas as pd
import altair as alt
import logging
import time
from gustavo.pages.config.Sidebar import sidebarInit
from gustavo.pages.config.Logging import setup_logging
from gustavo.pages.config.loadCss import load_css
load_css()
load_dotenv()
# Initialize sidebar and logging
sidebarInit()
setup_logging()
logging.basicConfig(level=logging.INFO)

class FileMonitoringApp:

    """
    The `FileMonitoringApp` class powers a real-time monitoring dashboard built with Streamlit. It visualizes metrics
    like CPU and memory usage pulled from Redis-stored reports. Each instance of the class corresponds to one panel in
    the dashboard.

    Users can:
    - Select a device group and host
    - View historical data (last 5 minutes)
    - Plot CPU usage for selected hosts
    - Visualize memory usage across selected apps or host metrics
    """

    def __init__(self):
        """
        Initializes state for a monitoring instance.

        Sets the application ID, initializes fields for user selection (group, host, apps, etc.), and connects to Redis.
        A historical data map is also initialized in Streamlit's session state, organized by hostname.
        """
        self.app_id = 1
        self.device_groups = []
        self.selected_group = None
        self.hosts = []
        self.selected_host = None
        self.selected_apps = []
        self.plot_hosts = []
        self.redis_client = self.get_redis_client()
        # Initialize historical data storage
        if 'historical_data' not in st.session_state:
            st.session_state.historical_data = {}  # Map hostname to list of data entries

    def get_redis_client(self):
        """
        Establishes a connection to a Redis server using configuration parameters
        stored in the Streamlit session state.

        Expected session state keys:
        - REDIS_HOST: The IP or hostname of the Redis server
        - REDIS_PORT: The port number Redis is listening on (usually 6379)
        - REDIS_AUTH_TOKEN: Password required to authenticate with Redis

        Logic:
        1. Read host, port, and password from `st.session_state`
        2. Create a `redis.Redis` client using these credentials
        3. Call `ping()` to validate the connection
        4. If successful, return the client object
        5. If a KeyError (missing config) or RedisError (e.g., auth failure or unreachable host) occurs:
           - Log the error using Python's logging module
           - Display an error message using `st.error()`
           - Return `None` to indicate failure

        Returns:
            redis.Redis or None: A connected Redis client instance, or None if the connection failed
        
        Tries to connect to Redis using credentials stored in `st.session_state`.

        - Uses keys: REDIS_HOST, REDIS_PORT, REDIS_AUTH_TOKEN
        - On success: Returns a connected `redis.Redis` client
        - On failure: Logs and displays an error in the Streamlit UI
        """

        try:
            redis_ip = st.session_state["REDIS_HOST"]
            redis_port = st.session_state["REDIS_PORT"]
            redis_auth_token = st.session_state["REDIS_AUTH_TOKEN"]
            client = redis.Redis(host=redis_ip, port=redis_port, db=0, password=redis_auth_token)
            client.ping()
            # logging.info("Successfully connected to Redis.")
            return client
        except (KeyError, redis.RedisError) as e:
            logging.error(f"Failed to initialize Redis client: {e}")
            st.error(f"Redis connection failed: {e}")
            return None

    def loadAllData(self):
        """
        Loads monitoring report entries from Redis, filtering for those created within the past 5 minutes.

        Workflow:
        1. Check if Redis client is connected. If not, alert the user and exit.
        2. Define a Redis key pattern using the prefix `CACHE_PREFIX` (default: 'nebula-reports').
        3. Set a time cutoff based on the current Unix timestamp minus 5 minutes.
        4. Use `scan_iter` to iterate over all Redis keys matching the pattern.
        5. For each key:
           - Decode the value
           - Unpickle the Python dictionary object
           - Check that it includes a valid `report_creation_time`
           - If recent enough, and not a duplicate timestamp for its hostname, add it to
             `st.session_state.historical_data[hostname]`
           - Add it to a `loaded_data` list to return
        6. After loading, clean old data from each host's historical list to maintain only recent entries.
        7. Print debug output showing the number of entries loaded.

        Returns:
            list: A list of valid entries recently pulled from Redis, suitable for visualization
        
        Scans Redis for all recent (<= 5 minutes old) keys that match a report pattern.

        - Each value is a pickled Python dict with metadata (e.g. hostname, timestamp)
        - Valid entries are de-duplicated (based on timestamp) and saved into
          `st.session_state.historical_data[hostname]`
        - Old data is cleaned from history to retain relevance

        Returns:
            list: All valid recent entries, useful for filtering and plotting
        """
        if not self.redis_client:
            st.error("Redis client not initialized")
            return []
        prefix = os.getenv("CACHE_PREFIX", "nebula-reports")
        pattern = f"{prefix}*"
        loaded_data = []
        time_window_minutes = 5  # Store data from the last 5 minutes
        cutoff_time = int(time.time()) - (time_window_minutes * 60)
        try:
            for key in self.redis_client.scan_iter(pattern):
                key_str = key.decode('utf-8')
                try:
                    value = self.redis_client.get(key)
                    if value:  # Ensure the key still exists (not expired)
                        data = pickle.loads(value)
                        if 'report_creation_time' in data and data['report_creation_time'] >= cutoff_time:
                            hostname = data.get('hostname')
                            if hostname:
                                # Append to historical data for this hostname
                                if hostname not in st.session_state.historical_data:
                                    st.session_state.historical_data[hostname] = []
                                # Avoid duplicates by checking timestamp
                                if not any(entry['report_creation_time'] == data['report_creation_time'] 
                                           for entry in st.session_state.historical_data[hostname]):
                                    st.session_state.historical_data[hostname].append(data)
                                loaded_data.append(data)
                                # logging.info(f"Loaded data for key {key_str} with timestamp {data['report_creation_time']}")
                        else:
                            logging.warning(f"Skipping data for key {key_str}: No timestamp or too old")
                except Exception as e:
                    logging.error(f"Error decoding value for key {key_str}: {e}")
            # Clean up historical data to remove old entries
            for hostname in st.session_state.historical_data:
                st.session_state.historical_data[hostname] = [
                    entry for entry in st.session_state.historical_data[hostname]
                    if entry.get('report_creation_time', 0) >= cutoff_time
                ]
            st.write(f"Debug: Loaded {len(loaded_data)} data entries")
            return loaded_data
        except Exception as e:
            logging.error(f"Error loading data from Redis: {e}")
            st.error(f"Error loading data: {e}")
            return []

    def handleTask(self, label, action_fn, result_container_key="action_result_placeholder"):
        """
        Handles the execution of a long-running or external task and gives real-time feedback to the user.

        Purpose:
        - Display a spinner (loading animation) during task execution
        - Show a floating tooltip near the cursor with the task result
        - Store the result in `st.session_state` for later reference

        Logic:
        1. Check if a previous result key exists in session state; if not, initialize it.
        2. Use Streamlit's `st.spinner` context to show the provided label while running `action_fn()`.
        3. Capture the return value (`result`) of `action_fn`.
        4. Analyze `result`:
           - If None: task failed silently — show generic failure ❌
           - If result contains `error: True`: show failure ❌ with details
           - Else: assume task success ✅ and show a success message
        5. Build an HTML snippet (styled tooltip) showing this message
        6. Inject the HTML into the Streamlit app using `st.markdown(..., unsafe_allow_html=True)`
        7. Update the result container key in session state for tracking

        Args:
            label (str): Text shown in the spinner while the task runs
            action_fn (Callable): Function to be executed (usually a service call or update)
            result_container_key (str): Where to store the result in Streamlit's session state

        Returns:
            dict: The result dictionary returned by `action_fn`, typically with keys like `error` and `response`
        
        Wraps a given task (`action_fn`) with:
        - Visual spinner while the task runs
        - HTML tooltip that shows the success/failure response near the cursor

        Useful for providing immediate, non-blocking UI feedback.

        Args:
            label (str): Spinner label while task executes
            action_fn (Callable): Function to run
            result_container_key (str): Where to save the result in session_state

        Returns:
            dict: Result from the `action_fn` call
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

    def refreshData(self):
        """
        Refreshes the application’s data layer by reloading recent Redis entries.

        Purpose:
        - Keeps the dashboard up-to-date by pulling the latest reports from Redis
        - Acts as a triggerable utility (e.g., via a "Refresh" button)

        Logic:
        1. Calls `self.load_all_data()` to fetch new entries from Redis
        2. Saves the result into `st.session_state.data`
        3. Handles exceptions gracefully:
           - If Redis connection or parsing fails, logs the error
           - Also shows the error in Streamlit UI using `st.error()`
        4. Returns a response dictionary for user-facing feedback via `handleTask()`

        Returns:
            dict: Contains either a success message or an error description with `error: True`
        
        Shortcut to re-load all Redis data and store into session.
        Uses `load_all_data` and handles error reporting.

        Returns:
            dict: {response: ..., error: bool}
        """
        try:
            st.session_state.data = self.loadAllData()
            # logging.info(f"Refreshed data with {len(st.session_state.data)} entries")
            return {"response": "Data refreshed successfully"}
        except Exception as e:
            logging.error(f"Error refreshing data: {e}")
            st.error(f"Error refreshing data: {e}")
            return {"error": True, "response": str(e)}

    def getDeviceGroups(self):
        """
        Extracts a unique set of `device_group` names from the current Redis data in session.

        Purpose:
        - Provide the options for the first-level dropdown menu (device group selection)
        - Ensure the list is always up-to-date with current Redis data

        Logic:
        1. Check if `st.session_state.data` exists and contains entries
        2. Iterate through each entry and extract its `device_group` value (if available)
        3. Use a set to ensure uniqueness
        4. Return the resulting list of device group names
        5. If no data is available or errors occur, log the issue and return an empty list

        Returns:
            list[str]: A list of distinct device group names extracted from the current data
        
        Extracts all distinct `device_group` values from loaded Redis data.

        This helps populate the first dropdown in the UI.

        Returns:
            list[str]: Unique device group names
        """

        try:
            if "data" not in st.session_state or not st.session_state.data:
                logging.warning("No data loaded into session state.")
                # st.warning("No data loaded.")
                return []
            device_groups = set(entry.get('device_group') for entry in st.session_state.data if 'device_group' in entry)
            # st.write(f'device_groups: {device_groups}')
            return list(device_groups)
        except Exception as e:
            logging.error(f"Error retrieving device groups: {e}")
            st.error(f"Error retrieving device groups: {e}")
            return []

    def selectDeviceGroup(self, iteration):
        """
        Displays a Streamlit dropdown widget that allows the user to choose a device group to visualize.

        Purpose:
        - Lets the user filter the view by a specific `device_group` from the list returned by `getDeviceGroups()`
        - Uses the `iteration` parameter to uniquely identify the dropdown in Streamlit’s session state

        Logic:
        1. Calls `getDeviceGroups()` to update `self.device_groups` with all available group names
        2. Constructs a session state key like `selected_group_<app_id>_<iteration>` to track the dropdown state
        3. Initializes the key to the first device group (if not already set)
        4. Displays the dropdown and stores the selected value in `self.selected_group`
        5. Logs and displays a warning if no device groups are available

        Args:
            iteration (int): An identifier used to differentiate dropdown state keys across multiple app instances
        
        Streamlit widget to allow user selection of device group.

        - Uses a unique key based on app_id + iteration
        - Updates `self.selected_group` with the selected value
        """
        try:
            self.device_groups = self.getDeviceGroups()
            if self.device_groups:
                selected_group_key = f"selected_group_{self.app_id}_{iteration}"
                if selected_group_key not in st.session_state:
                    st.session_state[selected_group_key] = self.device_groups[0]
                self.selected_group = st.selectbox(
                    f"Select a device group to Plot",
                    options=self.device_groups,
                    key=selected_group_key
                )
            else:
                logging.warning("No device groups available to select.")
                # st.warning("No device groups available.")
        except Exception as e:
            logging.error(f"Error selecting device group: {e}")
            st.error(f"Error selecting device group: {e}")

    def getHosts(self, filtered_data):
        """
        Extracts a list of unique hostnames from a list of filtered Redis report entries.

        Purpose:
        - Support host-level selection widgets and metrics (e.g., CPU and memory usage)
        - Acts as a utility for downstream components like `selectHost()` and `selectHostsForPlot()`

        Logic:
        1. Iterate through the `filtered_data`, which is a list of report dictionaries
        2. Collect the value of `hostname` from each entry where it exists
        3. Use a set to deduplicate hostnames
        4. Return the result as a list

        Args:
            filtered_data (list[dict]): Entries already filtered by device group or other criteria

        Returns:
            list[str]: Unique hostnames detected in the filtered dataset
        
        Returns unique hostnames found in filtered data entries.

        Each host typically represents one monitored machine.

        Returns:
            list[str]: Hostnames
        """
        try:
            hosts = set(entry.get('hostname') for entry in filtered_data if 'hostname' in entry)
            return list(hosts)
        except Exception as e:
            logging.error(f"Error retrieving hosts: {e}")
            st.error(f"Error retrieving hosts: {e}")
            return []

    def selectHost(self, filtered_data, iteration):
        """
        Displays a dropdown menu to allow the user to select a specific host from a list of filtered Redis entries.

        Purpose:
        - Narrow down the data view to a specific machine or container host
        - Enable detailed memory visualizations tied to that host

        Logic:
        1. Calls `getHosts(filtered_data)` to extract unique hostnames
        2. Uses `app_id` and `iteration` to construct a unique session state key like `selected_host_<app_id>_<iteration>`
        3. Sets a default value for this key (first host) if not already defined
        4. Renders a `st.selectbox()` widget with hostnames
        5. Updates `self.selected_host` with the user-selected value
        6. Displays a warning if no host data is found

        Args:
            filtered_data (list[dict]): Entries filtered by device group or other logic
            iteration (int): Used to uniquely track the dropdown's state across multiple app instances
        
        Lets the user select one host from dropdown.
        Sets `self.selected_host` accordingly.
        """
        try:
            self.hosts = self.getHosts(filtered_data)
            if self.hosts:
                selected_host_key = f"selected_host_{self.app_id}_{iteration}"
                if selected_host_key not in st.session_state:
                    st.session_state[selected_host_key] = self.hosts[0]
                self.selected_host = st.selectbox(
                    f"Select a host",
                    options=self.hosts,
                    key=selected_host_key
                )
            else:
                logging.warning("No hosts available to select.")
                # st.warning("No hosts available.")
        except Exception as e:
            logging.error(f"Error selecting host: {e}")
            st.error(f"Error selecting host: {e}")

    def filterDataGroupAndHost(self):
        """
        Narrows historical data to entries that match the selected group and host.

        Purpose:
        - Ensure that visualizations (especially memory usage) only use data specific to
          the user's selected device group and hostname

        Logic:
        1. Check if `st.session_state.historical_data` exists and has data
        2. Loop through each hostname and its data entries
        3. Filter entries where:
            - Hostname matches `self.selected_host`
            - `device_group` matches `self.selected_group`
        4. Log and return filtered results, or warn if nothing matched

        Returns:
            list[dict]: Final filtered records suitable for visualizations like memory usage plots
        
        Narrows historical data to entries that match the selected group and host.

        This is a prerequisite step for visualizations that depend on a single machine.

        Returns:
            list[dict]: Final filtered records
        """

        try:
            if not st.session_state.historical_data:
                # st.warning("No historical data available for filtering.")
                logging.warning("No historical data available.")
                return []
            
            filtered = []
            for hostname, entries in st.session_state.historical_data.items():
                if hostname == self.selected_host:
                    filtered.extend([
                        entry for entry in entries
                        if entry.get('device_group') == self.selected_group
                    ])
            
            if not filtered:
                # st.warning(f"No data found for device group {self.selected_group} and host {self.selected_host}.")
                logging.warning(f"No data found for device group {self.selected_group} and host {self.selected_host}.")
                return []
            
            # Log timestamps for debugging
            timestamps = [entry.get("report_creation_time") for entry in filtered]
            # logging.info(f"Filtered {len(filtered)} entries for {self.selected_host} with timestamps: {timestamps}")
            return filtered
        except Exception as e:
            logging.error(f"Error filtering data: {e}")
            st.error(f"Error filtering data: {e}")
            return []

    def selectApps(self, filtered_data):
        """
        Displays a multi-select box to choose:
        - Apps (from `apps_containers` inside each report)
        - Host-level memory metrics (Total/Used Memory)

        Purpose:
        - Let the user control what memory usage metrics get plotted
        - Supports both container-level app tracking and machine-level memory stats

        Logic:
        1. Traverse all `filtered_data` records
        2. Extract each app name from the `apps_containers` list (ignoring name '/ep1-1')
        3. Add additional metrics like:
           - 'Total Memory (Host)'
           - 'Used Memory (Host)'
        4. Combine everything into a multiselect widget
        5. Use session key `selected_apps_<app_id>` to persist choices
        6. If 'All' is selected, automatically include everything except 'All'
        7. Store final results in `self.selected_apps`

        Args:
            filtered_data (list[dict]): Records filtered by group and host
        
        Displays a multi-select box to choose:
        - Apps (from `apps_containers`)
        - Host-level memory metrics (e.g. Total/Used Memory)

        Handles defaulting, All-selection, and state persistence.
        Updates: `self.selected_apps`
        """
        try:
            apps = set()
            for entry in filtered_data:
                if 'apps_containers' in entry:
                    for app in entry['apps_containers']:
                        if 'name' in app and app['name'] != '/ep1-1':
                            apps.add(app['name'])
            apps.add('Total Memory (Host)')
            apps.add('Used Memory (Host)')
            if apps:
                apps_with_all = ["All"] + list(apps)
                selected_apps_key = f"selected_apps_{self.app_id}"
                if selected_apps_key not in st.session_state:
                    st.session_state[selected_apps_key] = []
                self.selected_apps = st.multiselect(
                    "Select apps to Plot (including 'All'):",
                    options=apps_with_all,
                    default=st.session_state[selected_apps_key],
                    key=selected_apps_key
                )
                if "All" in self.selected_apps:
                    self.selected_apps = list(apps)
            else:
                logging.warning("No apps or host metrics available.")
                # st.warning("No apps or host metrics available.")
                self.selected_apps = []
        except Exception as e:
            logging.error(f"Error selecting apps: {e}")
            st.error(f"Error selecting apps: {e}")
            self.selected_apps = []

    def plotCpuUsage(self, filtered_data):
        """
        Generates a bar chart showing the CPU usage percentage per host within a selected device group.

        Purpose:
        - Visualize relative CPU load across multiple hosts in the same device group
        - Give a quick snapshot of system performance and distribution of load

        Logic:
        1. Check if `filtered_data` is non-empty (entries must include `cpu_usage`)
        2. Extract the `hostname` and `cpu_usage.used_percent` for each entry
        3. Convert this list of records into a DataFrame for visualization
        4. Use Altair to build an interactive bar chart:
            - X-axis: Hostname
            - Y-axis: CPU Usage (%)
            - Tooltip: Shows detailed values on hover
        5. Render the chart with `st.altair_chart`
        6. Display a warning if no CPU usage data is found

        Args:
            filtered_data (list[dict]): Data already filtered by selected device group and hosts
        
        Creates a bar chart of CPU usage by host using Altair.

        Each entry is expected to contain a `cpu_usage.used_percent` field.
        The chart is grouped by hostname.
        """
        try:
            if not filtered_data:
                logging.warning("No data available for CPU usage visualization.")
                # st.warning("No data for CPU usage.")
                return
            cpu_usage_records = [
                {'hostname': entry['hostname'], 'cpu_usage': entry['cpu_usage'].get('used_percent', 0)}
                for entry in filtered_data if 'cpu_usage' in entry
            ]
            if cpu_usage_records:
                df_cpu_usage = pd.DataFrame(cpu_usage_records)
                cpu_chart = alt.Chart(df_cpu_usage).mark_bar().encode(
                    x='hostname:N',
                    y=alt.Y('cpu_usage:Q', title="CPU Usage (%)"),
                    tooltip=['hostname:N', 'cpu_usage:Q']
                ).properties(
                    title=f"CPU Usage by Host ({self.selected_group})"
                ).interactive()
                st.altair_chart(cpu_chart, use_container_width=True)
            else:
                logging.warning("No CPU usage records found.")
                # st.warning("No CPU usage records found.")
        except Exception as e:
            logging.error(f"Error plotting CPU usage: {e}")
            st.error(f"Error plotting CPU usage: {e}")

    def selectHostsForPlot(self, filtered_data):
        """
        Displays a multi-select widget allowing the user to pick multiple hosts for CPU usage visualization.

        Purpose:
        - Lets the user choose which host machines within the selected device group to plot
        - Enhances the CPU usage chart by enabling selective or full-host plotting

        Logic:
        1. Calls `getHosts(filtered_data)` to extract a list of hostnames
        2. Prepend 'All' to the list so users can select everything easily
        3. Uses `app_id` to construct a unique key in session state (e.g., `plot_hosts_<app_id>`) for persistence
        4. Initializes selection if not already stored in session state
        5. Updates `self.plot_hosts` with selected values
        6. If 'All' is selected, replaces selection with the full list of hosts

        Args:
            filtered_data (list[dict]): Entries already filtered by selected group
        
        Lets the user pick one or more hosts for CPU usage plots.
        Adds "All" option to quickly select everything.

        Updates: `self.plot_hosts`
        """
        try:
            available_hosts = self.getHosts(filtered_data)
            if available_hosts:
                hosts_with_all = ["All"] + available_hosts
                plot_hosts_key = f"plot_hosts_{self.app_id}"
                if plot_hosts_key not in st.session_state:
                    st.session_state[plot_hosts_key] = []
                self.plot_hosts = st.multiselect(
                    "Select hosts to Plot (including 'All'):",
                    options=hosts_with_all,
                    default=st.session_state[plot_hosts_key],
                    key=plot_hosts_key
                )
                if "All" in self.plot_hosts:
                    self.plot_hosts = available_hosts
            else:
                logging.warning("No hosts available for plotting.")
                # st.warning("No hosts available for plotting.")
                self.plot_hosts = []
        except Exception as e:
            logging.error(f"Error selecting hosts for plotting: {e}")
            st.error(f"Error selecting hosts for plotting: {e}")
            self.plot_hosts = []

    def visualizeMemoryUsage(self, filtered_data):
        """
        Generates a memory usage time-series plot using Altair for selected apps and host metrics.

        Combines two categories:
        - Host memory: 'Total Memory (Host)', 'Used Memory (Host)' from `memory_usage`
        - App memory: container-level usage from `apps_containers[*].memory_stats.usage`

        Filtering is done by:
        - Timestamp range (only recent entries from historical data)
        - Hostname (previously selected)
        - App name (user-selected via `selectApps`)

        Logic:
        1. Validate data is available; show a warning if not
        2. Parse each record to extract memory usage:
            - Convert host memory from KB ➝ MB
            - Convert app memory from Bytes ➝ MB
            - Skip records without a valid `report_creation_time`
        3. Build a DataFrame with [timestamp, name, memory_usage, type]
        4. Use Altair to draw the line/point chart:
            - X-axis: time
            - Y-axis: usage in MB
            - Color: by app or metric name
            - Tooltip: shows exact values
            - Automatically chooses a line chart if >1 unique timestamp, else shows points

        Args:
            filtered_data (list[dict]): Host-specific and group-filtered Redis entries

        Output:
            Renders Altair chart in Streamlit; warns if no records were found or processed
        
        Line or scatter plots showing memory usage over time.

        Combines two categories:
        - Host memory: `Total Memory`, `Used Memory`
        - App memory: parsed from `apps_containers[i].memory_stats.usage`

        Filtering is done by:
        - Timestamp range (must be recent)
        - App name (from `self.selected_apps`)
        - Host (selected earlier)

        Chart type adapts:
        - Line for multiple time points
        - Point for single snapshots
        """
        try:
            if not filtered_data:
                logging.warning("No data available for memory usage visualization.")
                # st.warning("No data for memory usage.")
                return

            memory_records = []
            selected_app_names = [name.lstrip('/') for name in self.selected_apps]

            for entry in filtered_data:
                apps_containers = entry.get('apps_containers', [])
                timestamp = entry.get('report_creation_time')
                if not timestamp:
                    logging.warning(f"Skipping entry without timestamp for host {entry.get('hostname')}")
                    continue

                # Host memory (convert KB to MB)
                host_memory = entry.get("memory_usage", {})
                if 'Total Memory (Host)' in self.selected_apps:
                    total_mb = host_memory.get("total", 0) / 1024.0
                    memory_records.append({
                        'name': 'Total Memory (Host)',
                        'memory_usage': total_mb,
                        'timestamp': int(timestamp),
                        'type': 'host'
                    })
                if 'Used Memory (Host)' in self.selected_apps:
                    used_mb = host_memory.get("used", 0) / 1024.0
                    memory_records.append({
                        'name': 'Used Memory (Host)',
                        'memory_usage': used_mb,
                        'timestamp': int(timestamp),
                        'type': 'host'
                    })

                # App memory usage (convert Bytes to MB)
                for app in apps_containers:
                    app_name_raw = app.get('name', 'unknown')
                    app_name = app_name_raw.lstrip('/')
                    if app_name in selected_app_names:
                        memory_stats = app.get('memory_stats', {})
                        memory_usage = memory_stats.get('usage', 0) / (1024 * 1024)
                        if memory_usage == 0:
                            continue
                        memory_records.append({
                            'name': app_name,
                            'memory_usage': memory_usage,
                            'timestamp': int(timestamp),
                            'type': 'app'
                        })

            if memory_records:
                df_usage = pd.DataFrame(memory_records)
                if df_usage.empty:
                    # st.warning("No valid data after processing.")
                    logging.warning("No valid memory records after processing.")
                    return

                df_usage['timestamp'] = pd.to_datetime(df_usage['timestamp'], unit='s', errors='coerce')
                df_usage = df_usage.dropna(subset=['timestamp', 'memory_usage']).sort_values(by='timestamp')

                if df_usage.empty:
                    # st.warning("No valid data after processing timestamps.")
                    logging.warning("No valid memory records after processing timestamps.")
                    return

                # Log the number of unique timestamps and records for debugging
                unique_timestamps = df_usage['timestamp'].nunique()
                # logging.info(f"Plotting {unique_timestamps} unique timestamps for {len(df_usage)} records for host {self.selected_host}")

                # Use line chart for multiple timestamps, point for single timestamp
                mark = alt.Chart(df_usage).mark_line() if unique_timestamps > 1 else alt.Chart(df_usage).mark_point()

                memory_chart = mark.encode(
                    x=alt.X('timestamp:T', title="Time"),
                    y=alt.Y('memory_usage:Q', title="Memory Usage (MB)", scale=alt.Scale(zero=False)),
                    color='name:N',
                    tooltip=['timestamp:T', 'name:N', 'memory_usage:Q']
                ).properties(
                    title=f"Memory Usage for {self.selected_host} ({self.selected_group})"
                ).interactive()

                st.altair_chart(memory_chart, use_container_width=True)
            else:
                # st.warning("No memory usage records found.")
                logging.warning("No memory usage records found.")  
        except Exception as e:
            logging.error(f"Error plotting memory usage: {e}")
            st.error(f"Error plotting memory usage: {e}")

    def run(self):
        """
        Executes a complete monitoring workflow for one dashboard instance.

        Purpose:
        - Acts as the logic engine for a single visualization panel
        - Chains together all selection steps and visual outputs

        Logic:
        1. If `st.session_state.data` doesn't exist, calls `load_all_data()` to fetch data
        2. Displays device group selector (`selectDeviceGroup`)
        3. Filters Redis data by selected group
        4. Displays multiselect widget to choose which hosts to visualize (`selectHostsForPlot`)
        5. Plots CPU usage across selected hosts (`plotCpuUsage`)
        6. Displays host selector widget to pick one host for detailed memory analysis (`selectHost`)
        7. Filters historical Redis data for matching group/host (`filterDataGroupAndHost`)
        8. Lets the user select apps or host memory metrics (`selectApps`)
        9. Displays memory usage chart if valid selections exist (`visualizeMemoryUsage`)

        Outcome:
        - Two possible visualizations are produced:
            - CPU usage (bar chart)
            - Memory usage (line or point chart)
        - If required fields are missing, warns the user accordingly
        """
        # self.check_redis_key_ttl()  # Debug TTL of keys
        if "data" not in st.session_state:
            st.session_state.data = self.loadAllData()
        
        self.selectDeviceGroup(0)
        if self.selected_group:
            filtered_data = [
                entry for entry in st.session_state.data if entry.get('device_group') == self.selected_group
            ]
            self.selectHostsForPlot(filtered_data)
            if self.plot_hosts:
                filtered_data_for_plot = [
                    entry for entry in filtered_data if entry.get('hostname') in self.plot_hosts
                ]
                self.plotCpuUsage(filtered_data_for_plot)
            self.selectHost(filtered_data, 0)
            if self.selected_host:
                final_filtered_data = self.filterDataGroupAndHost()
                self.selectApps(final_filtered_data)
                if self.selected_apps:
                    self.visualizeMemoryUsage(final_filtered_data)
                else:
                    # st.warning("No apps or host metrics selected.")
                    logging.warning("No apps or host metrics selected.")
            else: 
                # st.warning("No host selected.")
                logging.warning("No host selected.")
        else:
            # st.warning("No device group selected.")
            logging.warning("No device group selected.")        

    def run_dashboard(self):
        """
        Main entry point to render the full monitoring dashboard interface.

        Purpose:
        - Supports multiple independent monitoring panels using the `FileMonitoringApp` class
        - Provides UI controls to add, refresh, and delete individual plots

        Logic:
        1. Check if `st.session_state.app_instances` exists:
            - If not, initialize it with a single `FileMonitoringApp` instance
        2. Reassign each app instance a unique `app_id` based on its order
        3. Create a container (`st.container()`) to render each plot block
        4. For each instance:
            - Show plot title and run its `run()` method
            - Display two buttons:
                - "Refresh Plot <id>" ➝ calls `refreshData()` and updates the plot
                - "Delete Plot <id>" ➝ removes instance from list and calls `st.rerun()`
        5. Add a global button at the end: "New System"
            - Appends a new `FileMonitoringApp` to the session state
            - Triggers `st.rerun()` to re-render with updated plots

        Outcome:
            A multi-panel monitoring dashboard that can dynamically scale based on user interaction.

        Master dashboard function.

        - Renders multiple FileMonitoringApp instances (plots)
        - Adds UI controls to add, refresh, or remove each plot panel
        - Handles user actions like "New System", "Delete", "Refresh"

        Each app instance manages its own widgets and visualization context.
        """
        st.title("Monitoring Dashboard")
        if 'app_instances' not in st.session_state:
            st.session_state.app_instances = []
            default_app = FileMonitoringApp()
            default_app.app_id = 1
            st.session_state.app_instances.append(default_app)
        for i, app_instance in enumerate(st.session_state.app_instances):
            app_instance.app_id = i + 1
        app_container = st.container()
        for app_instance in st.session_state.app_instances:
            with app_container:
                st.markdown(f"### Plot {app_instance.app_id}")
                app_instance.run()
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(f"Refresh Plot {app_instance.app_id}", key=f"refresh_button_{app_instance.app_id}"):
                        self.handleTask(
                            label=f"Refreshing Plot {app_instance.app_id}...",
                            action_fn=app_instance.refreshData,
                            result_container_key=f"refresh_{app_instance.app_id}"
                        )
                with col2:
                    if st.button(f"Delete Plot {app_instance.app_id}", key=f"delete_button_{app_instance.app_id}"):
                        self.handleTask(
                            label=f"Deleting Plot {app_instance.app_id}...",
                            action_fn=lambda: st.session_state.app_instances.remove(app_instance),
                            result_container_key=f"delete_{app_instance.app_id}"
                        )
                        st.rerun()
                st.markdown("---")
        if st.button("New System"):
            self.handleTask(
                label="Adding new plot...",
                action_fn=lambda: st.session_state.app_instances.append(FileMonitoringApp()),
                result_container_key="new_system"
            )
            new_app = FileMonitoringApp()
            new_app.app_id = len(st.session_state.app_instances) + 1
            st.session_state.app_instances.append(new_app)
            st.rerun()

if __name__ == "__main__":
    app = FileMonitoringApp()
    app.run_dashboard()