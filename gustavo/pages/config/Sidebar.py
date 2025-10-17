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

        # Small logout button
        if st.button("🚪 Logout", use_container_width=True):
            # Clear Firebase tokens
            if "firebase" in st.session_state:
                st.session_state["firebase"]["id_token"] = None
                st.session_state["firebase"]["custom_token"] = None

            st.toast("👋 Logged out successfully!")
            # Force redirect to main route (Home.py)
            st.switch_page("🏠Home.py")
            st.rerun()

        st.text("Gustavo version {}".format(VERSION))