import yaml,time, sys,os, logging
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
from gustavo.pages.config.SyncerConfig import SyncerConfig
from gustavo.src.Manager import Manager
sidebarInit()
import docker
import datetime
import shutil
import pandas as pd
import subprocess
# from src.Manager import Manager # Manager import is kept but not directly used for backup handlers in this file
from gustavo.src.NebulaBase import setup_logging
setup_logging()

def load_css(file_name):
    """Load CSS from a file and inject into Streamlit."""
    try:
        with open(file_name) as f:
            css = f.read()
            st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        logging.warning(f"CSS file not found at {file_name}. Skipping CSS loading.")

# Correctly construct the path to style.css
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
css_url = os.path.join(parent_dir, "styles", "style.css")
load_css(css_url)


class BackupService:
    def __init__(self):
        # Initialize backup directories from session state or use defaults
        self.REDIS_BKP_DIR = st.session_state.get("REDIS_BKP_DIR", "/tmp/redis_backups")
        self.REGISTRY_BKP_DIR = st.session_state.get("REGISTRY_BKP_DIR", "/tmp/registry_backups")


        # Initialize all necessary session state variables to prevent KeyError
        if "redis_backups" not in st.session_state:
            st.session_state.redis_backups = []
        if "registry_backups" not in st.session_state:
            st.session_state.registry_backups = []
        if "selected_redis_backups" not in st.session_state:
            st.session_state.selected_redis_backups = []
        if "selected_registry_backups" not in st.session_state:
            st.session_state.selected_registry_backups = []

        # Initialize triggered flags to False
        if "create_redis_backup_triggered" not in st.session_state:
            st.session_state.create_redis_backup_triggered = False
        if "delete_redis_backups_triggered" not in st.session_state:
            st.session_state.delete_redis_backups_triggered = False
        if "create_registry_backup_triggered" not in st.session_state:
            st.session_state.create_registry_backup_triggered = False
        if "delete_registry_backups_triggered" not in st.session_state:
            st.session_state.delete_registry_backups_triggered = False

        # Remove initial_backup_load flag as it's handled by calling list_backups in backup()
        # if "initial_backup_load" not in st.session_state:
        #     st.session_state.initial_backup_load = False

        # The triggering logic should be in the `backup` method, not `__init__`
        # as it depends on user interaction with buttons.

    def create_redis_backup(self):
        result = self.create_redis_backup_handler()
        if not result["error"]:
            st.success(result["response"])
            # No need to call list_redis_backups here, it will be called at the end of backup()
        else:
            st.error(result["response"])

    def list_redis_backups(self):
        result = self.list_redis_backups_handler()
        if not result["error"]:
            st.session_state.redis_backups = result["response"]
        else:
            st.error(f"Error listing Redis backups: {result['response']}")
            st.session_state.redis_backups = []  # Clear list on error

    def delete_redis_backups(self, filenames):
        for filename in filenames:
            result = self.delete_redis_backup_handler(filename)
            if not result["error"]:
                st.success(result["response"])
            else:
                st.error(result["response"])
        # No need to call list_redis_backups here, it will be called at the end of backup()
        st.session_state.selected_redis_backups = []  # Clear selection

    def restore_redis_backup_handler(self, filename):
        client = docker.from_env()

        self.REDIS_BKP_DIR = st.session_state.get("REDIS_BKP_DIR", "/tmp/")
        self.REGISTRY_BKP_DIR = st.session_state.get("REGISTRY_BKP_DIR", "/tmp/")

        backup_file_path = os.path.join(self.REDIS_BKP_DIR, filename)
        redis_data_path = os.path.join(self.REDIS_BKP_DIR, "dump.rdb")  # This is the file Redis loads

        if not os.path.exists(backup_file_path):
            logging.error(f"Redis backup file not found: {backup_file_path}")
            return {"error": True, "response": f"Redis backup file not found: {filename}"}

        try:
            # 1. Stop Redis container
            try:
                redis_container = client.containers.get("redis")
                logging.info("Stopping Redis container for restoration...")
                redis_container.stop()
                logging.info("Redis container stopped.")
            except docker.errors.NotFound:
                logging.warning("Redis container not found, proceeding with file copy.")
            except docker.errors.APIError as e:
                logging.error(f"Docker API error stopping Redis: {e}")
                return {"error": True, "response": f"Docker API error stopping Redis: {e}"}

            # 2. Replace current dump.rdb with the selected backup
            if os.path.exists(redis_data_path):
                os.remove(redis_data_path)
                logging.info(f"Removed existing dump.rdb at {redis_data_path}")

            shutil.copyfile(backup_file_path, redis_data_path)
            logging.info(f"Copied {filename} to {redis_data_path}")

            # 3. Start Redis container
            try:
                # Attempt to get the container again in case it was removed or recreated
                redis_container = client.containers.get("redis")
                logging.info("Starting Redis container after restoration...")
                redis_container.start()
                logging.info("Redis container started successfully.")
                return {"error": False, "response": f"Redis restored from {filename} and restarted."}
            except docker.errors.NotFound:
                # If container was removed, try to run it again (assuming it's configured to mount the volume)
                logging.warning("Redis container not found after stop, attempting to run it.")
                run_result = self.runRedis(client)  # Use the existing runRedis method
                if run_result["error"]:
                    return {"error": True,
                            "response": f"Failed to restart Redis after restore: {run_result['response']}"}
                return {"error": False, "response": f"Redis restored from {filename} and restarted."}
            except docker.errors.APIError as e:
                logging.error(f"Docker API error starting Redis: {e}")
                return {"error": True, "response": f"Docker API error starting Redis: {e}"}

        except Exception as e:
            logging.error(f"Unexpected error during Redis restore: {e}")
            return {"error": True, "response": f"Unexpected error during Redis restore: {e}"}


    def restore_redis_backup(self,filename):

        logging.info(f"Redis Backup: Using {filename}")
        # Import Manager here to avoid circular dependency if ManagerService also imports BackupService

        result =self.restore_redis_backup_handler(filename) # Call the Manager's method
        if not result["error"]:
            st.toast(result["response"])
        else:
            st.error(result["response"])

    def restore_registry_backup_handler(self, dirname):
        client = docker.from_env()
        backup_dir_path = os.path.join(self.REGISTRY_BKP_DIR, dirname)
        live_registry_data_path = self.REGISTRY_BKP_DIR  # This is the host path mounted to /var/lib/registry

        if not os.path.exists(backup_dir_path) or not os.path.isdir(backup_dir_path):
            logging.error(f"Registry backup directory not found or is not a directory: {backup_dir_path}")
            return {"error": True, "response": f"Registry backup directory not found: {dirname}"}

        try:
            # 1. Stop Registry container
            try:
                registry_container = client.containers.get("registry")
                logging.info("Stopping Registry container for restoration...")
                registry_container.stop()
                logging.info("Registry container stopped.")
            except docker.errors.NotFound:
                logging.warning("Registry container not found, proceeding with directory replacement.")
            except docker.errors.APIError as e:
                logging.error(f"Docker API error stopping Registry: {e}")
                return {"error": True, "response": f"Docker API error stopping Registry: {e}"}

            # # 2. Clear current live registry data directory contents
            # # Iterate and remove contents, but not the directory itself
            # for item in os.listdir(live_registry_data_path):
            #     item_path = os.path.join(live_registry_data_path, item)
            #     if os.path.isfile(item_path) or os.path.islink(item_path):
            #         os.remove(item_path)
            #     elif os.path.isdir(item_path):
            #         shutil.rmtree(item_path)
            # logging.info(f"Cleared contents of live registry data directory: {live_registry_data_path}")

            # 3. Copy contents of the selected backup into the live registry data directory
            # Copy contents from backup_dir_path to live_registry_data_path
            for item in os.listdir(backup_dir_path):
                s = os.path.join(backup_dir_path, item)
                d = os.path.join(live_registry_data_path, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            logging.info(f"Copied contents from {dirname} to {live_registry_data_path}")

            # 4. Start Registry container
            try:
                # Attempt to get the container again in case it was removed or recreated
                registry_container = client.containers.get("registry")
                logging.info("Starting Registry container after restoration...")
                registry_container.start()
                logging.info("Registry container started successfully.")
                return {"error": False, "response": f"Registry restored from {dirname} and restarted."}
            except docker.errors.NotFound:
                # If container was removed, try to run it again (assuming it's configured to mount the volume)
                logging.warning("Registry container not found after stop, attempting to run it.")
                run_result = self.runRegistry(client)  # Use the existing runRegistry method
                if run_result["error"]:
                    return {"error": True,
                            "response": f"Failed to restart Registry after restore: {run_result['response']}"}
                return {"error": False, "response": f"Registry restored from {dirname} and restarted."}
            except docker.errors.APIError as e:
                logging.error(f"Docker API error starting Registry: {e}")
                return {"error": True, "response": f"Docker API error starting Registry: {e}"}

        except Exception as e:
            logging.error(f"Unexpected error during Registry restore: {e}")
            return {"error": True, "response": f"Unexpected error during Registry restore: {e}"}

    def restore_registry_backup(self, dirname):
        result = self.restore_registry_backup_handler(dirname)
        if not result["error"]:
            st.toast(result["response"])
        else:
            st.error(result["response"])

    def create_registry_backup(self):
        result = self.create_registry_backup_handler()
        if not result["error"]:
            st.success(result["response"])
            # No need to call list_registry_backups here, it will be called at the end of backup()
        else:
            st.error(result["response"])

    def list_registry_backups(self):
        result = self.list_registry_backups_handler()
        if not result["error"]:
            st.session_state.registry_backups = result["response"]
        else:
            st.error(f"Error listing Registry backups: {result['response']}")
            st.session_state.registry_backups = []  # Clear list on error

    def delete_registry_backups(self, filenames):
        for filename in filenames:
            result = self.delete_registry_backup_handler(filename)
            if not result["error"]:
                st.success(result["response"])
            else:
                st.error(result["response"])
        # No need to call list_registry_backups here, it will be called at the end of backup()
        st.session_state.selected_registry_backups = []  # Clear selection

    def create_redis_backup_handler(self):
        client = docker.from_env()
        try:

            redis_container = client.containers.get("redis")

            # Get Redis auth token from session state
            redis_auth_token = st.session_state.get("REDIS_AUTH_TOKEN")

            # Construct the redis-cli command with authentication if token exists
            if redis_auth_token:
                redis_cli_command = f"redis-cli -a '{redis_auth_token}' BGSAVE"
            else:
                st.error("REDIS_AUTH_TOKEN not set")
                return {"error": True, "response": f"REDIS_AUTH_TOKEN not set"}
                #redis_cli_command = "redis-cli BGSAVE"

            exec_result = redis_container.exec_run(redis_cli_command)

            if exec_result.exit_code != 0:
                logging.error(f"Redis BGSAVE command failed: {exec_result.output.decode()}")
                return {"error": True, "response": f"Redis BGSAVE failed: {exec_result.output.decode()}"}

            # Wait a moment for the BGSAVE to complete and dump.rdb to be written
            time.sleep(2)

            # Rename the dump.rdb file on the host to include a timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            original_path = os.path.join(self.REDIS_BKP_DIR, "dump.rdb")
            backup_filename = f"redis_backup_{timestamp}.rdb"
            new_path = os.path.join(self.REDIS_BKP_DIR, backup_filename)


            if os.path.exists(original_path):
                os.rename(original_path, new_path)
                logging.info(f"Created Redis backup: {backup_filename}")
                return {"error": False, "response": f"Redis backup created: {backup_filename}"}
            else:
                # try:
                #     os.makedirs(self.REGISTRY_BKP_DIR, exist_ok=True)
                # except Exception as e:
                #     #os.makedirs(self.REDIS_BKP_DIR, exist_ok=True)
                logging.error(f"Failed to create backup at {original_path}.")
                st.toast(f"Failed to create backup at {original_path}.")
                return {"error": True, "response": "Redis dump.rdb not found after BGSAVE."}

        except docker.errors.NotFound:
            logging.error("Redis container not found. Please ensure Redis is running.")
            return {"error": True, "response": "Redis container not found."}
        except docker.errors.APIError as e:
            logging.error(f"Docker API error during Redis backup: {e}")
            return {"error": True, "response": f"Docker API error: {e}"}
        except Exception as e:
            logging.error(f"Unexpected error during Redis backup: {e}")
            return {"error": True, "response": f"Unexpected error: {e}"}


    def list_redis_backups_handler(self):
        try:
            # Ensure the backup directory exists
            os.makedirs(self.REDIS_BKP_DIR, exist_ok=True)
            files = [f for f in os.listdir(self.REDIS_BKP_DIR) if f.startswith("redis_backup_") and f.endswith(".rdb")]
            backups = []
            for f in files:
                file_path = os.path.join(self.REDIS_BKP_DIR, f)
                timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                backups.append({"filename": f, "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")})
            logging.info(f"Listed Redis backups: {backups}")
            return {"error": False, "response": backups}
        except Exception as e:
            logging.error(f"Error listing Redis backups: {e}")
            return {"error": True, "response": f"Error listing Redis backups: {e}"}


    def delete_redis_backup_handler(self, filename):
        backup_path = os.path.join(self.REDIS_BKP_DIR, filename)
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                logging.info(f"Deleted Redis backup: {backup_path}")
                return {"error": False, "response": f"Redis backup deleted: {filename}"}
            else:
                logging.warning(f"Redis backup not found: {backup_path}")
                return {"error": True, "response": f"Redis backup not found: {filename}"}
        except Exception as e:
            logging.error(f"Error deleting Redis backup: {e}")
            return {"error": True, "response": f"Error deleting Redis backup: {e}"}


    def create_registry_backup_handler(self):
        client = docker.from_env()
        try:
            registry_container = client.containers.get("registry")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dirname = f"registry_backup_{timestamp}"
            backup_path_on_host = os.path.join(self.REGISTRY_BKP_DIR, backup_dirname)
            live_registry_path_on_host = os.path.join(self.REGISTRY_BKP_DIR, "docker")

            # Ensure the target directory exists on the host
            os.makedirs(backup_path_on_host, exist_ok=True)

            # Use docker cp to copy the registry data from the container to the host
            # Assuming registry data is at /var/lib/registry inside the container
            # Note: docker cp requires the container to be running.
            # For a consistent backup, the registry might need to be paused or stopped.
            # This implementation assumes a "hot" backup which might not be fully consistent.

            command = ["cp", "-r" ,live_registry_path_on_host, backup_path_on_host]
            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode == 0:
                logging.info(f"Created Registry backup: {backup_dirname}")
                return {"error": False, "response": f"Registry backup created: {backup_dirname}"}
            else:
                logging.error(f"Docker cp failed for Registry backup: {result.stderr}")
                # Clean up the partially created directory if cp failed
                if os.path.exists(backup_path_on_host) and not os.listdir(backup_path_on_host):
                    os.rmdir(backup_path_on_host)
                return {"error": True, "response": f"Registry backup failed: {result.stderr}"}

        except docker.errors.NotFound:
            logging.error("Registry container not found. Please ensure Registry is running.")
            return {"error": True, "response": "Registry container not found."}
        except docker.errors.APIError as e:
            logging.error(f"Docker API error during Registry backup: {e}")
            return {"error": True, "response": f"Docker API error: {e}"}
        except Exception as e:
            logging.error(f"Unexpected error during Registry backup: {e}")
            return {"error": True, "response": f"Unexpected error: {e}"}


    def list_registry_backups_handler(self):
        try:
            # Ensure the backup directory exists
            os.makedirs(self.REGISTRY_BKP_DIR, exist_ok=True)
            # List directories that start with 'registry_backup_'
            dirs = [d for d in os.listdir(self.REGISTRY_BKP_DIR) if
                    os.path.isdir(os.path.join(self.REGISTRY_BKP_DIR, d)) and d.startswith("registry_backup_")]
            backups = []
            for d in dirs:
                dir_path = os.path.join(self.REGISTRY_BKP_DIR, d)
                timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(dir_path))
                backups.append({"filename": d, "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")})
            logging.info(f"Listed Registry backups: {backups}")
            return {"error": False, "response": backups}
        except Exception as e:
            logging.error(f"Error listing Registry backups: {e}")
            return {"error": True, "response": f"Error listing Registry backups: {e}"}


    def delete_registry_backup_handler(self, dirname):
        backup_path = os.path.join(self.REGISTRY_BKP_DIR, dirname)
        try:
            if os.path.exists(backup_path) and os.path.isdir(backup_path):
                shutil.rmtree(backup_path)  # Use shutil.rmtree to delete directory and its contents
                logging.info(f"Deleted Registry backup: {backup_path}")
                return {"error": False, "response": f"Registry backup deleted: {dirname}"}
            else:
                logging.warning(f"Registry backup directory not found: {backup_path}")
                return {"error": True, "response": f"Registry backup directory not found: {dirname}"}
        except Exception as e:
            logging.error(f"Error deleting Registry backup: {e}")
            return {"error": True, "response": f"Error deleting Registry backup: {e}"}

    def backup(self):
        # Update backup directories from session state in case they changed via PlatformConfig
        self.REDIS_BKP_DIR = st.session_state.get("REDIS_BKP_DIR", "/tmp/")
        self.REGISTRY_BKP_DIR = st.session_state.get("REGISTRY_BKP_DIR", "/tmp/")

        # Always list backups at the start of the `backup` method to refresh the display
        self.list_redis_backups()
        self.list_registry_backups()

        with st.container():
            st.header("Manage Redis and Registry Backups")
            backup_tab_redis, backup_tab_registry = st.tabs(["Redis Backups", "Registry Backups"])

            with backup_tab_redis:
                st.subheader("Redis Backups")
                redis_backup_status_placeholder = st.empty()

                col1, col2 = st.columns(2) # Use columns for buttons
                with col1:
                    def create_redis_backup_callback():
                        logging.info("Creating Redis backup triggered.")
                        st.session_state.create_redis_backup_triggered = True
                    if st.button("Create Redis Backup", key="create_redis_backup_btn"):
                        create_redis_backup_callback()
                with col2:
                    # def restore_redis_backup_callback():
                    #     logging.info("Restore Redis backup triggered.")
                    #     st.session_state.restore_redis_backup_triggered = True
                    if st.button("Restore Selected Redis Backup", key="restore_redis_backup_btn",
                                 disabled=False):
                        if len(st.session_state.selected_redis_backups) > 1:
                            st.error("Multiple redis backup files selected")
                        elif len(st.session_state.selected_redis_backups) ==0:
                            st.error("No redis backup files selected")
                        else:
                            filename = st.session_state.selected_redis_backups[0]
                            self.restore_redis_backup(filename)


                # Display existing Redis backups
                if st.session_state.redis_backups:
                    df_redis_backups = pd.DataFrame(st.session_state.redis_backups)
                    redis_selection_data = st.dataframe(
                        df_redis_backups,
                        use_container_width=True,
                        hide_index=True,
                        key="redis_backups_table",
                        on_select="rerun",
                        selection_mode="single-row"  # Added selection_mode
                    )
                    # Get selected rows for deletion
                    # Only try to get selection if the dataframe key exists in session state
                    if "redis_backups_table" in st.session_state:
                        if "selection" in st.session_state.redis_backups_table:
                            selected_rows = st.session_state.redis_backups_table["selection"]["rows"]
                            st.session_state.selected_redis_backups = [
                                st.session_state.redis_backups[i]["filename"] for i in selected_rows
                            ]
                        else:
                            st.session_state.selected_redis_backups = []
                    else:
                        st.session_state.selected_redis_backups = []
                else:
                    st.info("No Redis backups found.")
                    st.session_state.selected_redis_backups = []  # Ensure it's empty if no backups

            with backup_tab_registry:
                st.subheader("Registry Backups")
                registry_backup_status_placeholder = st.empty()

                col1, col2, = st.columns(2)  # Added a third column for restore button
                with col1:
                    def create_registry_backup_callback():
                        logging.info("Creating Registry backup triggered.")
                        st.session_state.create_registry_backup_triggered = True

                    if st.button("Create Registry Backup", key="create_registry_backup_btn"):
                        create_registry_backup_callback()

                with col2:  # New restore button for Registry
                    if st.button("Restore Selected Registry Backup", key="restore_registry_backup_btn",disabled=False):
                        if len(st.session_state.selected_registry_backups) > 1:
                            st.error("Multiple registry backup files selected")
                        elif len(st.session_state.selected_registry_backups) == 0:
                            st.error("No registry backup files selected")
                        else:
                            filename = st.session_state.selected_registry_backups[0]
                            self.restore_registry_backup(filename)

                # Display existing Registry backups
                if st.session_state.registry_backups:
                    df_registry_backups = pd.DataFrame(st.session_state.registry_backups)
                    st.dataframe(
                        df_registry_backups,
                        use_container_width=True,
                        hide_index=True,
                        key="registry_backups_table",
                        on_select="rerun",
                        selection_mode="single-row"  # Added selection_mode
                    )
                    # Get selected rows for deletion
                    # Only try to get selection if the dataframe key exists in session state
                    if "registry_backups_table" in st.session_state:
                        if "selection" in st.session_state.registry_backups_table:
                            selected_rows = st.session_state.registry_backups_table["selection"]["rows"]
                            st.session_state.selected_registry_backups = [
                                st.session_state.registry_backups[i]["filename"] for i in selected_rows
                            ]
                        else:
                            st.session_state.selected_registry_backups = []
                    else:
                        st.session_state.selected_registry_backups = []
                else:
                    st.info("No Registry backups found.")
                    st.session_state.selected_registry_backups = []  # Ensure it's empty if no backups

            # def delete_registry_backups_callback():
            #         if st.session_state.selected_registry_backups:
            #             st.session_state.delete_registry_backups_triggered = True
            #         else:
            #             registry_backup_status_placeholder.warning("Please select backups to delete.")
            #
            # # if st.button("Delete Selected Registry Backups", key="delete_registry_backup_btn",
            # #              disabled=not st.session_state.selected_registry_backups):
            # #     delete_registry_backups_callback()

        # Process triggered actions after all UI elements are rendered
        if st.session_state.get("create_redis_backup_triggered"):
            self.create_redis_backup()
            st.session_state.create_redis_backup_triggered = False # Reset flag
            self.list_redis_backups() # Refresh list after action
        if st.session_state.get("delete_redis_backups_triggered"):
            self.delete_redis_backups(st.session_state.selected_redis_backups)
            st.session_state.delete_redis_backups_triggered = False # Reset flag
            self.list_redis_backups() # Refresh list after action

        if st.session_state.get("create_registry_backup_triggered"):
            self.create_registry_backup()
            st.session_state.create_registry_backup_triggered = False # Reset flag
            self.list_registry_backups() # Refresh list after action
        if st.session_state.get("delete_registry_backups_triggered"):
            self.delete_registry_backups(st.session_state.selected_registry_backups)
            st.session_state.delete_registry_backups_triggered = False # Reset flag
            self.list_registry_backups() # Refresh list after action


bkps = BackupService()
bkps.backup()
