import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from bson import ObjectId
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid Objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class StudentModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    email: str = Field(...)
    course: str = Field(...)
    gpa: float = Field(..., le=4.0)

    class Config:
        allow_populaton_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdo@example.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": "3.0",
            }
        }

MONGODB_ADMINUSERNAME = "root"
MONGODB_ADMINPASSWORD = "OTNmYTdjYmZkMjE5ZmYzODg0MDZiYWJh"
mongo_uri = (
        f"mongodb://{MONGODB_ADMINUSERNAME}:{MONGODB_ADMINPASSWORD}@127.0.0.1:27007"
    )

#mongo_uri = (
#        f"mongodb://{MONGODB_ADMINUSERNAME}:{MONGODB_ADMINPASSWORD}@127.0.0.1:27002"
#    )

print(mongo_uri)
import motor.motor_asyncio
from fastapi.encoders import jsonable_encoder

client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
db = client.diet_plan
student_item: StudentModel = StudentModel(name="陶志伟", email="29@qq.com", course="Science", gpa="3.1")
print("======manual constructed student======")
print(student_item)

async def do_insert():
    student_item_json = jsonable_encoder(student_item)
    new_student = await db["students"].insert_one(student_item_json)
    print("======inserted student======")
    print(new_student)
    print("inserted id is " + new_student.inserted_id)
    print("======the student in mongodb======")
    created_student = await db["students"].find_one({"_id": new_student.inserted_id})
    print(JSONResponse(status_code=status.HTTP_201_CREATED, content=created_student))
    print(created_student)

# do_insert()
# import asyncio
# asyncio.run(do_insert())
loop = client.get_io_loop()
loop.run_until_complete(do_insert())
