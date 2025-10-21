import streamlit as st
import os
from gustavo.pages.config.AuthTokenHandler import AuthTokenHandler



AUTH_ENABLED = str(os.getenv("AUTH_ENABLED", "false")).lower() in ("1", "true", "yes", "on")
st.session_state["AUTH_ENABLED"] = AUTH_ENABLED
ADMIN_UID = str(os.getenv("ADMIN_UID", None))
st.session_state["ADMIN_UID"] = ADMIN_UID
st.session_state["ADMIN_MODE"] = False

# --- SESSION STATE SETUP ---
if "firebase" not in st.session_state:
    st.session_state["firebase"] = {"id_token": None, "custom_token": None}
auth = AuthTokenHandler()

def login_page():
    st.set_page_config(page_title="Gustavo Login", layout="centered", initial_sidebar_state="collapsed")

    # Hide sidebar
    st.markdown("""
        <style>
            [data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none;}
            body {background-color: #f6f7fb;}
            div[data-testid="stForm"] {box-shadow:none !important;}
            div.block-container{padding-top:5vh;}
            .gustavo-title{
                text-align:center;
                font-weight:700;
                font-size:1.1rem;
                color:#1f1f2e;
                margin-top:1rem;
            }
            .gustavo-subtitle{
                text-align:center;
                color:#5e5e75;
                font-size:0.85rem;
                margin-bottom:1.5rem;
            }
            div.stButton>button:first-child{
                background-color:#1f1f2e;
                color:white;
                border-radius:0.4rem;
                height:2.5rem;
                width:100%;
                font-weight:600;
                border:none;
            }
            div.stButton>button:hover{background-color:#2b2b45;}
        </style>
    """, unsafe_allow_html=True)

    # Centered layout using columns
    left, center, right = st.columns([1,2,1])
    with center:
        parent = os.path.dirname(os.path.realpath(__file__))
        logo_path = os.path.join(parent, "images", "gustavo_login_transparent.png")

        if os.path.exists(logo_path):
            image_left, image_center, image_right = st.columns([1, 2, 1])
            with image_center:
                st.image(logo_path,)
        else:
            st.warning(f"Logo not found at {logo_path}")

        st.markdown("<p class='gustavo-title'>Sign in to Gustavo</p>", unsafe_allow_html=True)
        st.markdown("<p class='gustavo-subtitle'>Authenticate using your User ID and Token</p>", unsafe_allow_html=True)

        # Form
        with st.form("login_form", clear_on_submit=False):
            user_id = st.text_input("User ID")
            user_token = st.text_input("User Token", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:


                with st.spinner("Authenticating..."):
                    status, custom_token = auth.get_custom_token(user_id, user_token)
                    if status:
                        st.session_state["firebase"]["custom_token"] = custom_token
                        ok, id_token = auth.exchange_custom_with_id_token(custom_token)
                        if ok:
                            st.session_state["firebase"]["id_token"] = id_token
                            #st.toast("🎉 Successfully authenticated!")
                            if user_id == ADMIN_UID:
                                st.toast(f"Authenticated as admin with ADMIN_UID:{ADMIN_UID}")
                                st.session_state["ADMIN_UID"] = ADMIN_UID
                                st.session_state["ADMIN_MODE"] = True
                            else:
                                st.toast(f"Authenticated as user:{user_id}")
                                st.session_state["ADMIN_MODE"] = False
                            st.rerun()
                        else:
                            st.error("Failed to exchange custom token for ID token.")
                    else:
                        st.error("Authentication failed. Please check credentials.")

def home_page():
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

    from gustavo.pages.config.loadCss import load_css
    load_css()

    error_container = st.container()

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
                checkRegistryStatus(error_container)
            with refresh:
                refresh_button = st.button("Refresh", on_click=refresh_registry)

        st.data_editor(st.session_state.registry_dict_list,use_container_width=True)

if "logout_triggered" in st.session_state and st.session_state["logout_triggered"]:
    # Reset and go to login
    st.session_state["logout_triggered"] = False
    st.session_state["firebase"]["id_token"] = None
    st.session_state["firebase"]["custom_token"] = None
    st.rerun()

if AUTH_ENABLED:
    if st.session_state["firebase"]["id_token"]:
        home_page()
    else:
        login_page()
else:
    home_page()