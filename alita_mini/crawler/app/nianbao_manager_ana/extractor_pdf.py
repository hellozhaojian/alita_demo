import json
from alita_mini.crawler.pdf_text import SimplePdfTextParser
import requests
import time
import os


class ManagerAnaExteactor:
    def begin_mda(self, lines):
        len_lines = len(lines)
        if len_lines < 1:
            return False, -1
        # if type(lines[0]) != str:
        #     return False, -1
        # print(" check beign count ", len_lines)
        for index, item in enumerate(lines):
            # print("CHECK", item, index)
            if type(item) != str:
                continue
            if (
                (item.find("管理层讨论与分析") != -1 or item.find("董事会报告") != -1)
                and item.find("第三节") != -1
                and item.find("...............") == -1
                and item.find("请") == -1
            ):
                # print(' BEGIN ', index)
                return True, index
        return False, -1

    def end_mda(self, lines):
        if len(lines) < 1:
            return False, -1
        # if type(lines[0]) != str:
        #     return False, -1
        # print("check: ", lines[0], "$$$$$$")
        for index, item in enumerate(lines):
            if type(item) != str:
                continue
            if (
                item.find("公司治理") != -1
                and item.find("第四节") != -1
                and item.find("...............") == -1
                and item.find("请") == -1
            ):
                return True, index
        return False, -1

    def get_all_lines_about_mda(self, local_path):
        simple_pdf = SimplePdfTextParser(local_path=local_path)
        simple_pdf.get_foot_header()
        begin = False
        end = False
        all_lines = []
        # print(f"page number: {len(pdf.pages)}")
        for index in range(simple_pdf.get_page_count()):
            index += 1
            if index < 5:
                continue
            lines = simple_pdf.get_lines_from_page(index, need_table=False)  # get_lines_from_page(page, head, foot)
            # for line in lines:
            #     print(line)
            begin_mda_status, line_index = self.begin_mda(lines)
            # print(index, ' ---page   check ------', begin_mda_status)

            if begin is False and begin_mda_status:
                begin = True
                lines = lines[line_index:]
            end_mda_status, line_index = self.end_mda(lines)
            if begin and end_mda_status:
                all_lines.append(lines[:line_index])
                break
            if begin is True:
                all_lines.append(lines)
        # print(f" final page index {index}")
        content_list = []
        for lines in all_lines:
            for line_index, line in enumerate(lines):
                if type(line) != str:
                    line = json.dumps(line, ensure_ascii=False)
                # print(line, end='')
                if line.strip() == "":
                    continue
                content_list.append(line)
        return "".join(content_list)
