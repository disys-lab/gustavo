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

from gustavo.pages.config.loadCss import load_css
load_css()

error_container = st.container()

if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

if "registry_dict_list" not in st.session_state:
    st.session_state.registry_dict_list = []

st.header("Platform Configuration Handler")

with st.expander("Platform Config", expanded=True):
    pc = PlatformConfig()
    pc.platform()

with st.expander("Registry List", expanded = True):
    registry_container = st.container()
    with registry_container:
        status, refresh, _ = st.columns([100,100,100])
        with status:
            checkRegistryStatus(error_container)
        with refresh:
            refresh_button = st.button("Refresh", on_click=refresh_registry)

    st.data_editor(st.session_state.registry_dict_list,use_container_width=True)
