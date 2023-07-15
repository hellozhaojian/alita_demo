from tqdm import tqdm
from typing import Dict, Callable
import faiss
import json
import re
from collections import Counter


def full_to_half(s):
    """
    Convert full-width characters to half-width ones.
    """
    n = []
    for char in s:
        num = ord(char)
        if num == 0x3000:
            num = 32
        elif 0xFF01 <= num <= 0xFF5E:
            num -= 0xFEE0
        char = chr(num)
        n.append(char)
    return "".join(n)


class FaissTool:
    """
    Faiss index tools
    """

    def __init__(self, meta_filename, index_filename):
        self.engine = faiss.read_index(index_filename)
        self.id2text = []
        for line in open(meta_filename):
            self.id2text.append(json.loads(line.strip()))

    def search(self, q_embs, topk=5):
        res_dist, res_pid = self.engine.search(q_embs, topk)
        result_list = []
        for i in range(topk):
            result_list.append(self.id2text[res_pid[0][i]])
        return result_list


def process_file_with_tqdm(
    filename: str,
    map_func: Callable,
    map_kwargs: Dict,
    reduce_func: Callable,
    reduce_kwargs: Dict,
):
    # 打开文件
    with open(filename, "r") as file:
        # 获取文件的总行数
        total_lines = sum(1 for line in file)

    # 再次打开文件
    with open(filename, "r") as file:
        # 使用tqdm来展示进度条
        for line in tqdm(file, total=total_lines):
            # 在这里对每一行进行处理
            # 例如，打印每一行内容
            line_result = map_func(line.strip(), **map_kwargs)
            reduce_func(line_result, **reduce_kwargs)
    return reduce_func(None, **reduce_kwargs)


class DictionarySearcher:
    def __init__(self):
        self.words_map = {}
        self.must_have = []
        self.must_have_count = 0
        self.must_not = []
        self.query_chunk_pattern = re.compile("\s+")

    def extract_words(self, s):
        # 如果字符串是 [xxx|yyy|zzz] 模式
        if s.startswith("[") and s.endswith("]"):
            pattern = r"\[(.*?)\]"
            matched = re.match(pattern, s)
            if matched:
                return matched.group(1).split("|")

        # 如果字符串是 xxxx 模式
        else:
            return [s]

    def add_pattern(self, pattern):
        """ """
        store = self.must_have
        is_must_have = True
        if pattern[0] == "!":
            store = self.must_not
            pattern = pattern[1:]
            is_must_have = False
        words = self.extract_words(pattern)
        if len(words) > 0:
            if is_must_have:
                self.must_have_count += 1
        store.append(set(words))
        for word in words:
            self.add_word(word)

    def add_patterns(self, patterns):
        patterns = self.query_chunk_pattern.split(patterns)
        for pattern in patterns:
            self.add_pattern(pattern)

    def match(self, sentence):
        results = self.search(sentence, False)
        counter = Counter()
        must_match_indexes = set()
        for item in results:
            word = item["word"]
            for index, group in enumerate(self.must_have):
                if word in group:
                    must_match_indexes.add(index)
                    counter.update([index])
            for index, group in enumerate(self.must_not):
                if word in group:
                    return False, 0
        if len(must_match_indexes) == self.must_have_count:
            return True, counter.most_common()[-1][1]
        return False, 0

    def add_word(self, word):
        word_list = list(word)
        for i in range(len(word_list) - 1):
            self.words_map["".join(word_list[: i + 1])] = False
        self.words_map[word] = True

    def search(self, query, max_search=True):
        index = 0
        query_len = len(query)
        result = []
        while True:
            if index >= query_len:
                break
            match_results = []
            match_len = 0
            max_match_len = 0
            for start in range(index, query_len):
                check_word = query[index : start + 1]
                if check_word not in self.words_map:
                    break
                match_len += 1
                if self.words_map[check_word]:
                    match_results.append(check_word)
                    max_match_len = match_len

            if max_search is True and len(match_results) > 1:
                del match_results[:-1]
            for result_item in match_results:
                result.append({"pos": index, "word": result_item})

            if max_search and max_match_len > 0:
                index += max_match_len
            else:
                index += 1
        return result


if __name__ == "__main__":
    dictionary_searcher = DictionarySearcher()
    for word in ["浙大", "浙江大学", "浙江"]:
        dictionary_searcher.add_word(word)

    sentence = "浙江省内最好的大学是浙江大学"

    result = dictionary_searcher.search(sentence, max_search=False)
    for item in result:
        print(item)

    result = dictionary_searcher.search(sentence, max_search=True)
    for item in result:
        print(item)

    # 示例
    s = "ｈｅｌｌｏ，ｗｏｒｌｄ！"
    print(full_to_half(s))  # 输出: hello,world!

    dictionary_searcher = DictionarySearcher()
    dictionary_searcher.add_patterns("[浙大|浙江大学] !武大")
    print(dictionary_searcher.match(sentence))

    dictionary_searcher = DictionarySearcher()
    dictionary_searcher.add_patterns("[浙大|浙江大学] ![最好地]")
    print(dictionary_searcher.match(sentence))

    dictionary_searcher = DictionarySearcher()
    dictionary_searcher.add_patterns("![浙大|浙江大学] ![最好地]")
    print(dictionary_searcher.match(sentence))

    dictionary_searcher = DictionarySearcher()
    dictionary_searcher.add_patterns("[浙大|浙江大学] ![最好]")
    print(dictionary_searcher.match(sentence))
