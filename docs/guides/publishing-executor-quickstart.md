# PublishingExecutor 快速使用指南

## 一、核心概念

`PublishingExecutor` 是一个批量发布任务执行器，用于自动处理发布池中到期的内容。

### 关键特性
- **自动查询**：自动查找发布池中所有待发布且已到期的内容
- **批量处理**：一次性处理所有到期内容
- **容错机制**：单个内容发布失败不会影响其他内容
- **自动重试**：支持失败内容的自动重试

## 二、基本使用

### 1. 通过定时任务使用

```python
from app.db.database import get_db
from app.models.scheduler import ScheduledTask
from datetime import datetime, timedelta

db = next(get_db())

# 创建每5分钟执行一次的发布任务
task = ScheduledTask(
    name="自动发布任务",
    task_type="publishing",  # 使用 publishing 类型
    schedule_type="interval",
    interval_seconds=300,  # 5分钟
    params={},  # PublishingExecutor 不需要参数
    enabled=True,
    next_run=datetime.utcnow() + timedelta(seconds=5)
)

db.add(task)
db.commit()
```

### 2. 通过 CLI 使用

```bash
# 查看所有定时任务
contenthub scheduler list

# 创建发布任务
contenthub scheduler create

# 手动触发发布任务
contenthub scheduler trigger <task_id>

# 查看任务执行历史
contenthub scheduler history <task_id>
```

### 3. 手动执行（代码方式）

```python
from app.services.scheduler_service import scheduler_service
from app.db.database import get_db
import asyncio

db = next(get_db())

# 手动执行发布任务
result = await scheduler_service.execute_task(
    task_id=1,
    task_type="publishing",
    task_params={},
    db=db
)

# 查看结果
print(f"总数: {result.data['total_count']}")
print(f"成功: {result.data['success_count']}")
print(f"失败: {result.data['failed_count']}")
print(f"耗时: {result.duration:.2f}秒")
```

## 三、添加内容到发布池

### 1. 通过 API

```bash
POST /api/v1/publish-pool/add
{
  "content_id": 123,
  "priority": 5,
  "scheduled_at": "2026-02-06T12:00:00Z"
}
```

### 2. 通过 CLI

```bash
# 添加内容到发布池
contenthub publish-pool add 123

# 设置优先级和发布时间
contenthub publish-pool add 123 --priority 1 --scheduled-at "2026-02-06 12:00:00"
```

### 3. 通过代码

```python
from app.services.publish_pool_service import publish_pool_service
from app.db.database import get_db
from datetime import datetime, timedelta

db = next(get_db())

# 添加到发布池（5分钟后发布，优先级1）
entry = publish_pool_service.add_to_pool(
    db,
    content_id=123,
    priority=1,
    scheduled_at=datetime.utcnow() + timedelta(minutes=5)
)

print(f"已添加到发布池，ID: {entry.id}")
```

## 四、查看发布池状态

### 1. 通过 API

```bash
GET /api/v1/publish-pool/list
```

### 2. 通过 CLI

```bash
# 查看发布池列表
contenthub publish-pool list

# 查看发布池统计
contenthub publish-pool stats
```

### 3. 通过代码

```python
from app.services.publish_pool_service import publish_pool_service
from app.db.database import get_db

db = next(get_db())

# 获取发布池列表
pool_entries = publish_pool_service.get_publish_pool(db)

for entry in pool_entries:
    print(f"ID: {entry.id}, Content ID: {entry.content_id}, "
          f"Status: {entry.status}, Priority: {entry.priority}")

# 获取统计信息
stats = publish_pool_service.get_pool_statistics(db)
print(f"总计: {stats['total']}, 待发布: {stats['pending']}, "
      f"发布中: {stats['publishing']}, 已发布: {stats['published']}, "
      f"失败: {stats['failed']}")
```

## 五、执行结果说明

### 返回数据结构

```python
{
    "success": True,  # 整体是否成功
    "message": "Publishing completed: 5 succeeded, 2 failed",
    "data": {
        "total_count": 7,      # 总数
        "success_count": 5,    # 成功数
        "failed_count": 2,     # 失败数
        "skipped_count": 0,    # 跳过数
        "results": [           # 详细结果列表
            {
                "pool_id": 1,
                "content_id": 101,
                "status": "published",
                "log_id": 100,
                "media_id": "media_id_123"
            },
            {
                "pool_id": 2,
                "content_id": 102,
                "status": "failed",
                "error": "Publish failed"
            }
        ]
    },
    "duration": 12.34,  # 执行时长（秒）
    "metadata": {
        "task_id": 1,
        "average_time_per_item": 1.76
    }
}
```

