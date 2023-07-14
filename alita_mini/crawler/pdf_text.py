import multiprocessing
from urllib.parse import urljoin
import os
from tqdm import tqdm
import requests
import json
import os
import time
import pdfplumber
import sys
from functools import lru_cache

if "all_proxy" in os.environ:
    print("pop all proxy")
    os.environ.pop("all_proxy")
from pdfplumber.pdf import PDF
import json
from operator import itemgetter
import json
from pdfplumber.pdf import PDF
import re
from collections import Counter
from abc import abstractclassmethod
import logging


class BasePdfTextParser:
    def __init__(self):
        pass

    @abstractclassmethod
    def get_text_lines_from_pdf(self, page_no=0):
        ...

    @abstractclassmethod
    def get_foot_header(self, check_pages_num=20, threshold=0.9):
        ...


class SimplePdfTextParser(BasePdfTextParser):
    def __init__(self, local_path="/Users/alchemy_taotaox/Desktop/mygithub/alita_demo/corpus/600271.pdf"):
        try:
            self.pdf: PDF = pdfplumber.open(local_path)
        except Exception as e:
            logging.error(f"error{e} with file [{local_path}]")
            self.pdf: PDF = None
        self.foot = None
        self.head = None

    @lru_cache(maxsize=None)
    def get_foot_header(self, check_pages_num=20, threshold=0.9):
        if self.pdf is None:
            return None, None
        head_counter = Counter()
        foot_counter = Counter()
        pages_num = len(self.pdf.pages)
        if pages_num < check_pages_num:
            check_pages_num = pages_num
        for i in range(check_pages_num):
            text_lines = self.pdf.pages[i].extract_words()
            if text_lines is None:
                continue
            if text_lines is not None and len(text_lines) == 0:
                continue
            top_line = text_lines[0]["text"]
            bottom_line = text_lines[-1]["text"]
            bottom_line = re.sub(r"\d+", "#num#", bottom_line)
            head_counter.update([top_line])
            foot_counter.update([bottom_line])
        head, foot = None, None
        if len(head_counter) > 0:
            # 这里有一个bug, 如果有多个值的统计数据是一样的， 那么就有多个most_common
            most_common_head_word, count_head = head_counter.most_common(1)[0]
            if count_head * 1.0 / check_pages_num >= threshold:
                head = most_common_head_word
        if len(foot_counter) > 0:
            # 这里有一个bug, 如果有多个值的统计数据是一样的， 那么就有多个most_common
            most_common_foot_word, count_foot = foot_counter.most_common(1)[0]

            if count_foot * 1.0 / check_pages_num >= threshold:
                foot = most_common_foot_word
        self.head = head
        self.foot = foot
        return head, foot

    def is_header(self, first_line):
        if self.head is None:
            return False
        return first_line == self.head

    def is_foot(self, last_line):
        if self.foot is None:
            return False
        s = re.sub(r"\s*\d+\s*", "#num#", last_line)
        s = s.strip()
        # hard code sample number pattern
        return s == self.foot or s == "#num#/#num#" or s == "#num#."

    @lru_cache(maxsize=None)
    def get_page_count(self):
        if self.pdf is None:
            return -1
        return len(self.pdf.pages)

    def check_word_in_bboxes(self, word, table_bbox):
        """
          Check whether word is inside a table bbox.

           __ __top __ __
          |               |
        x0|     x         | x1
          |__ __bot __ __ |
        """
        l = word["x0"], word["top"], word["x1"], word["bottom"]
        r = table_bbox
        return l[0] > r[0] and l[1] > r[1] and l[2] < r[2] and l[3] < r[3]

    def get_lines_from_page(self, page_index, need_table=False):
        if self.pdf is None:
            return []
        if page_index < 0 or page_index >= self.get_page_count():
            logging.error(f"page size is {self.get_page_count()} but the index is {page_index}")
            return []
        page = self.pdf.pages[page_index]
        tables = page.find_tables()
        table_bboxes = [i.bbox for i in tables]
        tables = [{"table": i.extract(), "top": i.bbox[1]} for i in tables]
        non_table_words = [
            word
            for word in page.extract_words()
            if not any([self.check_word_in_bboxes(word, table_bbox) for table_bbox in table_bboxes])
        ]
        lines = []
        # 记录每一行的x0, x1坐标
        lines_x0_x1 = []
        for cluster in pdfplumber.utils.cluster_objects(non_table_words + tables, itemgetter("top"), tolerance=5):
            if "text" in cluster[0]:
                x_0 = x_1 = -1
                inner_lines = []
                for item in cluster:
                    if x_0 == -1:
                        if "x0" in item:
                            x_0 = item["x0"]
                    if "x1" in item:
                        x_1 = item["x1"]
                    if "text" in item:
                        inner_lines.append(item["text"])
                    elif "table" in item:
                        if need_table is True:
                            inner_lines.append("\n" + json.dumps(item["table"], ensure_ascii=False) + "\n")
                if len(inner_lines) > 0:
                    lines.append(" ".join(inner_lines))
                    lines_x0_x1.append((x_0, x_1))

            elif "table" in cluster[0]:
                if need_table:
                    lines.append(cluster[0]["table"])
                    lines_x0_x1.append((10000000, -1))

        # Find the minimum of the first elements
        if len(lines_x0_x1) == 0:
            return []
        min_first = min(x[0] for x in lines_x0_x1)
        # Find the maximum of the second elements
        max_second = max(x[1] for x in lines_x0_x1)

        # 去掉页眉，页脚
        if len(lines) > 0 and type(lines[0]) == str and self.is_header(lines[0]):
            lines = lines[1:]
        if len(lines) > 0 and type(lines[-1]) == str and self.is_foot(lines[-1]):
            lines = lines[:-1]
        # 由于pdf有很多后续的对象的位置移动的操作，下面的规则很有可能没有什么用
        for index, item in enumerate(lines):
            # 如果有缩进， 那么要换行
            if abs(lines_x0_x1[index][0] - min_first) > 0.1 and lines_x0_x1[index][0] < 1000000:
                if type(lines[index]) == str:
                    lines[index] = "\n" + lines[index]
            # 如果没有写完，那么换行
            if abs(lines_x0_x1[index][1] - max_second) > 16 and lines_x0_x1[index][1] > 0:
                if type(lines[index]) == str:
                    lines[index] = lines[index] + "\n"
            elif lines_x0_x1[index][1] > 0:
                pass
        return lines


if __name__ == "__main__":
    simple_pdf_text_parser = SimplePdfTextParser()
    print(simple_pdf_text_parser.get_foot_header())
    print(simple_pdf_text_parser.get_page_count())
    print(simple_pdf_text_parser.get_page_count())
    lines = simple_pdf_text_parser.get_lines_from_page(20)
    for line in lines:
        print(line)
