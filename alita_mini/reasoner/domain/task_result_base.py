from pydantic import BaseModel
from pathlib import Path
import logging
import importlib
from alita_mini.adapter.mongo_client import MongoClient


class BaseTaskResult(BaseModel):
    ...


def build_task_results_db():
    plugin_dir = Path(__file__).parent / "results"
    logging.info(f"Scanning plugins... {plugin_dir}")
    parent_module = "alita_mini.reasoner.domain.results"
    client = MongoClient.instance().client
    loop = client.get_io_loop()
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
            if class_name == "BaseTaskResult" or class_name == "BaseModel":
                continue
            if isinstance(cls_instance, type) and issubclass(cls_instance, BaseTaskResult):
                # 如果有,初始化对象
                loop.run_until_complete(cls_instance.build_db(client))
