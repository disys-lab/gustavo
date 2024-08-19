import os, sys
import streamlit as st
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from pages.config.PlatformConfig import PlatformConfig

st.set_page_config(

    layout="wide",
    initial_sidebar_state="expanded"

)

platform_tab, hosts_tab, syncer_tab = st.tabs(["Platform", "Hosts", "Syncer"])

with platform_tab:
   pc = PlatformConfig()
   pc.platform()

with hosts_tab:
   st.header("A dog")
   st.image("https://static.streamlit.io/examples/dog.jpg", width=200)

with syncer_tab:
   st.header("An owl")
   st.image("https://static.streamlit.io/examples/owl.jpg", width=200)