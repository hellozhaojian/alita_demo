# alita_demo

## install

```sh
poetry shell
poetry install
pip install scipy
```

## TODO

1. 爬虫代码，支持抓取半年报。  DONE
   解决方案：
       1. meta 抓取， 每天做
       2. 内容抓取，如果有了就不抓
       3. 抓取之后直接入库
       4. 有一个指令，人工执行： 抓取，入库

2. 搜索效果不太好。         TODO, 搜索之后完成一个直方图，展示哪些股票触碰的次数最多。DONE
    解决方案：
       1. 直接走词匹配。实现dictonary_searcher
       2. 实现一个页面，包括搜索结果， 也包括数据统计。

3. 不知道搜索什么
   抓取某一个比较经典的网站，一个或者多个
   抽取出实体词，计算热度，然后

3. 重构代码, 完成文档编写，收尾。
   三个指令
   * craw
   * reason
   * check api
