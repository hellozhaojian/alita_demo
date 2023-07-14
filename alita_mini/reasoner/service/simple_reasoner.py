import argparse
from alita_mini.log import config_log
from pathlib import Path
import os
from alita_mini.reasoner.domain.prompt_factory import PromptFactory
from alita_mini.reasoner.reasoner_config import ReasonerConfig
from alita_mini.adapter.mongo_client import MongoClient
from alita_mini.data.service.common_data_access_service import CommonDataAccessService
from alita_mini.llm.openai_utils import get_completion_from_messages as llm_func
from alita_mini.llm.openai_utils import set_open_ai
from alita_mini.reasoner.domain.task_result_base import build_task_results_db


# load all prompts Done
# construct reason function F Done, 先写死在prompts中。
# select prompt name
# call factory to use Concrete prompt init, get prompt_instance
# read data
# for every data item , call prompt_instance.reason(F, data_item) get task_result
# save task result
class SimpleReasoner(object):
    def __init__(self, config: ReasonerConfig):
        # load prompts

        self.config = config
        self.prompt_factory = PromptFactory.instance()
        self.prompt_objs = self.prompt_factory.load(task_config=self.config.task_config)

    def reason_process(self):
        common_data_access = CommonDataAccessService()
        for security_code in self.config.input_data_config.security_code_list:
            for doc in common_data_access.get_documents(
                security_code=security_code,
                doc_type=self.config.input_data_config.doc_type,
                doc_sub_type=self.config.input_data_config.doc_sub_type,
                market_name=self.config.input_data_config.market_name,
                report_year=self.config.input_data_config.report_year,
            ):
                print(doc)
                for prompt_obj in self.prompt_objs:
                    # @abstractmethod
                    # def reason(self, input_data: Document, llm_func: Callable) -> List[BaseTaskResult]:
                    #     pass
                    prompt_obj.reason(input_data=doc, llm_func=llm_func)


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
        default="report_manager_ana_sum_task.yml",
    )
    parser.add_argument("-k", "--command", help="command: [load|dump]")

    args = parser.parse_args()
    root_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    # init config
    config_file = root_dir / "scripts" / "config" / args.config

    config = ReasonerConfig.load(config_file)
    MongoClient.instance().build(config)
    PromptFactory.instance().scan_prompts()
    build_task_results_db()
    set_open_ai(config.open_ai_key)
    simple_reasoner = SimpleReasoner(config)
    simple_reasoner.reason_process()
