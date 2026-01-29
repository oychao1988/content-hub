#!/bin/bash

###############################################################################
# ContentHub 并发压力测试脚本
#
# 测试目标：
# - 100 并发用户
# - 持续 5 分钟
# - 成功率 > 99%
#
# 使用方法：
# chmod +x run_concurrent_test.sh
# ./run_concurrent_test.sh
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
HOST="${LOCUST_HOST:-http://localhost:8000}"
USERS="${LOCUST_USERS:-100}"
SPAWN_RATE="${LOCUST_SPAWN_RATE:-10}"
RUN_TIME="${LOCUST_RUN_TIME:-5m}"
REPORT_FILE="performance_report_$(date +%Y%m%d_%H%M%S).html"
LOG_FILE="locust_$(date +%Y%m%d_%H%M%S).log"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ContentHub 并发压力测试${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}配置参数：${NC}"
echo "  Host: $HOST"
echo "  并发用户数: $USERS"
echo "  启动速率: $SPAWN_RATE 用户/秒"
echo "  运行时间: $RUN_TIME"
echo "  报告文件: $REPORT_FILE"
echo "  日志文件: $LOG_FILE"
echo ""

# 检查后端服务是否运行
echo -e "${YELLOW}检查后端服务...${NC}"
if ! curl -s -f "$HOST/api/v1/system/health" > /dev/null 2>&1; then
    echo -e "${RED}错误: 后端服务未运行或无法访问${NC}"
    echo "请先启动后端服务：cd src/backend && python main.py"
    exit 1
fi
echo -e "${GREEN}✓ 后端服务运行正常${NC}"
echo ""

# 检查 Locust 是否安装
echo -e "${YELLOW}检查 Locust...${NC}"
if ! command -v locust &> /dev/null; then
    echo -e "${RED}错误: Locust 未安装${NC}"
    echo "请安装 Locust：pip install locust==2.29.0"
    exit 1
fi
echo -e "${GREEN}✓ Locust 已安装${NC}"
echo ""

# 运行测试
echo -e "${YELLOW}开始并发压力测试...${NC}"
echo "测试开始时间: $(date)"
echo ""

# 运行 Locust（headless 模式）
locust \
    -f locustfile.py \
    --headless \
    --host="$HOST" \
    --users="$USERS" \
    --spawn-rate="$SPAWN_RATE" \
    --run-time="$RUN_TIME" \
    --html="$REPORT_FILE" \
    --logfile="$LOG_FILE" \
    --loglevel=INFO

TEST_EXIT_CODE=$?

echo ""
echo "测试结束时间: $(date)"
echo ""

# 检查测试结果
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}测试完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${GREEN}报告已生成: $REPORT_FILE${NC}"
    echo -e "${GREEN}日志已保存: $LOG_FILE${NC}"
    echo ""

    # 检查成功率
    echo -e "${YELLOW}请查看 HTML 报告以获取详细结果：${NC}"
    echo "  - 响应时间（P50, P95, P99）"
    echo "  - 请求成功率"
    echo "  - RPS（每秒请求数）"
    echo "  - 错误分布"
    echo ""

    # 在 macOS 上自动打开报告
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${YELLOW}正在打开报告...${NC}"
        open "$REPORT_FILE"
    fi
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}测试失败！${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${RED}请查看日志文件: $LOG_FILE${NC}"
    exit $TEST_EXIT_CODE
fi

echo -e "${GREEN}完成！${NC}"
