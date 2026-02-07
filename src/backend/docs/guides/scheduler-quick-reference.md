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

### 3. workflow

**用途**: 编排多个执行步骤，支持步骤间数据传递

**参数**:
```python
task_params = {
    "steps": [
        {
            "type": "content_generation",
            "params": {
                "account_id": 49,
                "topic": "新能源汽车行业最新动态"
            }
        },
        {
            "type": "approve",
            "params": {
                "content_id": "${content_id}"  # 引用前面步骤的返回值
            }
        },
        {
            "type": "add_to_pool",
            "params": {
                "content_id": "${content_id}",
                "priority": 5
            }
        }
    ]
}
```

**执行器**: `WorkflowExecutor`

**特性**:
- 支持变量引用（`${variable_name}`）
- 步骤间上下文传递
- 任何步骤失败则中断工作流
- 详细记录每个步骤的执行结果

**详细文档**: [工作流执行器使用指南](./workflow-executor-guide.md)

### 4. add_to_pool

**用途**: 将内容加入发布池，支持自动审核

**参数**:
```python
task_params = {
    "content_id": 123,           # 必需：内容ID
    "priority": 5,               # 可选：优先级（1-10），默认5
    "scheduled_at": "2024-02-07 10:00:00",  # 可选：计划发布时间
    "auto_approve": True         # 可选：是否自动审核，默认False
}
```

**执行器**: `AddToPoolExecutor`

### 5. approve

**用途**: 审核内容，将审核状态设为 "approved"

**参数**:
```python
task_params = {
    "content_id": 123,              # 必需：内容ID
    "review_status": "approved",    # 可选：审核状态，默认"approved"
    "review_note": "内容审核通过"    # 可选：审核备注
}
```

**执行器**: `ApproveExecutor`

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

## 工作流执行器快速入门

### 基本概念

工作流执行器允许您将多个任务步骤组合成一个自动化流程：

1. **步骤（Steps）**: 按顺序执行的独立任务
2. **上下文（Context）**: 在步骤间传递的数据
3. **变量引用**: 使用 `${variable_name}` 引用上下文中的数据

### 快速示例

创建一个每天早上7点自动生成、审核并发布内容的工作流：

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()

task = ScheduledTask(
    name="每日自动内容发布",
    description="每天早上7点自动生成、审核、加入发布池",
    task_type="workflow",
    cron_expression="0 7 * * *",
    is_active=True,
    params={
        "steps": [
            {
                "type": "content_generation",
                "params": {
                    "account_id": 49,
                    "topic": "新能源汽车行业最新动态分析"
                }
            },
            {
                "type": "approve",
                "params": {
                    "content_id": "${content_id}"  # 引用第一步返回的content_id
                }
            },
            {
                "type": "add_to_pool",
                "params": {
                    "content_id": "${content_id}",
                    "priority": 5
                }
            }
        ]
    }
)

db.add(task)
db.commit()
db.refresh(task)
print(f"工作流任务创建成功，ID: {task.id}")
db.close()
```

### 变量引用说明

- 第一步（content_generation）返回 `{"content_id": 123, "title": "..."}`
- 第二步（approve）使用 `${content_id}` 会被替换为 `123`
- 第三步（add_to_pool）同样可以使用 `${content_id}` 或 `${title}`

### 常见工作流模式

#### 模式 1: 生成 → 发布

```python
{
    "steps": [
        {"type": "content_generation", "params": {...}},
        {"type": "add_to_pool", "params": {"content_id": "${content_id}"}}
    ]
}
```

#### 模式 2: 生成 → 审核 → 发布

```python
{
    "steps": [
        {"type": "content_generation", "params": {...}},
        {"type": "approve", "params": {"content_id": "${content_id}"}},
        {"type": "add_to_pool", "params": {"content_id": "${content_id}"}}
    ]
}
```

#### 模式 3: 批量生成

```python
{
    "steps": [
        {"type": "content_generation", "params": {"topic": "主题1"}},
        {"type": "add_to_pool", "params": {"content_id": "${content_id}"}},
        {"type": "content_generation", "params": {"topic": "主题2"}},
        {"type": "add_to_pool", "params": {"content_id": "${content_id}"}}
    ]
}
```

### CLI 创建工作流任务

```bash
python -m cli.main scheduler create \
  --name "每日自动内容发布" \
  --type "workflow" \
  --cron "0 7 * * *" \
  --enabled \
  --params '{
    "steps": [
      {"type": "content_generation", "params": {"account_id": 49, "topic": "..."}},
      {"type": "approve", "params": {"content_id": "${content_id}"}},
      {"type": "add_to_pool", "params": {"content_id": "${content_id}", "priority": 5}}
    ]
  }'
