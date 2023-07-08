import logging
import time
from collections import OrderedDict
from pathlib import Path
from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.history import InMemoryHistory
import requests
import yaml
import time
from functools import wraps

from alita_mini.exceptions import FileSystemOperationError

# TODO this is global definition
session = PromptSession(history=InMemoryHistory())


def check_open_ai_api_key():
    pass


def install_plugin_dependencies():
    pass


def get_random_quote():
    response = requests.get("https://api.quotable.io/random")
    if response.status_code == 200:
        data = response.json()
        return data["content"]
    return None


def touch_dir(path: Path) -> Path:
    if path.is_file():
        raise FileSystemOperationError(
            f"[[{path}]] is a file. May be you should use path.parent as the input parameter"
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def ordered_yaml_load(yaml_path, Loader=yaml.FullLoader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    with open(yaml_path) as stream:
        return yaml.load(stream, OrderedLoader)


def ordered_yaml_dump(data, stream=None, Dumper=yaml.SafeDumper, **kwds):
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(
        data,
        stream,
        OrderedDumper,
        default_flow_style=False,
        encoding="utf-8",
        allow_unicode=True,
        **kwds,
    )


def get_date_time_now():
    from datetime import datetime

    now = datetime.now()
    time = f"{now.year:0>4d}{now.month:0>2d}{now.day:2>2d}{now.hour:0>2d}{now.minute:0>2d}"
    return time


def retry(n_attempts, delay_time):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(n_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Failed to execute '{func.__name__}', retrying... exception: {str(e)}")
                    time.sleep(delay_time)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def add_cost_time(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        sys_status = "OK"
        sys_msg = "None"
        result = None
        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            logging.error(e)
            sys_status = "ERROR"
            sys_msg = e
        end_time = time.time()
        cost_seconds = end_time - start_time
        logging.info(f"Function {func.__name__} took {cost_seconds} seconds to execute.")
        return {
            "data": result,
            "cost_time": cost_seconds,
            "sys_status": sys_status,
            "sys_msg": sys_msg,
        }

    return wrapper


# TODO 根据open的设置来定义调用的频率
def rate_limited(max_calls=3, period=60):
    """
    装饰器函数，用于控制函数的调用频率。
    :param max_calls: 允许的最大调用次数，默认为3次。
    :param period: 时间周期（秒），默认为60秒。
    """
    calls = []

    def decorator(func):
        def wrapper(*args, **kwargs):
            now = time.time()
            # print(f"now: {now} previous is {calls}")
            calls_in_period = [call for call in calls if now - call < period]
            # print(f"..... collection: {calls_in_period}")
            if len(calls_in_period) >= max_calls:
                # 达到调用频率限制，暂时休眠 0.5 is trick, 屏蔽误差
                time_to_wait = period + 0.5 - (now - calls_in_period[0])
                logging.info(f"调用频率过高，休眠 {time_to_wait:.2f} 秒后重试... {now} --- {calls_in_period}")
                # print(f"调用频率过高，休眠 {time_to_wait:.2f} 秒后重试...")
                # print(f"调用频率过高，休眠 {time_to_wait:.2f} 秒后重试... {now} --- {calls_in_period}, len calls {len(calls)}")

                time.sleep(time_to_wait)
            now = time.time()
            result = func(*args, **kwargs)
            calls.append(now)
            # 清理超过时间周期的调用记录
            # calls[:] = [call for call in calls if now - call < period]
            calls[:] = calls[-3 * max_calls :]
            return result

        return wrapper

    return decorator


@rate_limited(max_calls=3, period=60)
def rate_limit_func():
    print("hello ...")


if __name__ == "__main__":
    touch_dir(Path("main.py").parent)
    yml_path = "/tmp/order.dump.yml"
    out = open(yml_path, "w")
    a = {
        "z": "he",
        "d": "hhh",
        "c": ["上", "中", "下"],
        "b": {"a": "xxx", "z": "xxx", "d": "xxx"},
        "e": [["a", "b", "c"], ["e", "f", "g"]],
    }

    a = {
        "constraints": [
            "~4000 word limit for short term memory. Your short term memory is short, so immediately save important information to  files.",
            "If you are unsure how you previously did something or want to recall past events, thinking about similar events will   help you remember.",
            "No user assistance",
            "Exclusively use the commands listed below e.g. command_name",
        ],
        "resources": [
            "Internet access for searches and information gathering.",
            "Long Term memory management.",
            "GPT-3.5 powered Agents for delegation of simple tasks.",
            "File output.",
        ],
        "performance_evaluations": [
            "Continuously review and analyze your actions to ensure you are performing to the best of your abilities.",
            "Constructively self-criticize your big-picture behavior constantly.",
            "Reflect on past decisions and strategies to refine your approach.",
            "Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.",
            "Write all code to a file.",
        ],
    }
    ordered_yaml_dump(a, out)
    b = ordered_yaml_load(yml_path)
    print(b)

    @add_cost_time
    async def add(a, b):
        return a + b

    import asyncio

    result = asyncio.run(add(1, 2))

    now = time.time()
    for i in range(10):
        rate_limit_func()
    print(f"time last {time.time()-now}, count : {i}")
    # print(result)
