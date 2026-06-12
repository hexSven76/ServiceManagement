import streamlit as st


def page_title(title: str, subtitle: str = ""):
    st.header(title)
    if subtitle:
        st.caption(subtitle)