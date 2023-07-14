import streamlit as st
import jieba
from markupsafe import Markup
from pathlib import Path
import os
from alita_mini.data.data_config import DataLoadingConfig
from alita_mini.data.service.indexer import IndexerService
from alita_mini.adapter.mongo_client import MongoClient
from alita_mini.reasoner.service.result_access import CommonDataAccessService
from alita_mini.reasoner.domain.results.summary_task_results import SummrayTaskResults
import streamlit.components.v1 as components

# from alita_mini.application.templates import search_result
st.markdown(
    """
   对年报进行总结
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
    common_data_access = CommonDataAccessService()
    return common_data_access


def search_result(i: int, summary_result: SummrayTaskResults) -> str:
    """HTML scripts to display search results."""

    return f"""
    <br/>
    <div style="font-size: 120%;">
    {i + 1}.
        {summary_result.security_name} - {summary_result.security_code} - {summary_result.task_type} - {summary_result.doc_sub_type}
</div>
<div style="font-size: 95%;">
    <div style="color: grey; font-size: 95%;">
        <!--{i}-->
    </div>
    <div style="float: right; font-style: italic; text-align: right;">
        <div style="text-align: right;">
            {summary_result.task_name} ·&nbsp;{summary_result.report_year}
        </div>
    </div>
    <div style="clear: both;"></div>
    {summary_result.summary}
</div>"""


# def render_hide_show_elements_old(elements):
#     html_code = """
#         <style>
#         .container {
#             display: none;
#             width: 100%;
#             color: black;
#             padding: 20px;
#             margin: 10px;
#             background-color: white;
#             overflow-y: scroll;  /* 在这里添加滚动属性 */
#             max-height: 500px;  /* 设定一个固定的最大高度 */
#         }
#         .trigger {
#             width: 100%;
#             height: 10px;
#             background-color: transparent;
#         }
#         .trigger:hover {
#             height: auto;
#         }
#         .trigger:hover .container {
#             display: block;
#         }
#         </style>
#         <div class="trigger">
#             <div class="container">
#     """

#     for element in elements:
#         html_code += f"<p>{element}</p>"

#     html_code += """
#             </div>
#         </div>
#     """
#     components.html(html_code)


def render_hide_show_elements(elements):
    html_code = """
        <style>
        .container {
            display: none;
            width: calc(100% - 40px);  /* 减去左右两侧的 padding ， 之前的是 width: 100%;*/
            color: black;
            padding: 20px;
            margin: 10px;
            background-color: white;
            overflow-y: auto;  /* 更改为 auto，仅在需要时显示滚动条 */
            max-height: 90vh;  /* 更改为视口高度的90%，以便在内容多时可以滚动 */
            border: 1px solid black;  /* 添加边框 */
        }
        .trigger {
            width: 100%;
            min-height: 10px;  /* 添加最小高度，确保触发区始终可见 */
            background-color: transparent;
            height: auto;  /* 更改为auto，以适应内容的高度 */
        }
        .trigger:hover .container {
            display: block;
        }
        </style>
        <div class="trigger">
            <div class="container">
    """

    for element in elements:
        html_code += f"<p>{element}</p>"

    html_code += """
            </div>
        </div>
    """
    components.html(html_code)


if __name__ == "__main__":
    task_type = st.sidebar.selectbox("Task Type", ["summary"])

    # Set report_year variable
    report_year = st.sidebar.selectbox("Report Year", ["2023", "2022", "2021", "2020", "2019"])
    doc_sub_type = st.sidebar.selectbox("报告类型", ["年报", "半年报"])

    # Set page_size variable
    page_size = st.sidebar.selectbox("Page Size", [10, 20, 30, 50])

    # Set page_number variable (dynamically filled dropdown)
    # Replace the options list with your desired logic to populate the dropdown
    options = list(range(1, 21))  # Example options list
    page_number = st.sidebar.selectbox("Page Number", options)

    # Display the selected variables
    st.write("Selected Variables:")
    st.write("Task Type:", task_type)
    st.write("Report Year:", report_year)
    st.write("Page Size:", page_size)
    st.write("Page Number:", page_number)

    query = st.text_input("股票代码：")

    search_button = st.button("搜索")
    common_data_access = get_search_service()
    if search_button:
        # 执行搜索操作
        # 调用搜索引擎的方法来执行搜索
        # results = search_engine.search(query, topk)
        #         # items = results = index_service.search(args.query)
        count, results = common_data_access.get_summary_results(
            security_code=query,
            task_type=task_type,
            report_year=report_year,
            page_size=page_size,
            page_number=page_number,
            doc_sub_type=doc_sub_type,
        )
        st.write(f"搜索到 {count} 条结果， 共{(count+1)//page_size + 1}页, 每页{page_size}个结果, 现在在第{page_number} 页")
        for i, item in enumerate(results):
            print(item)
            st.write(search_result(i, item), unsafe_allow_html=True)
            # Example list data
            data_list = ["Item 1", "Item 2", "Item 3"]

            # Call the show_list_on_hover function
            # 你可以像这样调用这个函数：
            detail_list = []
            for content in item.detail_list:
                content = content.replace("<", "&lt;")

                # Replace '>' with '&gt;'
                content = content.replace(">", "&gt;")
                detail_list.append(content)
            for tmp in range(10):
                detail_list.append("\n\n")
            render_hide_show_elements(detail_list)
