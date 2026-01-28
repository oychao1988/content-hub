# ContentHub 架构设计

**版本**: v1.0
**更新日期**: 2026-01-27
**架构基础**: omni-cast 模块注册系统

---

## 一、架构概述

### 1.1 技术栈

**后端**：
- **框架**: FastAPI (与 omni-cast 一致)
- **模块系统**: 复用 omni-cast 的模块系统
- **数据库**: SQLite (轻量，易于部署)
- **ORM**: SQLAlchemy
- **任务调度**: APScheduler
- **配置管理**: Pydantic Settings
- **外部 API**: Tavily API (选题搜索)

**前端**：
- **框架**: Vue 3 + Vite (现代、轻量)
- **UI 组件**: Element Plus (完整的后台管理组件)
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **路由**: Vue Router

**集成服务**：
- **content-creator**: CLI 调用 (subprocess)
- **content-publisher**: HTTP API (requests)

### 1.2 核心设计原则

1. **可插拔模块化架构**: 完全复用 omni-cast 的模块系统设计
   - 每个业务模块独立定义，可插拔集成
   - 通过模块加载器动态导入和初始化
   - 统一的模块接口定义（Module 数据类）

2. **API 优先**: 所有功能通过 Web API 提供
   - 每个模块有独立的 APIRouter
   - 统一的 API 前缀管理
   - 支持启动/关闭钩子函数

3. **数据库优先**: 所有配置和数据存储在数据库
   - 支持快速查询、并发编辑、事务保证
   - Markdown 文件仅用于初始化导入、配置备份、版本控制

4. **简化流程**: content-creator 已包含图片生成和质量检查，ContentHub 只需处理下载和发布

5. **轻量部署**: 单机部署，SQLite 数据库，无需复杂配置

### 1.3 模块系统架构

```
┌─────────────────────────────────────────────────┐
│  FastAPI 主应用                                │
├─────────────────────────────────────────────────┤
│  模块加载器 (Loader)                           │
│  ├─ 从设置读取 MODULES_ENABLED                │
│  ├─ 动态导入模块 module.py                    │
│  ├─ 验证 MODULE 对象                          │
│  └─ 包含模块路由                              │
├─────────────────────────────────────────────────┤
│  核心模块 (来自 omni-cast)                     │
│  ├─ auth/              # 认证模块              │
│  ├─ system/            # 系统模块              │
│  └─ shared/            # 共享模块（schemas/services）│
├─────────────────────────────────────────────────┤
│  ContentHub 业务模块                           │
│  ├─ accounts/          # 账号管理模块          │
│  ├─ content/           # 内容管理模块          │
│  ├─ scheduler/         # 定时任务模块          │
│  ├─ publisher/         # 发布管理模块          │
│  ├─ dashboard/         # 仪表盘模块            │
│  └─ publish_pool/      # 发布池模块            │
└─────────────────────────────────────────────────┘
```

---

## 二、项目结构

```
content-hub/
├── src/
│   ├── backend/                    # 后端（复用 omni-cast 架构）
│   │   ├── app/
│   │   │   ├── core/              # 核心模块（来自 omni-cast）
│   │   │   │   ├── module_system/ # 模块系统
│   │   │   │   │   ├── module.py  # Module 数据类
│   │   │   │   │   └── loader.py  # 模块加载器
│   │   │   ├── modules/           # 业务模块（完全遵循 omni-cast 架构）
│   │   │   │   ├── auth/          # 认证模块（保留 omni-cast）
│   │   │   │   ├── system/        # 系统模块（保留 omni-cast）
│   │   │   │   ├── shared/        # 共享模块（保留 omni-cast）
│   │   │   │   ├── accounts/      # 账号管理模块（新增）
│   │   │   │   ├── content/       # 内容管理模块（新增）
│   │   │   │   ├── scheduler/     # 定时任务模块（新增）
│   │   │   │   ├── publisher/     # 发布管理模块（新增）
│   │   │   │   ├── dashboard/     # 仪表盘模块（新增）
│   │   │   │   └── publish_pool/  # 发布池模块（新增）
│   │   │   ├── services/          # 通用服务层（跨模块共享）
│   │   │   ├── models/            # 共享数据模型（跨模块共享）
│   │   │   └── db/                # 数据库
│   │   └── ...
│   └── frontend/                  # 前端（Vue 3，待实现）
```

