<!-- This part of the project documentation focuses on
an **information-oriented** approach. Use it as a
reference for the technical implementation of the
`pages` project code.

# Device_Groups
::: pages.3_🖥️_Device_Groups -->
# 📚 `DGHandler` Class

<!-- The `DGHandler` class provides a Streamlit interface for managing Device Groups (DGs) via the Gustavo backend. It handles the UI for creating, updating, deleting, and listing device groups, all while providing visual feedback using tooltips and spinners. -->


The `DGHandler` class provides a UI and logic wrapper for managing device groups in a Streamlit application. It interacts with a backend through the `Composer` class and manages session state updates and UI feedback via spinners and tooltips.

Features: - List all device groups - Create a new group with selected apps - Update or delete existing groups - Provide real-time feedback with visual spinners and status tooltips - Dynamically reflect changes in the Streamlit interface using session state and reruns

---
<!-- 
## 🧠 Overview

* **UI Framework:** Streamlit
* **Backend API:** Composer, Nebula
* **Functional Scope:**

  * Create / Update / Delete Device Groups
  * Associate Apps with Groups
  * Live feedback via `st.spinner` and mouse-based tooltips
  * Auto-refresh using `st.rerun()` on deletions

---

## 🚀 Initialization -->

### Constructor

Initializes session variables used for group tracking and creation.

::: pages.3_🖥️_Device_Groups.DGHandler.__init__

---

## Task Handler

### Tooltip Wrapper for Async Operations

Adds a spinner and mouse-following tooltip to any backend action.

::: pages.3_🖥️_Device_Groups.DGHandler.handleTask

---

## Device Group Lifecycle

### Create Device Group

::: pages.3_🖥️_Device_Groups.DGHandler.createDeviceGroup

### Update Device Group

::: pages.3_🖥️_Device_Groups.DGHandler.updateDeviceGroup

### Delete Device Group

::: pages.3_🖥️_Device_Groups.DGHandler.deleteDeviceGroup

### List Device Groups

::: pages.3_🖥️_Device_Groups.DGHandler.listAllDeviceGroups

---

## UI Renderer

### Full Device Group Manager UI

Builds the Streamlit page to view, edit, and add device groups.

::: pages.3_🖥️_Device_Groups.DGHandler.deviceGroups
