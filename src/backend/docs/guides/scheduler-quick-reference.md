# 定时任务系统快速参考指南

## 快速开始

### 1. 创建定时任务

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()

# 方法1: 使用Cron表达式（每小时执行）
task = ScheduledTask(
    name="每小时内容生成",
    description="每小时生成一次内容",
    task_type="content_generation",
    cron_expression="0 * * * *",
    is_active=True
)

# 方法2: 使用间隔调度（每10分钟执行）
task = ScheduledTask(
    name="每10分钟发布",
    description="每10分钟检查发布池",
    task_type="publishing",
    interval=10,
    interval_unit="minutes",
    is_active=True
)

db.add(task)
db.commit()
db.refresh(task)
print(f"任务创建成功，ID: {task.id}")
db.close()
```

### 2. 手动加载任务（无需重启应用）

```python
from app.services.scheduler_service import scheduler_service
from app.db.database import SessionLocal

db = SessionLocal()
loaded_count = scheduler_service.load_tasks_from_db(db)
print(f"加载了 {loaded_count} 个任务")
db.close()
```

### 3. 查看调度器状态

```python
from app.services.scheduler_service import scheduler_service

# 检查调度器是否运行
print(f"调度器运行中: {scheduler_service.is_running}")

# 查看已注册的执行器
executors = scheduler_service.get_registered_executors()
print(f"已注册的执行器: {list(executors.keys())}")

# 查看所有已调度的任务
jobs = scheduler_service.get_scheduled_jobs()
for job in jobs:
    print(f"任务: {job['name']}, 下次运行: {job['next_run_time']}")
```

### 4. 查看任务执行记录

```python
from app.db.database import SessionLocal
from app.models.scheduler import TaskExecution
from datetime import datetime, timedelta

db = SessionLocal()

# 查询最近1小时的执行记录
recent = datetime.now() - timedelta(hours=1)
executions = db.query(TaskExecution).filter(
    TaskExecution.start_time >= recent
).order_by(TaskExecution.start_time.desc()).all()

for execution in executions:
    print(f"{execution.start_time} - {execution.status} - {execution.duration}秒")
    if execution.error_message:
        print(f"  错误: {execution.error_message}")

db.close()
```

### 5. 暂停/恢复任务

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask
from app.services.scheduler_service import scheduler_service

db = SessionLocal()

# 暂停任务
task = db.query(ScheduledTask).filter(ScheduledTask.id == 8).first()
if task:
    task.is_active = False
    db.commit()
    scheduler_service.unregister_task(task.id)
    print(f"任务 {task.name} 已暂停")

# 恢复任务
task = db.query(ScheduledTask).filter(ScheduledTask.id == 8).first()
if task:
    task.is_active = True
    db.commit()
    scheduler_service.register_scheduled_task(db, task)
    print(f"任务 {task.name} 已恢复")

db.close()
```

## Cron 表达式参考

```
# ┌───────────── 分钟 (0 - 59)
# │ ┌─────────── 小时 (0 - 23)
# │ │ ┌───────── 日期 (1 - 31)
# │ │ │ ┌─────── 月份 (1 - 12)
# │ │ │ │ ┌───── 星期 (0 - 6，0 = 周日)
# │ │ │ │ │
# * * * * *
```

### 常用示例

```python
# 每分钟
"* * * * *"

# 每5分钟
"*/5 * * * *"

# 每小时
"0 * * * *"

# 每天凌晨
"0 0 * * *"

# 每周一早上9点
"0 9 * * 1"

# 每月1号凌晨
"0 0 1 * *"

# 工作日早上9点（周一到周五）
"0 9 * * 1-5"

# 每天12点和18点
"0 12,18 * * *"
```

## 间隔调度参考

```python
# 支持的单位
interval_unit = "seconds"   # 秒
interval_unit = "minutes"   # 分钟
interval_unit = "hours"     # 小时
interval_unit = "days"      # 天

# 示例
# 每30秒
interval=30, interval_unit="seconds"

# 每5分钟
interval=5, interval_unit="minutes"

# 每2小时
interval=2, interval_unit="hours"

# 每1天
interval=1, interval_unit="days"
```

## 任务类型

### 1. content_generation

**用途**: 自动生成内容

**参数**:
```python
task_params = {
    "account_id": 1,        # 必需：账号ID
    "topic": "AI技术趋势",  # 可选：选题
    "title": "...",         # 可选：标题
    "requirements": "...",  # 可选：创作要求
    "target_audience": "...",  # 可选：目标受众
    "tone": "..."           # 可选：语气风格
}
```

