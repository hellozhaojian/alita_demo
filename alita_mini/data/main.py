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
base_url = "http://static.cninfo.com.cn/"


def is_header(str, header):
    if header is None:
        return False
    return str == header


def is_foot(str, foot):
    if foot is None:
        return False

    s = re.sub(r"\s*\d+\s*", "#num#", str)
    s = s.strip()
    return s == foot or s == "#num#/#num#" or s == "#num#."


def get_foot_header(pdf: PDF, check_pages_num=20, threshold=0.9):
    head_counter = Counter()
    foot_counter = Counter()
    pages_num = len(pdf.pages)
    if pages_num < check_pages_num:
        check_pages_num = pages_num
    for i in range(check_pages_num):
        text_lines = pdf.pages[i].extract_words()
        if text_lines is not None and len(text_lines) == 0:
            continue
        top_line = text_lines[0]["text"]
        bottom_line = text_lines[-1]["text"]
        # print(bottom_line, " !!!!! ", top_line)
        bottom_line = re.sub(r"\d+", "#num#", bottom_line)
        head_counter.update([top_line])
        foot_counter.update([bottom_line])
    head, foot = "fadfasdfa", "dfadfadsfsdf"
    try:
        most_common_head_word, count_head = head_counter.most_common(1)[0]
        most_common_foot_word, count_foot = foot_counter.most_common(1)[0]

        if count_head * 1.0 / check_pages_num >= threshold:
            head = most_common_head_word
        if count_foot * 1.0 / check_pages_num >= threshold:
            foot = most_common_foot_word
    except:
        pass
    return head, foot


def check_bboxes(word, table_bbox):
    """
    Check whether word is inside a table bbox.
    """
    l = word["x0"], word["top"], word["x1"], word["bottom"]
    r = table_bbox
    return l[0] > r[0] and l[1] > r[1] and l[2] < r[2] and l[3] < r[3]


def get_lines_from_page(page, head, foot):
    tables = page.find_tables()
    table_bboxes = [i.bbox for i in tables]
    tables = [{"table": i.extract(), "top": i.bbox[1]} for i in tables]
    non_table_words = [
        word
        for word in page.extract_words()
        if not any([check_bboxes(word, table_bbox) for table_bbox in table_bboxes])
    ]
    lines = []
    lines_x0_x1 = []
    for cluster in pdfplumber.utils.cluster_objects(non_table_words + tables, itemgetter("top"), tolerance=5):
        if "text" in cluster[0]:
            x_0 = x_1 = -1
            inner_lines = []
            for item in cluster:
                # if len(cluster) == 1 and (is_foot(item['text'], foot) or  is_header(item['text'], head)):
                #    continue
                # print(item, cluster)
                if x_0 == -1:
                    if "x0" in item:
                        x_0 = item["x0"]
                if "x1" in item:
                    x_1 = item["x1"]
                if "text" in item:
                    inner_lines.append(item["text"])
                elif "table" in item:
                    inner_lines.append("\n" + json.dumps(item["table"], ensure_ascii=False) + "\n")
            if len(inner_lines) > 0:
                lines.append(" ".join(inner_lines))
                lines_x0_x1.append((x_0, x_1))

            # lines.append(' '.join([i['text'] for i in cluster if not is_foot(i['text'], foot) and not is_header(i['text'], head)]))
        elif "table" in cluster[0]:
            lines.append(cluster[0]["table"])
            lines_x0_x1.append((10000000, -1))

    # Find the minimum of the first elements
    if len(lines_x0_x1) == 0:
        return []
    min_first = min(x[0] for x in lines_x0_x1)

    # Find the maximum of the second elements
    max_second = max(x[1] for x in lines_x0_x1)

    # print(lines)

    # lines = lines[1:-1]
    if len(lines) > 0 and  type(lines[0]) == str and is_header(lines[0], head):
        lines = lines[1:]
    if len(lines) > 0 and type(lines[-1]) == str and is_foot(lines[-1], foot):
        lines = lines[:-1]
    # return lines
    for index, item in enumerate(lines):
        # if type(lines[index]) == str:
        #     lines[index] = lines[index].strip()

        # 如果锁进， 那么要换行

        if abs(lines_x0_x1[index][0] - min_first) > 0.1 and lines_x0_x1[index][0] < 1000000:
            # print(lines_x0_x1[index][0], min_first, "----")
            if type(lines[index]) == str:
                lines[index] = "\n" + lines[index]
        # 如果没有写完，那么换行
        if abs(lines_x0_x1[index][1] - max_second) > 16 and lines_x0_x1[index][1] > 0:
            # print(lines_x0_x1[index][1], max_second, "----", lines[index])
            if type(lines[index]) == str:
                lines[index] = lines[index] + "\n"
        elif lines_x0_x1[index][1] > 0:
            # print('******FULL LINE******', lines_x0_x1[index][1], max_second, "----", lines[index])
            pass
        # print(lines[index], end='')
    return lines


