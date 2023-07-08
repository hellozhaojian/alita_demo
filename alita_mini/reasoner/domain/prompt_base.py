from __future__ import annotations
import importlib
from pydantic import BaseModel
from typing import List, Dict, Callable
from abc import abstractmethod

from pathlib import Path
import os

from alita_mini.reasoner.reasoner_config import ReasonerConfig
from alita_mini.data.domain.document import Document
from alita_mini.reasoner.domain.task_result_base import BaseTaskResult


class PromptsBase(BaseModel):
    # prompts_id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    task_type: str = ""
    task_name: str = ""
    version: str = ""
    prompt_template_dict: Dict[str, str]  # key: file_name, value: file_content
    # created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, alias="create_at")
    # updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, alias="update_at")

    @abstractmethod
    def reason(self, input_data: Document, llm_func: Callable) -> List[BaseTaskResult]:
        pass


if __name__ == "__main__":
    ...
