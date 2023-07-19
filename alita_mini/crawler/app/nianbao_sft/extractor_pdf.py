import json
import random
from alita_mini.crawler.pdf_text import SimplePdfTextParser
from alita_mini.data.data_utils import full_to_half
import requests
import time
import os
from langchain.text_splitter import CharacterTextSplitter


class TrainingDataExteactor:
    def simple_split(self, current_str, chunk_size=512, pre_boundary=set(["。"]), post_boundary=set(["("]), overlap=150):
        result = []
        # chunk
        current_tokens = []
        chunk_list = []
        for i in range(len(current_str)):
            if current_str[i] in pre_boundary:
                current_tokens.append(current_str[i])
                chunk_list.append("".join(current_tokens))
                current_tokens = []
                continue
            if current_str[i] in post_boundary:
                chunk_list.append("".join(current_tokens))
                current_tokens = [current_str[i]]
                continue
            if len(current_tokens) >= chunk_size:
                chunk_list.append("".join(current_tokens))
                current_tokens = [current_str[i]]
                continue

            current_tokens.append(current_str[i])
        if len(current_tokens) > 0:
            chunk_list.append("".join(current_tokens))
        # merge
        pre_fix_chunks = []
        current_chunks = ""
        for i in range(len(chunk_list)):
            if len(current_chunks + chunk_list[i]) < chunk_size:
                current_chunks += chunk_list[i]
                pre_fix_chunks.append(chunk_list[i])
            else:
                result.append(current_chunks)
                # 有可能此时的current_chunks已经超过了限制
                overlap_str = ""
                for index in list(range(1, 1 + len(pre_fix_chunks))):
                    if len(overlap_str) + len(pre_fix_chunks[-index]) > overlap:
                        break
                    overlap_str = pre_fix_chunks[-index] + overlap_str

                current_chunks = overlap_str[-overlap:] + chunk_list[i]
                pre_fix_chunks = [chunk_list[i]]
        if current_chunks != "":
            result.append(current_chunks)
        return result

    def get_all_train_lines(self, local_path, min_count=200, max_count=500):
        simple_pdf = SimplePdfTextParser(local_path=local_path)
        simple_pdf.get_foot_header()
        all_lines = []
        for index in range(5, simple_pdf.get_page_count()):
            index += 1
            if index < 5:
                continue
            lines = simple_pdf.get_lines_from_page(index, need_table=False)  # get_lines_from_page(page, head, foot)

            all_lines.append(lines)
        content_list = []
        for lines in all_lines:
            for line_index, line in enumerate(lines):
                if type(line) != str:
                    line = json.dumps(line, ensure_ascii=False)
                if line.strip() == "":
                    continue
                content_list.append(line)
        whole_content = "".join(content_list)
        whole_content = whole_content.replace("\n", "")
        whole_content = full_to_half(whole_content)
        result_list = self.simple_split(whole_content)
        return result_list


if __name__ == "__main__":
    local_path = "/Users/alchemy_taotaox/Desktop/mygithub/alita_demo/corpus/year_report.pdf"
    train_data_extractor = TrainingDataExteactor()
    lines = train_data_extractor.get_all_train_lines(local_path=local_path)
    for index, item in enumerate(lines):
        print(f"{item}\n {len(item)}\n\n\n\n")
        if index > 10:
            break
