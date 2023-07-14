import logging
from alita_mini.reasoner.domain.prompt_base import PromptsBase
from alita_mini.data.domain.document import Document
from alita_mini.reasoner.domain.results.summary_task_results import SummrayTaskResults
from typing import List, Callable
import json
import time
import traceback
import jinja2
from alita_mini.llm.openai_utils import count_string_tokens, get_completion_from_messages
from langchain.text_splitter import CharacterTextSplitter
from alita_mini.adapter.mongo_client import MongoClient


class SummaryThenMergePrompt(PromptsBase):
    def reason(self, input_data: Document = None, llm_func: Callable = None) -> List[SummrayTaskResults]:
        if input_data is None:
            return []
        # TODO , 只针对ContentType = 管理层分析的进行执行
        result = {
            "doc_id": str(input_data.doc_id),
            "task_type": self.task_type,
            "task_name": self.task_name,
            "doc_sub_type": input_data.doc_sub_type,
            "market_name": input_data.market_name.value,
            "security_code": input_data.security_code,
            "security_name": input_data.security_name,
            "report_year": input_data.report_year,
        }

        # if input_data is not None:
        #     print(input_data.security_code + "---------reason -------")
        #     print(result)
        client = MongoClient.instance().client
        result["client"] = client
        loop = client.get_io_loop()
        # print("I am Here")
        query = SummrayTaskResults.build_query(
            security_code=input_data.security_code,
            task_type=self.task_type,
            task_name=self.task_name,
            report_year=input_data.report_year,
            doc_sub_type=input_data.doc_sub_type,
        )
        count, _ = loop.run_until_complete(SummrayTaskResults.list_docs(client, query))
        if count > 0:
            logging.warn(f"doc_id {result['doc_id']}  on {result['task_type']} {result['task_name']} already in db ")
            return False
        content = input_data.content
        # get summarize Template
        detail_list = self.sum(content)
        if len(detail_list) == 0:
            return False
        # for item in detail_list:
        #     print(item)
        # reason
        summary = self.merge(detail_list=detail_list)
        result["summary"] = summary
        result["detail_list"] = detail_list

        insert_ok = loop.run_until_complete(SummrayTaskResults.insert(**result))
        if insert_ok:
            logging.info(f"process doc_id {result['doc_id']}  on {result['task_type']} {result['task_name']} done ")
        else:
            logging.info(f"process doc_id {result['doc_id']}  on {result['task_type']} {result['task_name']} wrong ")
        return insert_ok

    def merge(self, detail_list: List[str]):
        template_str = self.prompt_template_dict.get("merge_prompts.txt", None)
        if template_str is None or template_str == "":
            logging.warn("no prompts file for merge summary")
            return ""
        environment = jinja2.Environment()
        template = environment.from_string(template_str)
        prompts = template.render(enumerate=enumerate, lines=detail_list)

        data = get_completion_from_messages(prompts, model="gpt-3.5-turbo-16k-0613")
        return data

    def sum(self, content):
        sum_details = []
        template_str = self.prompt_template_dict.get("summary_prompts.txt", None)
        if template_str is None or template_str == "":
            logging.warn("no prompts file for summary")
            return sum_details
        environment = jinja2.Environment()
        template = environment.from_string(template_str)

        # print(content)
        template_count = count_string_tokens(template_str)
        # TODO
        OPENAI_MAX_TOKEN = 10396 - 300
        content_token_count = OPENAI_MAX_TOKEN - template_count - 700

        text_spliter = CharacterTextSplitter(
            separator="\n", chunk_size=content_token_count, chunk_overlap=100, length_function=len
        )
        tmp_para_list = text_spliter.split_text(content)
        tmp_title_list = []
        tmp_meta_list = []
        index = 0
        num_para = len(tmp_para_list)
        max_count = -1
        max_item = ""

        for para_item in tmp_para_list:
            item = template.render(content_fragment=para_item)

            token_count = count_string_tokens(item)
            data = get_completion_from_messages(item, model="gpt-3.5-turbo-16k-0613")
            try:
                sum_details.append(data)
                print(f"process done {index+1} / {num_para}")

            except Exception as e:
                traceback.print_exc()
                print(data)
                print(e)
                print(f"process wrong {index+1} / {num_para}")
            index += 1
        if token_count > max_count:
            max_count = token_count
            max_item = item

        return sum_details
