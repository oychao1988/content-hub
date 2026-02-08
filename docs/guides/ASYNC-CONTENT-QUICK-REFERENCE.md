# 异步内容生成系统 - 快速参考

## 核心服务使用指南

### 1. AsyncContentGenerationService - 任务管理服务

#### 基本使用

```python
from app.services.async_content_generation_service import AsyncContentGenerationService
from app.db.database import SessionLocal

# 创建服务实例
db = SessionLocal()
service = AsyncContentGenerationService(db)

try:
    # 提交异步生成任务
    task_id = service.submit_task(
        account_id=1,
        topic="人工智能的未来发展",
        keywords="AI,人工智能,技术",
        category="科技",
        requirements="请详细论述 AI 在未来 10 年的发展趋势",
        tone="专业",
        priority=8,
        auto_approve=True
    )
    print(f"任务已提交: {task_id}")

    # 查询任务状态
    status = service.get_task_status(task_id)
    print(f"任务状态: {status['status']}")

    # 列出所有任务
    tasks = service.list_tasks(account_id=1, status="pending")

finally:
    service.close()
```

#### 上下文管理器使用

```python
with AsyncContentGenerationService() as service:
    task_id = service.submit_task(account_id=1, topic="测试选题")
    status = service.get_task_status(task_id)
```

#### 取消任务

```python
success = service.cancel_task(task_id)
if success:
    print(f"任务 {task_id} 已取消")
```

#### 清理旧任务

```python
# 清理 7 天前已完成/失败的任务
deleted_count = service.cleanup_old_tasks(days=7)
print(f"已清理 {deleted_count} 个旧任务")
```

---

### 2. TaskStatusPoller - 状态轮询器

#### 手动轮询

```python
from app.services.task_status_poller import TaskStatusPoller

# 创建轮询器（每 30 秒轮询一次）
poller = TaskStatusPoller(poll_interval=30)

# 执行一次轮询
stats = poller.poll_running_tasks()
print(f"轮询结果: {stats}")
# 输出: {'total': 10, 'completed': 3, 'failed': 1, 'timeout': 0, 'still_running': 5, 'error': 1}
```

#### 轮询单个任务

```python
status = poller.poll_single_task(task_id)
print(f"任务状态: {status}")  # 'pending'/'processing'/'completed'/'failed'
```

#### 处理超时任务

```python
timeout_count = poller.handle_timeout_tasks()
print(f"处理了 {timeout_count} 个超时任务")
```

---

### 3. TaskResultHandler - 结果处理器

#### 处理成功任务

```python
from app.services.task_result_handler import TaskResultHandler
from app.db.database import SessionLocal

db = SessionLocal()
handler = TaskResultHandler()

try:
    # 假设从轮询器获取到任务和结果
    task = db.query(ContentGenerationTask).filter_by(task_id=task_id).first()
    result = {
        "content": "生成的内容...",
        "htmlContent": "<p>生成的内容...</p>",
        "images": ["image1.jpg", "image2.jpg"],
        "qualityScore": 0.85
    }

    # 处理成功结果（会自动创建 Content、更新任务、添加到发布池）
    content = handler.handle_success(db, task, result)
    print(f"内容已创建: {content.id}")

finally:
    db.close()
```

#### 处理失败任务

```python
handler.handle_failure(db, task, "生成失败：网络超时")
```

#### 重试失败任务

```python
success = handler.retry_task(db, task)
if success:
    print(f"任务已重试 (第 {task.retry_count} 次)")
else:
    print("已达到最大重试次数")
```

---

### 4. TaskQueueService - 任务队列和 Worker

#### 使用 Worker 池

```python
from app.services.task_queue_service import start_worker_pool, stop_worker_pool, get_task_worker_pool

# 启动 Worker 池（3 个 Worker）
start_worker_pool(num_workers=3)

# 获取 Worker 池实例
pool = get_task_worker_pool()

# 查看状态
status = pool.get_status()
print(f"Worker 数量: {status['num_workers']}")
print(f"活跃 Worker: {status['active_workers']}")
print(f"队列大小: {status['total_queue_size']}")

# 停止 Worker 池
stop_worker_pool()
```

#### 直接使用队列

```python
from app.services.task_queue_service import MemoryTaskQueue

# 创建队列
queue = MemoryTaskQueue(maxsize=100)

# 添加任务
task = ContentGenerationTask(task_id="test-task", ...)
queue.put(task, block=False)

# 获取任务
task = queue.get(block=False)
if task:
    print(f"获取到任务: {task.task_id}")

# 查看队列大小
print(f"队列大小: {queue.size()}")
```

---

## 完整工作流示例

### 场景：提交任务 -> 轮询状态 -> 处理结果

```python
from app.services.async_content_generation_service import AsyncContentGenerationService
from app.services.task_status_poller import TaskStatusPoller
from app.db.database import SessionLocal

# 1. 提交任务
db = SessionLocal()
service = AsyncContentGenerationService(db)
task_id = service.submit_task(
    account_id=1,
    topic="测试选题",
    priority=5,
    auto_approve=True
)
print(f"任务已提交: {task_id}")
db.close()

# 2. 等待并轮询状态
poller = TaskStatusPoller()
max_wait = 300  # 最多等待 5 分钟
waited = 0

while waited < max_wait:
    import time
    time.sleep(10)  # 每 10 秒检查一次
    waited += 10

    status = service.get_task_status(task_id)
    if status['status'] in ['completed', 'failed', 'timeout']:
        break

    # 执行轮询（会自动处理结果）
    poller.poll_running_tasks()

print(f"最终状态: {status['status']}")
```

