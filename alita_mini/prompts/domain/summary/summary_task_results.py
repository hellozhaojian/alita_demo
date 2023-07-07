from __future__ import annotations
import logging
import json
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
import datetime
from alita_mini.data.domain.doc_enum import DOC_TYPES, MarketType, DocMainType, DocSubType, Databases, Tables
from alita_mini.custom_types import PyObjectId
from alita_mini.prompts.domain.prompts_enum import TaskType
from typing import List


class SummrayTaskResults(BaseModel):
    result_id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    doc_id: str
    task_type: str = TaskType.SUMMARY_TYPE.value
    task_name: str
    summary: str
    detail_list: List[str]
    doc_sub_type: str
    market_name: MarketType = Field(..., description="Field with values from MyEnum")
    security_code: str
    security_name: str
    report_year: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, alias="create_at")
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, alias="update_at")