**执行器**: `ContentGenerationExecutor`

### 2. publishing

**用途**: 批量发布内容到发布池

**参数**:
```python
task_params = {}  # 无需参数，自动处理发布池
```

**执行器**: `PublishingExecutor`

## 故障排查

### 任务未执行

1. **检查任务是否启用**
```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()
task = db.query(ScheduledTask).filter(ScheduledTask.id == 8).first()
print(f"任务启用状态: {task.is_active}")
db.close()
```

2. **检查调度器状态**
```python
from app.services.scheduler_service import scheduler_service
print(f"调度器运行中: {scheduler_service.is_running}")
```

3. **检查执行器是否注册**
```python
from app.services.scheduler_service import scheduler_service
executors = scheduler_service.get_registered_executors()
print(f"已注册的执行器: {list(executors.keys())}")
```

4. **检查下次运行时间**
```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()
task = db.query(ScheduledTask).filter(ScheduledTask.id == 8).first()
print(f"下次运行: {task.next_run_time}")
db.close()
```

### 查看失败原因

```python
from app.db.database import SessionLocal
from app.models.scheduler import TaskExecution

db = SessionLocal()
failed_executions = db.query(TaskExecution).filter(
    TaskExecution.status == "failed"
).order_by(TaskExecution.start_time.desc()).limit(5).all()

for execution in failed_executions:
    print(f"任务ID: {execution.task_id}")
    print(f"错误: {execution.error_message}")
    print(f"时间: {execution.start_time}")
    print()

db.close()
```

## 常用命令

### CLI 命令

```bash
# 列出所有定时任务
contenthub scheduler list

# 查看任务详情
contenthub scheduler info <task_id>

# 创建任务（交互式）
contenthub scheduler create

# 暂停任务
contenthub scheduler pause <task_id>

# 恢复任务
contenthub scheduler resume <task_id>

# 查看执行历史
contenthub scheduler history <task_id>

# 手动触发任务
contenthub scheduler trigger <task_id>

# 查看调度器状态
contenthub scheduler status
```

### Python API

```python
# 查询所有启用的任务
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()
active_tasks = db.query(ScheduledTask).filter(
    ScheduledTask.is_active == True
).all()

for task in active_tasks:
    print(f"{task.name} - {task.task_type}")
db.close()
```

## 配置文件

**环境变量** (`.env`):

```bash
# 调度器配置
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Shanghai
```

## 注意事项

1. **时区**: 确保使用正确的时区（默认：Asia/Shanghai）
2. **Cron表达式**: 使用标准的5段式cron表达式
3. **任务参数**: 确保任务参数正确，特别是 content_generation 需要 account_id
4. **执行器注册**: 新的任务类型需要先注册对应的执行器
5. **数据库会话**: 任务执行时会创建独立的数据库会话，无需担心会话冲突

## 扩展：自定义任务类型

### 1. 创建执行器

```python
from app.services.scheduler_service import TaskExecutor, TaskExecutionResult

class MyCustomExecutor(TaskExecutor):
    @property
    def executor_type(self) -> str:
        return "my_custom_type"

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        # 实现任务逻辑
        return TaskExecutionResult.success_result(
            message="Task completed"
        )
```

### 2. 注册执行器

在 `app/modules/scheduler/module.py` 中添加：

```python
from app.services.executors.my_custom_executor import MyCustomExecutor

def startup(app):
    # 注册自定义执行器
    my_executor = MyCustomExecutor()
    scheduler_service.register_executor(my_executor)
```

### 3. 创建任务

```python
from app.models.scheduler import ScheduledTask

task = ScheduledTask(
    name="我的自定义任务",
    task_type="my_custom_type",  # 与 executor_type 匹配
    cron_expression="0 * * * *",
    is_active=True
)
```

## 性能建议

1. **避免任务过于频繁**: 最小间隔建议不要小于1分钟
2. **控制并发任务数**: 如果有大量任务，考虑使用间隔错开
3. **设置合理的超时**: 长时间运行的任务应该有超时机制
4. **监控任务执行**: 定期检查执行日志和成功率

## 相关文档

- [完整实现报告](../archive/sessions/phase4-5-6-task-loading-and-scheduling-implementation.md)
- [阶段总结报告](../archive/sessions/phase4-5-6-summary.md)
- [定时任务实施总结](../development/SCHEDULER-TASK-IMPLEMENTATION-SUMMARY.md)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)
- [项目开发指南](../CLAUDE.md)
