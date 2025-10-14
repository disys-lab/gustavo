import os
import streamlit as st

def load_css():
    """
    Loads and injects a custom CSS stylesheet into the current Streamlit app.

    Purpose:
    - Apply global UI styles across the app using a central `style.css` file

    Logic:
    - Determines the absolute path to `styles/style.css` located two levels up from this file
    - Opens and reads the CSS content
    - Injects the CSS using `st.markdown` with `unsafe_allow_html=True`
    - Catches and displays any file access or loading errors as Streamlit error messages

    Error Handling:
    - If the file cannot be found or read, a user-friendly error message is shown in the app

    Returns:
        None
    """
    try:
        # One level up from this file
        current_dir = os.path.dirname(os.path.realpath(__file__))
        css_path = os.path.join(current_dir, "..", "..", "styles", "style.css")
        css_path = os.path.abspath(css_path)  # Normalize the path
        with open(css_path) as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Failed to load CSS: {e}")
