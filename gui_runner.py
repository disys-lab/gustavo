#import hydralit as hy
#from hydralit import HydraApp
import streamlit as st
# import numpy as np # np mean, np random
# import pandas as pd # read csv, df manipulation
# import time # to simulate a real time data, time loop
# import plotly.express as px # interactive charts
from gui.PlatformConfig import PlatformConfig
from gui.Sidebar import Sidebar

#######################
st.set_page_config(

    page_title="Gustavo Admin Console",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"

)

sc = Sidebar()

# for key in platform_config_keys:
#     platform_config[key] = ""

#
# if __name__ == '__main__':
#     over_theme = {'txc_inactive': '#FFFFFF'}
#     # this is the host application, we add children to it and that's it!
#     app = HydraApp(
#         title='Blockalytics Manager Administration',
#         favicon="🐙",
#         hide_streamlit_markers=False,
#         # add a nice banner, this banner has been defined as 5 sections with spacing defined by the banner_spacing array below.
#         use_banner_images=["./resources/hydra.png", None, {
#             'header': "<h1 style='text-align:center;padding: 0px 0px;color:black;font-size:200%;'>Blockalytics Manager Administration Panel</h1><br>"},
#                            None, "./resources/lock.png"],
#         banner_spacing=[5, 30, 60, 30, 5],
#         use_navbar=True,
#         navbar_sticky=True,
#         navbar_theme=over_theme
#     )
#
# @app.addapp(is_home=True)
# def my_home():
#     hy.info('Hello from Home!')
#
# @app.addapp(title="Platform")
#
#
#     # text_input = st.text_input(
#     #  "Enter some text 👇",
#     #  label_visibility=st.session_state.visibility,
#     #  disabled=st.session_state.disabled,
#     #  placeholder=st.session_state.placeholder,
#     # )
#     #
#     # if text_input:
#     #  st.write("You entered: ", text_input)
#
#
# #manager_config = st.file_uploader("Upload manager.env")
# @app.addapp(title="Syncer")
# def Syncer():
#  hy.info('Hello from app 3, A.K.A, The Best 🥰')
#
# @app.addapp(title='Hosts')
# def Hosts():
#  hy.info('Hello from app 3, A.K.A, The Best 🥰')
#
# #Run the whole lot, we get navbar, state management and app isolation, all with this tiny amount of work.
# app.run()
#
# #
# # # read csv from a github repo
# # df = pd.read_csv("https://raw.githubusercontent.com/Lexie88rus/bank-marketing-analysis/master/bank.csv")
# #
# #
# # st.set_page_config(
# #     page_title = 'Gustavo Administration Page',
# #     page_icon = '✅',
# #     layout = 'wide',
# #     initial_sidebar_state="expanded"
# # )
# #
# # admin_panel_list = ["Apps","Device Groups","Nodes"]
# # config_panel_list = ["Platform","Hosts"]
# # monitor_panel_list = ["Apps","Containers"]
# #
# # # dashboard title
# # st.title("Gustavo Administration Page")
# #
# # # Sidebar
# # with st.sidebar:
# #     st.title('Admin Panels')
# #
