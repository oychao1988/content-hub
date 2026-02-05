```
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
```

# ContentHub - Claude Code 开发指南

本文档帮助 Claude Code 实例快速理解 ContentHub 项目的架构和开发约定。

## 项目概述

**ContentHub** 是一个内容运营管理系统，支持多账号管理、内容生成、审核和批量发布。

**核心价值**：
- 多账号内容运营管理
- 自动化内容生成流程
- 混合配置管理（数据库为主，Markdown 为辅）
- 多平台批量发布

**技术栈**：
- 后端：FastAPI 0.109.0 + SQLAlchemy 2.0 + SQLite + APScheduler
- 前端：Vue 3 + Vite + Element Plus + Pinia

## 常用命令

### 项目管理（Makefile）

```bash
make help                          # 显示所有可用命令
make init                         # 初始化项目（首次部署）
make build                        # 构建 Docker 镜像
make up                           # 启动开发环境服务
make up-prod                     # 启动生产环境服务
make down                        # 停止开发环境服务
make down-prod                   # 停止生产环境服务
make restart                     # 重启所有服务
make logs                        # 查看所有服务日志
make logs-backend                # 查看后端服务日志
make logs-frontend               # 查看前端服务日志
make ps                          # 查看服务状态
make test                        # 运行后端测试
make lint                        # 代码检查（flake8 + black）
make format                      # 代码格式化（black）
make shell-backend               # 进入后端容器
make shell-frontend              # 进入前端容器
make backup                      # 备份数据
make clean                       # 清理未使用的 Docker 资源
```

### 后端开发

```bash
cd src/backend
pip install -r requirements.txt   # 安装依赖
cp .env.example .env             # 配置环境变量
python -c "from app.db.database import init_db; init_db()"  # 初始化数据库
python main.py                   # 启动后端服务（开发模式）
pytest                          # 运行所有测试
pytest tests/test_config.py     # 运行单个测试文件
pytest tests/test_config.py::test_get_config  # 运行单个测试用例
```

### 前端开发

```bash
cd src/frontend
npm install                     # 安装依赖
npm run dev                     # 启动开发服务器
npm run build                   # 构建生产版本
npm run lint                    # 代码检查
```

## CLI工具

ContentHub 提供了功能强大的命令行工具，使用 Typer 框架实现，支持多种管理操作。

### 启动CLI

```bash
cd src/backend
python -m cli.main --help       # 查看CLI帮助
contenthub --help              # 如果已安装到系统PATH
```

### 常用CLI指令

#### 系统管理

```bash
contenthub version             # 显示版本信息
contenthub system info         # 显示系统信息
contenthub system status       # 检查服务状态
contenthub system health       # 健康检查
```

#### 数据库管理

```bash
contenthub db init             # 初始化数据库
contenthub db reset            # 重置数据库（危险操作）
contenthub db backup [PATH]    # 备份数据库
contenthub db restore <FILE>   # 从备份恢复数据库
contenthub db info             # 显示数据库信息
contenthub db stats            # 数据库统计信息
contenthub db shell            # 进入SQLite shell
```

#### 用户管理

```bash
contenthub users list          # 列出所有用户
contenthub users create        # 创建新用户
contenthub users update <ID>   # 更新用户信息
contenthub users delete <ID>   # 删除用户（需确认）
contenthub users info <ID>     # 查看用户详情
contenthub users activate <ID>     # 激活用户
contenthub users deactivate <ID>   # 停用用户
contenthub users change-password <ID>  # 修改密码
contenthub users set-role <ID> <ROLE>  # 设置用户角色
contenthub users reset-password <ID>  # 重置密码（生成随机密码）
```

#### 账号管理

```bash
contenthub accounts list       # 列出所有账号
contenthub accounts create     # 创建账号（必须指定客户、平台和所有者）
contenthub accounts update <ID>  # 更新账号信息
contenthub accounts delete <ID>  # 删除账号（需确认）
contenthub accounts info <ID>  # 查看账号详情
contenthub accounts list-config <ID>  # 查看完整配置（JSON格式）
contenthub accounts import-md <ID> <FILE>  # 从Markdown导入配置
contenthub accounts export-md <ID> [FILE]  # 导出配置到Markdown
contenthub accounts test-connection <ID>  # 测试平台连接
contenthub accounts writing-style  # 管理写作风格配置
contenthub accounts publish-config  # 管理发布配置
```

#### 内容管理

```bash
contenthub content list        # 列出所有内容
contenthub content create      # 创建内容（草稿）
contenthub content generate    # 生成内容（调用content-creator）
contenthub content batch-generate # 批量生成内容
contenthub content topic-search  # 选题搜索（调用Tavily API）
contenthub content update <ID> # 更新内容
contenthub content delete <ID> # 删除内容（需确认）
contenthub content info <ID>   # 查看内容详情
contenthub content submit-review <ID>  # 提交审核
contenthub content approve <ID>  # 审核通过
contenthub content reject <ID>   # 审核拒绝
contenthub content review-list  # 待审核列表
contenthub content statistics  # 审核统计
```

#### 定时任务管理

