from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    SUMMARY_TYPE = "summary"


if __name__ == "__main__":
    print(TaskType.SUMMARY_TYPE.value)
