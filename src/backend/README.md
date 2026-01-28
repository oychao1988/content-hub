# ContentHub Backend

ContentHub 后端服务，基于 FastAPI + SQLAlchemy + APScheduler。

## 技术栈

- **框架**: FastAPI 0.109.0
- **数据库**: SQLite + SQLAlchemy 2.0
- **任务调度**: APScheduler 3.10
- **模块系统**: omni-cast 模块注册系统

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的配置项
```

### 3. 初始化数据库

```bash
python -c "from app.db.database import init_db; init_db()"
```

### 4. 启动服务

```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

### 5. 访问 API 文档

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 项目结构

```
app/
├── core/               # 核心模块（来自 omni-cast）
│   ├── module_registry/   # 模块注册系统
│   ├── module_system/     # 模块基类和接口
│   ├── config.py          # 配置管理
│   ├── exceptions.py      # 异常定义
│   ├── cache.py           # 缓存工具
│   └── security.py        # 安全工具
├── models/             # 数据模型
│   ├── account.py         # 账号相关模型
│   ├── content.py         # 内容相关模型
│   ├── scheduler.py       # 定时任务模型
│   └── publisher.py       # 发布相关模型
├── services/           # 业务服务
├── modules/            # 业务模块（API 路由）
├── db/                 # 数据库
│   └── database.py        # 数据库配置和会话
├── utils/              # 工具函数
└── factory.py          # 应用工厂
```

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/contenthub.db` |
| `PUBLISHER_API_URL` | content-publisher 服务地址 | `http://150.158.88.23:3010` |
| `PUBLISHER_API_KEY` | content-publisher API 密钥 | - |
| `CREATOR_CLI_PATH` | content-creator CLI 路径 | - |
| `TAVILY_API_KEY` | Tavily API 密钥 | - |
| `SCHEDULER_ENABLED` | 是否启用调度器 | `true` |
| `DEBUG` | 调试模式 | `false` |

## 开发指南

### 添加新模块

1. 在 `app/modules/` 创建模块目录
2. 创建路由文件 `routes.py`
3. 创建服务文件 `services.py`
4. 在模块中注册路由

### 数据库迁移

当前使用 SQLAlchemy 自动创建表，生产环境建议使用 Alembic 进行迁移管理。

```bash
# 初始化 Alembic（如需要）
alembic init migrations

# 创建迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head
```

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_accounts.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 部署

### Docker 部署

```bash
docker build -t contenthub-backend .
docker run -d -p 8000:8000 --env-file .env contenthub-backend
```

### 传统部署

```bash
# 使用 gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 相关文档

- [架构设计](../../docs/ARCHITECTURE.md)
- [API 文档](http://localhost:8000/docs)
