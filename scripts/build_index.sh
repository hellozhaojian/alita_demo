# 根据配置文件执行摘要推理，并存储到TaskResults中以供查询

basepath=$(cd `dirname $0`; pwd)
echo "basepath: $basepath"

bin=${basepath}/../.venv/bin/python
config_file=load_data_config.yml

#load
py_file=${basepath}/../alita_mini/data/service/offline_op_service.py
echo "PYTHONPATH=${basepath}/../  && nohup ${bin}  ${py_file} -c ${config_file}  > sum_reason.log 2>&1 &"
export PYTHONPATH=${basepath}/../  &&  ${bin}  ${py_file} -k load -c ${config_file}  

#dump
# py_file=${basepath}/../alita_mini/data/service/offline_op_service.py
# echo "PYTHONPATH=${basepath}/../  && nohup ${bin}  ${py_file} -c ${config_file}  > dump_for_index.log 2>&1 &"
# export PYTHONPATH=${basepath}/../  &&  ${bin}  ${py_file} -k dump -c ${config_file}  

#index
# py_file=${basepath}/../alita_mini/data/service/indexer.py
# echo "PYTHONPATH=${basepath}/../  && nohup ${bin}  ${py_file} -k build -c ${config_file}  > index.log 2>&1 &"
# export PYTHONPATH=${basepath}/../  &&  ${bin}  ${py_file} -k build -c ${config_file}  

# #query
#py_file=${basepath}/../alita_mini/data/service/indexer.py
#echo "PYTHONPATH=${basepath}/../  && nohup ${bin}  ${py_file} -k query -q '筷子 砧板'-c ${config_file}  > query_index.log 2>&1 &"
#export PYTHONPATH=${basepath}/../  &&  ${bin}  ${py_file} -k query -q '筷子 砧板' -c ${config_file}  
