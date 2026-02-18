#!/bin/bash
# ContentHub 启动脚本
# 初始化调度器并启动应用

set -e

echo "=== ContentHub 启动脚本 ==="
echo "当前时间: $(date)"

# 初始化调度器
echo "初始化调度器..."
python /app/scripts/init_scheduler.py

if [ $? -eq 0 ]; then
    echo "✓ 调度器初始化成功"
else
    echo "⚠ 调度器初始化失败，继续启动应用..."
fi

# 启动应用
echo "启动应用服务..."
exec gunicorn main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:18010 \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    --log-level info
