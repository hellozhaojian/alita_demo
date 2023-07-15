from alita_mini.log import config_log
import argparse
import logging
import os
import re
import json
from pathlib import Path
from alita_mini.data.data_config import DataLoadingConfig
from alita_mini.adapter.mongo_client import MongoClient
from alita_mini.adapter.redis_client import RedisClient, RedisCache
from alita_mini.data.service.offline_op_service import DocumentsOfflineService
from alita_mini.data.data_utils import DictionarySearcher, full_to_half
from alita_mini.data.domain.doc_enum import DocMainType, DocSubType, ContentType
import pandas as pd
from collections import Counter
import time


# dump mongo
# 实现一个count接口，doc_type, doc_sub_type, content_type, report_year
# 输出
class WordCounterStat:
    def __init__(self, data_config: DataLoadingConfig):
        self.data_config = data_config

        self.alreay_dowload_file = self.data_config.dump_file
        self.doc_offline_service = DocumentsOfflineService(self.data_config)
        self.redis_cache: RedisCache = RedisCache.instance()
        self.db = []
        self.total = 0
        self.url_dict = {}
        self.query_chunk_pattern = re.compile("\s+")

    def build_index(self):
        # self.doc_offline_service.dump_data_for_index(need_index=True)
        lines = open(self.alreay_dowload_file, "r").readlines()
        for line in lines:
            info = json.loads(line.strip())
            info["content"] = info["content"].replace("\n", "")
            info["content"] = full_to_half(info["content"].lower())
            self.db.append(info)
            self.total += 1
            security_code = info["security_code"]
            security_name = info["security_name"]
            key = f"{security_name}({security_code})"
            self.url_dict[key] = info["url"]
        logging.info("build index done")

    def get_latest_search_keys(self):
        return self.redis_cache.get_latest_keys()

    def search(
        self,
        query: str,
        doc_type: str = None,
        doc_sub_type: str = None,
        content_type: str = None,
        report_year: str = "2023",
        need_streamlit_bar=False,
        use_cache=True,
    ):
        query = full_to_half(query.lower())
        data_add_url = None
        if use_cache:
            data_add_url_content = self.redis_cache.get_item_from_cache(query)
            if data_add_url_content is not None:
                try:
                    data_add_url = json.loads(data_add_url_content)
                except Exception as e:
                    logging.error(e)
                    data_add_url = None
        begin = time.time()
        if data_add_url is None:
            dict_search = DictionarySearcher()
            dict_search.add_patterns(query)
            word_counter = {}

            if need_streamlit_bar:
                import streamlit as st

                progress_bar = st.progress(0)
            i = 0
            for info in self.db:
                if need_streamlit_bar:
                    percent_complete = (i + 1) / self.total
                    # 更新进度条的值
                    progress_bar.progress(percent_complete)
                i += 1
                if doc_type is not None and info["doc_type"] != doc_type:
                    continue
                if doc_sub_type is not None and info["doc_sub_type"] != doc_sub_type:
                    continue
                if content_type is not None and info["content_type"] != content_type:
                    continue
                if report_year is not None and info["report_year"] != report_year:
                    continue
                security_code = info["security_code"]
                security_name = info["security_name"]
                key = f"{security_name}({security_code})"
                matched, count = dict_search.match(info["content"])
                if matched:
                    word_counter[key] = count

            # 然后将Counter对象转换为一个列表的字典
            dict_counter = dict(word_counter)

            data = list(dict_counter.items())
            data_add_url = [(key, count, self.url_dict.get(key, "None")) for key, count in data]
            self.redis_cache.cache_item(query, json.dumps(data_add_url, ensure_ascii=False))

        # 最后，使用Pandas DataFrame将字典转换为dataframe
        df = pd.DataFrame(data_add_url, columns=["股票代码", "匹配次数", "URL"])
        last_time = time.time() - begin
        return df, last_time


if __name__ == "__main__":
    config_log(
        project="alita_mini",
        module="data_offline_op",
        log_root="./log",
        print_termninal=True,
    )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        help="config: config file ",
        default="load_data_config.yml",
    )
    parser.add_argument("-k", "--command", help="command: [load|dump]")

    args = parser.parse_args()
    root_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    # init config
    config_file = root_dir / "scripts" / "config" / args.config
    config = DataLoadingConfig.load(config_file)
    MongoClient.instance().build(config)
    RedisClient.instance().build(config.redis_config)
    RedisCache.instance().build(config.redis_config, RedisClient.instance())
    word_countet_stat = WordCounterStat(config)
    word_countet_stat.build_index()
    results = word_countet_stat.search(
        query="800g 光模块",
        doc_sub_type=DocSubType.Annual_Report.value,
        doc_type=DocMainType.REPORT.value,
        content_type=ContentType.Manager_Ana.value,
        report_year="2023",
        need_streamlit_bar=True,
    )
    print(results)
