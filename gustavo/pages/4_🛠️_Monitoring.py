from dotenv import load_dotenv
import redis
import json
import pickle
import streamlit as st
import pandas as pd
import altair as alt
import time
import datetime
from time import time, sleep
from gustavo.pages.config.Sidebar import sidebarInit
sidebarInit()

def load_css(file_name):
    """Load CSS from a file and inject into Streamlit."""
    with open(file_name) as f:
        css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css("gustavo/pages/styles/style.css")

# Initialize Redis client using session state
def get_redis_client():
    """Create a Redis client using session state variables."""
    try:
        # Directly access session state without setting defaults
        redis_ip = st.session_state["REDIS_HOST"]
        redis_port = st.session_state["REDIS_PORT"]
        redis_auth_token = st.session_state["REDIS_AUTH_TOKEN"]

        # Create and return the Redis client
        return redis.Redis(host=redis_ip, port=redis_port, db=0, password=redis_auth_token)
    except KeyError as e:
        st.error(f"Missing Redis configuration in session state: {e}")
        return None
    except Exception as e:
        st.error(f"Failed to initialize Redis client: {e}")
        return None


# Initialize Redis client
# client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_AUTH_TOKEN)

# Initialize the Redis client
client = get_redis_client()
if not client:
    st.error("Redis client could not be initialized. Please check your configuration.")

# @st.cache_resource
def load_all_data(_redis_client):
    """Load all JSON data entries from Redis."""
    pattern = "nebula-reports*"
    loaded_data = []
    try:
        for key in _redis_client.scan_iter(pattern):
            # st.write(f"Found Redis key: {key.decode('utf-8')}")  # Debug: Log each key
            value = _redis_client.get(key)
            try:
                data = pickle.loads(value)
                # st.write(f"Loaded data for key {key.decode('utf-8')}: {data}")  # Debug: Log the data
                loaded_data.append(data)
            except Exception as e:
                st.error(f"Error decoding value for key {key.decode('utf-8')}: {e}")
    except Exception as e:
        st.error(f"An error occurred while loading data from Redis: {e}")
    return loaded_data

# Load data into session state
if "data" not in st.session_state:
    st.session_state.data = load_all_data(client)  # Pass `client` as `_redis_client`


