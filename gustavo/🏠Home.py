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

def load_css(file_name):
    """Load CSS from a file and inject into Streamlit."""
    with open(file_name) as f:
        css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

parent = os.path.dirname(os.path.realpath(__file__))
css_url = os.path.join(parent,"styles","style.css")
load_css(css_url)

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
            checkRegistryStatus()
        with refresh:
            refresh_button = st.button("Refresh", on_click=refresh_registry)

    st.data_editor(st.session_state.registry_dict_list,use_container_width=True)
