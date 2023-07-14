from datetime import datetime, timedelta
from alita_mini.data.domain.doc_enum import MarketType, DocMainType, DocSubType, ContentType
import requests
import time
from tqdm import tqdm
import json
import logging
from alita_mini.log import config_log
from pathlib import Path
import argparse
import os
from alita_mini.log import config_log
from alita_mini.data.data_config import DataLoadingConfig
import logging
import json
from urllib.parse import urljoin
from alita_mini.adapter.mongo_client import MongoClient
from alita_mini.data.domain.document import Document
from alita_mini.data.service.offline_op_service import DocumentsOfflineService
from dateutil.relativedelta import relativedelta
from alita_mini.crawler.app.nianbao_manager_ana.extractor_pdf import ManagerAnaExteactor


class Craw:
    def __init__(self, config: DataLoadingConfig):
        today = datetime.now()
        self.last_year = str(today - relativedelta(years=1))
        self.this_year = today.strftime("%Y")
        self.market_name = MarketType.A_STOCK_MARKET.value
        self.doc_type = DocMainType.REPORT.value
        self.base_url = "http://static.cninfo.com.cn/"
        self.meta_post_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
        self.url_info = {
            DocSubType.Annual_Report: {
                "url_tag": "category_ndbg_szsh",
                "start_date": f"{self.this_year}-01-01",
                "end_date": self.get_proper_end_day(f"{self.this_year}-07-10"),
            },
            DocSubType.Half_Yearly_Report: {
                "url_tag": "category_bndbg_szsh",
                "start_date": f"{self.this_year}-06-30",
                "end_date": self.get_proper_end_day(f"{self.this_year}-09-30"),
            },
        }
        # mongo里已经下载的信息
        self.alreay_dowload_file = config.dump_file
        # 需要写入到mongo的文件
        self.data_file = config.data_file
        # 需要下载的url
        self.meta_file = config.meta_file
        MongoClient.instance().build(config)
        self.doc_offline_service = DocumentsOfflineService(config)
        self.tmp_file = "/tmp/axzzy.pdf"

    def get_proper_end_day(self, end_day):
        date_format = "%Y-%m-%d"
        today = datetime.now()
        formatted_today = today.strftime(date_format)
        end_date = datetime.strptime(end_day, date_format)
        if today > end_date:
            return end_day
        else:
            return formatted_today

    def get_already_download_info(self):
        self.doc_offline_service.dump_data_for_index(need_index=False)
        lines = open(self.alreay_dowload_file, "r").readlines()
        download_dict = {}
        for line in lines:
            info = json.loads(line.strip())
            key = info["url"] + "-" + info.get("content_type", ContentType.Manager_Ana.value)
            download_dict[key] = 1
        num_docs = len(download_dict)
        logging.info(f"{num_docs} already in db")
        return download_dict

    def split_interval(self, start, end, day_cnt=1):
        date_format = "%Y-%m-%d"
        start_date = datetime.strptime(start, date_format)
        end_date = datetime.strptime(end, date_format)

        result = []

        while start_date < end_date:
            # Calculate the end date of the current interval.
            interval_end_date = start_date + timedelta(days=day_cnt - 1)

            # Ensure that the interval doesn't go beyond the overall end date.
            if interval_end_date > end_date:
                interval_end_date = end_date

            # Append the current interval to the result list.
            result.append(
                (
                    start_date.strftime(date_format),
                    interval_end_date.strftime(date_format),
                    (interval_end_date - start_date).days + 1,
                )
            )
            # Move the start date to the next day after the current interval.
            start_date = interval_end_date + timedelta(days=1)

        return result

    def download_meta_file(self):
        file = open(self.meta_file, "w")
        for doc_type in self.url_info:
            category = self.url_info[doc_type]["url_tag"]
            start_date = self.url_info[doc_type]["start_date"]
            end_date = self.url_info[doc_type]["end_date"]
            results = self.split_interval(start_date, end_date, 1)
            results = results[::-1]
            # for date_range in results:
            for i, date_range in enumerate(tqdm(results)):
                se_date = f"{date_range[0]}~{date_range[1]}"

                page_size = 30
                data = self.request_data(page_size=10, se_date=se_date, category=category)
                try_times = 0
                while data is None:
                    time.sleep(1)
                    data = self.request_data(page_size=10, se_date=se_date, category=category)
                    try_times += 1
                    print(f"craw data wrong, try {try_times}")
                    if try_times == 3:
                        break
                if data is None:
                    continue
                page_count = (data["totalAnnouncement"] - 1) // page_size + 1
                print(page_count)
                begin = time.time()
                for index in range(1, page_count + 1):
                    data = self.request_data(page_num=index, page_size=page_size, se_date=se_date, category=category)
                    try_times = 0
                    while data is None:
                        time.sleep(3)
                        data = self.request_data(
                            page_num=index, page_size=page_size, se_date=se_date, category=category
                        )
                        try_times += 1
                        print(f"craw data wrong, try {try_times}")
                        if try_times == 3:
                            break

                    last = time.time() - begin
                    need_time = last / index * page_count - last
                    every_time = last * 1.0 / index
                    print(
                        f"{index}/{page_count}: last time {last} 秒， need {need_time}, every page cost: {every_time}, count: { len(data['announcements'])}, but page size is {page_size}"
                    )
                    for item in data["announcements"]:
                        item["content_type"] = str(ContentType.Manager_Ana.value)
                        item["doc_type"] = str(DocMainType.REPORT.value)
                        item["doc_sub_type"] = doc_type.value
                        # print(item)
                        file.write(json.dumps(item, ensure_ascii=False) + "\n")
        file.close()

    def craw(self):
        # 1.  抓取url, 年报， 半年报
        self.download_meta_file()
        # 2. 从mongodb中获得已经下载的url
        already_download_dict = self.get_already_download_info()
        # 3. 去掉重复url
        lines = open(self.meta_file).readlines()
        data_list = lines  # 请替换为实际的数组元素
        new_data_list = []
        processed_set = set()
        already_count = 0
        for item in data_list:
            info = json.loads(item.strip())
            relative_url = info["adjunctUrl"]
            url = urljoin(self.base_url, relative_url)
            info["url"] = url
            content_type = info["content_type"]
            key = url + "-" + content_type
            if key in already_download_dict:
                already_count += 1
                continue
            """
            "secCode": "001211", "secName": "双枪科技, adjunctUrl
            """
            title = info["announcementTitle"]
            if (
                title.find("关于") != -1
                or title.find("摘要") != -1
                or (title.find(self.last_year + "年年度") == -1 and title.find(self.this_year + "年半年度") == -1)
                or title.find("英文") != -1
            ):
                continue
            stock_code = info["secCode"]
            doc_sub_type = info["doc_sub_type"]
            processed_key = stock_code + "-" + doc_sub_type
            if processed_key in processed_set:
                continue
            processed_set.add(processed_key)
            new_data_list.append(item)

        file = open(self.data_file, "w")
        # 4.下载抽取
        logging.info(f"***** begin to download {len(new_data_list)} already in db count is {already_count}")

        for i, item in enumerate(new_data_list):
            self.process_item(item, file)
        file.close()
        # 5. 数据加载到mongo
        self.doc_offline_service.load_data_into_mongo()

    def download_and_process_file(self, url, local_path="/tmp/a.PDF", try_count=3):
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
        manager_ana_extractor = ManagerAnaExteactor()
        # pdf = pdfplumber.open(local_path)
        # head, foot = get_foot_header(pdf)
        content = manager_ana_extractor.get_all_lines_about_mda(local_path=local_path)
        # print(content)
        # 删除临时文件
        os.remove(local_path)

        return content

    def process_item(self, item, file):
        # item, file = args
        info = json.loads(item.strip())
        """
        "secCode": "001211", "secName": "双枪科技, adjunctUrl
        """
        title = info["announcementTitle"]

        stock_code = info["secCode"]

        stock_name = info["secName"]
        # url = info["url"]
        relative_url = info["adjunctUrl"]
        pub_time = relative_url.split("/")[-2]
        url = urljoin(self.base_url, relative_url)
        logging.info(f"begin download {stock_name} {url}")
        content = self.download_and_process_file(url, self.tmp_file)

        logging.info(f"done download {stock_name}")
        if content is None or content == "":
            logging.warning(f"url: {url} {stock_name} extract content wrong")
        result = {
            "title": title,
            "pubtime": pub_time,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "content": content,
            "url": url,
            "doc_type": info["doc_type"],
            "doc_sub_type": info["doc_sub_type"],
            "market_name": MarketType.A_STOCK_MARKET.value,
            "content_type": info["content_type"],
        }
        file.write(json.dumps(result, ensure_ascii=False) + "\n")

    def request_data(self, page_size=1000, page_num=1, se_date="2023-04-26~2023-04-26", category="category_bndbg_szsh"):
        url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
        if page_num > 1:
            url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"

        params = {
            "pageNum": page_num,
            "pageSize": page_size,
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": "",
            "searchkey": "",
            "secid": "",
            "category": category,
            "trade": "",
            "seDate": se_date,
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }

        response = requests.post(url, data=params)

        if response.status_code == 200:
            return response.json()  # 或者返回response.text取决于你需要什么样的数据格式
        else:
            return None


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
    root_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
    # init config
    config_file = root_dir / "scripts" / "config" / args.config

    config = DataLoadingConfig.load(config_file)
    craw = Craw(config)
    print(craw.url_info)
    craw.craw()
