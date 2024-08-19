import streamlit as st
from pages.PlatformConfig import PlatformConfig
from gustavo.pages.SyncerConfig import SyncerConfig
from gustavo.pages.Sidebar import Sidebar
from gustavo.src.Composer import Composer
import socket

def checkSocket(ip,port):
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    location = (ip, int(port))
    check = a_socket.connect_ex(location)

    return check
    # if check == 0:
    #     print("Port is open")
    # else:
    #     print("Port is not open")

def refresh_registry():



    # #with st.spinner("Checking reachability of {}:{}".format(st.session_state.REGISTRY_HOST,st.session_state.REGISTRY_PORT)):
    # with spinner:
    #     check = checkSocket(st.session_state.REGISTRY_HOST,st.session_state.REGISTRY_PORT)
    # # check = checkSocket(st.session_state.REGISTRY_HOST, st.session_state.REGISTRY_PORT)
    # if check:
    #     st.error("Unable to reach {}:{}".format(st.session_state.REGISTRY_HOST,st.session_state.REGISTRY_PORT),icon="🚨")
    #else:
    bcmp = Composer(mode="streamlit", params=st.session_state)

    try:
        r = bcmp.checkLocalRepoImages("all", "all")
        if not r["error"]:
            rep_name_list = r["response"]["repositories"]
            rep_dict_list = []
            for rep in rep_name_list:
                r = bcmp.checkLocalRepoImages(rep, "all")
                if not r["error"]:
                    print(r["response"])
                    rep_dict_list.append(r["response"])
                else:
                    st.error(
                        "rep:{} registry@{}:{} responded with status {}".format(rep,st.session_state.REGISTRY_HOST,
                                                                st.session_state.REGISTRY_PORT,
                                                                r["response"]["status"]),
                        icon="🚨")
            st.session_state.registry_list = rep_dict_list
        else:
            st.error(
                "registry@{}:{} responded with status {}".format(st.session_state.REGISTRY_HOST, st.session_state.REGISTRY_PORT,r["response"]["status"]),
                icon="🚨")
    except Exception as e:
        st.exception(e)

#######################
st.set_page_config(

    page_title="Gustavo Admin Console",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"

)

sc = Sidebar()

if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

if "registry_list" not in st.session_state:
    st.session_state.registry_list = []

with st.expander("Platform Config", expanded=False):
    pc = PlatformConfig()
    pc.platform()

with st.expander("Syncer Config", expanded=False):
    sy = SyncerConfig()
    sy.syncer()

with st.expander("Registry List", expanded = False):
    registry_container = st.container()
    with registry_container:
        status, refresh, _ = st.columns([100,100,100])
        with status:
            if "REGISTRY_HOST" not in st.session_state.keys():
                st.error('REGISTRY_HOST undefined', icon="🚨")

            elif "REGISTRY_PORT" not in st.session_state.keys():
                st.error('REGISTRY_PORT undefined', icon="🚨")

            else:
                with st.spinner(
                    "Checking reachability of {}:{}".format(st.session_state.REGISTRY_HOST, st.session_state.REGISTRY_PORT)):
                    check = checkSocket(st.session_state.REGISTRY_HOST, st.session_state.REGISTRY_PORT)
                    if check:
                        st.error(
                            "Unable to reach {}:{}".format(st.session_state.REGISTRY_HOST, st.session_state.REGISTRY_PORT),
                            icon="🚨")
        with refresh:
            refresh_button = st.button("Refresh", on_click=refresh_registry)

    st.data_editor(st.session_state.registry_list,use_container_width=True)
