from pathlib import Path
import argparse
import os
from alita_mini.log import config_log
from alita_mini.data.data_config import DataLoadingConfig
from alita_mini.adapter.mongo_client import MongoClient
from alita_mini.data.domain.document import Document
from alita_mini.data.domain.doc_enum import DocMainType, DocSubType, MarketType
from typing import List


class CommonDataAccessService(object):
    def __init__(self):
        self.client = MongoClient.instance().client

    def get_documents(
        self,
        security_code: str = "300033",
        doc_type: str = DocMainType.REPORT.value,
        doc_sub_type: str = DocSubType.Annual_Report.value,
        market_name: str = MarketType.A_STOCK_MARKET.value,
        report_year: str = "2023",
    ) -> List[Document]:
        loop = self.client.get_io_loop()
        query = Document.build_query(
            security_code=security_code,
            doc_sub_type=doc_sub_type,
            doc_type=doc_type,
            market_name=market_name,
            report_year=report_year,
        )
        # TODO, do pagination
        count, documents = loop.run_until_complete(Document.list_docs(self.client, query))
        for document in documents:
            id_str = str(document["_id"])
            detail_document = loop.run_until_complete(Document.find_detail(self.client, doc_id=id_str))
            yield Document(**detail_document)


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
    common_data_access = CommonDataAccessService()
    for doc in common_data_access.get_documents():
        print(doc)
