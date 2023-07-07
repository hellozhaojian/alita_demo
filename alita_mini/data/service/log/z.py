import getpass
import json
import logging
import platform
from logging import Formatter, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

def config_log(log_file='log', print_termninal=True):
    print(log_file)
    handlers = [TimedRotatingFileHandler(log_file, when="D")]
    if print_termninal:
        handlers.append(StreamHandler())
    logging.basicConfig(
        format="[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(process)s] [%(filename)s] [%(lineno)s] [%(message)s]",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
        handlers=handlers,
    )

config_log()
logging.info("hi")
