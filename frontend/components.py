import streamlit as st


def page_title(title: str, subtitle: str = ""):
    st.header(title)
    if subtitle:
        st.caption(subtitle)


def placeholder_page(title: str, description: str = ""):
    st.subheader(title)

    if description:
        st.write(description)

    st.info("This page UI will be implemented in a later card.")


def render_user_card(username: str, role: str):
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **{username}**")
    st.sidebar.caption(f"Role: {role}")
    st.sidebar.markdown("---")