```

**详细文档**: [工作流执行器使用指南](./workflow-executor-guide.md)

---

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

- [工作流执行器使用指南](./workflow-executor-guide.md) - 详细的工作流执行器文档
- [定时任务系统设计](../design/scheduler-system-design.md) - 系统架构和接口设计
- [完整实现报告](../archive/sessions/phase4-5-6-task-loading-and-scheduling-implementation.md)
- [阶段总结报告](../archive/sessions/phase4-5-6-summary.md)
- [定时任务实施总结](../development/SCHEDULER-TASK-IMPLEMENTATION-SUMMARY.md)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)
- [项目开发指南](../CLAUDE.md)

## 生产环境案例

### "车界显眼包"每日自动发布任务

**实施状态**: ✅ 已部署并运行中（自 2026-02-08 起）

**任务详情**:
- 任务ID: 1
- 任务名称: "车界显眼包-每日7点自动发布"
- 账号ID: 49
- 执行时间: 每天早上 07:00
- 工作流: 生成内容 → 自动审核 → 加入发布池

**完整配置示例**:

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()

task = ScheduledTask(
    name="车界显眼包-每日7点自动发布",
    description="每天早上7点自动生成内容、审核、加入发布池",
    task_type="workflow",
    cron_expression="0 7 * * *",
    is_active=True,
    params={
        "steps": [
            {
                "type": "content_generation",
                "params": {
                    "account_id": 49,
                    "topic": "新能源汽车行业最新动态分析",
                    "target_audience": "汽车爱好者和潜在购车者",
                    "tone": "专业但通俗易懂"
                }
            },
            {
                "type": "approve",
                "params": {
                    "content_id": "${content_id}"
                }
            },
            {
                "type": "add_to_pool",
                "params": {
                    "content_id": "${content_id}",
                    "priority": 5,
                    "auto_approve": True
                }
            }
        ]
    }
)

db.add(task)
db.commit()
db.refresh(task)
print(f"任务创建成功，ID: {task.id}")
db.close()
```

**验证脚本**:

```python
#!/usr/bin/env python3
"""验证车界显眼包任务"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.scheduler_service import scheduler_service
from app.db.database import SessionLocal

# 注册执行器
from app.services.executors import (
    ContentGenerationExecutor,
    PublishingExecutor,
    WorkflowExecutor,
    AddToPoolExecutor,
    ApproveExecutor
)

executors = [
    ContentGenerationExecutor(),
    PublishingExecutor(),
    WorkflowExecutor(),
    AddToPoolExecutor(),
    ApproveExecutor()
]

for executor in executors:
    scheduler_service.register_executor(executor)

# 启动调度器
scheduler_service.start()

# 加载任务
db = SessionLocal()
loaded_count = scheduler_service.load_tasks_from_db(db)
print(f"✅ 成功加载 {loaded_count} 个任务")

# 查看任务详情
task = db.query(ScheduledTask).filter(
    ScheduledTask.name == "车界显眼包-每日7点自动发布"
).first()

if task:
    print(f"✅ 任务状态: {'启用' if task.is_active else '禁用'}")
    print(f"✅ 下次运行: {task.next_run_time}")

    # 验证参数
    workflow_executor = scheduler_service.get_executor("workflow")
    if workflow_executor:
        is_valid = workflow_executor.validate_params(task.params)
        print(f"✅ 参数验证: {'通过' if is_valid else '失败'}")

db.close()
```

**运行验证**:
```bash
cd src/backend
PYTHONPATH=. python verify_with_service.py
```

**预期输出**:
```
======================================================================
验证工作流任务（包含服务启动）
======================================================================

🔧 注册执行器...
  ✅ 已注册执行器: ['content_generation', 'publishing', 'workflow', 'add_to_pool', 'approve']

⏰ 启动调度器...
  ✅ 调度器已启动 (运行状态: True)

📋 从数据库加载任务...
  ✅ 成功加载 1 个任务

🔍 查询任务详情...
  ✅ 找到任务:
     ID: 1
     名称: 车界显眼包-每日7点自动发布
     类型: workflow
     Cron: 0 7 * * *
     状态: 启用

🔍 验证工作流参数...
  ✅ 工作流参数验证通过

======================================================================
验证完成！
======================================================================
```

**相关文件**:
- 任务创建脚本: `src/backend/create_chejie_task.py`
- 验证脚本: `src/backend/verify_with_service.py`
- 实施报告: `src/backend/CHEJIE_TASK_REPORT.md`