---

## 三、模块系统设计

### 3.1 模块接口定义

```python
# app/core/module_system/module.py
@dataclass(frozen=True)
class Module:
    name: str                    # 模块名称（如 "accounts"、"content"）
    router: APIRouter           # 模块的 API 路由
    startup: Optional[StartupFn] = None    # 启动时的钩子函数
    shutdown: Optional[ShutdownFn] = None  # 关闭时的钩子函数
```

### 3.2 模块加载流程

```python
# app/core/module_system/loader.py
def load_modules(app: FastAPI, settings: Any) -> List[Module]:
    """动态加载所有启用的模块"""
    enabled = getattr(settings, "MODULES_ENABLED", []) or []
    modules: List[Module] = []

    for module_name in enabled:
        # 1. 动态导入模块的 module.py
        mod = importlib.import_module(f"app.modules.{module_name}.module")

        # 2. 获取 MODULE 对象
        module_obj = getattr(mod, "MODULE", None)

        # 3. 验证并注册模块
        if module_obj is not None and isinstance(module_obj, Module):
            app.include_router(module_obj.router, prefix=settings.API_STR)
            modules.append(module_obj)

    return modules
```

### 3.3 模块定义示例

每个模块需要在 `app/modules/{module_name}/module.py` 中定义：

```python
# app/modules/accounts/module.py
from fastapi import APIRouter
from app.core.module_system.module import Module

router = APIRouter()

def startup(app):
    """账号管理模块启动时执行的代码"""
    pass

def shutdown(app):
    """账号管理模块关闭时执行的代码"""
    pass

MODULE = Module(
    name="accounts",
    router=router,
    startup=startup,
    shutdown=shutdown
)
```

### 3.4 配置模块启用

在配置中通过 `MODULES_ENABLED` 列表指定要启用的模块：

```python
# app/core/config.py
class Settings(BaseSettings):
    MODULES_ENABLED = [
        "auth",          # 认证模块（保留 omni-cast）
        "system",        # 系统模块（保留 omni-cast）
        "shared",        # 共享模块（保留 omni-cast）
        "accounts",      # 账号管理模块（新增）
        "content",       # 内容管理模块（新增）
        "scheduler",     # 定时任务模块（新增）
        "publisher",     # 发布管理模块（新增）
        "dashboard",     # 仪表盘模块（新增）
        "publish-pool"   # 发布池模块（新增）
    ]
```

---

## 四、业务模块架构

### 4.1 模块通用结构

每个业务模块遵循相同的架构：

```
app/modules/{module_name}/
├── module.py          # 模块定义（导出 MODULE 对象）
├── endpoints.py       # API 路由
├── services.py        # 业务服务层
├── models.py          # 数据模型层
├── schemas.py         # Pydantic 模式层
└── __init__.py
```

### 4.2 各业务模块概述

#### 4.2.1 accounts 模块（账号管理）
- 账号 CRUD 操作
- 配置同步（Markdown ↔ 数据库）
- 账号切换和激活

#### 4.2.2 content 模块（内容管理）
- 内容生成（调用 content-creator）
- 内容审核流程
- 内容状态管理

#### 4.2.3 scheduler 模块（定时任务）
- 任务调度器集成（APScheduler）
- 任务管理和触发
- 执行历史记录

#### 4.2.4 publisher 模块（发布管理）
- 内容发布（调用 content-publisher）
- 发布历史查询
- 发布状态跟踪

#### 4.2.5 dashboard 模块（仪表盘）
- 系统概览和关键指标
- 内容生成和发布趋势图
- 快速操作入口

#### 4.2.6 publish_pool 模块（发布池）
- 待发布内容管理
- 内容优先级调整
- 发布队列管理

---

## 五、数据架构

### 5.1 数据库设计原则

1. **单一真实数据源**: 所有配置和数据存储在 SQLite 数据库中
2. **混合配置**: Markdown 文件仅用于初始化导入和配置备份
3. **敏感信息加密**: 微信凭证和 API 密钥使用 AES 加密存储
4. **状态管理**: 内容状态通过数据库字段管理

### 5.2 核心数据表

