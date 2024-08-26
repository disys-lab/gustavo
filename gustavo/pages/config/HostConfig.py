import streamlit as st
from urllib.error import URLError
import pandas as pd
from pages.Sidebar import Sidebar
import yaml

class HostConfig:
    def __init__(self):
        self.hosts_list = {}
        self.df = pd.DataFrame(
            [
                {"Node Name": "manager", "Active?": True, "Host Name":"172.31.18.128",
                 "Blockchain REST Port":"9000", "Blockchain Discovery Port": "30303", "IPFS REST Port":"5001",
                 "IPFS Discovery Port": "4001"},
            ]
        )
        st.session_state["df"] = self.df
        if "visibility" not in st.session_state:
            st.session_state.visibility = "visible"
            st.session_state.disabled = False

    def save_params(self):
        temp_df = self.df.copy(deep=True).rename(columns={"Node Name":"hostid","Active?":"active","Host Name":"hostname",
                                        "Blockchain REST Port":"rest_port","Blockchain Discovery Port":"disc_port",
                                        "IPFS REST Port":"ipfs_rest_port","IPFS Discovery Port":"ipfs_disc_port"
                                })
        temp_df.set_index("hostid",inplace=True)

        self.hosts_list = yaml.dump(temp_df.T.to_dict())

        st.session_state.hosts_list = self.hosts_list

        return self.hosts_list

    def process_uploaded_file(self,uploaded_file):
        temp_hosts_dict = yaml.load(uploaded_file,Loader=yaml.Loader)

        temp_df = pd.DataFrame.from_dict(temp_hosts_dict,orient="index",)
        temp_df.reset_index(drop=False,inplace=True)
        temp_df = temp_df.rename(columns={"index":"Node Name",'active': 'Active?', 'hostname': 'Host Name',
                                      'rest_port': 'Blockchain REST Port', 'disc_port': 'Blockchain Discovery Port',
                                      'ipfs_rest_port': 'IPFS REST Port', 'ipfs_disc_port': 'IPFS Discovery Port'})
        self.df = temp_df
        st.session_state["df"] = temp_df
        # st.experimental_rerun()
        #temp_df.set_index("hostid",inplace=False)
        # print(temp_df)
        # print(self.df)


    def hosts(self):
        st.header("Hosts Configuration")
        # st.divider()
        with st.container():
            #add_row, delete_row, load_config, save_config, download_config = st.columns([50, 50, 50, 50, 50])
            load_config, save_config, download_config = st.columns([50, 50, 50],gap="large")

            with load_config:
                if 'load_config_clicked' not in st.session_state:
                    st.session_state.load_config_clicked = False

                def set_load_config_clicked():
                    st.session_state.load_config_clicked = not (st.session_state.load_config_clicked)

                st.button('Upload Configuration 📤', on_click=set_load_config_clicked)
                if st.session_state.load_config_clicked:
                    uploaded_env_file = st.file_uploader("Upload Configuration File", type=[".yaml",".yml"])
                    if uploaded_env_file is not None:
                        self.process_uploaded_file(uploaded_env_file)
                        #self.edited_df.update(temp_df)

            with save_config:
                if 'save_config_clicked' not in st.session_state:
                    st.session_state.save_config_clicked = False

                def set_save_config_clicked():
                    st.session_state.save_config_clicked = True  # not(st.session_state.save_config_clicked)

                st.button("Save Configuration 💾", on_click=set_save_config_clicked)
                if st.session_state.save_config_clicked:
                    global_platform_env_file_str = self.save_params()
                    st.session_state.save_config_clicked = False

            with download_config:
                # print(global_platform_env_file_str)
                st.download_button(
                    label="Download Configuration ⬇️",
                    data=self.save_params(),
                    file_name='hosts_config.yaml',
                    mime='text',
                )

        self.edited_df = st.data_editor(st.session_state["df"], num_rows="dynamic", use_container_width=True,
                                        key="HOSTS_CONFIG_EDITOR")

        #
        # favorite_command = edited_df.loc[edited_df["rating"].idxmax()]["command"]
        # st.markdown(f"Your favorite command is **{favorite_command}** 🎈")


# st.set_page_config(
#
#     layout="wide",
#     initial_sidebar_state="expanded"
#
# )
# sb = Sidebar()
hc = HostConfig()
hc.hosts()
#


# with add_row:
            #     if 'add_row_clicked' not in st.session_state:
            #         st.session_state.add_row_clicked = False
            #
            #     def set_add_row_clicked():
            #         st.session_state.add_row_clicked= not (st.session_state.add_row_clicked)
            #
            #     st.button('Add ➕', on_click=set_add_row_clicked)
            #     if st.session_state.add_row_clicked:
            #         pass
            #
            # with delete_row:
            #     if 'delete_row_clicked' not in st.session_state:
            #         st.session_state.delete_row_clicked = False
            #
            #     def set_delete_row_clicked():
            #         st.session_state.delete_row_clicked= not (st.session_state.delete_row_clicked)
            #
            #     st.button('Delete ❌', on_click=set_delete_row_clicked)
            #     if st.session_state.delete_row_clicked:
            #         pass