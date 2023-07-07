from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    SUMMARY_TYPE = "总结和分析"


if __name__ == "__main__":
    print(TaskType.SUMMARY_TYPE.value)
