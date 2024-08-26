import yaml,time, sys,os,copy
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
from src.Composer import Composer

sidebarInit()

class DGHandler:
    def __init__(self):
        if "app_list" in st.session_state:
            self.dg_list = st.session_state.app_list
        else:
            self.dg_list = []
            st.session_state.dg_list = []

    def dgs(self):
        st.header("Device Group Handler")

        #TODO: Create a visualization for device groups and their corresponding apps
        #TODO: Must be capable of adding more apps or deleting existing apps

#
# st.set_page_config(
#     layout="wide",
#     initial_sidebar_state="expanded"
# )
#
# sb = Sidebar()
dh = DGHandler()
dh.dgs()