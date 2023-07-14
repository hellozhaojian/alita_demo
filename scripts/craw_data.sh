# 抓取定期报告，年报和中报

basepath=$(cd `dirname $0`; pwd)
echo "basepath: $basepath"

bin=${basepath}/../.venv/bin/python
config_file=load_data_config.yml

py_file=${basepath}/../alita_mini/crawler/app/nianbao_manager_ana/craw.py
echo "PYTHONPATH=${basepath}/../  && nohup ${bin}  ${py_file}  > craw.log 2>&1 &"
export PYTHONPATH=${basepath}/../  &&  ${bin}  ${py_file}  