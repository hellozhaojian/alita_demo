import streamlit as st
import jieba
from markupsafe import Markup
from pathlib import Path
import os
from alita_mini.data.data_config import DataLoadingConfig
from alita_mini.data.service.indexer import IndexerService

# from alita_mini.application.templates import search_result
st.markdown(
    """
   在年报或者中报中搜索管理层的分析内容
"""
)


@st.cache_data
def get_search_service():
    # root_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    # # init config
    # config_file = root_dir / "scripts" / "config" / args.config

    # config = DataLoadingConfig.load(config_file)
    # index_service = IndexerService(config)
    # index_service.load_index()
    # return index_service
    return None


index_service = get_search_service()


def search_result(
    i: int, url: str, title: str, highlights: str, security_code: str, security_name: str, **kwargs
) -> str:
    """HTML scripts to display search results."""
    return f"""
    <br/>
    <div style="font-size: 120%;">
    {i + 1}.
    <a href="{url}">
        {title}
    </a>
</div>
<div style="font-size: 95%;">
    <div style="color: grey; font-size: 95%;">
        <!--{url[:90] + '...' if len(url) > 100 else url}-->
    </div>
    <div style="float: right; font-style: italic; text-align: right;">
        <div style="text-align: right;">
            {security_code} ·&nbsp;{security_name}
        </div>
    </div>
    <div style="clear: both;"></div>
    {highlights}
</div>"""


# 在此处导入您的搜索引擎对象

# 创建搜索引擎对象
# search_engine = YourSearchEngine()
query = st.text_input("Query：")
# 创建输入框和下拉框，并放置在同一行
col1, col2, col3 = st.columns(5)[:3]
# with col1:
#     st.text(" ")
#     st.text(" ")
#     st.text("topk:")
with col1:
    topk = st.selectbox("", [10, 20, 30, 100])
with col2:
    st.text(" ")
    st.text(" ")
    search_button = st.button("搜索")


# 当用户点击“搜索”按钮时执行以下代码
if search_button:
    # 执行搜索操作
    # 调用搜索引擎的方法来执行搜索
    # results = search_engine.search(query, topk)
    #         # items = results = index_service.search(args.query)
    # results = index_service.search(query, int(topk))
    # for item in items:
    #     print(item)
    # 替换以下示例结果为实际结果
    results = [
        {
            "title": "年报1",
            "security_code": "001",
            "security_name": "Company 1",
            "content": "This is some sample content.",
            "url": "https://www.baidu.com",
        },
        {
            "title": "年报1",
            "security_code": "002",
            "security_name": "Company 2",
            "content": "Another example content.",
            "url": "https://www.baidu.com",
        },
        {
            "title": "年报1",
            "security_code": "003",
            "security_name": "Company 3",
            "content": "Content with query keyword.",
            "url": "https://www.baidu.com",
        },
    ]

    # 分词
    query_tokens = jieba.lcut(query)

    # 显示搜索结果
    st.write("搜索结果：")
    from_i = 0
    for i, result in enumerate(results):
        # 在content中逐个词标记为红色
        content = result["content"]
        for token in query_tokens:
            content = content.replace(token, f"<font color='red'>{token}</font>")
        result["highlights"] = content
        st.write(search_result(i + from_i, **result), unsafe_allow_html=True)

        # # 创建自定义布局
        # col1, col2 = st.beta_columns([1, 9])
        # with col1:
        #     st.write("🔍")
        # with col2:
        #     st.markdown(content, unsafe_allow_html=True)
        # st.write("---")
