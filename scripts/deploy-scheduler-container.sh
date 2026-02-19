#!/bin/bash
# ContentHub 调度器容器部署验证脚本
# 用于在服务器上快速部署和验证独立的调度器容器

set -e

echo "=== ContentHub 调度器容器部署验证 ==="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印成功消息
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 函数：打印错误消息
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 函数：打印警告消息
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 检查必要的命令
check_commands() {
    echo "1. 检查必要的命令..."
    for cmd in docker docker-compose; do
        if ! command -v $cmd &> /dev/null; then
            print_error "$cmd 未安装"
            exit 1
        fi
        print_success "$cmd 已安装"
    done
    echo ""
}

# 检查项目文件
check_files() {
    echo "2. 检查项目文件..."
    files=(
        "src/backend/scheduler.Dockerfile"
        "src/backend/scripts/scheduler_entrypoint.sh"
        "src/backend/scripts/init_scheduler.py"
        "docker-compose.yml"
    )

    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            print_success "$file"
        else
            print_error "$file 不存在"
            exit 1
        fi
    done
    echo ""
}

# 构建调度器镜像
build_scheduler_image() {
    echo "3. 构建调度器镜像..."
    if docker build -f src/backend/scheduler.Dockerfile -t content-hub-scheduler:latest .; then
        print_success "镜像构建成功"
    else
        print_error "镜像构建失败"
        exit 1
    fi
    echo ""
}

# 启动调度器容器
start_scheduler_container() {
    echo "4. 启动调度器容器..."

    # 检查容器是否已存在
    if docker ps -a | grep -q contenthub-scheduler; then
        print_warning "调度器容器已存在，停止并删除..."
        docker stop contenthub-scheduler 2>/dev/null || true
        docker rm contenthub-scheduler 2>/dev/null || true
    fi

    # 启动新容器
    if docker-compose up -d scheduler; then
        print_success "调度器容器启动成功"
    else
        print_error "调度器容器启动失败"
        exit 1
    fi
    echo ""
}

# 等待容器就绪
wait_for_container() {
    echo "5. 等待容器就绪..."
    sleep 5

    # 检查容器状态
    if docker ps | grep -q contenthub-scheduler; then
        print_success "容器正在运行"
    else
        print_error "容器未运行"
        docker logs contenthub-scheduler --tail 50
        exit 1
    fi
    echo ""
}

# 验证调度器状态
verify_scheduler() {
    echo "6. 验证调度器状态..."

    # 执行验证脚本
    result=$(docker exec contenthub-scheduler python3 -c "
from app.services.scheduler_service import scheduler_service
running = scheduler_service.is_running
executors = len(scheduler_service.get_registered_executors())
jobs = len(scheduler_service.get_scheduled_jobs())
print(f'{running},{executors},{jobs}')
" 2>&1)

    # 解析结果
    IFS=',' read -r running executors jobs <<< "$result"

    if [ "$running" == "True" ]; then
        print_success "调度器运行状态: 正常"
    else
        print_error "调度器运行状态: 停止"
        exit 1
    fi

    if [ "$executors" == "7" ]; then
        print_success "已注册执行器: $executors 个"
    else
        print_warning "已注册执行器: $executors 个（预期 7 个）"
    fi

    if [ "$jobs" == "2" ]; then
        print_success "定时任务数量: $jobs 个"
    else
        print_warning "定时任务数量: $jobs 个（预期 2 个）"
    fi
    echo ""
}

# 显示调度器任务
show_tasks() {
    echo "7. 显示定时任务..."
    docker exec contenthub-scheduler python3 -c "
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()
tasks = db.query(ScheduledTask).filter(ScheduledTask.is_active == True).all()
print('已启用的定时任务:')
for task in tasks:
    print(f\"  {task.id}. {task.name}\")
    print(f\"     Cron: {task.cron_expression}\")
    print(f\"     类型: {task.task_type}\")
db.close()
" 2>&1 | grep -v "WARNING" || true
    echo ""
}

# 显示日志
show_logs() {
    echo "8. 显示最近的调度器日志..."
    docker logs contenthub-scheduler --tail 20
    echo ""
}

# 生成健康检查报告
generate_report() {
    echo "9. 生成健康检查报告..."

    # 容器状态
    echo "=== 容器状态 ==="
    docker ps --filter name=contenthub-scheduler --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""

    # 健康检查
    echo "=== 健康检查 ==="
    health_status=$(docker inspect --format='{{.State.Health.Status}}' contenthub-scheduler 2>/dev/null || echo "unknown")
    echo "状态: $health_status"
    echo ""

    # 资源使用
    echo "=== 资源使用 ==="
    docker stats contenthub-scheduler --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    echo ""
}

# 主流程
main() {
    check_commands
    check_files
    build_scheduler_image
    start_scheduler_container
    wait_for_container
    verify_scheduler
    show_tasks
    show_logs
    generate_report

    echo "=== 部署验证完成 ==="
    echo ""
    echo "后续操作："
    echo "  - 查看日志: docker logs -f contenthub-scheduler"
    echo "  - 重启容器: docker-compose restart scheduler"
    echo "  - 停止容器: docker-compose stop scheduler"
    echo "  - 查看状态: docker-compose ps"
    echo ""
    print_success "调度器容器部署成功！"
}

# 运行主流程
main