---

## 服务配置

### 环境变量

```bash
# .env
CREATOR_CLI_PATH=/path/to/content-creator  # content-creator CLI 路径
```

### 默认配置

```python
# AsyncContentGenerationService
DEFAULT_TIMEOUT_MINUTES = 30  # 任务超时时间

# TaskStatusPoller
poll_interval = 30  # 轮询间隔（秒）

# TaskWorkerPool
num_workers = 3  # Worker 数量
poll_interval = 5  # Worker 拉取任务间隔（秒）

# MemoryTaskQueue
maxsize = 100  # 队列最大容量
```

---

## 任务状态说明

| 状态 | 说明 | 可转移到的状态 |
|------|------|---------------|
| `pending` | 待处理（已创建，未提交） | `submitted`, `cancelled` |
| `submitted` | 已提交到 CLI，等待处理 | `processing`, `failed`, `timeout` |
| `processing` | CLI 正在处理 | `completed`, `failed`, `timeout` |
| `completed` | 已完成 | - |
| `failed` | 失败 | `pending` (重试) |
| `timeout` | 超时 | `pending` (重试) |
| `cancelled` | 已取消 | - |

---

## 错误处理

### 常见异常

```python
from app.core.exceptions import (
    CreatorCLINotFoundException,
    CreatorException,
    InvalidStateException,
    ResourceNotFoundException
)

try:
    task_id = service.submit_task(account_id=999, topic="测试")
except ResourceNotFoundException as e:
    print(f"资源不存在: {e.message}")
except CreatorCLINotFoundException as e:
    print(f"CLI 未配置: {e.message}")
except CreatorException as e:
    print(f"CLI 调用失败: {e.message}")
    print(f"详情: {e.details}")
except InvalidStateException as e:
    print(f"状态无效: {e.message}")
    print(f"当前状态: {e.current_state}")
    print(f"需要状态: {e.required_state}")
```

---

## 调试技巧

### 1. 查看日志

```python
from app.utils.custom_logger import log

# 所有服务都有详细日志
log.info("任务已提交")
log.error("任务失败", exc_info=True)
```

### 2. 查询数据库

```python
# 查看所有任务
tasks = db.query(ContentGenerationTask).all()

# 查看待处理任务
pending = db.query(ContentGenerationTask).filter_by(status="pending").all()

# 查看运行中的任务
running = db.query(ContentGenerationTask).filter(
    ContentGenerationTask.status.in_(["submitted", "processing"])
).all()

# 查看失败的任务
failed = db.query(ContentGenerationTask).filter_by(status="failed").all()
```

### 3. 监控 Worker 池

```python
pool = get_task_worker_pool()
status = pool.get_status()

for worker_status in status['worker_statuses']:
    print(f"Worker {worker_status['worker_id']}:")
    print(f"  运行中: {worker_status['running']}")
    print(f"  队列大小: {worker_status['queue_size']}")
```

---

## 性能优化建议

### 1. 批量操作

```python
# 批量查询任务状态
task_ids = ["task-1", "task-2", "task-3"]
statuses = [service.get_task_status(tid) for tid in task_ids]
```

### 2. 并发轮询

```python
# 使用多个轮询器并发处理
import threading

poller1 = TaskStatusPoller()
poller2 = TaskStatusPoller()

def poll_loop(poller):
    while True:
        poller.poll_running_tasks()
        time.sleep(30)

thread1 = threading.Thread(target=poll_loop, args=(poller1,))
thread2 = threading.Thread(target=poll_loop, args=(poller2,))
thread1.start()
thread2.start()
```

### 3. Worker 数量调整

```python
# 根据负载调整 Worker 数量
# CPU 密集型: num_workers = CPU 核心数
# I/O 密集型: num_workers = CPU 核心数 * 2-4

start_worker_pool(num_workers=4)
```

---

## 故障排查

### 问题：任务一直处于 `submitted` 状态

**可能原因**:
1. content-creator CLI 未启动
2. CLI 路径配置错误
3. 网络问题

**解决方法**:
```bash
# 检查 CLI 是否可用
content-creator --version

# 检查配置
echo $CREATOR_CLI_PATH

# 手动测试 CLI
content-creator create --topic "测试" --mode async
```

### 问题：Worker 无法启动

**可能原因**:
1. 数据库连接失败
2. 端口被占用

**解决方法**:
```python
# 检查数据库连接
from app.db.database import SessionLocal
db = SessionLocal()
print(db.execute("SELECT 1").scalar())
db.close()

# 检查 Worker 状态
pool = get_task_worker_pool()
status = pool.get_status()
print(status)
```

### 问题：内存队列满了

**可能原因**:
1. 任务提交速度 > 处理速度
2. Worker 数量不足

**解决方法**:
```python
# 增加 Worker 数量
stop_worker_pool()
start_worker_pool(num_workers=5)

# 或增加队列容量
queue = MemoryTaskQueue(maxsize=200)
```

---

## 相关文档

- [阶段 2 完成报告](ASYNC-CONTENT-STAGE2-SUMMARY.md)
- [异步内容生成架构](../architecture/ASYNC-CONTENT-ARCHITECTURE.md)
- [数据库模型](../architecture/DATABASE-DESIGN.md#contentgenerationtask)

---

**更新时间**: 2026-02-08
**版本**: 1.0
