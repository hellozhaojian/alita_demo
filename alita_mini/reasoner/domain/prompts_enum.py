from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    SUMMARY_TYPE = "summary"


class RawDataTypes(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    LIST = "list"


if __name__ == "__main__":
    print(TaskType.SUMMARY_TYPE.value)
