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

## 快速开始

### 启动服务（Docker）

```bash
make init                         # 首次部署：初始化项目
make up                           # 启动开发环境
make up-prod                      # 启动生产环境
```

### 本地开发

```bash
# 后端
cd src/backend
pip install -r requirements.txt
cp .env.example .env
python -c "from app.db.database import init_db; init_db()"
python main.py

# 前端
cd src/frontend
npm install
npm run dev
```

### 访问地址

- **后端 API**：http://localhost:18010
- **API 文档**：http://localhost:18010/docs
- **前端界面**：http://localhost:18030

> 快速开始详细指南：[docs/guides/quick-start.md](docs/guides/quick-start.md)

## 项目结构

```
src/backend/
├── app/
│   ├── core/                    # 核心模块（模块系统、配置、日志）
│   ├── models/                  # SQLAlchemy 数据模型
│   ├── services/                # 业务服务层
│   ├── modules/                 # 业务模块（API 路由）
│   ├── db/                      # 数据库
│   ├── utils/                   # 工具函数
│   └── factory.py               # 应用工厂
├── cli/                         # 命令行工具
├── data/                        # 数据目录
├── logs/                        # 日志目录
└── main.py                      # 应用入口

src/frontend/                    # Vue 3 前端
docs/                            # 项目文档
```

## 模块系统

ContentHub 使用完全可插拔的模块系统，支持运行时动态加载。

### 模块定义规范

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

### 模块加载机制

1. 从环境变量 `MODULES_ENABLED` 读取启用的模块列表
2. 动态导入 `app.modules.{module_name}.module`
3. 获取 `MODULE` 对象并验证类型
4. 注册路由到 FastAPI（前缀：`/api/v1/`）
5. 调用 startup/shutdown 钩子

**模块加载器位置**：`app/core/module_system/loader.py:13`

> 详细架构说明：[docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)

## 重要文件路径

| 文件 | 路径 |
|------|------|
| 应用入口 | `src/backend/main.py` |
| 应用工厂 | `src/backend/app/factory.py` |
| 模块加载器 | `src/backend/app/core/module_system/loader.py` |
| Module 数据类 | `src/backend/app/core/module_system/module.py` |
| 环境配置 | `src/backend/.env` |
| 数据库文件 | `src/backend/data/contenthub.db` |
| API 文档 | http://localhost:8000/docs |

## CLI 工具

ContentHub 提供功能强大的命令行工具，使用 Typer 框架实现。

### 启动 CLI

```bash
cd src/backend
python -m cli.main --help       # 查看帮助
contenthub --help              # 如果已安装到系统 PATH
```

### 核心命令模块（13 个）

| 模块 | 命令前缀 | 功能 |
|------|---------|------|
| 系统管理 | `contenthub system` | 版本、状态、健康检查 |
| 数据库 | `contenthub db` | 初始化、备份、恢复、统计 |
| 用户管理 | `contenthub users` | 创建、更新、删除、角色管理 |
| 账号管理 | `contenthub accounts` | 账号配置、导入导出、连接测试 |
| 内容管理 | `contenthub content` | 创建、生成、审核、统计 |
| 定时任务 | `contenthub scheduler` | 任务管理、历史、暂停恢复 |
| 发布管理 | `contenthub publisher` | 发布历史、重试、统计 |
| 发布池 | `contenthub publish-pool` | 发布池管理、优先级、计划 |
| 平台管理 | `contenthub platform` | 平台信息、配置同步 |
| 客户管理 | `contenthub customer` | 客户信息管理 |
| 配置管理 | `contenthub config` | 写作风格、主题、系统参数 |
| 审计日志 | `contenthub audit` | 日志查询、搜索 |
| 仪表盘 | `contenthub dashboard` | 总览、统计 |

**全局选项**：
- `--format {table,json,csv}` - 输出格式
- `--debug` - 调试模式
- `--quiet` - 静默模式

> 完整 CLI 命令参考（123 个命令）：[docs/references/CLI-REFERENCE.md](docs/references/CLI-REFERENCE.md)
> CLI 快速入门：[docs/guides/cli-quick-start.md](docs/guides/cli-quick-start.md)
> CLI 实施总结：[docs/development/CLI-IMPLEMENTATION-SUMMARY.md](docs/development/CLI-IMPLEMENTATION-SUMMARY.md)

