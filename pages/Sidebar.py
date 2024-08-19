import streamlit as st
import os
class Sidebar:
    def __init__(self):
        parent = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        with st.sidebar:
            logo_url = os.path.join(parent,"images","gustavo_bw.jpeg")
            #logo_url = "./images/gustavo_bw.jpeg"
            st.image(logo_url)
        #     #st.title('')

            home_url = os.path.join(parent,"Home.py")
            st.page_link(home_url,label="Home", icon="🏠")

            st.page_link("pages/ManagerServices.py", label="Manager", icon="💼")
            st.page_link("pages/Apps.py",label="Apps", icon="📊")
            st.page_link("pages/Device_Groups.py",label="Device Groups", icon="🖥️")
            #st.page_link("pages/Connections.py",label="Connections", icon="🌐")
            st.page_link("pages/Monitoring.py",label="Monitoring", icon="⚠️")
            # st.page_link("pages/Configuration.py",label="Configuration",icon="⚙️")
            # with st.expander("Configuration :gear:"):
            #         st.page_link("pages/PlatformConfig.py", label="Platform", icon="🛠️️")
            #         st.page_link("pages/HostConfig.py", label="Hosts", icon="📡️")
            #         st.page_link("pages/SyncerConfig.py", label="Syncer", icon="🔄")