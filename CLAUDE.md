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

## 快速启动

### 后端

```bash
cd src/backend
pip install -r requirements.txt
cp .env.example .env
python -c "from app.db.database import init_db; init_db()"
python main.py
```

### 前端

```bash
cd src/frontend
npm install
npm run dev
```

## 模块系统架构（核心）

ContentHub 使用完全可插拔的模块系统，复用 omni-cast 的模块注册系统。

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

### Module 数据类结构

```python
@dataclass(frozen=True)
class Module:
    name: str                               # 模块名称
    router: APIRouter                        # API 路由
    startup: Optional[StartupFn] = None      # 启动钩子
    shutdown: Optional[ShutdownFn] = None    # 关闭钩子
```

### 模块加载机制

1. 从环境变量 `MODULES_ENABLED` 读取启用的模块列表
2. 动态导入 `app.modules.{module_name}.module`
3. 获取 `MODULE` 对象并验证类型
4. 注册路由到 FastAPI（前缀：`/api/v1/`）
5. 调用 startup/shutdown 钩子

**模块加载器位置**：`app/core/module_system/loader.py:13`

### 模块结构模板

```
app/modules/{module_name}/
├── module.py          # 模块定义（必须）
├── routes.py          # 路由定义
├── services.py        # 业务服务
└── schemas.py         # Pydantic 模型
```

## 项目结构

### 后端结构

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

### 前端结构

```
src/frontend/
└── src/
    ├── components/              # Vue 组件
    ├── views/                   # 页面视图
    ├── stores/                  # Pinia 状态管理
    ├── router/                  # 路由配置
    └── api/                     # API 客户端
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
pytest
```

### API 验证
- 访问 `/docs` 查看 Swagger 文档
- 使用 `/redoc` 查看 ReDoc 文档
