# ContentHub 独立调度器容器部署指南

## 📋 概述

本指南介绍如何使用独立的调度器容器来运行 ContentHub 的定时任务系统。

### 架构优势

**之前的问题**：
- 调度器运行在 gunicorn 的 worker 进程中
- 多 worker 导致调度器状态无法共享
- 容器重启后需要手动启动调度器

**新的架构**：
- 调度器运行在独立的容器中
- 与 Web 服务完全解耦
- 容器自动重启时调度器自动启动
- 可以独立监控和扩展

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────┐
│              Docker Network                     │
│                                                 │
│  ┌─────────────────┐    ┌──────────────────┐  │
│  │   Backend Web   │    │   Scheduler      │  │
│  │   容器          │    │   容器           │  │
│  │                 │    │                  │  │
│  │  - FastAPI      │    │  - APScheduler   │  │
│  │  - gunicorn     │    │  - 执行器        │  │
│  │  - 4 workers    │    │  - 定时任务      │  │
│  │                 │    │                  │  │
│  │  端口: 18010    │    │  无端口          │  │
│  └─────────────────┘    └──────────────────┘  │
│         │                      │              │
│         └──────────┬───────────┘              │
│                    │                          │
│         ┌──────────▼──────────┐               │
│         │  SQLite Database    │               │
│         │  (共享卷)           │               │
│         └─────────────────────┘               │
└─────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 使用 Docker Compose（推荐）

```bash
# 启动所有服务（包括调度器）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看调度器日志
docker-compose logs -f scheduler

# 重启调度器
docker-compose restart scheduler
```

### 2. 手动部署（生产环境）

#### 步骤 1：构建调度器镜像

```bash
cd src/backend
docker build -f scheduler.Dockerfile -t content-hub-scheduler:latest .
```

#### 步骤 2：运行调度器容器

```bash
docker run -d \
  --name contenthub-scheduler \
  --network contenthub-network \
  -v /path/to/data/backend:/app/data \
  -v /path/to/logs/backend:/app/logs \
  -e DATABASE_URL=sqlite:///./data/contenthub.db \
  -e SCHEDULER_ENABLED=true \
  -e SCHEDULER_TIMEZONE=Asia/Shanghai \
  -e PUBLISHER_API_URL=http://150.158.88.23:3010 \
  -e PUBLISHER_API_KEY=your_api_key \
  -e TAVILY_API_KEY=your_tavily_key \
  --restart unless-stopped \
  content-hub-scheduler:latest
```

#### 步骤 3：验证调度器状态

```bash
# 检查容器状态
docker ps | grep contenthub-scheduler

# 查看调度器日志
docker logs contenthub-scheduler

# 进入容器检查
docker exec -it contenthub-scheduler python3 -c "
from app.services.scheduler_service import scheduler_service
print('运行状态:', scheduler_service.is_running)
print('执行器数:', len(scheduler_service.get_registered_executors()))
print('任务数:', len(scheduler_service.get_scheduled_jobs()))
"
```

---

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/contenthub.db` |
| `SCHEDULER_ENABLED` | 是否启用调度器 | `true` |
| `SCHEDULER_TIMEZONE` | 时区 | `Asia/Shanghai` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

### 健康检查

调度器容器包含健康检查，每 60 秒检查一次调度器运行状态：

```yaml
healthcheck:
  test: ["CMD", "python3", "-c", "from app.services.scheduler_service import scheduler_service; exit(0 if scheduler_service.is_running else 1)"]
  interval: 60s
  timeout: 10s
  retries: 3
  start_period: 10s
```

---

## 📊 监控和维护

### 查看调度器状态

```bash
# 方式 1：通过容器日志
docker logs -f contenthub-scheduler

# 方式 2：进入容器检查
docker exec -it contenthub-scheduler python3 -c "
from app.services.scheduler_service import scheduler_service
from app.db.database import SessionLocal

print('=== 调度器状态 ===')
print(f'运行状态: {scheduler_service.is_running}')
print(f'执行器数量: {len(scheduler_service.get_registered_executors())}')
print(f'定时任务数量: {len(scheduler_service.get_scheduled_jobs())}')

