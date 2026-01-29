# ContentHub Docker 管理命令
# 使用方法: make <target>

.PHONY: help build up down restart logs ps clean backup

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
GREEN  := \033[0;32m
YELLOW := \033[0;33m
BLUE   := \033[0;34m
NC     := \033[0m # No Color

help: ## 显示帮助信息
	@echo "$(GREEN)ContentHub Docker 管理命令$(NC)"
	@echo ""
	@echo "$(YELLOW)使用方法:$(NC)"
	@echo "  make <target>"
	@echo ""
	@echo "$(YELLOW)可用命令:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'

build: ## 构建 Docker 镜像
	@echo "$(GREEN)构建 Docker 镜像...$(NC)"
	docker compose build
	@echo "$(GREEN)构建完成！$(NC)"

build-no-cache: ## 构建 Docker 镜像（无缓存）
	@echo "$(GREEN)构建 Docker 镜像（无缓存）...$(NC)"
	docker compose build --no-cache
	@echo "$(GREEN)构建完成！$(NC)"

up: ## 启动所有服务
	@echo "$(GREEN)启动所有服务...$(NC)"
	docker compose up -d
	@echo "$(GREEN)服务已启动！$(NC)"
	@echo "$(BLUE)前端地址: http://localhost$(NC)"
	@echo "$(BLUE)后端 API: http://localhost:8000/docs$(NC)"

up-prod: ## 启动生产环境服务
	@echo "$(GREEN)启动生产环境服务...$(NC)"
	docker compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)生产环境服务已启动！$(NC)"

down: ## 停止所有服务
	@echo "$(YELLOW)停止所有服务...$(NC)"
	docker compose down
	@echo "$(GREEN)服务已停止！$(NC)"

down-prod: ## 停止生产环境服务
	@echo "$(YELLOW)停止生产环境服务...$(NC)"
	docker compose -f docker-compose.prod.yml down
	@echo "$(GREEN)生产环境服务已停止！$(NC)"

restart: ## 重启所有服务
	@echo "$(YELLOW)重启所有服务...$(NC)"
	docker compose restart
	@echo "$(GREEN)服务已重启！$(NC)"

logs: ## 查看所有服务日志
	docker compose logs -f

logs-backend: ## 查看后端服务日志
	docker compose logs -f backend

logs-frontend: ## 查看前端服务日志
	docker compose logs -f frontend

ps: ## 查看服务状态
	docker compose ps

clean: ## 清理未使用的 Docker 资源
	@echo "$(YELLOW)清理 Docker 资源...$(NC)"
	docker system prune -f
	@echo "$(GREEN)清理完成！$(NC)"

clean-all: ## 清理所有 Docker 资源（包括停止的容器和未使用的镜像）
	@echo "$(YELLOW)清理所有 Docker 资源...$(NC)"
	docker system prune -a -f
	@echo "$(GREEN)清理完成！$(NC)"

backup: ## 备份数据
	@echo "$(GREEN)备份数据...$(NC)"
	@mkdir -p backups
	@tar -czf backups/data-$$(date +%Y%m%d_%H%M%S).tar.gz data/
	@echo "$(GREEN)备份完成：backups/data-$$(date +%Y%m%d_%H%M%S).tar.gz$(NC)"

shell-backend: ## 进入后端容器
	docker compose exec backend bash

shell-frontend: ## 进入前端容器
	docker compose exec frontend sh

test: ## 运行测试
	@echo "$(GREEN)运行后端测试...$(NC)"
	docker compose exec backend pytest

lint: ## 代码检查
	@echo "$(GREEN)运行代码检查...$(NC)"
	docker compose exec backend flake8 app/
	docker compose exec backend black --check app/

format: ## 代码格式化
	@echo "$(GREEN)格式化代码...$(NC)"
	docker compose exec backend black app/
	@echo "$(GREEN)格式化完成！$(NC)"

stats: ## 查看容器资源使用情况
	docker stats

init: ## 初始化项目（首次部署）
	@echo "$(GREEN)初始化 ContentHub 项目...$(NC)"
	@mkdir -p data/backend logs/backend logs/frontend
	@cp src/backend/.env.example src/backend/.env
	@echo "$(YELLOW)请编辑 src/backend/.env 文件配置环境变量$(NC)"
	@echo "$(GREEN)初始化完成！运行 'make build && make up' 启动服务$(NC)"

rebuild: down build up ## 重新构建并启动服务

status: ## 显示服务状态和健康检查
	@echo "$(GREEN)服务状态:$(NC)"
	@docker compose ps
	@echo ""
	@echo "$(GREEN)健康检查:$(NC)"
	@curl -s http://localhost/health && echo "前端: OK" || echo "前端: FAIL"
	@curl -s http://localhost:8000/docs > /dev/null && echo "后端: OK" || echo "后端: FAIL"
