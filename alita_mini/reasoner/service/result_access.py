from pathlib import Path
import argparse
import os
from alita_mini.log import config_log
from alita_mini.data.data_config import DataLoadingConfig
from alita_mini.adapter.mongo_client import MongoClient
from alita_mini.reasoner.domain.results.summary_task_results import SummrayTaskResults
from alita_mini.reasoner.domain.prompts_enum import TaskType
from typing import List


"""
#     print("Hello world")
#     MONGODB_ADMINUSERNAME = "root"
#     MONGODB_ADMINPASSWORD = "OTNmYTdjYmZkMjE5ZmYzODg0MDZiYWJh"
#     mongo_uri = f"mongodb://{MONGODB_ADMINUSERNAME}:{MONGODB_ADMINPASSWORD}@127.0.0.1:27007"
#     import motor.motor_asyncio

#     client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)

#     # import asyncio
#     loop = client.get_io_loop()
#     loop.run_until_complete(SummrayTaskResults.build_db(client))
#     # loop.run_until_complete(do_insert())
#     doc_id = "111111"
#     task_name = "管理层关于竞争力的分析总结"
#     summary = "xxxxxxx, 垄断"
#     detail_list = ["xxxxx", "xxxx"]
#     security_code = "300033"
#     security_name = "同花顺"
#     report_year = "2020"

#     insert_ok = loop.run_until_complete(
#         SummrayTaskResults.insert(
#             client,
#             doc_id=doc_id,
#             task_name=task_name,
#             security_code=security_code,
#             security_name=security_name,
#             summary=summary,
#             detail_list=detail_list,
#             report_year=report_year,
#         )
#     )
#     print(insert_ok)
#     query = SummrayTaskResults.build_query(security_code=security_code)
#     count, documents = loop.run_until_complete(SummrayTaskResults.list_docs(client, query))
#     print(count)
#     for document in documents:
#         id_str = str(document["_id"])
#         print(document)

"""


class CommonDataAccessService(object):
    def __init__(self):
        self.client = MongoClient.instance().client

    def get_summary_results(
        self,
        security_code: str = "300308",
        task_type: str = TaskType.SUMMARY_TYPE.value,
        report_year: str = "2023",
        doc_sub_type: str = "年报",
        page_size=20,
        page_number=0,
    ) -> List[SummrayTaskResults]:
        loop = self.client.get_io_loop()
        query = SummrayTaskResults.build_query(
            security_code=security_code, task_type=task_type, report_year=report_year, doc_sub_type=doc_sub_type
        )
        print(query)
        # TODO, do pagination
        count, documents = loop.run_until_complete(
            SummrayTaskResults.list_docs(self.client, query, page_size=page_size, page_number=page_number)
        )

        results = []
        for document in documents:
            id_str = str(document["_id"])
            results.append(SummrayTaskResults(**document))
        return count, results


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
    count, docs = common_data_access.get_summary_results()
    for doc in docs:
        print(doc)

    print(count)
