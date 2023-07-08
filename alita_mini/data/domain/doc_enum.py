from dataclasses import dataclass
from enum import Enum


@dataclass
class DocType:
    doc_type: str = "report"
    doc_sub_type: str = "year_report"


class DocMainType(Enum):
    REPORT = "公告"


class DocSubType(Enum):
    Annual_Report = "年报"
    Half_Yearly_Report = "半年报"


class MarketType(Enum):
    A_STOCK_MARKET = "A股"


class Databases(Enum):
    DB = "alita_mini"


class Tables(Enum):
    DOCUMENTS_TABLE = "docs"
    TASK_RESULTS_TABLE = "task_results"


DOC_TYPES = [
    DocType(doc_type=DocMainType.REPORT.value, doc_sub_type=DocSubType.Annual_Report.value),
    DocType(doc_type=DocMainType.REPORT.value, doc_sub_type=DocSubType.Half_Yearly_Report.value),
]


if __name__ == "__main__":
    for item in DOC_TYPES:
        print(item.doc_type, item.doc_sub_type)
    print("hello")
    print(MarketType.A_STOCK_MARKET.value)
