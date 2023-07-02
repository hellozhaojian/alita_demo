import threading
from enum import Enum
from typing import TypedDict
import logging


class RoleType(Enum):
    User = "user"
    System = "system"


class OpenAIResponseStatus(Enum):
    OK = "stop"
    UNKNOWN_ERROR = "unknown_error"


class Platform(Enum):
    WEIXIN = "WEIXIN"


class Message(TypedDict):
    role: str
    content: str


class SingletonType(type):
    _instance_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with SingletonType._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = super().__call__(*args, **kwargs)
        else:
            logging.debug(f"use old instance {cls}")
            print(f"use old instance {cls}")
        return cls._instance
