# 异步内容生成执行器 - 快速参考

## 📋 概述

`AsyncContentGenerationExecutor` 是 ContentHub 调度系统的任务执行器，负责批量提交异步内容生成任务。

**执行器类型**: `async_content_generation`

## 🚀 快速开始

### 1. 创建定时任务

#### 通过 API

```bash
curl -X POST http://localhost:18010/api/v1/scheduler/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "每日内容生成",
    "description": "每天早上8点生成技术内容",
    "task_type": "async_content_generation",
    "cron_expression": "0 8 * * *",
    "params": {
      "account_ids": [49, 50, 51],
      "count_per_account": 3,
      "category": "技术",
      "auto_approve": false,
      "priority": 8
    },
    "is_active": true
  }'
```

#### 通过 Python 脚本

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()
task = ScheduledTask(
    name='每日内容生成',
    task_type='async_content_generation',
    cron_expression='0 8 * * *',
    params={
        'account_ids': [49, 50],
        'count_per_account': 2,
        'category': '技术'
    },
    is_active=True
)
db.add(task)
db.commit()
```

### 2. 手动触发任务

```bash
curl -X POST http://localhost:18010/api/v1/scheduler/tasks/18/trigger
```

### 3. 查看执行历史

```bash
curl http://localhost:18010/api/v1/scheduler/executions
```

## 📝 任务参数

### 必需参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `account_ids` | `List[int]` | 账号ID列表 | `[49, 50, 51]` |
| `count_per_account` | `int` | 每个账号生成数量 | `3` |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `category` | `str` | `None` | 内容板块（技术/产品/运营/营销） |
| `auto_approve` | `bool` | `True` | 是否自动审核通过 |
| `priority` | `int` | `5` | 优先级（1-10） |
| `topics` | `List[Dict]` | `None` | 自定义选题列表 |

## 📊 执行结果

```json
{
  "success": true,
  "message": "Successfully submitted 6 async tasks for 3 accounts",
  "data": {
    "total_submitted": 6,
    "total_failed": 0,
    "tasks": [
      {
        "task_id": "task-abc123",
        "account_id": 49,
        "account_name": "车界显眼包",
        "topic": "车界显眼包 - 技术解析 1",
        "category": "技术"
      }
    ],
    "errors": [],
    "account_stats": {
      "49": {
        "account_name": "车界显眼包",
        "success": 2,
        "failed": 0,
        "total": 2
      }
    }
  },
  "duration": 0.05
}
```

## ⏰ Cron 表达式

| 表达式 | 说明 |
|--------|------|
| `0 8 * * *` | 每天 8:00 |
| `0 */2 * * *` | 每 2 小时 |
| `0 0 * * 1` | 每周一 0:00 |
| `0 8 * * 1-5` | 周一到周五 8:00 |
| `0 8,12,18 * * *` | 每天 8:00, 12:00, 18:00 |
| `0 0 1 * *` | 每月 1 号 0:00 |

## 🎯 使用场景

### 场景 1: 每日批量生成

```python
params = {
    'account_ids': [49, 50, 51],
    'count_per_account': 3,
    'category': '技术',
    'cron_expression': '0 8 * * *'  # 每天早上8点
}
```

### 场景 2: 高频更新

```python
params = {
    'account_ids': [49],
    'count_per_account': 1,
    'interval': 2,
    'interval_unit': 'hours'  # 每2小时
}
```

### 场景 3: 自定义选题

```python
params = {
    'account_ids': [49],
    'topics': [
        {
            'topic': 'AI 技术未来趋势',
            'keywords': 'AI,人工智能',
            'requirements': '深度分析',
            'tone': '专业'
        }
    ]
}
```

## 🔧 高级配置

### 使用间隔调度

```python
task = ScheduledTask(
    name='每小时内容生成',
    task_type='async_content_generation',
    cron_expression=None,  # 不使用 cron
    interval=1,             # 间隔值
    interval_unit='hours',  # 间隔单位
    params={...}
)
```

### 设置优先级

优先级范围：1-10（10 最高）

```python
params = {
    'account_ids': [49],
    'count_per_account': 1,
    'priority': 10  # 最高优先级
}
```

### 自动审核开关

```python
params = {
    'account_ids': [49],
    'auto_approve': True  # 生成后自动审核通过
}
```

## 📈 监控和日志

### 查看调度器状态

```bash
curl http://localhost:18010/api/v1/scheduler/status
```

### 查看已注册的执行器

```python
from app.services.scheduler_service import scheduler_service

executors = scheduler_service.get_registered_executors()
print(executors)
# {'async_content_generation': {...}, ...}
```

### 日志位置

- **日志目录**: `logs/`
- **调度器日志**: `logs/scheduler.log`
- **执行器日志**: `logs/async_content_executor.log`

## ⚠️ 注意事项

### Redis 依赖

异步模式需要 Redis 支持。如果 Redis 不可用：

1. **测试**: 使用 Mock 测试（见 `test_async_executor_mock.py`）
2. **生产**: 配置 Redis 或改用同步模式

### 错误处理

- 单个任务失败不会影响其他任务
- 详细的错误信息在返回结果的 `errors` 字段中
- 所有错误都会记录到日志

### 性能考虑

- 批量任务数量建议不超过 100 个
- 大批量任务建议分批提交
- 注意观察 Redis 和数据库的性能

## 🧪 测试

### 运行测试

```bash
# Mock 测试（不需要 Redis）
python test_async_executor_mock.py

# 完整测试（需要 Redis）
python test_async_scheduler.py
```

### 创建测试任务

```bash
python create_async_generation_task.py
```

## 📚 相关文档

- [调度器系统设计](../../docs/architecture/SCHEDULER-ARCHITECTURE.md)
- [阶段 4 完成报告](./PHASE4_COMPLETION_REPORT.md)
- [CLI 命令参考](../../docs/references/CLI-REFERENCE.md)

## 🔗 相关文件

- 执行器实现: `app/services/executors/async_content_generation_executor.py`
- 调度器模块: `app/modules/scheduler/module.py`
- 测试脚本: `test_async_executor_mock.py`
- 示例脚本: `create_async_generation_task.py`
