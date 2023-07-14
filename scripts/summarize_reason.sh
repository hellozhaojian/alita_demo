# 根据配置文件执行摘要推理，并存储到TaskResults中以供查询

basepath=$(cd `dirname $0`; pwd)
echo "basepath: $basepath"

bin=${basepath}/../.venv/bin/python
py_file=${basepath}/../alita_mini/reasoner/service/simple_reasoner.py
config_file=report_manager_ana_sum_task.yml
echo ${bin}
echo ${py_file}

echo "PYTHONPATH=${basepath}/../  && nohup ${bin}  ${py_file} -c ${config_file}  > sum_reason.log 2>&1 &"
export PYTHONPATH=${basepath}/../  && ${bin}  ${py_file} -c ${config_file}  