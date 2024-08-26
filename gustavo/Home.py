import streamlit as st
#######################
st.set_page_config(

    page_title="Gustavo Admin Console",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"

)
from gustavo.pages.config.Sidebar import sidebarInit
sidebarInit()

from gustavo.pages.config.PlatformConfig import PlatformConfig
from gustavo.pages.config.SyncerConfig import SyncerConfig, refresh_registry, checkRegistryStatus
from gustavo.src.Composer import Composer
import socket,os



    # if check == 0:
    #     print("Port is open")
    # else:
    #     print("Port is not open")

if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

if "registry_dict_list" not in st.session_state:
    st.session_state.registry_dict_list = []

with st.expander("Platform Config", expanded=False):
    pc = PlatformConfig()
    pc.platform()

# with st.expander("Syncer Config", expanded=False):
#     sy = SyncerConfig()
#     sy.syncer()

with st.expander("Registry List", expanded = False):
    registry_container = st.container()
    with registry_container:
        status, refresh, _ = st.columns([100,100,100])
        with status:
            checkRegistryStatus()
        with refresh:
            refresh_button = st.button("Refresh", on_click=refresh_registry)

    st.data_editor(st.session_state.registry_dict_list,use_container_width=True)
