#!/bin/bash

# ContentHub 手动部署脚本
# 适用于没有 Docker 的环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Python 环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装 Python 3.10+"
        exit 1
    fi

    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    if [[ "$python_version" < "3.10" ]]; then
        log_warn "Python 版本 $python_version，建议使用 Python 3.10+"
    fi
    
    log_info "Python 版本: $python_version"
}

# 检查 Node.js 环境
check_node() {
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js 18+"
        exit 1
    fi

    node_version=$(node --version | cut -d'v' -f2)
    major_version=$(echo $node_version | cut -d'.' -f1)
    
    if [[ $major_version -lt 18 ]]; then
        log_warn "Node.js 版本 $node_version，建议使用 Node.js 18+"
    fi
    
    log_info "Node.js 版本: $node_version"
}

# 初始化项目
init_project() {
    log_info "初始化 ContentHub 项目..."

    # 创建必要的目录
    mkdir -p "$PROJECT_ROOT/data/backend"
    mkdir -p "$PROJECT_ROOT/logs/backend"
    mkdir -p "$PROJECT_ROOT/logs/frontend"

    # 复制环境变量文件（如果不存在）
    if [ ! -f "$PROJECT_ROOT/src/backend/.env" ]; then
        cp "$PROJECT_ROOT/src/backend/.env.example" "$PROJECT_ROOT/src/backend/.env"
        log_warn "已创建 .env 文件，请编辑并配置必要的环境变量"
    fi

    log_info "初始化完成！"
}

# 部署后端
deploy_backend() {
    log_info "部署后端服务..."
    
    cd "$PROJECT_ROOT/src/backend"
    
    # 安装依赖
    log_info "安装 Python 依赖..."
    pip3 install -r requirements.txt
    
    # 初始化数据库
    log_info "初始化数据库..."
    python3 -c "from app.db.database import init_db; init_db()"
    
    log_info "后端服务部署完成！"
}

# 部署前端
deploy_frontend() {
    log_info "部署前端服务..."
    
    cd "$PROJECT_ROOT/src/frontend"
    
    # 安装依赖
    log_info "安装 Node.js 依赖..."
    npm install
    
    log_info "前端服务部署完成！"
}

# 启动后端
start_backend() {
    log_info "启动后端服务..."
    
    cd "$PROJECT_ROOT/src/backend"
    
    # 检查环境变量
    if [ ! -f ".env" ]; then
        log_error "找不到 .env 文件，请先运行 ./deploy_manual.sh init"
        exit 1
    fi
    
    # 启动服务
    python3 main.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_ROOT/backend.pid"
    
    log_info "后端服务已启动 (PID: $BACKEND_PID)"
    log_info "API 文档: http://localhost:8000/docs"
}

# 启动前端
start_frontend() {
    log_info "启动前端服务..."
    
    cd "$PROJECT_ROOT/src/frontend"
    
    # 启动开发服务器
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PROJECT_ROOT/frontend.pid"
    
    log_info "前端服务已启动 (PID: $FRONTEND_PID)"
    log_info "前端地址: http://localhost:3010"
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."
    
    if [ -f "$PROJECT_ROOT/backend.pid" ]; then
        BACKEND_PID=$(cat "$PROJECT_ROOT/backend.pid")
        kill $BACKEND_PID 2>/dev/null && log_info "后端服务已停止 (PID: $BACKEND_PID)" || log_warn "后端服务未运行"
        rm "$PROJECT_ROOT/backend.pid"
    fi
    
    if [ -f "$PROJECT_ROOT/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$PROJECT_ROOT/frontend.pid")
        kill $FRONTEND_PID 2>/dev/null && log_info "前端服务已停止 (PID: $FRONTEND_PID)" || log_warn "前端服务未运行"
        rm "$PROJECT_ROOT/frontend.pid"
    fi
}

# 查看状态
view_status() {
    log_info "服务状态："
    
    if [ -f "$PROJECT_ROOT/backend.pid" ]; then
        BACKEND_PID=$(cat "$PROJECT_ROOT/backend.pid")
        if ps -p $BACKEND_PID > /dev/null; then
            echo -e "${GREEN}✓${NC} 后端服务运行中 (PID: $BACKEND_PID)"
        else
            echo -e "${RED}✗${NC} 后端服务未运行"
        fi
    else
        echo -e "${RED}✗${NC} 后端服务未运行"
    fi
    
    if [ -f "$PROJECT_ROOT/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$PROJECT_ROOT/frontend.pid")
        if ps -p $FRONTEND_PID > /dev/null; then
            echo -e "${GREEN}✓${NC} 前端服务运行中 (PID: $FRONTEND_PID)"
        else
            echo -e "${RED}✗${NC} 前端服务未运行"
        fi
    else
        echo -e "${RED}✗${NC} 前端服务未运行"
    fi
    
    echo ""
    log_info "健康检查："
    
    # 检查后端
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} 后端 API 正常"
    else
        echo -e "${RED}✗${NC} 后端 API 异常"
    fi
    
    # 检查前端
    if curl -s http://localhost:3010 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} 前端服务正常"
    else
        echo -e "${RED}✗${NC} 前端服务异常"
    fi
}

# 显示帮助
show_help() {
    echo "ContentHub 手动部署脚本"
    echo ""
    echo "使用方法: $0 <command>"
    echo ""
    echo "可用命令:"
    echo "  init       初始化项目（首次部署）"
    echo "  deploy     部署所有服务（安装依赖）"
    echo "  start      启动所有服务"
    echo "  stop       停止所有服务"
    echo "  restart    重启所有服务"
    echo "  status     查看服务状态"
    echo "  help       显示此帮助信息"
}

# 主函数
main() {
    check_python
    check_node

    case "${1:-help}" in
        init)
            init_project
            ;;
        deploy)
            deploy_backend
            deploy_frontend
            ;;
        start)
            start_backend
            sleep 2
            start_frontend
            view_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 2
            start_backend
            sleep 2
            start_frontend
            view_status
            ;;
        status)
            view_status
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