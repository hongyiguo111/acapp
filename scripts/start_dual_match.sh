#!/bin/bash

# 启动双人匹配服务器
cd /home/acs/acapp
python3 match_system/src/dual_main.py &

echo "Dual match server started on port 9091"