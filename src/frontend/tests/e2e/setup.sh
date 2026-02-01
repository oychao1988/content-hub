#!/bin/bash

# E2E 测试环境设置和运行脚本

set -e

echo "🚀 ContentHub E2E 测试环境设置"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Node.js
echo -n "检查 Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅${NC} $(node -v)"

# 检查 npm
echo -n "检查 npm..."
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅${NC} $(npm -v)"

# 安装依赖
echo -e "\n${YELLOW}📦 安装项目依赖...${NC}"
npm install

# 安装 Playwright 浏览器
echo -e "\n${YELLOW}🌐 安装 Playwright 浏览器...${NC}"
npx playwright install

# 检查后端服务
echo -e "\n${YELLOW}🔍 检查后端服务...${NC}"
if curl -s http://localhost:8010/docs > /dev/null; then
    echo -e "${GREEN}✅ 后端服务运行中 (http://localhost:8010)${NC}"
else
    echo -e "${RED}❌ 后端服务未运行${NC}"
    echo -e "${YELLOW}请在另一个终端运行: cd src/backend && python main.py${NC}"
fi

# 检查前端服务
echo -e "\n${YELLOW}🔍 检查前端服务...${NC}"
if curl -s http://localhost:3010 > /dev/null; then
    echo -e "${GREEN}✅ 前端服务运行中 (http://localhost:3010)${NC}"
else
    echo -e "${RED}❌ 前端服务未运行${NC}"
    echo -e "${YELLOW}请运行: npm run dev${NC}"
fi

# 运行测试选项
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ 环境设置完成！${NC}"
echo -e "\n${YELLOW}运行测试选项：${NC}"
echo "  npm run test:e2e           - 运行所有 E2E 测试"
echo "  npm run test:e2e:ui        - 使用 UI 模式运行测试"
echo "  npm run test:e2e:headed    - 显示浏览器运行测试"
echo "  npm run test:e2e:debug     - 调试模式运行测试"
echo "  npm run test:e2e:report    - 查看 HTML 测试报告"
echo ""