class FileMonitoringApp:
    def __init__(self):
        self.app_id = 1
        self.device_groups = []
        self.selected_group = None
        self.hosts = []
        self.selected_host = None

    def refreshData(self):
        """Refresh data from Redis."""
        try:
            # st.write("Refreshing data...")  # Debugging log
            if "data" not in st.session_state:
                st.session_state.data = []
            st.session_state.data = load_all_data(client)
            # st.write(f"Data loaded: {st.session_state.data}")  # Debug: Log loaded data
        except Exception as e:
            st.error(f"An error occurred while refreshing data: {e}")


    def getDeviceGroups(self):
        """Extract unique device groups from the data."""
        try:
            if "data" not in st.session_state or not st.session_state.data:
                st.warning("No data loaded into session state.")
                return []
            # st.write(f"Session data: {st.session_state.data}")  # Debug: Log session data
            device_groups = set()
            for entry in st.session_state.data:
                if 'device_group' in entry:
                    device_groups.add(entry['device_group'])
            return list(device_groups)
        except Exception as e:
            st.error(f"An error occurred while retrieving device groups: {e}")
            return []


    def selectDeviceGroup(self, iteration):
        """Allow the user to select a device group to monitor."""
        try:
            self.device_groups = self.getDeviceGroups()
            if self.device_groups:
                selected_group_key = f"selected_group_{self.app_id}_{iteration}"  # Unique key per iteration
                if selected_group_key not in st.session_state:
                    st.session_state[selected_group_key] = self.device_groups[0]  # Default to the first group
                
                self.selected_group = st.selectbox(
                    f"Select a device group to Plot",
                    options=self.device_groups,
                    key=selected_group_key
                )
            else:
                st.warning("No device groups available to select.")
        except Exception as e:
            st.error(f"An error occurred while selecting a device group: {e}")

    def getHosts(self, filtered_data):
        """Extract unique hosts from the filtered data."""
        try:
            hosts = set()
            for entry in filtered_data:
                if 'hostname' in entry:
                    hosts.add(entry['hostname'])
            return list(hosts)
        except Exception as e:
            st.error(f"An error occurred while retrieving hosts: {e}")
            return []

    def selectHost(self, filtered_data, iteration):
        """Allow the user to select a host to monitor."""
        try:
            self.hosts = self.getHosts(filtered_data)
            if self.hosts:
                selected_host_key = f"selected_host_{self.app_id}_{iteration}"  # Unique key per iteration
                if selected_host_key not in st.session_state:
                    st.session_state[selected_host_key] = self.hosts[0]  # Default to the first host
                
                self.selected_host = st.selectbox(
                    f"Select a host",
                    options=self.hosts,
                    key=selected_host_key
                )
            else:
                st.warning("No hosts available to select.")
        except Exception as e:
            st.error(f"An error occurred while selecting a host: {e}")

    def filterDataGroupAndHost(self):
        """Filter data based on the selected device group and host."""
        try:
            if "data" not in st.session_state or not st.session_state.data:
                return []
            if self.selected_group and self.selected_host:
                return [
                    entry
                    for entry in st.session_state.data
                    if entry.get('device_group') == self.selected_group and entry.get('hostname') == self.selected_host
                ]
            return []
        except Exception as e:
            st.error(f"An error occurred while filtering data: {e}")
            return []

    def selectApps(self, filtered_data):
        """Allow the user to select apps and host metrics to monitor for the selected host, including an 'All' option."""
        try:
            # Extract available apps for the selected host
            apps = set()
            for entry in filtered_data:
                if 'apps_containers' in entry:
                    for app in entry['apps_containers']:
                        if 'name' in app:
                            apps.add(app['name'])

            # Add host metrics to the options
            apps.add('Total Memory (Host)')
            apps.add('Used Memory (Host)')

            if apps:
                # Add an "All" option to the list of apps
                apps_with_all = ["All"] + list(apps)
                selected_apps_key = f"selected_apps_{self.app_id}"  # Unique key for the dropdown

                # Ensure session state is initialized
                if selected_apps_key not in st.session_state:
                    st.session_state[selected_apps_key] = []  # Default to empty selection

                # Render the multiselect dropdown
                selected_apps = st.multiselect(
                    "Select apps to Plot (including 'All'):",
                    options=apps_with_all,
                    default=st.session_state[selected_apps_key],
                    key=selected_apps_key
                )

                # If "All" is selected, set the selection to all apps
                if "All" in selected_apps:
                    self.selected_apps = list(apps)
                else:
                    self.selected_apps = selected_apps  # Otherwise, use the explicitly selected apps
            else:
                st.warning("No apps or host metrics available for selection.")
                self.selected_apps = []
        except Exception as e:
            st.error(f"An error occurred while selecting apps and host metrics: {e}")
            self.selected_apps = []


    def plotCpuUsage(self, filtered_data):
        """Plot CPU usage percentages for all hosts in the selected device group."""
        try:
            if not filtered_data:
                st.warning("No data available for CPU usage visualization.")
                return

            # Extract CPU usage and host information
            cpu_usage_records = []
            for entry in filtered_data:
                if 'cpu_usage' in entry and 'hostname' in entry:
                    cpu_usage = entry['cpu_usage'].get('used_percent', 0)
                    hostname = entry['hostname']
                    cpu_usage_records.append({'hostname': hostname, 'cpu_usage': cpu_usage})

            if cpu_usage_records:
                # Create a DataFrame
                df_cpu_usage = pd.DataFrame(cpu_usage_records)

                # Plot CPU usage
                st.write(f"CPU Usage for Device Group: {self.selected_group}")
                cpu_chart = alt.Chart(df_cpu_usage).mark_bar().encode(
                    x='hostname:N',
                    y='cpu_usage:Q',
                    tooltip=['hostname:N', 'cpu_usage:Q']
                ).properties(
                    title="CPU Usage by Host"
                ).interactive()

                st.altair_chart(cpu_chart, use_container_width=True)
            else:
                st.warning("No CPU usage records found for visualization.")
        except Exception as e:
            st.error(f"An error occurred while visualizing CPU usage: {e}")

    def selectHostsForPlot(self, filtered_data):
        """Allow the user to select multiple hosts for plotting, including an 'All' option."""
        try:
            # Get unique hosts from the filtered data
            available_hosts = self.getHosts(filtered_data)
            if available_hosts:
                # Add an "All" option to the list of hosts
                hosts_with_all = ["All"] + available_hosts
                plot_hosts_key = f"plot_hosts_{self.app_id}"  # Unique key for host selection

                # Initialize session state before rendering the widget
                if plot_hosts_key not in st.session_state:
                    st.session_state[plot_hosts_key] = []
                    # hosts_with_all  # Default to "All" selected

                # Render the multiselect dropdown
                selected_hosts = st.multiselect(
                    "Select hosts to Plot (including 'All'):",
                    options=hosts_with_all,
                    default=st.session_state[plot_hosts_key],
                    key=plot_hosts_key
                )

                # If "All" is selected, set the selection to all hosts
                if "All" in selected_hosts:
                    self.plot_hosts = available_hosts
                else:
                    self.plot_hosts = selected_hosts  # Otherwise, use selected hosts
            else:
                st.warning("No hosts available for plotting.")
                self.plot_hosts = []
        except Exception as e:
            st.error(f"An error occurred while selecting hosts for plotting: {e}")
            self.plot_hosts = []

    def visualizeMemoryUsage(self, filtered_data):
        """Visualize memory usage for each app and host memory metrics in the selected device group and host."""
        try:
            memory_cpu_records = []

            # Process the filtered data
            for entry in filtered_data:
                apps_containers = entry.get('apps_containers', [])
                timestamp = entry.get('report_creation_time')

                if not timestamp:
                    continue

                # Add host-level memory metrics
                host_memory = entry.get("memory_usage", {})
                host_memory_total = host_memory.get("total", 0)
                host_memory_used = host_memory.get("used", 0)

                if 'Total Memory (Host)' in self.selected_apps:
                    memory_cpu_records.append({
                        'name': 'Total Memory (Host)',
                        'memory_usage': host_memory_total,
                        'timestamp': int(timestamp),
                        'type': 'host'
                    })
                if 'Used Memory (Host)' in self.selected_apps:
                    memory_cpu_records.append({
                        'name': 'Used Memory (Host)',
                        'memory_usage': host_memory_used,
                        'timestamp': int(timestamp),
                        'type': 'host'
                    })

                # Add app-level memory metrics
                if apps_containers:
                    for app in apps_containers:
                        app_name = app.get('name', 'unknown')
                        if app_name in self.selected_apps:
                            memory_stats = app.get('memory_stats', {})
                            memory_usage = memory_stats.get('usage', 0)

                            memory_cpu_records.append({
                                'name': app_name,
                                'memory_usage': memory_usage,
                                'timestamp': int(timestamp),
                                'type': 'app',
                            })

            if memory_cpu_records:
                # Create DataFrame
                df_usage = pd.DataFrame(memory_cpu_records)
                df_usage['timestamp'] = pd.to_datetime(df_usage['timestamp'], unit='s')
                df_usage = df_usage.sort_values(by='timestamp')

                # Filter for the last 15 seconds
                current_time = df_usage['timestamp'].max()
                time_threshold = current_time - pd.Timedelta(seconds=15)
                filtered_df = df_usage[df_usage['timestamp'] >= time_threshold]

                # Fallback to all data if filtered data is empty
                if filtered_df.empty:
                    filtered_df = df_usage
                    st.warning("No data found for the last 15 seconds. Displaying all available data.")
                # st.write("plot this ", filtered_df)

                # Memory usage line chart
                usage_chart = alt.Chart(filtered_df).mark_line().encode(
                    x=alt.X('timestamp:T', scale=alt.Scale(nice='second')),
                    y=alt.Y('memory_usage:Q', title="Memory Usage (MB)"),
                    color='name:N',  # Use name (app or host metric) as the legend
                    tooltip=['timestamp:T', 'name:N', 'memory_usage:Q']
                ).properties(
                    title="Memory Usage per App"
                )

                # Render the chart
                st.altair_chart(usage_chart, use_container_width=True)
            else:
                st.warning("No memory usage records found for visualization.")
        except Exception as e:
            st.error(f"An error occurred while visualizing memory usage: {e}")

    def run(self):
        """Run the instance to select device groups and visualize the memory usage."""
        if "data" not in st.session_state:
            st.session_state.data = load_all_data()  # Load data into session state

        self.selectDeviceGroup(0)  # Allow group selection
        if self.selected_group:
            # Filter data by selected group
            filtered_data = [
                entry for entry in st.session_state.data if entry.get('device_group') == self.selected_group
            ]

            # Add multiselect dropdown to select hosts for plotting
            self.selectHostsForPlot(filtered_data)

            # Plot CPU usage for selected hosts only
            if self.plot_hosts:
                filtered_data_for_plot = [
                    entry for entry in filtered_data if entry.get('hostname') in self.plot_hosts
                ]
                self.plotCpuUsage(filtered_data_for_plot)

            self.selectHost(filtered_data, 0)  # Allow host selection
            if self.selected_host:
                final_filtered_data = self.filterDataGroupAndHost()
                self.selectApps(final_filtered_data)
                if self.selected_apps:
                    # st.write(f"Selected apps and host metrics: {', '.join(self.selected_apps)}")
                    self.visualizeMemoryUsage(final_filtered_data)  # Show visualization
                else:
                    st.warning("No apps or host metrics selected for visualization.")


    def run_dashboard(self):
        """Run the complete dashboard."""
        st.title("Monitoring Dashboard")

        # Ensure default app instances are always initialized
        if 'app_instances' not in st.session_state:
            st.session_state.app_instances = []
            # Add a default instance
            default_app = FileMonitoringApp()
            default_app.app_id = 1
            st.session_state.app_instances.append(default_app)

        # Reassign app_ids to ensure continuity
        for i, app_instance in enumerate(st.session_state.app_instances):
            app_instance.app_id = i + 1

        # Render all instances
        app_container = st.container()
        for app_instance in st.session_state.app_instances:
            with app_container:
                st.markdown(f"### Plot {app_instance.app_id}")
                app_instance.run()

                # Add Refresh and Delete buttons for each plot
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(
                        f"Refresh Plot {app_instance.app_id}",
                        key=f"refresh_button_{app_instance.app_id}"
                    ):
                        app_instance.refreshData()
                with col2:
                    if st.button(
                        f"Delete Plot {app_instance.app_id}",
                        key=f"delete_button_{app_instance.app_id}"
                    ):
                        st.session_state.app_instances.remove(app_instance)

                # Add "New System" button at the bottom
                st.markdown("---")
        if st.button("New System"):
            # Create a new instance with the next available sequential ID
            new_app = FileMonitoringApp()
            new_app.app_id = len(st.session_state.app_instances) + 1
            st.session_state.app_instances.append(new_app)

app = FileMonitoringApp()
app.run_dashboard() 
