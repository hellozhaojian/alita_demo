import tiktoken
import openai
import os
from alita_mini.utils import rate_limited

# from dotenv import load_dotenv


def count_string_tokens(string: str, model_name: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(string))


def create_msg(msg: str):
    messages = [
        {"role": "user", "content": msg},
    ]
    return messages


@rate_limited(max_calls=1, period=35)
def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0, max_tokens=2000):
    if type(messages) == str:
        messages = create_msg(messages)
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]


def set_open_ai(api_key):
    openai.api_key = api_key


def test_open_ai():
    msg = "北京是哪个国家的首都"
    print(get_completion_from_messages(messages=create_msg(msg)))
    print(f"count({msg}) ={count_string_tokens(msg)} ")