## 开发指南

### 代码规范

**API 路由**：
- 路由前缀：`/api/v1/`
- 在模块的 `routes.py` 中定义路由
- 使用 FastAPI 依赖注入处理通用逻辑

**数据模型**：
- 位置：`app/models/`
- 使用 SQLAlchemy 声明式基类
- 模型文件按业务域划分

**服务层**：
- 位置：`app/services/`
- 封装业务逻辑
- 可被多个模块复用

### 测试

```bash
cd src/backend
pytest                          # 运行所有测试
pytest tests/test_config.py     # 运行单个测试文件
pytest -v                       # 详细输出
pytest -k "config"              # 运行名称包含 "config" 的测试
```

> 开发文档：[docs/development/](docs/development/)
> 测试指南：[docs/testing/](docs/testing/)

### 文档管理

当需要创建、更新或维护项目文档时，可以使用 **project-documentation-management** skill：

```bash
# 使用文档管理 skill
/project-documentation-management
```

**功能包括**：
- 文档结构规划
- 文档内容生成
- 文档格式统一
- 文档索引更新
- API 文档生成

**适用场景**：
- 创建新的功能文档
- 更新架构设计文档
- 维护开发指南
- 生成 API 参考文档
- 更新 README 和索引文件

## 外部服务集成

| 服务 | 用途 | 调用方式 | 配置变量 |
|------|------|---------|---------|
| content-creator | 内容生成 | subprocess | `CREATOR_CLI_PATH` |
| content-publisher | 微信公众号发布 | HTTP API | `PUBLISHER_API_URL`, `PUBLISHER_API_KEY` |
| Tavily API | 选题搜索 | HTTP API | `TAVILY_API_KEY` |

