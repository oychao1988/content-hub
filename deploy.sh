#!/bin/bash

# ContentHub Docker 快速部署脚本
# 使用方法: ./deploy.sh [init|start|stop|restart|logs|status|backup]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# 检查 Docker 环境
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi

    log_info "Docker 环境检查通过"
}

# 初始化项目
init_project() {
    log_info "初始化 ContentHub 项目..."

    # 创建必要的目录
    mkdir -p "$PROJECT_ROOT/data/backend"
    mkdir -p "$PROJECT_ROOT/logs/backend"
    mkdir -p "$PROJECT_ROOT/logs/frontend"
    mkdir -p "$PROJECT_ROOT/backups"

    # 复制环境变量文件（如果不存在）
    if [ ! -f "$PROJECT_ROOT/src/backend/.env" ]; then
        cp "$PROJECT_ROOT/src/backend/.env.example" "$PROJECT_ROOT/src/backend/.env"
        log_warn "已创建 .env 文件，请编辑并配置必要的环境变量"
    fi

    log_info "初始化完成！"
    log_info "请先配置环境变量：$PROJECT_ROOT/src/backend/.env"
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."
    cd "$PROJECT_ROOT"
    docker compose build
    log_info "镜像构建完成！"
}

# 启动服务
start_services() {
    log_info "启动 ContentHub 服务..."
    cd "$PROJECT_ROOT"
    docker compose up -d
    log_info "服务启动完成！"
    log_info "前端地址: http://localhost:18030"
    log_info "后端 API: http://localhost:18010/docs"
}

# 停止服务
stop_services() {
    log_info "停止 ContentHub 服务..."
    cd "$PROJECT_ROOT"
    docker compose down
    log_info "服务已停止！"
}

# 重启服务
restart_services() {
    log_info "重启 ContentHub 服务..."
    stop_services
    start_services
}

# 查看日志
view_logs() {
    cd "$PROJECT_ROOT"
    if [ -n "$2" ]; then
        docker compose logs -f "$2"
    else
        docker compose logs -f
    fi
}

# 查看状态
view_status() {
    cd "$PROJECT_ROOT"
    log_info "服务状态："
    docker compose ps

    echo ""
    log_info "健康检查："

    # 检查前端
    if curl -s http://localhost/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} 前端服务正常"
    else
        echo -e "${RED}✗${NC} 前端服务异常"
    fi

    # 检查后端
    if curl -s http://localhost:18010/docs > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} 后端服务正常"
    else
        echo -e "${RED}✗${NC} 后端服务异常"
    fi
}

# 备份数据
backup_data() {
    log_info "备份数据..."
    local backup_dir="$PROJECT_ROOT/backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)

    mkdir -p "$backup_dir"

    # 备份数据库
    if [ -f "$PROJECT_ROOT/data/backend/contenthub.db" ]; then
        cp "$PROJECT_ROOT/data/backend/contenthub.db" "$backup_dir/contenthub-$timestamp.db"
    fi

    # 打包数据目录
    tar -czf "$backup_dir/data-$timestamp.tar.gz" -C "$PROJECT_ROOT" data/

    log_info "备份完成：$backup_dir/data-$timestamp.tar.gz"
}

# 清理资源
cleanup_resources() {
    log_warn "清理 Docker 资源..."
    docker system prune -f
    log_info "清理完成！"
}

# 显示帮助
show_help() {
    echo "ContentHub Docker 部署脚本"
    echo ""
    echo "使用方法: $0 <command>"
    echo ""
    echo "可用命令:"
    echo "  init       初始化项目（首次部署）"
    echo "  build      构建 Docker 镜像"
    echo "  start      启动所有服务"
    echo "  stop       停止所有服务"
    echo "  restart    重启所有服务"
    echo "  logs       查看所有服务日志"
    echo "  logs [service] 查看指定服务日志（backend/frontend）"
    echo "  status     查看服务状态"
    echo "  backup     备份数据"
    echo "  cleanup    清理 Docker 资源"
    echo "  help       显示此帮助信息"
}

# 主函数
main() {
    check_docker

    case "${1:-help}" in
        init)
            init_project
            ;;
        build)
            build_images
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            view_logs "$@"
            ;;
        status)
            view_status
            ;;
        backup)
            backup_data
            ;;
        cleanup)
            cleanup_resources
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
