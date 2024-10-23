import yaml, time, sys, os, copy
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gustavo.pages.config.Sidebar import sidebarInit
sidebarInit()
from src.Cache import Cache

def load_css(file_name):
    """Load CSS from a file and inject into Streamlit."""
    with open(file_name) as f:
        css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css("gustavo/pages/styles/style.css")
