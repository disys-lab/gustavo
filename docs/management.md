# 💼 `ManagerService` Class

The `ManagerService` class provides a Streamlit-based dashboard for managing and monitoring core backend services including Redis, Mongo, Registry, Syncer, and Manager. It integrates tightly with the `Manager` class and uses session state to control service lifecycle operations and present real-time feedback.

### Constructor

Initializes all configuration dictionaries, status variables, and the `Manager` instance.

::: pages.1_💼_Manager_Services.ManagerService.__init__

---

## Core Task Execution

### Run Tasks with Tooltip Feedback

Handles async task execution (launch/remove/status) with spinner and custom tooltip.

::: pages.1_💼_Manager_Services.ManagerService.handleTask

---

## Status & Visual Indicators

### Status Badge (Pill)

Generates an HTML badge for service status: `Up`, `Down`, `Unknown`.

::: pages.1_💼_Manager_Services.ManagerService.status_pill

---

## Configuration Extractors

Each method retrieves config values from `st.session_state`, updates the local config dictionary, and syncs with the backend `Manager` instance.

### Redis Config:
::: pages.1_💼_Manager_Services.ManagerService.obtainRedisConf
---
<!-- spacer -->
### MongoDB Config:
::: pages.1_💼_Manager_Services.ManagerService.obtainMongoConf
---
### Registry Config:
::: pages.1_💼_Manager_Services.ManagerService.obtainRegistryConf
---
### Syncer Config:
::: pages.1_💼_Manager_Services.ManagerService.obtainSyncerConf
---
### Manager Config:
::: pages.1_💼_Manager_Services.ManagerService.obtainManagerConf

---

## Service Interaction Panels

### UI for One Service (Redis / Mongo / Manager /Registry /Syncer)

Renders the expander section for each service, including:

- Status
- Config table
- Launch / Remove buttons

::: pages.1_💼_Manager_Services.ManagerService.serviceExpander

---

### Status Button Handler

Logic for the status check button inside each expander.

::: pages.1_💼_Manager_Services.ManagerService.statusButton

---

### Top Row Controls

Generates a row of status pills + quick-check buttons for all 5 services.

::: pages.1_💼_Manager_Services.ManagerService.statusButtonTop

---

## Main Dashboard

### Full Manager Interface Renderer

Assembles the full dashboard with expanders and status panels.

::: pages.1_💼_Manager_Services.ManagerService.manager
