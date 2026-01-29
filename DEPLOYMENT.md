# ContentHub Docker 部署指南

本文档详细说明如何使用 Docker 和 Docker Compose 部署 ContentHub 系统。

---

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [环境变量配置](#环境变量配置)
- [数据持久化](#数据持久化)
- [服务管理](#服务管理)
- [生产环境部署](#生产环境部署)
- [常见问题排查](#常见问题排查)
- [升级和备份](#升级和备份)

---

## 环境要求

### 软件版本要求

- **Docker**: 20.10 或更高版本
- **Docker Compose**: 2.0 或更高版本
- **操作系统**: Linux/macOS/Windows（支持 Docker）
- **内存**: 至少 2GB 可用内存
- **磁盘空间**: 至少 5GB 可用空间

### 验证环境

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker compose version

# 检查 Docker 是否运行
docker ps
```

---

## 快速开始

### 1. 克隆项目（如果还没有）

```bash
git clone <repository-url>
cd content-hub
```

### 2. 配置环境变量

复制环境变量示例文件并编辑：

```bash
cp src/backend/.env.example src/backend/.env
```

编辑 `.env` 文件，配置必要的环境变量（见 [环境变量配置](#环境变量配置)）。

### 3. 构建并启动服务

```bash
# 构建镜像
docker compose build

# 启动所有服务（后台运行）
docker compose up -d

# 查看服务状态
docker compose ps
```

### 4. 验证部署

- **前端应用**: http://localhost
- **后端 API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost/health

```bash
# 查看服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 5. 停止服务

```bash
# 停止所有服务
docker compose down

# 停止并删除数据卷（谨慎使用）
docker compose down -v
```

---

## 环境变量配置

### 必需配置

编辑 `src/backend/.env` 文件，设置以下必需的环境变量：

```bash
# 安全配置（必须修改）
SECRET_KEY=your-random-secret-key-at-least-32-characters-long

# 外部服务配置
PUBLISHER_API_URL=http://your-publisher-service-url:port
PUBLISHER_API_KEY=your-publisher-api-key
TAVILY_API_KEY=your-tavily-api-key

# Content-Creator CLI 配置（如果使用）
CREATOR_CLI_PATH=/path/to/content-creator
```

### 可选配置

```bash
# 应用配置
APP_NAME=ContentHub
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# 任务调度
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Shanghai

# 文件上传
MAX_UPLOAD_SIZE=10485760  # 10MB
```

### 生成安全的 SECRET_KEY

```bash
# 使用 Python 生成随机密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 或使用 OpenSSL
openssl rand -hex 32
```

---

## 数据持久化

### 持久化目录

Docker Compose 配置了以下数据卷：

| 目录 | 容器路径 | 说明 |
|------|----------|------|
| `./data/backend` | `/app/data` | SQLite 数据库、上传文件 |
| `./logs/backend` | `/app/logs` | 后端应用日志 |
| `./logs/frontend` | `/var/log/nginx` | Nginx 访问日志 |

### 备份数据

```bash
# 创建备份目录
mkdir -p backups

# 备份数据库
cp data/backend/contenthub.db backups/contenthub-$(date +%Y%m%d).db

# 备份完整数据目录
tar -czf backups/data-$(date +%Y%m%d).tar.gz data/
```

### 恢复数据

```bash
# 恢复数据库
cp backups/contenthub-20250129.db data/backend/contenthub.db

# 恢复完整数据目录
tar -xzf backups/data-20250129.tar.gz
```

---

## 服务管理

### 启动和停止

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose stop

# 重启服务
docker compose restart

# 重新启动特定服务
docker compose restart backend
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs

# 实时查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend

# 查看最近 100 行日志
docker compose logs --tail=100
```

### 进入容器

```bash
# 进入后端容器
docker compose exec backend bash

# 进入前端容器
docker compose exec frontend sh

# 在容器中执行命令
docker compose exec backend python -c "print('Hello')"
```

### 更新镜像

```bash
# 重新构建镜像
docker compose build

# 重新构建并启动
docker compose up -d --build

# 强制重新构建（不使用缓存）
docker compose build --no-cache
```

---

## 生产环境部署

### 1. 使用外部 Nginx 反向代理

如果已有 Nginx 服务器，可以只运行后端服务：

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile
    restart: always
    ports:
      - "127.0.0.1:8000:8000"  # 仅监听本地
    volumes:
      - ./data/backend:/app/data
      - ./logs/backend:/app/logs
    env_file:
      - src/backend/.env
```

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 2. 配置 HTTPS

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 3. 性能优化

#### 调整 Gunicorn Worker 数量

编辑 `src/backend/Dockerfile`：

```dockerfile
CMD ["gunicorn", "main:app", \
     "-w", "8", \  # 根据 CPU 核心数调整
     "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000"]
```

#### 启用 Nginx 缓存

已在 `nginx.conf` 中配置，可调整缓存大小：

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:50m max_size=500m inactive=60m;
```

### 4. 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 5. 日志轮转

创建 `/etc/logrotate.d/contenthub`：

```
/path/to/content-hub/logs/*/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
}
```

---

## 常见问题排查

### 1. 容器无法启动

```bash
# 查看容器日志
docker compose logs backend

# 检查端口占用
lsof -i :8000
lsof -i :80

# 检查磁盘空间
df -h
```

### 2. 后端服务无响应

```bash
# 检查健康状态
docker compose ps

# 查看后端日志
docker compose logs backend

# 进入容器检查
docker compose exec backend bash
curl http://localhost:8000/docs
```

### 3. 前端无法连接后端

检查 `nginx.conf` 中的代理配置：

```nginx
location /api {
    proxy_pass http://backend:8000;  # 确保使用服务名
}
```

检查 docker-compose 网络配置：

```bash
# 查看网络
docker network ls
docker network inspect contenthub-network
```

### 4. 数据库文件丢失

检查数据卷挂载：

```bash
# 查看挂载点
docker compose exec backend ls -la /app/data

# 检查宿主机目录
ls -la ./data/backend
```

### 5. 权限问题

```bash
# 修改数据目录权限
chmod -R 755 data/
ls -la data/
```

### 6. 镜像构建失败

```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建（无缓存）
docker compose build --no-cache
```

### 7. 内存不足

```bash
# 查看容器资源使用
docker stats

# 减少 worker 数量或增加内存限制
```

---

## 升级和备份

### 升级流程

1. **备份数据**

```bash
# 停止服务
docker compose down

# 备份数据
cp -r data/ backups/data-$(date +%Y%m%d)/
```

2. **拉取最新代码**

```bash
git pull origin main
```

3. **重新构建镜像**

```bash
docker compose build --no-cache
```

4. **启动服务**

```bash
docker compose up -d
```

5. **验证升级**

```bash
# 检查服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 回滚流程

如果升级出现问题，执行回滚：

```bash
# 停止服务
docker compose down

# 恢复数据
cp -r backups/data-20250129/* data/

# 恢复代码（如果需要）
git checkout <previous-commit>

# 重新构建
docker compose build
docker compose up -d
```

### 定期备份

创建备份脚本 `backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR/$DATE"

# 备份数据库
docker compose exec backend \
    sqlite3 /app/data/contenthub.db ".backup /tmp/backup.db"
docker cp contenthub-backend:/tmp/backup.db \
    "$BACKUP_DIR/$DATE/contenthub.db"

# 备份数据目录
tar -czf "$BACKUP_DIR/$DATE/data.tar.gz" data/

# 清理旧备份（保留最近 7 天）
find "$BACKUP_DIR" -type d -mtime +7 -exec rm -rf {} \;
```

添加到 crontab：

```bash
# 每天凌晨 2 点备份
0 2 * * * /path/to/backup.sh
```

---

## 安全建议

1. **修改默认密钥**

```bash
# 生成强随机密钥
SECRET_KEY=$(openssl rand -hex 32)
```

2. **限制容器权限**

```yaml
services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

3. **使用非 root 用户**

编辑 `Dockerfile` 添加：

```dockerfile
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser
```

4. **启用防火墙**

```bash
# 仅开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

5. **定期更新镜像**

```bash
# 更新基础镜像
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull nginx:alpine
```

---

## 监控和告警

### 查看容器状态

```bash
# 实时监控
docker stats

# 查看健康状态
docker compose ps
```

### 日志监控

```bash
# 监控错误日志
docker compose logs -f backend | grep ERROR

# 统计错误数量
docker compose logs backend | grep ERROR | wc -l
```

### 设置告警（可选）

使用 Prometheus + Grafana 或第三方服务（如 Sentry）进行监控。

---

## 支持和帮助

- **项目文档**: [CLAUDE.md](./CLAUDE.md)
- **API 文档**: http://localhost:8000/docs
- **GitHub Issues**: <repository-url>/issues

---

## 附录

### Docker Compose 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 查看状态
docker compose ps

# 进入容器
docker compose exec backend bash

# 重新构建
docker compose build

# 强制重新构建
docker compose build --no-cache

# 查看资源使用
docker stats
```

### 目录结构

```
content-hub/
├── docker-compose.yml          # Docker Compose 配置
├── .dockerignore              # Docker 忽略文件
├── DEPLOYMENT.md              # 部署文档（本文件）
├── data/                      # 数据持久化目录
│   └── backend/              # 后端数据
├── logs/                      # 日志目录
│   ├── backend/              # 后端日志
│   └── frontend/             # 前端日志
└── src/
    ├── backend/              # 后端代码
    │   ├── Dockerfile        # 后端镜像构建文件
    │   └── .env              # 环境变量配置
    └── frontend/             # 前端代码
        ├── Dockerfile        # 前端镜像构建文件
        └── nginx.conf        # Nginx 配置
```

---

**最后更新**: 2025-01-29
