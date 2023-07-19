import logging
from pydantic import BaseModel, Field
from alita_mini.utils import ordered_yaml_load
from alita_mini.config import MongoConfig
from alita_mini.data.domain.doc_enum import MarketType, DocMainType, DocSubType
from alita_mini.reasoner.domain.prompts_enum import TaskType
from typing import List
from alita_mini.llm.openai_utils import set_open_ai, test_open_ai


# for data loader
class InputDataConfig(BaseModel):
    doc_type: str = DocMainType.REPORT.value
    doc_sub_type: str = DocSubType.Annual_Report.value  # TODO 改成一个列表
    market_name: str = MarketType.A_STOCK_MARKET.value
    security_code_list: List[str]
    report_year: str = "2023"


# for prompts loader
class TaskConfig(BaseModel):
    prompts_path_list: List[str]


class ReasonerConfig(BaseModel):
    mongo_config: MongoConfig
    input_data_config: InputDataConfig
    task_config: TaskConfig
    open_ai_model_name: str = "gpt-3.5-turbo"
    open_ai_key: str
    temperature: int = 0
    max_tokens: int = 2000

    # Add more config for indexer config
    @classmethod
    def load(cls, file_path, load_feature_map=True):
        logging.info(f"begin load [{file_path}]")
        config_data = ordered_yaml_load(file_path)
        config = cls(**config_data)
        logging.info(f"done load [{file_path}] mongo_uri is [{config.mongo_uri}]")
        return config

    @property
    def mongo_uri(self):
        mongo_uri = f"mongodb://{self.mongo_config.user}:{self.mongo_config.password}@{self.mongo_config.host}:{self.mongo_config.port}"
        return mongo_uri

    def __hash__(self):
        return hash(self.meta_file + self.data_file + self.mongo_uri)


if __name__ == "__main__":
    yml_path = "../../scripts/config/report_manager_ana_sum_task.yml"
    c = ReasonerConfig.load(yml_path)
    print(c)
    print(c.mongo_uri)
    print(c.input_data_config.security_code_list)
    print(c.task_config.prompts_path_list)
    set_open_ai(c.open_ai_key)
    test_open_ai()
