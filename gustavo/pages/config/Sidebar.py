import streamlit as st
import os, pkg_resources

def sidebarInit():
    parent = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    logo_url = os.path.join(parent,"images","gustavo_scaled.png")
    icon_url = os.path.join(parent, "images", "gustavo_icon.png")
    st.logo(image=logo_url,icon_image=icon_url)

    with st.sidebar:
        try:
            VERSION = pkg_resources.require("gustavo")[0].version
        except Exception as e:
            VERSION = "dev"

        st.text("Gustavo version {}".format(VERSION))