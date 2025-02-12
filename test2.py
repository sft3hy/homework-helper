import streamlit as st
from custom_st_components import gen_copy_button
import streamlit.components.v1 as components


with st.container(border=True):
    components.html(gen_copy_button('asdf'), height=60)
