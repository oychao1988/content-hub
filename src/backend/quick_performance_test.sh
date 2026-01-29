#!/bin/bash

###############################################################################
# ContentHub 性能测试快速开始脚本
#
# 这是一个一键式性能测试脚本，会：
# 1. 检查环境
# 2. 准备测试数据
# 3. 运行 API 响应时间测试
# 4. 运行数据库查询性能测试
# 5. 生成性能测试报告
#
# 使用方法：
# chmod +x quick_performance_test.sh
# ./quick_performance_test.sh
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装"
        return 1
    fi
    return 0
}

# 主流程
main() {
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════╗"
    echo "║   ContentHub 性能测试快速开始脚本      ║"
    echo "║   Performance Test Quick Start         ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""

    # 步骤 1: 检查环境
    print_step "步骤 1/5: 检查测试环境"

    print_info "检查 Python 环境..."
    if ! python --version &> /dev/null; then
        print_error "Python 未安装或不在 PATH 中"
        exit 1
    fi
    print_success "Python 版本: $(python --version)"

    print_info "检查必要的工具..."
    check_command pytest || exit 1
    print_success "pytest 已安装"

    print_info "检查后端服务..."
    if ! curl -s -f "http://localhost:8000/api/v1/system/health" > /dev/null 2>&1; then
        print_warning "后端服务未运行"
        print_info "请先启动后端服务：python main.py"
        print_info "在另一个终端运行，然后按回车继续..."
        read
    else
        print_success "后端服务运行正常"
    fi

    # 步骤 2: 准备测试数据
    print_step "步骤 2/5: 准备测试数据"

    print_info "检查是否需要创建测试数据..."
    read -p "是否创建新的测试数据？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "创建测试数据..."
        python init_performance_test_data.py
        print_success "测试数据创建完成"
    else
        print_info "跳过测试数据创建"
    fi

    # 步骤 3: 运行 API 响应时间测试
    print_step "步骤 3/5: 运行 API 响应时间测试"

    print_info "开始 API 响应时间测试..."
    if pytest tests/performance/test_api_response_time.py \
        -v \
        --benchmark-only \
        --benchmark-json=benchmark_reports/api_response.json \
        --benchmark-sort=name \
        --benchmark-min-rounds=3; then
        print_success "API 响应时间测试完成"
    else
        print_warning "API 响应时间测试完成（部分测试可能失败）"
    fi

    # 步骤 4: 运行数据库查询性能测试
    print_step "步骤 4/5: 运行数据库查询性能测试"

    print_info "开始数据库查询性能测试..."
    if pytest tests/performance/test_db_query_performance.py \
        -v \
        --benchmark-only \
        --benchmark-json=benchmark_reports/db_query.json \
        --benchmark-sort=name \
        --benchmark-min-rounds=3; then
        print_success "数据库查询性能测试完成"
    else
        print_warning "数据库查询性能测试完成（部分测试可能失败）"
    fi

    # 步骤 5: 生成报告
    print_step "步骤 5/5: 生成性能测试报告"

    print_info "生成性能测试报告..."
    python tests/performance/test_template.py

    print_success "报告已生成"

    # 显示总结
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}性能测试完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}测试报告：${NC}"
    echo "  - API 响应时间: benchmark_reports/api_response.json"
    echo "  - 数据库查询: benchmark_reports/db_query.json"
    echo "  - 综合报告: PERFORMANCE_TEST_REPORT.md"
    echo ""
    echo -e "${YELLOW}下一步：${NC}"
    echo "  1. 查看 PERFORMANCE_TEST_REPORT.md 了解测试结果"
    echo "  2. 运行并发测试：./run_concurrent_test.sh"
    echo "  3. 查看优化建议：PERFORMANCE_TEST_GUIDE.md"
    echo ""

    # 在 macOS 上自动打开报告
    if [[ "$OSTYPE" == "darwin"* ]]; then
        read -p "是否打开报告？ (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open PERFORMANCE_TEST_REPORT.md
        fi
    fi

    print_success "所有步骤完成！"
}

# 捕获错误
trap 'print_error "测试过程中发生错误"; exit 1' ERR

# 运行主流程
main
