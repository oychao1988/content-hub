#!/bin/bash

###############################################################################
# ContentHub 基准测试脚本
#
# 测试 API 响应时间和数据库查询性能
#
# 使用方法：
# chmod +x run_benchmark_test.sh
# ./run_benchmark_test.sh
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
HOST="${API_HOST:-http://localhost:8000}"
REPORT_DIR="benchmark_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JSON_REPORT="$REPORT_DIR/benchmark_$TIMESTAMP.json"
HTML_REPORT="$REPORT_DIR/benchmark_$TIMESTAMP.html"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ContentHub 基准测试${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}配置参数：${NC}"
echo "  API Host: $HOST"
echo "  JSON 报告: $JSON_REPORT"
echo "  HTML 报告: $HTML_REPORT"
echo ""

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 检查后端服务是否运行
echo -e "${YELLOW}检查后端服务...${NC}"
if ! curl -s -f "$HOST/api/v1/system/health" > /dev/null 2>&1; then
    echo -e "${RED}错误: 后端服务未运行或无法访问${NC}"
    echo "请先启动后端服务：cd src/backend && python main.py"
    exit 1
fi
echo -e "${GREEN}✓ 后端服务运行正常${NC}"
echo ""

# 运行 API 响应时间测试
echo -e "${YELLOW}运行 API 响应时间测试...${NC}"
pytest tests/performance/test_api_response_time.py \
    -v \
    --benchmark-only \
    --benchmark-json="$JSON_REPORT" \
    --benchmark-sort=name \
    --benchmark-warmup=on \
    --benchmark-warmup-iterations=5 \
    --benchmark-min-rounds=5

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API 响应时间测试完成${NC}"
else
    echo -e "${RED}✗ API 响应时间测试失败${NC}"
fi
echo ""

# 运行数据库查询性能测试
echo -e "${YELLOW}运行数据库查询性能测试...${NC}"
pytest tests/performance/test_db_query_performance.py \
    -v \
    --benchmark-only \
    --benchmark-json="db_benchmark_$TIMESTAMP.json" \
    --benchmark-sort=name \
    --benchmark-warmup=on \
    --benchmark-warmup-iterations=3

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 数据库查询性能测试完成${NC}"
else
    echo -e "${RED}✗ 数据库查询性能测试失败${NC}"
fi
echo ""

# 生成 HTML 报告
echo -e "${YELLOW}生成 HTML 报告...${NC}"
if command -v pytest-benchmark &> /dev/null; then
    pytest-benchmark "$JSON_REPORT" -o "$HTML_REPORT" 2>/dev/null || echo "HTML 报告生成失败（需要安装 pytest-benchmark extra）"
    if [ -f "$HTML_REPORT" ]; then
        echo -e "${GREEN}✓ HTML 报告已生成: $HTML_REPORT${NC}"
    fi
fi
echo ""

# 显示总结
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}测试完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}报告文件：${NC}"
echo "  - JSON: $JSON_REPORT"
if [ -f "$HTML_REPORT" ]; then
    echo "  - HTML: $HTML_REPORT"
fi
echo ""

# 在 macOS 上自动打开报告
if [[ "$OSTYPE" == "darwin"* ]] && [ -f "$HTML_REPORT" ]; then
    echo -e "${YELLOW}正在打开报告...${NC}"
    open "$HTML_REPORT"
fi

echo -e "${GREEN}完成！${NC}"