def begin_mda(lines):
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
            ( item.find("管理层讨论与分析") != -1 or item.find("董事会报告") != -1)
            and item.find("第三节") != -1
            and item.find("...............") == -1
            and item.find("请") == -1
        ):
            # print(' BEGIN ', index)
            return True, index
    return False, -1


def end_mda(lines):
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


def get_all_lines_about_mda(pdf: PDF, head: str, foot: str):
    begin = False
    end = False
    all_lines = []
    index = 0
    # print(f"page number: {len(pdf.pages)}")
    for page in pdf.pages:
        index += 1
        if index < 5:
            continue
        # print(index, " ----- page ", head, foot)
        lines = get_lines_from_page(page, head, foot)
        # for line in lines:
        #     print(line)
        begin_mda_status, line_index = begin_mda(lines)
        # print(index, ' ---page   check ------', begin_mda_status)

        if begin is False and begin_mda_status:
            begin = True
            lines = lines[line_index:]
        end_mda_status, line_index = end_mda(lines)
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


def download_and_process_file(url, local_path="/tmp/a.PDF", try_count=3):
    try_times = 0
    response = None
    while True:
        # 下载文件
        print(f"in request {url}")
        response = requests.get(url, proxies={})
        if response.status_code == 200:
            break
            # return response.json()  # 或者返回response.text取决于你需要什么样的数据格式
        else:
            response = None
        try_times += 1
        if try_times >= try_count:
            time.sleep(3)
            break
    if response is None:
        return response
    # response.raise_for_status()  # 确保请求成功

    # 将文件写入本地
    with open(local_path, "wb") as output_file:
        output_file.write(response.content)

    # 读取PDF文件的内容

    pdf = pdfplumber.open(local_path)
    head, foot = get_foot_header(pdf)
    content = get_all_lines_about_mda(pdf, head, foot)
    # print(content)
    # 删除临时文件
    os.remove(local_path)

    return content


def process_item(item, file):
    #item, file = args
    info = json.loads(item.strip())
    """
    "secCode": "001211", "secName": "双枪科技, adjunctUrl
    """
    title = info["announcementTitle"]
    if title.find("关于") != -1 or title.find("摘要") != -1 or title.find("2022") == -1 or title.find("英文") != -1:
        return
    stock_code = info["secCode"]
    # with lock:
    # if stock_code in code_set:
    # return
    # code_set.add(stock_code)
    stock_name = info["secName"]
    relative_url = info["adjunctUrl"]
    pub_time = relative_url.split("/")[-2]
    url = urljoin(base_url, relative_url)
    print(f"begin download {stock_name} {url}")
    content = download_and_process_file(url, "/tmp/a.PDF")
    
    print("done download {stock_name}")
    if content is None or content == "":
        pass
    else:
        pass
        # with lock:
        # code_set.add(stock_code)
    result = {
        "title": title,
        "pubtime": pub_time,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "content": content,
        "url": url,
    }
    #if lock:
    #    with lock:
    #        with open("output.txt", "a") as file:
            # file.write(str(result) + "\n")
    #            file.write(json.dumps(result, ensure_ascii=False) + "\n")

    #with open("output.txt", "a") as file:
        # file.write(str(result) + "\n")
    file.write(json.dumps(result, ensure_ascii=False) + "\n")

def get_processed_codes(filename='output.txt'):
    lines = open(filename, "r").readlines()
    set_code = set()
    for line in lines:
        line = json.loads(line.strip())
        code = line['stock_code']
        set_code.add(code)
    return set_code

if __name__ == "__main__": 
    meta_file = "report_meta_info.txt"
    lines = open(meta_file).readlines()
    set_codes = get_processed_codes()
    # 定义要处理的数组
    data_list = lines  # 请替换为实际的数组元素
    new_data_list = []
    stock_code_set = set_codes
    for item in data_list:
        info = json.loads(item.strip())
        """
        "secCode": "001211", "secName": "双枪科技, adjunctUrl
        """
        title = info["announcementTitle"]
        if title.find("关于") != -1 or title.find("摘要") != -1 or title.find("2022") == -1 or title.find("英文") != -1:
            continue
        stock_code = info["secCode"]
        if stock_code in stock_code_set:
            continue
        if stock_code in [ '300033']:
            print("Not Done")
        stock_code_set.add(stock_code)
        new_data_list.append(item)

    file = open("output.txt.new", "a")

    print(len(new_data_list), " ----- ")
    for item in new_data_list:
        process_item(item, file)

    sys.exit(0)
    # 定义要开启的进程数量
    n = 1  # 请替换为实际需要的进程数量

    # 创建进程池
    pool = multiprocessing.Pool(processes=n)

    # 创建进程锁和共享的集合
    with multiprocessing.Manager() as manager:
        lock = manager.Lock()
        # processed_set = manager.set()

        # 使用进程池并行处理数组中的每个元素
        pool.map(process_item, [(item, lock) for item in new_data_list])

    # 关闭进程池
    pool.close()
    pool.join()