```bash
contenthub scheduler list      # 列出定时任务
contenthub scheduler create    # 创建定时任务
contenthub scheduler update <ID>  # 更新定时任务
contenthub scheduler delete <ID>  # 删除定时任务（需确认）
contenthub scheduler info <ID> # 查看任务详情
contenthub scheduler trigger <ID>  # 手动触发任务
contenthub scheduler history <ID>  # 查看任务执行历史
contenthub scheduler start     # 启动调度器
contenthub scheduler stop      # 停止调度器
contenthub scheduler status    # 查看调度器状态
contenthub scheduler pause <ID> # 暂停任务
contenthub scheduler resume <ID> # 恢复任务
```

#### 发布管理

```bash
contenthub publisher history       # 查看发布历史
contenthub publisher publish <ID>  # 手动发布内容
contenthub publisher retry <ID>    # 重试失败的发布
contenthub publisher batch-publish # 批量发布待发布内容
contenthub publisher records       # 查看发布记录（与history相同）
contenthub publisher stats         # 查看发布统计
```

#### 发布池管理

```bash
contenthub publish-pool list            # 列出发布池内容
contenthub publish-pool add <ID>        # 添加内容到发布池
contenthub publish-pool remove <ID>     # 从发布池移除内容
contenthub publish-pool set-priority <ID> <PRIORITY>  # 设置优先级
contenthub publish-pool schedule <ID> <TIME>  # 设置计划发布时间
contenthub publish-pool publish         # 从发布池批量发布
contenthub publish-pool clear           # 清空发布池（需确认）
contenthub publish-pool stats           # 查看发布池统计
```

#### 平台管理

```bash
contenthub platform list       # 列出支持的平台
contenthub platform info <ID>  # 查看平台详情
contenthub platform sync       # 同步平台配置
```

#### 客户管理

```bash
contenthub customer list       # 列出所有客户
contenthub customer create     # 创建新客户
contenthub customer update <ID>  # 更新客户信息
contenthub customer delete <ID>  # 删除客户
contenthub customer info <ID>  # 查看客户详情
```

#### 配置管理

```bash
contenthub config list                # 列出所有配置分类
contenthub config writing-style       # 写作风格配置
contenthub config content-theme       # 内容主题配置
contenthub config system-params       # 系统参数配置
contenthub config platform-config     # 平台配置
```

#### 审计日志

```bash
contenthub audit list          # 列出审计日志
contenthub audit info <ID>     # 查看审计详情
contenthub audit search        # 搜索审计日志
```

#### 仪表盘

```bash
contenthub dashboard overview  # 显示总览
contenthub dashboard stats     # 显示统计数据
```

### CLI选项

所有命令支持以下全局选项：

```bash
--format {table,json,csv}      # 输出格式（默认：table）
--debug                        # 调试模式
--quiet                        # 静默模式（仅输出错误）
--user <USER>                  # 操作用户（用于审计，默认：cli-user）
```

### 使用示例

```bash
# 列出所有账号（JSON格式）
contenthub accounts list --format json

# 创建新用户（交互模式）
contenthub users create

# 备份数据库到指定路径
contenthub db backup /path/to/backup.db

# 搜索审计日志
contenthub audit search --action login --user admin --start-date 2024-01-01

# 立即运行定时任务
contenthub scheduler run 123

# 查看内容详情
contenthub content info 456
```

### CLI开发

CLI代码位于 `src/backend/cli/` 目录，结构如下：

```
cli/
├── main.py                    # 主入口文件
├── config.py                  # 配置文件
├── utils.py                   # 工具函数
└── modules/                   # 各功能模块
    ├── db.py                  # 数据库管理
    ├── users.py               # 用户管理
    ├── accounts.py            # 账号管理
    ├── content.py             # 内容管理
    ├── scheduler.py           # 定时任务管理
    ├── publisher.py           # 发布管理
    ├── publish_pool.py        # 发布池管理
    ├── platform.py            # 平台管理
    ├── customer.py            # 客户管理
    ├── config.py              # 配置管理
    ├── audit.py               # 审计日志
    ├── dashboard.py           # 仪表盘
    └── system.py              # 系统管理
```

## 架构概览

### 模块系统架构（核心）

ContentHub 使用完全可插拔的模块系统，复用 omni-cast 的模块注册系统。

#### 模块定义规范

每个模块必须位于 `app/modules/{module_name}/module.py`，并导出 `MODULE` 对象：

```python
from fastapi import APIRouter
from app.core.module_system.module import Module

router = APIRouter()

def startup(app):
    """模块启动钩子（可选）"""
    pass

def shutdown(app):
    """模块关闭钩子（可选）"""
    pass

# 必须导出此对象
MODULE = Module(
    name="accounts",
    router=router,
    startup=startup,
    shutdown=shutdown
)
```

#### 模块加载机制

1. 从环境变量 `MODULES_ENABLED` 读取启用的模块列表
2. 动态导入 `app.modules.{module_name}.module`
3. 获取 `MODULE` 对象并验证类型
4. 注册路由到 FastAPI（前缀：`/api/v1/`）
5. 调用 startup/shutdown 钩子

**模块加载器位置**：`app/core/module_system/loader.py:13`

