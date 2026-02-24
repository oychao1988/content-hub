# ContentHub 调度器容器部署快速指南

## 🚀 快速部署

### 前提条件

- Docker 已安装
- Docker Compose 已安装（推荐）
- 项目代码已拉取到最新

### 方式 1：使用部署验证脚本（推荐）

```bash
# 进入项目根目录
cd /path/to/content-hub

# 运行部署验证脚本
./scripts/deploy-scheduler-container.sh
```

脚本会自动完成：
1. ✅ 检查必要命令和文件
2. ✅ 构建调度器镜像
3. ✅ 启动调度器容器
4. ✅ 验证调度器状态
5. ✅ 显示定时任务
6. ✅ 生成健康检查报告

### 方式 2：手动部署

```bash
# 1. 构建镜像
cd src/backend
docker build -f scheduler.Dockerfile -t content-hub-scheduler:latest .

# 2. 启动容器（使用 docker-compose）
cd ../..
docker-compose up -d scheduler

# 3. 验证状态
docker logs -f contenthub-scheduler
```

### 方式 3：完全手动（适合调试）

```bash
# 1. 构建镜像
docker build -f src/backend/scheduler.Dockerfile -t content-hub-scheduler:latest .

# 2. 手动运行容器
docker run -d \
  --name contenthub-scheduler \
  --network contenthub-network \
  -v $(pwd)/data/backend:/app/data \
  -v $(pwd)/logs/backend:/app/logs \
  -e DATABASE_URL=sqlite:///./data/contenthub.db \
  -e SCHEDULER_ENABLED=true \
  -e SCHEDULER_TIMEZONE=Asia/Shanghai \
  --restart unless-stopped \
  content-hub-scheduler:latest

# 3. 查看日志
docker logs -f contenthub-scheduler

# 4. 验证状态
docker exec contenthub-scheduler python3 -c "
from app.services.scheduler_service import scheduler_service
print('运行状态:', scheduler_service.is_running)
print('执行器数:', len(scheduler_service.get_registered_executors()))
print('任务数:', len(scheduler_service.get_scheduled_jobs()))
"
```

---

## 📊 验证部署

### 快速验证

```bash
# 检查容器状态
docker ps | grep contenthub-scheduler

# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' contenthub-scheduler

# 查看日志
docker logs contenthub-scheduler | tail -50
```

### 详细验证

```bash
# 进入容器检查
docker exec -it contenthub-scheduler bash

# 在容器内执行
python3 -c "
from app.services.scheduler_service import scheduler_service
from app.db.database import SessionLocal

print('=== 调度器状态 ===')
print(f'运行状态: {scheduler_service.is_running}')
print(f'执行器数量: {len(scheduler_service.get_registered_executors())}')
print(f'定时任务数量: {len(scheduler_service.get_scheduled_jobs())}')

# 显示所有任务
db = SessionLocal()
jobs = scheduler_service.get_scheduled_jobs()
print('\n=== 定时任务 ===')
for job in jobs:
    print(f\"任务: {job['name']}\")
    print(f\"  下次运行: {job['next_run_time']}\")
db.close()
"
```

---

## 🛠️ 常用命令

### 容器管理

```bash
# 启动
docker-compose start scheduler

# 停止
docker-compose stop scheduler

# 重启
docker-compose restart scheduler

# 查看日志
docker-compose logs -f scheduler

# 删除容器
docker-compose down scheduler
```

### 调度器管理

```bash
# 查看状态
docker exec contenthub-scheduler python3 -c "
from app.services.scheduler_service import scheduler_service
print('运行状态:', scheduler_service.is_running)
"

# 手动初始化（如果调度器停止）
docker exec contenthub-scheduler python /app/scripts/init_scheduler.py

# 查看执行历史
docker exec contenthub-scheduler python3 -c "
from app.db.database import SessionLocal
from app.models.scheduler import TaskExecutionHistory

db = SessionLocal()
histories = db.query(TaskExecutionHistory).order_by(
    TaskExecutionHistory.started_at.desc()
).limit(10).all()

print('=== 最近执行历史 ===')
for h in histories:
    print(f\"{h.started_at} | {h.task_name} | {h.status} | {h.duration_ms}ms\")
db.close()
"
```

---

## 🔄 从旧架构迁移

### 停止旧的调度器

如果你之前在 backend 容器中运行调度器：

```bash
# 停止旧调度器
docker exec contenthub-backend-full python3 -c "
from app.services.scheduler_service import scheduler_service
scheduler_service.stop()
"

# 或者删除 init_scheduler.py 的调用
# 修改 src/backend/scripts/start.sh
```

### 启动新的调度器容器

```bash
# 使用 docker-compose
docker-compose up -d scheduler

# 或使用部署脚本
./scripts/deploy-scheduler-container.sh
```

### 验证迁移

```bash
# 检查旧容器中的调度器已停止
docker exec contenthub-backend-full python3 -c "
from app.services.scheduler_service import scheduler_service
print('运行状态:', scheduler_service.is_running)
"

# 检查新容器中的调度器已启动
docker exec contenthub-scheduler python3 -c "
from app.services.scheduler_service import scheduler_service
print('运行状态:', scheduler_service.is_running)
"
```

---

## 📚 更多文档

- [完整部署指南](docs/deployment/SCHEDULER-CONTAINER-GUIDE.md)
- [架构设计文档](docs/architecture/SCHEDULER-ARCHITECTURE.md)
- [故障排查手册](docs/deployment/SCHEDULER-CONTAINER-GUIDE.md#故障排查)

---

## 🆘 获取帮助

如果遇到问题：

1. 查看日志：`docker logs contenthub-scheduler`
2. 检查健康状态：`docker inspect contenthub-scheduler`
3. 运行验证脚本：`./scripts/deploy-scheduler-container.sh`
4. 参考详细文档：`docs/deployment/SCHEDULER-CONTAINER-GUIDE.md`

---

**部署脚本版本**: 1.0
**最后更新**: 2026-02-20
