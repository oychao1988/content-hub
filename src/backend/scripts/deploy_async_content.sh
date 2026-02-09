#!/bin/bash
#
# ContentHub 异步内容生成系统部署脚本
#
# 用途: 自动化部署和验证异步内容生成系统
# 使用: bash scripts/deploy_async_content.sh
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印分隔线
print_section() {
    echo ""
    echo "==================================="
    echo "$1"
    echo "==================================="
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 主流程
main() {
    print_section "ContentHub 异步内容生成系统部署"

    # 1. 检查依赖
    print_section "1/6 检查系统依赖"
    check_command python3
    check_command pip
    check_command sqlite3
    log_info "✓ 系统依赖检查通过"

    # 2. 备份数据库
    print_section "2/6 备份数据库"
    BACKUP_DIR="backups"
    mkdir -p $BACKUP_DIR

    BACKUP_FILE="$BACKUP_DIR/contenthub_backup_$(date +%Y%m%d_%H%M%S).db"

    if [ -f "data/contenthub.db" ]; then
        cp data/contenthub.db $BACKUP_FILE
        log_info "✓ 数据库已备份到: $BACKUP_FILE"
    else
        log_warn "数据库文件不存在，跳过备份"
    fi

    # 3. 运行测试
    print_section "3/6 运行测试套件"
    log_info "运行集成测试..."

    if pytest tests/integration/test_async_content_full_workflow.py -v --tb=short; then
        log_info "✓ 集成测试通过"
    else
        log_error "✗ 集成测试失败"
        exit 1
    fi

    # 4. 验证数据库模型
    print_section "4/6 验证数据库模型"
    python3 -c "
from app.db.database import engine
from sqlalchemy import inspect
import sys

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = ['content_generation_tasks', 'contents', 'accounts']
    missing = [t for t in required_tables if t not in tables]

    if missing:
        print(f'✗ 缺少表: {missing}')
        sys.exit(1)

    # 检查任务表结构
    columns = [col['name'] for col in inspector.get_columns('content_generation_tasks')]
    required_columns = ['task_id', 'account_id', 'topic', 'status', 'priority']
    missing_cols = [c for c in required_columns if c not in columns]

    if missing_cols:
        print(f'✗ 缺少列: {missing_cols}')
        sys.exit(1)

    print('✓ 数据库模型验证通过')
except Exception as e:
    print(f'✗ 数据库验证失败: {e}')
    sys.exit(1)
"

    log_info "✓ 数据库模型验证通过"

    # 5. 验证服务
    print_section "5/6 验证服务导入"
    python3 -c "
import sys

services = [
    'app.services.async_content_generation_service',
    'app.services.task_status_poller',
    'app.services.task_result_handler',
    'app.services.task_queue_service',
    'app.services.monitoring.async_task_monitor'
]

for service in services:
    try:
        __import__(service)
        print(f'✓ {service}')
    except ImportError as e:
        print(f'✗ {service}: {e}')
        sys.exit(1)

print('✓ 所有服务导入成功')
"

    log_info "✓ 服务验证通过"

    # 6. 验证 CLI
    print_section "6/6 验证 CLI 命令"
    python3 -m cli.main --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "✓ CLI 主命令可用"
    else
        log_error "✗ CLI 主命令失败"
        exit 1
    fi

    python3 -m cli.main task --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "✓ task 命令组可用"
    else
        log_error "✗ task 命令组失败"
        exit 1
    fi

    python3 -m cli.main monitor --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "✓ monitor 命令组可用"
    else
        log_error "✗ monitor 命令组失败"
        exit 1
    fi

    # 7. 健康检查
    print_section "7/7 健康检查"
    python3 -c "
from app.services.monitoring.async_task_monitor import AsyncTaskMonitor

monitor = AsyncTaskMonitor()
metrics = monitor.get_metrics()

health = metrics.get('health', 'unknown')
total_tasks = metrics.get('total_tasks', 0)

# 对于新系统（没有任务），允许 unhealthy 状态
if health in ['healthy', 'warning'] or total_tasks == 0:
    if total_tasks == 0:
        print(f'✓ 系统状态: 新系统就绪（暂无任务数据）')
    else:
        print(f'✓ 系统状态: {health}')
    print(f'✓ 总任务数: {total_tasks}')
    print(f'✓ 成功率: {metrics.get(\"success_rate\", 0):.1f}%')
else:
    print(f'⚠ 系统状态: {health}')
    print(f'⚠ 请检查任务执行情况')
"

    # 完成
    print ""
    print "==================================="
    echo -e "${GREEN}✅ 部署检查完成！${NC}"
    echo "==================================="
    echo ""
    echo "下一步操作："
    echo "1. 配置环境变量: 编辑 .env"
    echo "2. 启动服务: python main.py"
    echo "3. 验证功能: contenthub monitor health"
    echo ""
    echo "如需回滚，使用备份: $BACKUP_FILE"
}

# 执行主流程
main "$@"
