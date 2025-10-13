
# 💻 `AppHandler` Class

The `AppHandler` class is responsible for rendering and managing application lifecycle operations within a Streamlit-based interface, leveraging Gustavo’s Composer, Manager, and registry services.

Core Responsibilities: - List all apps and their configurations from Nebula - Render dynamic UI to create, update, or delete apps - Manage form-based app configurations (env vars, volumes, ports) - Sync app states with associated device groups - Handle YAML upload/download for app configurations - Display tooltip-based feedback for operations

Session State: - Dynamically reads/writes app configs under session keys (e.g., `st.session_state["myapp"]`) - Maintains auxiliary keys like `app_list`, `fields_size`, `deletes`, `create`, etc.

Dependencies: - Requires `Composer` and `Manager` objects for backend communication - Uses helper functions for transforming and validating YAML and UI data

UI Components: - Main app handler UI (`apps()`) - Per-app expander UI (`appExpander()`) - Feedback containers (`error_container`, `log_placeholder`)

###  Constructor

Initializes the app list and related UI tracking variables.

::: pages.2_📊_Apps_Creation.AppHandler.__init__

___

<!-- ## Task Execution -->

###  Tooltip-based Async Task Wrapper

Provides feedback and spinner for app operations.

::: pages.2_📊_Apps_Creation.AppHandler.handleTask


___
<!-- ## App Lifecycle Operations -->

###  Create App

Generates and submits a new app configuration.

::: pages.2_📊_Apps_Creation.AppHandler.createApp
___
###  Update App

Pushes changes to an existing app.

::: pages.2_📊_Apps_Creation.AppHandler.updateApp
___
###  Delete App

Removes app from Nebula and all device groups.

::: pages.2_📊_Apps_Creation.AppHandler.deleteApp

___

## Device Group Management

###  List All Groups

Fetches all Nebula device groups.

::: pages.2_📊_Apps_Creation.AppHandler.listAllDeviceGroups
___
###  List App-bound Groups

Identifies which groups reference a given app.

::: pages.2_📊_Apps_Creation.AppHandler.listDeviceGroups
___


## App Query & Config

###  List Apps

Fetches app list and stores configs in session state.

::: pages.2_📊_Apps_Creation.AppHandler.listAllApps
___
###  Load from YAML

Parses an uploaded YAML file to populate UI state.

::: pages.2_📊_Apps_Creation.AppHandler.process_uploaded_file


___
## UI Formatters

###  Port Mapper

### Set UI Format:### 
::: pages.2_📊_Apps_Creation.AppHandler.setPorts
___
### Get Backend Format:### 
::: pages.2_📊_Apps_Creation.AppHandler.getPorts
___
###  Volume Mapper

### Set UI Format:### 
::: pages.2_📊_Apps_Creation.AppHandler.setVolumes
___
### Get Backend Format:### 
::: pages.2_📊_Apps_Creation.AppHandler.getVolumes
___
###  Env Var Mapper

### Set UI Format:### 
::: pages.2_📊_Apps_Creation.AppHandler.setEnvVars
___
###  Get Backend Format:###  
::: pages.2_📊_Apps_Creation.AppHandler.getEnvVars
___
###   Default Env Var Builder

::: pages.2_📊_Apps_Creation.AppHandler.getLatestEnvVars


___
## Expanders & UI Panels

###   App Form

Renders a form for viewing/editing a single app.

::: pages.2_📊_Apps_Creation.AppHandler.appExpander
___
###   Refresh Existing App List

Regenerates and renders all app forms from backend.

::: pages.2_📊_Apps_Creation.AppHandler.refreshAppListForm

___

## Dashboard Renderer

<!-- ###   apps() -->

The main dashboard entry method, assembles the full app handler interface.

::: pages.2_📊_Apps_Creation.AppHandler.apps
