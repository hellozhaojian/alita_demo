from __future__ import annotations
import logging
import json
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
import datetime
from alita_mini.data.domain.doc_enum import (
    DOC_TYPES,
    MarketType,
    DocMainType,
    DocSubType,
    Databases,
    Tables,
    ContentType,
)
from alita_mini.custom_types import PyObjectId


class Document(BaseModel):
    doc_id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    doc_type: str
    doc_sub_type: str
    content_type: str = ContentType.Manager_Ana.value
    market_name: MarketType = Field(..., description="Field with values from MyEnum")
    security_code: str
    security_name: str
    report_year: str
    report_date: str
    title: str
    content: str
    url: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, alias="create_at")
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, alias="update_at")

    @validator("doc_sub_type")
    def validate_value_2(cls, value, values):
        doc_type = values.get("doc_type")
        for pair in DOC_TYPES:
            if doc_type == pair.doc_type and value == pair.doc_sub_type:
                return value

        raise ValueError("Invalid combination of doc_type {doc_type} and doc sub type: {value}")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = False
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "doc_type": "report",
                "doc_sub_type": "year_report",
                "content_type": ContentType.Manager_Ana.value,
                "market_name": MarketType.A_STOCK_MARKET.value,
                "security_code": "300033",
                "security_name": "同花顺",
                "report_year": "2022",
                "report_date": "2022-02-28",
                "title": "xxxx",
                "content": "yyyy",
                "url": "zzzz",
            }
        }

    @classmethod
    async def build_index(cls, client: AsyncIOMotorClient):
        db = client[Databases.DB.value]
        collection = db[Tables.DOCUMENTS_TABLE.value]
        if await Document.find_one(client) is None:
            index_name = await collection.create_index(
                [
                    ("doc_type", pymongo.DESCENDING),
                    ("doc_sub_type", pymongo.DESCENDING),
                    ("market_name", pymongo.DESCENDING),
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
        title,
        report_date,
        security_code,
        security_name,
        content,
        url,
        doc_type=DocMainType.REPORT.value,
        doc_sub_type=DocSubType.Annual_Report.value,
        market_name=MarketType.A_STOCK_MARKET.value,
        content_type=ContentType.Manager_Ana.value,
    ):
        report_year = report_date.split("-")[0]
        db = client[Databases.DB.value]
        collection = db[Tables.DOCUMENTS_TABLE.value]
        doc_item_json = {
            "title": title,
            "report_date": report_date,
            "security_code": security_code,
            "security_name": security_name,
            "content": content,
            "url": url,
            "doc_type": doc_type,
            "doc_sub_type": doc_sub_type,
            "market_name": market_name,
            "report_year": report_year,
            "content_type": content_type,
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
        doc_type=None,
        doc_sub_type=None,
        market_name=None,
        content_type=None,
    ):
        query = {}
        if report_year is not None and report_year != "":
            query["report_year"] = report_year
        if security_code is not None and security_code != "":
            query["security_code"] = security_code
        if security_name is not None and security_name != "":
            query["security_name"] = security_name
        if doc_type is not None and doc_type != "":
            query["doc_type"] = doc_type
        if doc_sub_type is not None and doc_sub_type != "":
            query["doc_sub_type"] = doc_sub_type
        if market_name is not None and market_name != "":
            query["market_name"] = market_name
        if content_type is not None and content_type != "":
            query["content_type"] = content_type
        return query

    @classmethod
    async def list_docs(cls, client: AsyncIOMotorClient, query: dict, page_size=20, page_number=0):
        skip_count = (page_number - 1) * page_size
        limit_count = page_size

        db = client[Databases.DB.value]
        collection = db[Tables.DOCUMENTS_TABLE.value]

        # query = {"doc_type": doc_type, "report_year": report_year}

        projection = {"title": 1, "security_code": 1, "security_name": 1, "report_date": 1, "url": 1, "_id": 1}

        # 查询符合条件的文档数量
        total_count = await collection.count_documents(query)
        if skip_count == 0:
            cursor = (
                collection.find(query, projection)
                .sort("report_date", pymongo.DESCENDING)
                .skip(skip_count)
                .limit(limit_count)
            )
        else:
            cursor = collection.find(query, projection).sort("report_date", pymongo.DESCENDING).limit(limit_count)
        documents = await cursor.to_list(length=limit_count)
        # async for document in cursor:
        #     objects.append(Document(**document))
        # return objects
        return total_count, documents

    @classmethod
    async def find_detail(cls, client: AsyncIOMotorClient, doc_id):
        db = client[Databases.DB.value]
        collection = db[Tables.DOCUMENTS_TABLE.value]
        document = await collection.find_one({"_id": ObjectId(doc_id)})  # 查询指定_id的文档
        return document

    @classmethod
    async def find_one(cls, client: AsyncIOMotorClient):
        db = client[Databases.DB.value]
        collection = db[Tables.DOCUMENTS_TABLE.value]

        doc_item = await collection.find_one()
        if doc_item is None:
            return None
        return Document(**doc_item)

    async def build_db(client: AsyncIOMotorClient):
        await Document.build_index(client=client)

    @classmethod
    async def export_collection_to_jsonl(cls, client: AsyncIOMotorClient, output_file, need_index=False):
        db = client[Databases.DB.value]
        collection = db[Tables.DOCUMENTS_TABLE.value]
        # 指定要导出的字段
        fields = [
            "_id",
            "title",
            # "content",
            "security_code",
            "security_name",
            "report_year",
            "url",
            "doc_type",
            "doc_sub_type",
            "content_type",
        ]
        if need_index:
            fields.append("content")

        writer = open(output_file, "w")
        # 查询并逐行写入文档数据
        async for document in collection.find({}, {field: 1 for field in fields}):
            data = {
                "_id": str(document["_id"]),
                "title": "{}({}):{}".format(document["security_name"], document["security_code"], document["title"]),
                # "content": document["content"],
                "security_name": document["security_name"],
                "security_code": document["security_code"],
                "report_year": document["report_year"],
                "url": document["url"],
                "doc_type": document["doc_type"],
                "doc_sub_type": document["doc_sub_type"],
                "content_type": document.get("content_type", ContentType.Manager_Ana.value),
            }
            if need_index:
                data["content"] = document["content"]
            writer.write(json.dumps(data, ensure_ascii=False) + "\n")
        writer.close()
        return True


if __name__ == "__main__":
    print("Hello world")
    MONGODB_ADMINUSERNAME = "root"
    MONGODB_ADMINPASSWORD = "OTNmYTdjYmZkMjE5ZmYzODg0MDZiYWJh"
    mongo_uri = f"mongodb://{MONGODB_ADMINUSERNAME}:{MONGODB_ADMINPASSWORD}@127.0.0.1:27007"
    import motor.motor_asyncio

    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)

    # import asyncio
    loop = client.get_io_loop()
    loop.run_until_complete(Document.build_db(client))
    # loop.run_until_complete(do_insert())
    title = "年报"
    report_date = "2022-02-13"
    security_code = "600000"
    security_name = "中国种棉"
    content = "xxxxsdsfasd扯淡"
    url = "hhhhhhh"
    insert_ok = loop.run_until_complete(
        Document.insert(
            client,
            title=title,
            report_date=report_date,
            security_code=security_code,
            security_name=security_name,
            content=content,
            url=url,
        )
    )
    print(insert_ok)
    query = Document.build_query(security_code=security_code)
    count, documents = loop.run_until_complete(Document.list_docs(client, query))
    print(count)
    for document in documents:
        id_str = str(document["_id"])
        print(document)
        print(f"use {id_str} to find")
        detail = loop.run_until_complete(Document.find_detail(client, doc_id=id_str))
        print(detail)
