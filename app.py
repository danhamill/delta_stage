import streamlit as st
from multiapp import MultiApp
from apps import (
    vector,

)

st.set_page_config(layout="wide")


apps = MultiApp()

apps.add_app("Delta Stage Record Extenstion", vector.app)


# The main app
apps.run()
