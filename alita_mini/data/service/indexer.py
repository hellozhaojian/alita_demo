import os
import sys
import numpy as np
import faiss
from pathlib import Path
from alita_mini.log import config_log
from alita_mini.data.data_config import DataLoadingConfig
import argparse
import rocketqa
import logging
import json
from tqdm import tqdm
from langchain.text_splitter import CharacterTextSplitter
from alita_mini.data.data_utils import FaissTool


class IndexerService(object):
    def __init__(self, config: DataLoadingConfig):
        self.config = config
        self.index_meta_file = self.config.index_meta_file
        self.dump_file = self.config.dump_file
        self.index_file = self.config.index_file
        self.index_fields = self.config.index_meta_fileds
        # we try to index title and content
        self.encoder_conf = {
            "model": self.config.rocket_model,
            "use_cuda": self.config.use_cuda,
            "device_id": 0,
            "batch_size": self.config.batch_size,
        }
        self.faiss_tool = None
        self.dual_encoder = rocketqa.load_model(**self.encoder_conf)

    def build_index(self):
        index_meta_writer = open(self.index_meta_file, "w")
        # 打开文件
        with open(self.dump_file, "r") as file:
            # 获取文件的总行数
            total_lines = sum(1 for line in file)

        # 再次打开文件
        para_list = []
        title_list = []
        meta_list = []
        with open(self.dump_file, "r") as file:
            # 使用tqdm来展示进度条
            for line in tqdm(file, total=total_lines):
                line = line.strip()
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logging.error(f"JSON解析错误: {e}")
                    continue
                except TypeError as e:
                    logging.error(f"TypeError: {e}")
                    continue
                title = data["title"]
                para = data["content"]
                if title == "" or para == "" or title is None or para is None:
                    continue
                # write meta
                # split para
                # 对para 做必要的处理 TODO
                # 将段落切片
                text_spliter = CharacterTextSplitter(
                    separator="\n", chunk_size=400, chunk_overlap=100, length_function=len
                )
                tmp_para_list = text_spliter.split_text(para)
                # print(len(tmp_para_list))
                tmp_title_list = []
                tmp_meta_list = []
                index = 0
                global_index = len(para_list)
                for para_item in tmp_para_list:
                    # print(para_item)
                    tmp_title_list.append(title)
                    tmp_meta = {key: data.get(key, "null") for key in self.index_fields}
                    tmp_meta["title"] = title
                    tmp_meta["index"] = index
                    tmp_meta["global_index"] = global_index
                    tmp_meta["security_code"] = data["security_code"]
                    tmp_meta["security_name"] = data["security_name"]
                    tmp_meta["report_year"] = data["report_year"]
                    tmp_meta["url"] = data["url"]
                    tmp_meta["content"] = para_item
                    tmp_meta_list.append(json.dumps(tmp_meta, ensure_ascii=False))
                    index += 1
                    global_index += 1
                title_list.extend(tmp_title_list)
                para_list.extend(tmp_para_list)
                meta_list.extend(tmp_meta_list)
        for meta_item in meta_list:
            index_meta_writer.write(meta_item + "\n")
        self._build_index(title_list=title_list, para_list=para_list)
        index_meta_writer.close()

    def _build_index(self, title_list, para_list):
        para_embs = self.dual_encoder.encode_para(para=para_list, title=title_list)
        para_embs = np.array(list(para_embs))

        print("Building index with Faiss...")
        indexer = faiss.IndexFlatIP(768)
        indexer.add(para_embs.astype("float32"))
        faiss.write_index(indexer, self.index_file)

    def load_index(self):
        self.faiss_tool = FaissTool(self.config.index_meta_file, self.config.index_file)

    def search(self, query, top_k=5):
        # encode query
        q_embs = self.dual_encoder.encode_query(query=[query])
        q_embs = np.array(list(q_embs))
        # search with faiss
        search_result = self.faiss_tool.search(q_embs, top_k)
        return search_result


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
    parser.add_argument("-k", "--command", default="build", help="command: [build|query]")
    parser.add_argument("-q", "--query", default="800g 光模块", help="concrete qeury")
    parser.add_argument("-n", "--num", default="20", help="number of results")

    args = parser.parse_args()
    root_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    # init config
    config_file = root_dir / "scripts" / "config" / args.config

    config = DataLoadingConfig.load(config_file)
    index_service = IndexerService(config)
    if args.command == "build":
        index_service.build_index()
    elif args.command == "query":
        index_service.load_index()
        # items = results = index_service.search(args.query)
        items = index_service.search(args.query, int(args.num))
        for item in items:
            print(item)