### 项目结构

```
src/backend/
├── app/
│   ├── core/                    # 核心模块（来自 omni-cast）
│   │   ├── module_registry/     # 模块注册系统
│   │   ├── module_system/       # 模块基类和接口
│   │   ├── config.py            # 配置管理（Pydantic Settings）
│   │   └── custom_logger.py     # 日志系统
│   ├── models/                  # SQLAlchemy 数据模型
│   │   ├── account.py           # 账号模型
│   │   ├── content.py           # 内容模型
│   │   ├── scheduler.py         # 定时任务模型
│   │   └── publisher.py         # 发布模型
│   ├── services/                # 业务服务层
│   ├── modules/                 # 业务模块（API 路由）
│   │   ├── auth/                # 认证模块
│   │   ├── accounts/            # 账号管理模块
│   │   ├── content/             # 内容管理模块
│   │   ├── scheduler/           # 定时任务模块
│   │   ├── publisher/           # 发布管理模块
│   │   └── dashboard/           # 仪表板模块
│   ├── db/                      # 数据库
│   │   └── database.py          # 数据库配置和会话
│   ├── utils/                   # 工具函数
│   └── factory.py               # 应用工厂
├── data/                        # 数据目录
├── logs/                        # 日志目录
├── main.py                      # 应用入口
└── requirements.txt             # 依赖清单
```

## 关键设计模式

### 1. 模块注册系统
- 完全解耦的模块架构
- 运行时动态加载
- 启动/关闭钩子支持

### 2. FastAPI 依赖注入
- 数据库会话：`Depends(get_db)`
- 当前用户：`Depends(get_current_user)`

### 3. SQLAlchemy ORM
- 声明式模型定义
- 自动表创建（开发环境）
- 异步会话管理

### 4. 配置管理（Pydantic Settings）
- 类型安全的配置
- 环境变量自动加载
- 配置文件：`src/backend/.env`

## 外部服务集成

### content-creator CLI

**用途**：内容生成

**调用方式**：通过 `subprocess` 调用 CLI

**配置**：`CREATOR_CLI_PATH` 环境变量

### content-publisher API

**用途**：微信公众号发布

**调用方式**：HTTP API

**配置**：
- `PUBLISHER_API_URL`：服务地址
- `PUBLISHER_API_KEY`：API 密钥

### Tavily API

**用途**：选题搜索

**配置**：`TAVILY_API_KEY`

## 开发约定

### API 路由
- 路由前缀：`/api/v1/`
- 在模块的 `routes.py` 中定义路由
- 使用 FastAPI 依赖注入处理通用逻辑

### 数据模型
- 位置：`app/models/`
- 使用 SQLAlchemy 声明式基类
- 模型文件按业务域划分

### 服务层
- 位置：`app/services/`
- 封装业务逻辑
- 可被多个模块复用

### 模块启用
- 配置：`MODULES_ENABLED` 环境变量
- 格式：逗号分隔的模块名列表
- 示例：`auth,accounts,content,scheduler,publisher,dashboard`

## 重要文件路径

| 文件 | 路径 |
|------|------|
| 应用入口 | `src/backend/main.py` |
| 应用工厂 | `src/backend/app/factory.py` |
| 模块加载器 | `src/backend/app/core/module_system/loader.py` |
| Module 数据类 | `src/backend/app/core/module_system/module.py` |
| 环境配置 | `src/backend/.env` |
| 数据库文件 | `src/backend/data/contenthub.db` |
| API 文档 | `http://localhost:8000/docs` |

## 测试

### 测试文件
- 单元测试：`tests/test_*.py`
- 集成测试：`tests/integration/`

### 运行测试

```bash
cd src/backend
pytest                          # 运行所有测试
pytest tests/test_config.py     # 运行单个测试文件
pytest tests/test_config.py::test_get_config  # 运行单个测试用例
pytest -v                       # 详细输出
pytest -x                       # 遇到第一个失败停止
pytest -k "config"              # 运行名称包含 "config" 的测试
```

### API 验证
- 访问 `/docs` 查看 Swagger 文档
- 使用 `/redoc` 查看 ReDoc 文档

## 部署

### Docker 部署

```bash
make init                       # 初始化项目
make build                      # 构建镜像
make up                         # 启动服务
```

### 生产环境部署

```bash
cp .env.production.example .env.production
# 编辑 .env.production 配置生产环境变量
make build                      # 构建镜像
make up-prod                    # 启动生产环境服务
```

## 配置说明

### 后端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/contenthub.db` |
| `PUBLISHER_API_URL` | content-publisher 服务地址 | `http://150.158.88.23:3010` |
| `PUBLISHER_API_KEY` | content-publisher API 密钥 | - |
| `CREATOR_CLI_PATH` | content-creator CLI 路径 | - |
| `TAVILY_API_KEY` | Tavily API 密钥 | - |
| `SCHEDULER_ENABLED` | 是否启用调度器 | `true` |
| `SECRET_KEY` | JWT 密钥 | `your-secret-key-here` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌过期时间 | `60` |

详细配置说明请参考 `src/backend/.env.example` 文件。
