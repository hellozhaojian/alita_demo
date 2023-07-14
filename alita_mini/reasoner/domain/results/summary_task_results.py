from __future__ import annotations
import logging
import json
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
import datetime
from alita_mini.reasoner.domain.task_result_base import BaseTaskResult
from alita_mini.data.domain.doc_enum import DOC_TYPES, MarketType, DocMainType, DocSubType, Databases, Tables
from alita_mini.custom_types import PyObjectId
from alita_mini.reasoner.domain.prompts_enum import TaskType
from typing import List, Union


class SummrayTaskResults(BaseTaskResult):
    result_id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    doc_id: str
    task_type: str = TaskType.SUMMARY_TYPE.value
    task_name: str
    summary: str
    detail_list: List[str]
    doc_sub_type: str  # DocSubType = Field(..., description="Field with values from MyEnum")
    market_name: str  # MarketType = Field(..., description="Field with values from MyEnum")
    security_code: str
    security_name: str
    report_year: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, alias="create_at")
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, alias="update_at")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = False
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "doc_id": "111111",
                "task_type": TaskType.SUMMARY_TYPE.value,
                "task_name": "管理层关于竞争力的分析总结",
                "summary": "xxxxxxx, 垄断",
                "detail_list": ["xxxxx", "xxxx"],
                "doc_sub_type": DocSubType.Annual_Report.value,
                "market_name": MarketType.A_STOCK_MARKET.value,
                "security_code": "300033",
                "security_name": "同花顺",
                "report_year": "2022",
            }
        }

    @classmethod
    async def build_index(cls, client: AsyncIOMotorClient):
        db = client[Databases.DB.value]
        collection = db[Tables.SUMMARY_RESULTS_TALBE.value]
        if await SummrayTaskResults.find_one(client) is None:
            index_name = await collection.create_index(
                [
                    ("doc_id", pymongo.DESCENDING),
                    ("task_type", pymongo.DESCENDING),
                    ("task_name", pymongo.DESCENDING),
                    ("security_name", pymongo.DESCENDING),
                    ("security_code", pymongo.DESCENDING),
                    ("report_year", pymongo.DESCENDING),
                ],
                unique=True,
            )
            logging.info(f"db: docs with index {index_name}")
        else:
            logging.info("db: docs no need build index")

    @classmethod
    async def insert(
        cls,
        client: AsyncIOMotorClient,
        doc_id,
        summary,
        detail_list: List[str],
        security_code,
        security_name,
        report_year,
        task_type=TaskType.SUMMARY_TYPE.value,
        task_name="管理层关于竞争力的分析总结",
        doc_sub_type=DocSubType.Annual_Report.value,
        market_name=MarketType.A_STOCK_MARKET.value,
    ):
        db = client[Databases.DB.value]
        collection = db[Tables.SUMMARY_RESULTS_TALBE.value]
        doc_item_json = {
            "doc_id": doc_id,
            "summary": summary,
            "detail_list": detail_list,
            "security_name": security_name,
            "security_code": security_code,
            "task_name": task_name,
            "task_type": task_type,
            "doc_sub_type": doc_sub_type,
            "market_name": market_name,
            "report_year": report_year,
        }
        try:
            result = await collection.insert_one(doc_item_json)
        except pymongo.errors.DuplicateKeyError as e:
            logging.info(str(e))
            return None
        # result = await collection.insert_one(user.dict())
        if result.acknowledged:
            return result.inserted_id
        else:
            return None

    @classmethod
    def build_query(
        cls,
        report_year=None,
        security_code=None,
        security_name=None,
        doc_sub_type=None,
        market_name=None,
        task_type=None,
        task_name=None,
    ):
        query = {}
        if report_year is not None and report_year != "":
            query["report_year"] = str(report_year)
        if security_code is not None and security_code != "":
            query["security_code"] = security_code
        if security_name is not None and security_name != "":
            query["security_name"] = security_name
        if task_type is not None and task_type != "":
            query["task_type"] = task_type
        if doc_sub_type is not None and doc_sub_type != "":
            query["doc_sub_type"] = doc_sub_type
        if market_name is not None and market_name != "":
            query["market_name"] = market_name
        if task_name is not None and task_name != "":
            query["task_name"] = task_name
        return query

    @classmethod
    async def list_docs(cls, client: AsyncIOMotorClient, query: dict, page_size=20, page_number=0):
        skip_count = (page_number - 1) * page_size
        limit_count = page_size

        db = client[Databases.DB.value]
        collection = db[Tables.SUMMARY_RESULTS_TALBE.value]

        # query = {"doc_type": doc_type, "report_year": report_year}

        # projection = {"title": 1, "security_code": 1, "security_name": 1, "report_date": 1, "url": 1, "_id": 1}

        # 查询符合条件的文档数量
        total_count = await collection.count_documents(query)
        if skip_count > 0:
            cursor = collection.find(query).sort("report_date", pymongo.DESCENDING).skip(skip_count).limit(limit_count)
        else:
            cursor = collection.find(query).sort("report_date", pymongo.DESCENDING).limit(limit_count)
        documents = await cursor.to_list(length=limit_count)
        # async for document in cursor:
        #     objects.append(Document(**document))
        # return objects
        return total_count, documents

    # @classmethod
    # async def find_detail(cls, client: AsyncIOMotorClient, doc_id):
    #     db = client[Databases.DB.value]
    #     collection = db[Tables.TASK_RESULTS_TABLE.value]
    #     print("fuck here")
    #     document = await collection.find_one({"_id": ObjectId(doc_id)})  # 查询指定_id的文档
    #     return document

    @classmethod
    async def find_one(cls, client: AsyncIOMotorClient):
        db = client[Databases.DB.value]
        collection = db[Tables.SUMMARY_RESULTS_TALBE.value]

        doc_item = await collection.find_one()
        if doc_item is None:
            return None
        # print(doc_item)
        return SummrayTaskResults(**doc_item)

    @classmethod
    async def build_db(cls, client: AsyncIOMotorClient):
        await SummrayTaskResults.build_index(client=client)


# if __name__ == "__main__":
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
