import streamlit as st
from pathlib import Path
import os
from alita_mini.data.data_config import DataLoadingConfig
from alita_mini.adapter.mongo_client import MongoClient
from alita_mini.adapter.redis_client import RedisCache, RedisClient
from alita_mini.data.service.words_counter import WordCounterStat
import streamlit.components.v1 as components
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt


# from streamlit import caching


def app():
    st.title("chaggpt摘要")


st.write("# 公告词频统计工具箱! 👋")


st.markdown(
    """
    输入词汇统计管理层分析中出现的评率， 词的格式 
    
    * 一般and 组合， 例如 “800g 光模块"
    * 支持词组 [光模块|光组件]
    * 支持否定 !行业光模块
"""
)
# from alita_mini.application.templates import search_result
st.markdown(
    """
   公告 CTR+F 匹配
"""
)

import asyncio

# loop = asyncio.get_event_loop()


@st.cache_resource
def get_search_service():
    root_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    # init config
    config_file = root_dir / "scripts" / "config" / "load_data_config.yml"

    config = DataLoadingConfig.load(config_file)
    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()

    MongoClient.instance().build(config, loop)
    RedisClient.instance().build(config.redis_config)
    RedisCache.instance().build(config.redis_config, RedisClient.instance())

    word_countet_stat = WordCounterStat(config)
    word_countet_stat.build_index()
    return word_countet_stat


if __name__ == "__main__":
    # caching.clear_cache()
    doc_type = st.sidebar.selectbox("文档类型", ["公告"])
    content_type = st.sidebar.selectbox("内容类型", ["管理层分析"])
    # Set report_year variable
    report_year = st.sidebar.selectbox("Report Year", ["2023", "2022", "2021", "2020", "2019"])
    doc_sub_type = st.sidebar.selectbox("报告类型", ["年报", "半年报"])
    counter_service = get_search_service()
    # 历史搜索记录
    st.sidebar.header("历史记录")
    history = counter_service.get_latest_search_keys()
    if history is None or len(history) == 0:
        history = ["800g 光模块"]
    selected_history = st.sidebar.selectbox("", history)

    input_value = st.empty()
    if selected_history:
        query = input_value.text_input("输入框", value=selected_history)
    # query = st.text_input("关键词：")

    search_button = st.button("搜索")

    if search_button:
        df, cost_time = counter_service.search(
            query=query,
            doc_sub_type=doc_sub_type,
            doc_type=doc_type,
            content_type=content_type,
            report_year=report_year,
            need_streamlit_bar=True,
        )
        st.write(f" COST {cost_time:.2f} 秒")
        # 对df按'匹配次数'列进行排序，取前20个
        df_sorted = df.sort_values(by="匹配次数", ascending=False).head(20)

        # 创建一个交互式的柱状图
        chart = alt.Chart(df_sorted).mark_bar().encode(x="股票代码", y="匹配次数", tooltip=["股票代码", "匹配次数"]).interactive()

        # 在Streamlit中显示图表
        st.altair_chart(chart)

        # 添加序号列
        df_sorted["序号"] = range(1, len(df_sorted) + 1)

        # 重排列列
        df_sorted = df_sorted[["序号", "股票代码", "匹配次数", "URL"]]

        # 生成包含链接的HTML表格
        def make_clickable(val):
            # 将url转换为html链接
            return '<a href="{}">{}</a>'.format(val, "公告地址")

        df_sorted["URL"] = df["URL"].apply(make_clickable)

        # df_sorted.style.format({"URL": make_clickable})
        # st.dataframe(df_sorted)

        # 将数据帧转换为HTML表格
        html_table = df_sorted.to_html(escape=False, index=False)

        # 在Streamlit应用中显示HTML表格
        st.markdown(html_table, unsafe_allow_html=True)
