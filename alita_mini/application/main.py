import streamlit as st

st.set_page_config(
    page_title="你好",
    page_icon="👋",
)

st.write("# 欢迎来到你的投资分析工具箱! 👋")

st.sidebar.success("Select a demo above.")

st.markdown(
    """
    Alita 是一个开箱即用的投资专家系统，他将AGI和金融投资的专家知识有机结合以为你所用，他要颠覆的是一些中低档的人类投顾和理财分析师！
"""
)
