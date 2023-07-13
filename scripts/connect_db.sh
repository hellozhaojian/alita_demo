#!/bin/bash

# MongoDB连接信息
host="localhost:27007"
username="root"
password="OTNmYTdjYmZkMjE5ZmYzODg0MDZiYWJh"

# 判断操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
  # 在 macOS 上执行命令
  mongosh --port 27007 --username $username --password $password
else
  # 在其他操作系统上执行命令（例如 Ubuntu）
  mongo --host $host --username $username --password $password
fi

