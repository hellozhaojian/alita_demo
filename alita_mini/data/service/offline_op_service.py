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
from alita_mini.data.domain.doc_enum import DocMainType, DocSubType, ContentType, MarketType


class DocumentsOfflineService(object):
    def __init__(self, config: DataLoadingConfig) -> None:
        self.config = config
        self.client = MongoClient.instance().client

    def load_data_into_mongo(self):
        logging.info("begin .... load data {} into {} ".format(self.config.data_file, self.config.mongo_uri))
        base_url = "http://static.cninfo.com.cn/"
        meta_infos = open(self.config.meta_file, "r").readlines()
        url_dict = {}
        for meta in meta_infos:
            meta = json.loads(meta.strip())
            key = meta["secCode"] + meta["announcementTitle"] + meta["adjunctUrl"].split("/")[-2]
            relative_url = meta["adjunctUrl"]
            url = urljoin(base_url, relative_url)
            url_dict[key] = url
        logging.info("url key length {}".format(len(url_dict)))
        data_f = open(self.config.data_file, "r")
        read_count = 0
        read_bad_count = 0
        insert_ok_count = 0

        loop = self.client.get_io_loop()
        loop.run_until_complete(Document.build_db(self.client))
        while True:
            line = data_f.readline()
            if line == "":
                break
            if line.strip() == "":
                continue
            read_count += 1
            try:
                line_info = json.loads(line.strip())
            except Exception as e:
                print(line)
                read_bad_count += 1
                continue
            title = line_info["title"]
            report_date = line_info["pubtime"]
            security_code = line_info["stock_code"]
            security_name = line_info["stock_name"]
            content = line_info["content"]
            url = line_info.get("url", None)
            if url is None:
                key = security_code + title + report_date
                url = url_dict.get(key)
            doc_type = line_info.get("doc_type", DocMainType.REPORT.value)
            doc_sub_type = line_info.get("doc_sub_type", DocSubType.Annual_Report.value)
            market_name = line_info.get("market_name", MarketType.A_STOCK_MARKET.value)
            content_type = line_info.get("content_type", ContentType.Manager_Ana.value)

            insert_ok = loop.run_until_complete(
                Document.insert(
                    self.client,
                    title=title,
                    report_date=report_date,
                    security_code=security_code,
                    security_name=security_name,
                    content=content,
                    url=url,
                    doc_sub_type=doc_sub_type,
                    doc_type=doc_type,
                    content_type=content_type,
                    market_name=market_name,
                )
            )
            if insert_ok:
                insert_ok_count += 1
            else:
                logging.info("{} wrong".format(key))

        logging.info("load {} docs bad {} docs insert count {}".format(read_count, read_bad_count, insert_ok_count))
        logging.info("Done .... load data {} into {} ".format(self.config.data_file, self.config.mongo_uri))

    def dump_data_for_index(self, need_index=True):
        logging.info("begin .... dump {} into {} ".format(self.config.mongo_uri, self.config.dump_file))
        loop = self.client.get_io_loop()
        loop.run_until_complete(Document.build_db(self.client))
        dump_ok = loop.run_until_complete(
            Document.export_collection_to_jsonl(self.client, self.config.dump_file, need_index=need_index)
        )
        logging.info(
            "Done .... dump {} into {}  status {}".format(self.config.mongo_uri, self.config.dump_file, dump_ok)
        )


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
    doc_offline_service = DocumentsOfflineService(config)
    if args.command == "load":
        doc_offline_service.load_data_into_mongo()
    elif args.command == "dump":
        doc_offline_service.dump_data_for_index()
    else:
        logging.error("-k [load|dump] but you provides: {args.command}")
