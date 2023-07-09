from tqdm import tqdm
from typing import Dict, Callable
import faiss
import json


class FaissTool:
    """
    Faiss index tools
    """

    def __init__(self, meta_filename, index_filename):
        self.engine = faiss.read_index(index_filename)
        self.id2text = []
        for line in open(meta_filename):
            self.id2text.append(json.loads(line.strip()))

    def search(self, q_embs, topk=5):
        res_dist, res_pid = self.engine.search(q_embs, topk)
        result_list = []
        for i in range(topk):
            result_list.append(self.id2text[res_pid[0][i]])
        return result_list


def process_file_with_tqdm(
    filename: str,
    map_func: Callable,
    map_kwargs: Dict,
    reduce_func: Callable,
    reduce_kwargs: Dict,
):
    # 打开文件
    with open(filename, "r") as file:
        # 获取文件的总行数
        total_lines = sum(1 for line in file)

    # 再次打开文件
    with open(filename, "r") as file:
        # 使用tqdm来展示进度条
        for line in tqdm(file, total=total_lines):
            # 在这里对每一行进行处理
            # 例如，打印每一行内容
            line_result = map_func(line.strip(), **map_kwargs)
            reduce_func(line_result, **reduce_kwargs)
    return reduce_func(None, **reduce_kwargs)
