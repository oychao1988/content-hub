#!/bin/bash
# ContentHub 调度器容器启动脚本
# 专门用于运行调度器服务的入口脚本

set -e

echo "=== ContentHub 调度器容器启动 ==="
echo "当前时间: $(date)"
echo "容器模式: 调度器专用"

# 等待数据库就绪（如果使用 PostgreSQL）
if [ -n "$DATABASE_HOST" ]; then
    echo "等待数据库连接..."
    while ! nc -z $DATABASE_HOST ${DATABASE_PORT:-5432} 2>/dev/null; do
        sleep 1
    done
    echo "✓ 数据库连接成功"
fi

# 初始化调度器
echo ""
echo "初始化调度器..."
python /app/scripts/init_scheduler.py

if [ $? -eq 0 ]; then
    echo "✓ 调度器初始化成功"
else
    echo "✗ 调度器初始化失败"
    exit 1
fi

# 显示调度器状态
echo ""
echo "调度器状态："
python3 -c "
from app.services.scheduler_service import scheduler_service
from app.db.database import SessionLocal

print(f'运行状态: {scheduler_service.is_running}')
print(f'执行器数量: {len(scheduler_service.get_registered_executors())}')
print(f'定时任务数量: {len(scheduler_service.get_scheduled_jobs())}')

db = SessionLocal()
try:
    jobs = scheduler_service.get_scheduled_jobs()
    for job in jobs:
        print(f\"  - {job['name']} (下次运行: {job['next_run_time']})\")
finally:
    db.close()
"

echo ""
echo "=== 调度器已启动，开始监听定时任务 ==="

# 保持容器运行，定期检查调度器状态
# 使用一个简单的循环来保持容器活跃
while true; do
    sleep 300  # 每 5 分钟检查一次

    # 检查调度器是否仍在运行
    if ! python3 -c "from app.services.scheduler_service import scheduler_service; exit(0 if scheduler_service.is_running else 1)" 2>/dev/null; then
        echo "⚠️  调度器已停止，尝试重启..."
        python /app/scripts/init_scheduler.py
    fi
done
