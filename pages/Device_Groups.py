import yaml,time, sys,os,copy
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
# from pages.Sidebar import Sidebar
from src.Composer import Composer

parent = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
logo_url = os.path.join(parent,"images","gustavo_bw.png")
st.logo(logo_url)

with st.sidebar:
    st.text("Gustavo Admin Tool")

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