### 状态说明

- **published**: 发布成功
- **failed**: 发布失败
- **error**: 处理异常

## 六、常见使用场景

### 场景1：定时自动发布

```python
# 每10分钟检查并发布到期内容
task = ScheduledTask(
    name="定时发布",
    task_type="publishing",
    schedule_type="interval",
    interval_seconds=600,  # 10分钟
    params={},
    enabled=True
)
```

### 场景2：高峰期延迟发布

```python
from datetime import time

# 在非高峰期发布（如凌晨2点）
scheduled_time = datetime.utcnow().replace(
    hour=2,
    minute=0,
    second=0,
    microsecond=0
)

entry = publish_pool_service.add_to_pool(
    db,
    content_id=123,
    priority=5,
    scheduled_at=scheduled_time
)
```

### 场景3：紧急内容优先发布

```python
# 设置优先级为1（最高优先级）
entry = publish_pool_service.add_to_pool(
    db,
    content_id=123,
    priority=1,
    scheduled_at=datetime.utcnow()  # 立即发布
)
```

### 场景4：批量发布

```python
# 批量添加内容到发布池
content_ids = [101, 102, 103, 104, 105]

for content_id in content_ids:
    publish_pool_service.add_to_pool(
        db,
        content_id=content_id,
        priority=5,
        scheduled_at=datetime.utcnow() + timedelta(minutes=5)
    )
```

## 七、故障排查

### 问题1：内容没有被发布

**检查项**：
1. 内容是否在发布池中？
   ```python
   entries = db.query(PublishPool).filter(
       PublishPool.content_id == content_id
   ).all()
   ```

2. 状态是否为 "pending"？
   ```python
   entry.status == "pending"
   ```

3. scheduled_at 是否已过期？
   ```python
   entry.scheduled_at <= datetime.utcnow()
   ```

4. 优先级是否过高（数字过大）？
   ```python
   entry.priority  # 1-10，数字越小优先级越高
   ```

### 问题2：发布失败后没有重试

**检查项**：
1. retry_count 是否达到 max_retries？
   ```python
   entry.retry_count < entry.max_retries
   ```

2. 状态是否被重置为 "pending"？
   ```python
   entry.status == "pending"  # 应该在重试后重置
   ```

### 问题3：执行结果显示成功但内容未发布

**检查项**：
1. 查看 results 详细信息
2. 检查发布日志 (PublishLog)
3. 查看系统日志

```python
# 查看发布日志
from app.models.publisher import PublishLog

log = db.query(PublishLog).filter(
    PublishLog.content_id == content_id
).first()

print(f"状态: {log.status}")
print(f"错误: {log.error_message}")
print(f"媒体ID: {log.media_id}")
```

## 八、最佳实践

### 1. 优先级设置
- **1-3**: 紧急内容（立即发布）
- **4-6**: 普通内容（正常发布）
- **7-10**: 非紧急内容（可延迟）

### 2. 发布间隔
- **高频率**: 5-10分钟（适用于频繁更新的账号）
- **中频率**: 15-30分钟（适用于常规账号）
- **低频率**: 1小时以上（适用于不活跃账号）

### 3. 重试策略
- **max_retries**: 建议设置为 3 次
- **重试间隔**: 通过调度任务的 interval 控制

### 4. 监控建议
- 定期检查发布池状态
- 监控失败率
- 设置告警阈值

## 九、相关文件

### 核心文件
- `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/executors/publishing_executor.py`
- `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/publish_pool_service.py`
- `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/modules/publisher/services.py`

### 模型文件
- `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/models/publisher.py`

### 测试文件
- `/Users/Oychao/Documents/Projects/content-hub/src/backend/tests/test_publishing_executor.py`
- `/Users/Oychao/Documents/Projects/content-hub/src/backend/tests/verify_publishing_executor.py`

## 十、获取帮助

- 查看详细实现文档：`docs/phase3-publishing-executor-implementation.md`
- 运行验证脚本：`python tests/verify_publishing_executor.py`
- 运行单元测试：`pytest tests/test_publishing_executor.py -v`