# 显示所有定时任务
db = SessionLocal()
jobs = scheduler_service.get_scheduled_jobs()
print('\n=== 定时任务列表 ===')
for job in jobs:
    print(f\"任务: {job['name']}\")
    print(f\"  下次运行: {job['next_run_time']}\")
db.close()
"
```

### 查看执行历史

```bash
docker exec -it contenthub-scheduler python3 -c "
from app.db.database import SessionLocal
from app.models.scheduler import TaskExecutionHistory

db = SessionLocal()
histories = db.query(TaskExecutionHistory).order_by(
    TaskExecutionHistory.started_at.desc()
).limit(10).all()

print('=== 最近 10 次执行历史 ===')
for h in histories:
    print(f\"{h.started_at} | {h.task_name} | {h.status} | {h.duration_ms}ms\")
db.close()
"
```

### 重启调度器

```bash
# Docker Compose
docker-compose restart scheduler

# 手动部署
docker restart contenthub-scheduler
```

---

## 🛠️ 故障排查

### 问题 1：调度器未启动

**症状**：容器运行但调度器状态显示停止

**解决**：
```bash
# 查看启动日志
docker logs contenthub-scheduler | grep "调度器"

# 手动初始化
docker exec contenthub-scheduler python /app/scripts/init_scheduler.py
```

### 问题 2：定时任务未执行

**症状**：调度器运行但任务没有触发

**解决**：
```bash
# 检查任务是否已加载
docker exec -it contenthub-scheduler python3 -c "
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()
tasks = db.query(ScheduledTask).filter(ScheduledTask.is_active == True).all()
print(f'活跃任务数: {len(tasks)}')
for task in tasks:
    print(f'{task.id}. {task.name} - {task.cron_expression}')
db.close()
"

# 检查执行器是否注册
docker exec -it contenthub-scheduler python3 -c "
from app.services.scheduler_service import scheduler_service
executors = scheduler_service.get_registered_executors()
print(f'已注册执行器: {len(executors)}')
for name in executors:
    print(f'  - {name}')
"
```

### 问题 3：容器自动重启

**症状**：调度器容器不断重启

**解决**：
```bash
# 查看详细日志
docker logs contenthub-scheduler --tail 100

# 检查健康检查状态
docker inspect contenthub-scheduler | grep -A 10 Health

# 临时禁用健康检查进行调试
docker update --no-healthcheck contenthub-scheduler
```

---

## 🔄 从旧架构迁移

### 场景 1：从手动启动迁移

如果你之前使用手动方式启动调度器：

```bash
# 停止在 backend 容器中运行的调度器
docker exec contenthub-backend-full python3 -c "
from app.services.scheduler_service import scheduler_service
scheduler_service.stop()
"

# 启动新的调度器容器
docker-compose up -d scheduler
```

### 场景 2：从 start.sh 脚本迁移

如果之前使用 `start.sh` 脚本自动启动调度器：

```bash
# 1. 更新 backend 容器的启动命令
# 修改 Dockerfile 或 docker-compose.yml
# 移除 init_scheduler.py 调用

# 2. 部署新的调度器容器
docker-compose up -d scheduler

# 3. 验证
docker-compose ps
docker-compose logs -f scheduler
```

---

## 📝 生产环境建议

### 1. 资源限制

```yaml
# docker-compose.yml
scheduler:
  # ... 其他配置
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
      reservations:
        cpus: '0.25'
        memory: 256M
```

### 2. 日志轮转

```yaml
scheduler:
  # ... 其他配置
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

### 3. 监控告警

建议配置以下监控指标：
- 调度器运行状态（健康检查）
- 定时任务执行成功率
- 任务执行时长
- 容器资源使用率

### 4. 备份策略

```bash
# 备份数据库
docker exec contenthub-scheduler cp /app/data/contenthub.db /app/data/backup_$(date +%Y%m%d).db

# 定期备份（cron）
0 2 * * * docker exec contenthub-scheduler cp /app/data/contenthub.db /app/data/backup_$(date +\%Y\%m\%d).db
```

---

## 🎯 验证清单

部署完成后，请验证以下项目：

- [ ] 调度器容器成功启动
- [ ] 健康检查通过
- [ ] 所有执行器已注册（7 个）
- [ ] 定时任务已加载（2 个）
- [ ] 调度器运行状态为 true
- [ ] 日志输出正常
- [ ] 可以查看任务执行历史
- [ ] 容器重启后调度器自动启动

---

## 📚 相关文档

- [调度器架构设计](../architecture/SCHEDULER-ARCHITECTURE.md)
- [Docker Compose 配置参考](../../docker-compose.yml)
- [生产环境部署指南](DEPLOYMENT.md)

---

**文档版本**: 1.0
**最后更新**: 2026-02-20
**维护人员**: Claude Code
