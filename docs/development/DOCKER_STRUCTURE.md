# ContentHub Docker 部署文件结构

本文档展示 Docker 容器化部署相关的所有文件及其用途。

```
content-hub/
├── docker-compose.yml              # 开发环境 Docker Compose 配置
├── docker-compose.prod.yml         # 生产环境 Docker Compose 配置
├── .dockerignore                   # Docker 构建忽略文件
├── Makefile                        # Docker 管理命令（make）
├── deploy.sh                       # 部署脚本（bash）
├── .env.production.example         # 生产环境配置示例
├── DEPLOYMENT.md                   # 详细部署文档
├── PHASE3_COMPLETION_REPORT.md     # 阶段 3 完成报告
│
├── src/backend/
│   ├── Dockerfile                  # 后端 Docker 镜像构建文件
│   ├── requirements.txt            # Python 依赖清单
│   ├── .env                        # 环境变量配置
│   ├── .env.example                # 环境变量示例
│   └── main.py                     # 应用入口
│
├── src/frontend/
│   ├── Dockerfile                  # 前端 Docker 镜像构建文件
│   ├── nginx.conf                  # Nginx 配置文件
│   ├── package.json                # Node.js 依赖清单
│   ├── vite.config.js              # Vite 构建配置
│   └── src/                        # Vue 源代码
│
├── data/                           # 数据持久化目录
│   └── backend/                    # 后端数据（SQLite、上传文件等）
│
└── logs/                           # 日志目录
    ├── backend/                    # 后端日志
    └── frontend/                   # 前端 Nginx 日志
```

---

## 文件说明

### 核心配置文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `docker-compose.yml` | 2.8KB | 开发环境配置，包含 backend 和 frontend 服务 |
| `docker-compose.prod.yml` | 2.2KB | 生产环境配置，优化了资源限制和安全选项 |
| `.dockerignore` | 2.1KB | 排除不必要的文件，加快构建速度 |

### Docker 镜像文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `src/backend/Dockerfile` | 1.2KB | 后端镜像，基于 Python 3.11-slim |
| `src/frontend/Dockerfile` | 972B | 前端镜像，多阶段构建 + nginx |
| `src/frontend/nginx.conf` | 2.8KB | Nginx 配置，包含反向代理和缓存 |

### 管理工具

| 文件 | 大小 | 说明 |
|------|------|------|
| `Makefile` | 4.0KB | 提供 `make` 命令管理 Docker 服务 |
| `deploy.sh` | 5.0KB | Bash 部署脚本，提供自动化部署功能 |

### 文档

| 文件 | 大小 | 说明 |
|------|------|------|
| `DEPLOYMENT.md` | 11.4KB | 详细的部署文档，包含所有必要信息 |
| `PHASE3_COMPLETION_REPORT.md` | - | 阶段 3 完成报告 |
| `.env.production.example` | 1.3KB | 生产环境配置示例 |

### 数据目录

| 目录 | 说明 |
|------|------|
| `data/backend/` | 后端数据持久化（SQLite 数据库、上传文件） |
| `logs/backend/` | 后端应用日志 |
| `logs/frontend/` | 前端 Nginx 日志 |

---

## 快速参考

### 使用 Makefile

```bash
# 查看所有命令
make help

# 构建并启动
make build && make up

# 查看状态
make status

# 查看日志
make logs

# 停止服务
make down
```

### 使用部署脚本

```bash
# 初始化项目
./deploy.sh init

# 启动服务
./deploy.sh start

# 查看状态
./deploy.sh status

# 备份数据
./deploy.sh backup
```

### 使用 Docker Compose

```bash
# 启动开发环境
docker compose up -d

# 启动生产环境
docker compose -f docker-compose.prod.yml up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

---

## 端口映射

| 服务 | 开发环境 | 生产环境 |
|------|----------|----------|
| 后端 API | 8000 | 127.0.0.1:8000 |
| 前端 Web | 80 | 127.0.0.1:8080 |

---

## 环境变量

主要环境变量在 `.env` 文件中配置：

```bash
# 必需配置
SECRET_KEY=your-secret-key
PUBLISHER_API_URL=http://your-publisher-url
PUBLISHER_API_KEY=your-api-key
TAVILY_API_KEY=your-tavily-key

# 可选配置
DEBUG=false
LOG_LEVEL=INFO
SCHEDULER_ENABLED=true
```

---

## 健康检查

所有服务都配置了健康检查：

```bash
# 后端健康检查
curl http://localhost:8000/docs

# 前端健康检查
curl http://localhost/health
```

---

**最后更新**: 2025-01-29
