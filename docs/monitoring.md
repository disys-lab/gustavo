<!-- This part of the project documentation focuses on
an **information-oriented** approach. Use it as a
reference for the technical implementation of the
`pages` project code.

# Monitoring
::: pages.4_🛠️_Monitoring -->
# 📊 `FileMonitoringApp` Class

<!-- The `FileMonitoringApp` class powers a real-time dashboard that visualizes host- and app-level metrics such as CPU and memory usage. It reads reports from Redis, processes them, and renders interactive plots using Streamlit and Altair. -->

The `FileMonitoringApp` class powers a real-time monitoring dashboard built with Streamlit. It visualizes metrics like CPU and memory usage pulled from Redis-stored reports. Each instance of the class corresponds to one panel in the dashboard.

Users can: - Select a device group and host - View historical data (last 5 minutes) - Plot CPU usage for selected hosts - Visualize memory usage across selected apps or host metrics

---
<!-- 
## 🧠 Overview

* **UI Framework:** Streamlit
* **Visualization:** Altair
* **Data Source:** Redis (Pickle-encoded reports)
* **User Features:**

  * Select device groups and hosts
  * Plot CPU and memory usage across apps or hosts
  * View historical metrics over a 5-minute window
  * Manage multiple monitoring panels dynamically

---

## 🚀 Initialization -->

### Constructor

Initializes app ID, connects to Redis, and sets up session state.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.__init__

### Redis Connection

Establishes and validates Redis connection.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.get_redis_client

---

## Data Handling

### Load Recent Redis Data

Loads and filters Redis keys to retrieve recent metrics.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.loadAllData

### Manual Refresh

Pulls new data and updates session state.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.refreshData

---

## Selection Utilities

### Device Groups

Dropdown for selecting available device groups.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.selectDeviceGroup

### Hosts per Group

Filters hostnames based on selected group.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.selectHostsForPlot

### Single Host Selector

Dropdown for one host (used for memory plots).

::: pages.4_🛠️_Monitoring.FileMonitoringApp.selectHost

### Apps & Host Metrics

Multi-select to choose which apps or host memory stats to plot.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.selectApps

---

## Plotting Functions

### CPU Usage Chart

Bar chart grouped by hostname.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.plotCpuUsage

### Memory Usage Chart

Line or point chart for host/app memory over time.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.visualizeMemoryUsage

---

## Helper Functions

### Filter Historical Records

Narrows `st.session_state.historical_data` by group and host.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.filterDataGroupAndHost

### Extract Unique Hosts

Utility to extract hostnames from Redis entries.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.getHosts

### Get Unique Device Groups

Scans Redis-loaded data for unique `device_group` values.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.getDeviceGroups

---

## Task Feedback

### Tooltip Wrapper

Wraps tasks with a spinner and shows feedback tooltip.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.handleTask

---

## Dashboard Logic

### Single Panel Runner

Executes full visualization logic for one panel.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.run

___

### Full Dashboard

Supports multiple monitoring instances with add/refresh/delete.

::: pages.4_🛠️_Monitoring.FileMonitoringApp.run_dashboard
