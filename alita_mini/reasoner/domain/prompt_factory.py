from alita_mini.custom_types import SingletonType
import importlib
from pathlib import Path
import logging
from alita_mini.reasoner.domain.prompt_base import PromptsBase
from alita_mini.exceptions import FileSystemOperationError
from alita_mini.reasoner.reasoner_config import TaskConfig, ReasonerConfig
from typing import List
import os


class PromptFactory(metaclass=SingletonType):
    @classmethod
    def instance(cls):
        return PromptFactory()

    def scan_prompts(self):
        self.prompts_dict = {}
        plugin_dir = Path(__file__).parent / "prompts"
        logging.info(f"Scanning plugins... {plugin_dir}")
        parent_module = "alita_mini.reasoner.domain.prompts"

        # 扫描插件目录
        directories = plugin_dir.glob("*/")
        for directory in directories:
            if directory.is_dir():
                continue
            if directory.name.startswith("__"):
                continue

            logging.debug(f"try to load class in {directory} #############")
            module_name = ".".join(directory.name.split(".")[:-1])
            module = importlib.import_module(f"{parent_module}.{module_name}")
            for class_name in dir(module):
                cls_instance = getattr(module, class_name)
                # 检查是否有AutoGPTPluginTemplate的子类
                if class_name == "PromptsBase" or class_name == "BaseModel":
                    continue
                if isinstance(cls_instance, type) and issubclass(cls_instance, PromptsBase):
                    # 如果有,初始化对象
                    self.prompts_dict[class_name] = cls_instance

    def get_prompt_class(self, name):
        return self.prompts_dict.get(name, None)

    def scan_files(self, path):
        result = {}
        path = Path(path)

        for file_path in path.iterdir():
            if file_path.is_file():
                filename = file_path.name
                content = file_path.read_text()
                result[filename] = content

        return result

    def load(self, task_config: TaskConfig) -> List:
        """
        return list of PromptsBase
        """
        prompt_objs = []
        root_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "kg"))
        for relative_path_name in task_config.prompts_path_list:
            task_type = relative_path_name.split("/")[0]
            task_name = "/".join(relative_path_name.split("/")[1:])
            version = relative_path_name.split("/")[-1]
            abs_path = root_dir / relative_path_name
            prompt_template_dict = self.scan_files(abs_path)
            class_name_file = root_dir / "/".join(relative_path_name.split("/")[:-1]) / "prompt_class"
            if class_name_file.exists() is False:
                raise FileSystemOperationError(f"file not found {class_name_file}")
            class_name = class_name_file.read_text()
            args = {
                "version": version,
                "prompt_template_dict": prompt_template_dict,
                "class_name": class_name,
                "task_type": task_type,
                "task_name": task_name,
            }
            prompt_impl_cls = PromptFactory.instance().get_prompt_class(class_name)
            obj = prompt_impl_cls(**args)
            prompt_objs.append(obj)
            # prompt_objs.append((version, prompt_template_dict, class_name, task_type, task_name))
        return prompt_objs


if __name__ == "__main__":
    from alita_mini.log import config_log

    config_log(
        project="alita_mini",
        module="load_prompts",
        log_root="./log",
        print_termninal=True,
    )
    prompt_factory = PromptFactory.instance()
    prompt_factory.scan_prompts()
    print("hello")
    yml_path = "../../../scripts/config/report_manager_ana_sum_task.yml"
    c = ReasonerConfig.load(yml_path)
    prompt_objs = prompt_factory.load(task_config=c.task_config)
    for prompt_obj in prompt_objs:
        prompt_obj.reason()
