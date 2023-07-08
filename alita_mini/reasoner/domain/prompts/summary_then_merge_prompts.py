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


class SummaryThenMergePrompt(PromptsBase):
    def reason(self, input_data: Document = None, llm_func: Callable = None) -> List[SummrayTaskResults]:
        if input_data is None:
            return []

        result = {
            "doc_id": input_data.doc_id,
            "task_type": self.task_type,
            "task_name": self.task_name,
            "doc_sub_type": input_data.doc_sub_type,
            "market_name": input_data.market_name.value,
            "security_code": input_data.security_code,
            "security_name": input_data.security_name,
            "report_year": input_data.report_year,
        }
        if input_data is not None:
            print(input_data.security_code + "---------reason -------")
            print(result)
        print("I am Here")
        content = input_data.content
        # get summarize Template
        detail_list = self.sum(content)
        for item in detail_list:
            print(item)
        # reason
        summray = self.merge(detail_list=detail_list)
        print(summray)
        return None

    def merge(self, detail_list: List[str]):
        template_str = self.prompt_template_dict.get("merge_prompts.txt", None)
        if template_str is None or template_str == "":
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