- `accounts` - 账号信息表
- `writing_styles` - 写作风格配置表
- `content_sections` - 内容板块配置表
- `data_sources` - 数据源配置表
- `publish_configs` - 发布配置表
- `contents` - 内容表
- `publish_logs` - 发布记录表
- `scheduled_tasks` - 定时任务表

---

## 六、API 架构

### 6.1 API 设计原则

1. **RESTful 风格**: 使用标准的 HTTP 方法
2. **统一前缀**: 所有 API 以 `/api/v1/` 为前缀
3. **模块化路由**: 每个业务模块有独立的路由前缀
4. **错误处理**: 统一的错误响应格式
5. **文档化**: 自动生成 Swagger 和 ReDoc 文档

### 6.2 模块 API 前缀

| 模块名 | 路由前缀 | 说明 |
|--------|----------|------|
| accounts | `/api/v1/accounts` | 账号管理 |
| content | `/api/v1/content` | 内容管理 |
| scheduler | `/api/v1/scheduler` | 定时任务 |
| publisher | `/api/v1/publisher` | 发布管理 |
| dashboard | `/api/v1/dashboard` | 仪表盘 |
| publish_pool | `/api/v1/publish-pool` | 发布池 |

---

## 七、集成架构

### 7.1 与 content-creator 集成

- **方式**: CLI 调用（subprocess）
- **输入**: 配置参数（从数据库读取）
- **输出**: 生成的文章内容和图片 URL
- **处理**: 异步调用，支持任务取消

### 7.2 与 content-publisher 集成

- **方式**: HTTP API（requests）
- **输入**: 文章内容和配置参数
- **输出**: 发布结果和媒体 ID
- **处理**: 同步调用，支持重试机制

### 7.3 与 Tavily API 集成

- **方式**: HTTP API（requests）
- **输入**: 搜索关键词和配置参数
- **输出**: 搜索结果和评分
- **处理**: 异步调用，支持超时设置

---

## 八、部署架构

### 8.1 部署方式

**单机部署**：
- SQLite 数据库（无需额外安装）
- 前后端分离部署
- 建议使用 Nginx 反向代理整合

**Docker 部署**：
- 提供 Dockerfile 和 docker-compose.yml
- 支持环境变量配置
- 易于部署和维护

### 8.2 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/contenthub.db` |
| `PUBLISHER_API_URL` | content-publisher 服务地址 | `http://150.158.88.23:3010` |
| `PUBLISHER_API_KEY` | content-publisher API 密钥 | - |
| `CREATOR_CLI_PATH` | content-creator CLI 路径 | - |
| `TAVILY_API_KEY` | Tavily API 密钥 | - |
| `SCHEDULER_ENABLED` | 是否启用调度器 | `true` |

---

## 九、架构优势

### 9.1 技术优势

1. **可扩展性**: 完全复用 omni-cast 的模块系统，支持动态添加新模块
2. **可维护性**: 模块化设计，降低了代码耦合度
3. **可测试性**: 每个模块可以独立测试
4. **灵活性**: 支持配置驱动的模块启用和禁用
5. **轻量性**: 单机部署，无需复杂的基础设施

### 9.2 业务优势

1. **统一管理**: 所有内容运营功能集成在一个系统中
2. **自动化流程**: 从选题到发布的完整自动化流程
3. **多平台支持**: 支持微信公众号等多个平台的发布
4. **配置灵活**: 支持账号级别的配置和管理
5. **可定制化**: 支持写作风格、内容板块等的定制

---

## 十、架构决策记录

### 10.1 数据库选型

**选择**: SQLite
**原因**: 轻量、易于部署、无需额外安装、性能足够满足当前需求

**替代方案**: PostgreSQL、MySQL
**放弃原因**: 需要额外的数据库服务，增加了部署复杂度

### 10.2 任务调度选型

**选择**: APScheduler
**原因**: 轻量、易于集成、支持多种调度方式

**替代方案**: Celery、RQ
**放弃原因**: 需要额外的消息队列服务，增加了部署复杂度

### 10.3 模块系统

**选择**: 复用 omni-cast 的模块系统
**原因**: 已有的成熟架构、可插拔设计、支持动态加载

**替代方案**: 从零开始设计
**放弃原因**: 重复造轮子，增加了开发成本