> 详细集成说明：[docs/architecture/ARCHITECTURE.md#七、集成架构](docs/architecture/ARCHITECTURE.md#七、集成架构)

## 文档导航

### 按角色查找

**新成员入门**：
1. [快速开始](docs/guides/quick-start.md) - 5 分钟启动项目
2. [CLI 快速入门](docs/guides/cli-quick-start.md) - CLI 基础操作
3. [系统架构](docs/architecture/ARCHITECTURE.md) - 理解项目架构

**开发者**：
1. [开发指南](docs/development/) - 开发规范和最佳实践
2. [API 文档](http://localhost:8000/docs) - Swagger UI 交互式文档
3. [错误处理](docs/references/error-handling-quick-reference.md) - 错误排查

**运维人员**：
1. [部署指南](docs/deployment/DEPLOYMENT.md) - Docker 部署
2. [运维手册](docs/operations/) - 运维操作和监控

### 按功能查找

- **模块系统**：[架构文档 - 模块系统设计](docs/architecture/ARCHITECTURE.md#三、模块系统设计)
- **数据库**：[数据库设计](docs/architecture/DATABASE-DESIGN.md)
- **定时任务**：[调度系统](docs/architecture/SCHEDULER-ARCHITECTURE.md)
- **发布系统**：[发布架构](docs/architecture/PUBLISHER-ARCHITECTURE.md)
- **CLI 工具**：[CLI 命令参考](docs/references/CLI-REFERENCE.md)

### 文档中心

> [docs/README.md](docs/README.md) - 完整文档目录
> [docs/INDEX.md](docs/INDEX.md) - 快速查找指南

## 常见问题

### 服务启动失败

1. 检查环境变量配置：`src/backend/.env`
2. 查看日志：`make logs-backend`
3. 验证端口占用：`lsof -i :8000`

### CLI 命令找不到

1. 确认在 `src/backend` 目录下
2. 使用 `python -m cli.main` 启动
3. 或安装到系统 PATH

### 数据库错误

1. 重新初始化：`python -c "from app.db.database import init_db; init_db()"`
2. 查看数据库文件权限：`ls -la data/contenthub.db`
3. 备份恢复：参考 [数据库管理](docs/references/CLI-REFERENCE.md#二、数据库管理)

### 模块加载失败

1. 检查 `MODULES_ENABLED` 环境变量
2. 验证模块文件存在：`ls app/modules/{module_name}/module.py`
3. 查看启动日志中的错误信息

> 更多问题排查：[docs/guides/troubleshooting.md](docs/guides/troubleshooting.md)
> 错误处理参考：[docs/references/error-handling-quick-reference.md](docs/references/error-handling-quick-reference.md)

## 常用命令速查

### Makefile

```bash
make help               # 显示所有命令
make up                 # 启动开发环境
make down               # 停止服务
make logs               # 查看日志
make test               # 运行测试
make shell-backend      # 进入后端容器
```

### 后端

```bash
python main.py          # 启动服务（开发模式）
pytest                  # 运行测试
make format             # 代码格式化
```

### 前端

```bash
npm run dev             # 启动开发服务器
npm run build           # 构建生产版本
npm run lint            # 代码检查
```

### 内容管理和发布（常用 CLI 指令）

```bash
# 查看系统状态
python -m cli.main dashboard stats              # 查看系统总览统计

# 内容管理
python -m cli.main content list                 # 查看所有内容
python -m cli.main content info <id>            # 查看内容详情
python -m cli.main content review-list          # 查看待审核列表
python -m cli.main content approve <id>         # 审核通过内容
python -m cli.main content reject <id>          # 审核拒绝内容

# 内容生成
python -m cli.main content create -a <account_id> -t "标题"  # 创建内容草稿
python -m cli.main content generate -a <account_id> -t "选题" --keywords "关键词1,关键词2"  # AI 生成内容
python -m cli.main content topic-search -a <account_id> -k "关键词1,关键词2" --max-results 5  # 选题搜索
python -m cli.main content batch-generate       # 批量生成内容

# 发布管理
python -m cli.main publisher history            # 查看发布历史
python -m cli.main publisher publish <id>       # 手动发布内容（到草稿箱）
python -m cli.main publisher publish <id> --no-draft  # 直接发布（不进草稿箱）
python -m cli.main publisher retry <id>         # 重试失败的发布
python -m cli.main publisher batch-publish      # 批量发布待发布内容
python -m cli.main publisher stats              # 查看发布统计

# 发布池管理
python -m cli.main publish-pool list            # 查看发布池任务
python -m cli.main publish-pool add <id> -p 5   # 添加内容到发布池（优先级1-10）
python -m cli.main publish-pool remove <id>     # 从发布池移除内容
python -m cli.main publish-pool schedule <id>   # 设置计划发布时间
python -m cli.main publish-pool set-priority <id> -p 3  # 设置优先级
python -m cli.main publish-pool publish         # 手动触发批量发布
python -m cli.main publish-pool retry <id>      # 重试发布池任务

# 调度器管理
python -m cli.main scheduler status             # 查看调度器状态
python -m cli.main scheduler start              # 启动调度器
python -m cli.main scheduler stop               # 停止调度器
python -m cli.main scheduler list               # 查看所有定时任务
python -m cli.main scheduler info <task_id>     # 查看任务详情和执行历史

# 账号管理
python -m cli.main accounts list                # 查看所有账号
```

**典型工作流程**：

**流程1：生成并发布文章**
1. `python -m cli.main content create -a <account_id> -t "标题"` - 创建内容草稿
2. `python -m cli.main content generate -a <account_id> -t "选题" --keywords "关键词"` - AI 生成内容
3. `python -m cli.main content approve <id>` - 审核通过内容
4. `python -m cli.main publisher publish <id>` - 发布内容到微信公众号
5. `python -m cli.main publisher history` - 查看发布历史确认状态

**流程2：发布池自动发布**
1. `python -m cli.main content create` + `generate` - 生成内容
2. `python -m cli.main content approve <id>` - 审核通过
3. `python -m cli.main publish-pool add <id> -p 5` - 添加到发布池
4. `python -m cli.main scheduler status` - 确认调度器运行中
5. 等待定时任务自动执行（每分钟检查一次）或手动触发：
   `python -m cli.main publish-pool publish`

---

> **提示**：本文档仅包含核心信息。详细操作指南、API 参考、架构设计等文档请查看 [docs/](docs/) 目录。
