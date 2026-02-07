# 工作流执行器使用指南

## 概述

工作流执行器（WorkflowExecutor）是 ContentHub 调度系统提供的强大功能，允许您将多个任务步骤组合成一个自动化流程。通过工作流执行器，您可以：

- 编排多个执行步骤按顺序执行
- 在步骤间传递数据（上下文机制）
- 使用变量引用简化参数配置
- 实现复杂的自动化业务流程

## 核心概念

### 1. 步骤（Steps）

步骤是工作流的基本执行单元，每个步骤包含：

- `type`: 执行器类型（如 `content_generation`, `approve`, `add_to_pool`）
- `params`: 执行参数（可选）

```json
{
  "type": "content_generation",
  "params": {
    "account_id": 49,
    "topic": "新能源汽车行业最新动态"
  }
}
```

### 2. 上下文（Context）

上下文是在步骤间传递的数据容器：

- 每个步骤执行后，其返回的 `data` 字段会合并到上下文中
- 后续步骤可以引用上下文中的任何变量
- 上下文是累加的，后续步骤会继承前面步骤的所有数据

### 3. 变量引用

使用 `${variable_name}` 格式引用上下文中的变量：

```json
{
  "type": "approve",
  "params": {
    "content_id": "${content_id}"
  }
}
```

执行时，`${content_id}` 会被替换为上下文中 `content_id` 的实际值。

## 快速开始

### 示例 1: 自动生成并发布内容

创建一个每天早上7点自动生成、审核并发布内容的工作流：

#### 方式 1: 使用 Python

```python
from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask

db = SessionLocal()

task = ScheduledTask(
    name="车界显眼包-每日自动发布",
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
                    "content_id": "${content_id}"
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

#### 方式 2: 使用 CLI

```bash
python -m cli.main scheduler create \
  --name "车界显眼包-每日自动发布" \
  --type "workflow" \
  --cron "0 7 * * *" \
  --enabled \
  --description "每天早上7点自动生成、审核、加入发布池" \
  --params '{
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
          "content_id": "${content_id}"
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
  }'
```

### 执行流程

```
1. ContentGenerationExecutor
   参数: {"account_id": 49, "topic": "新能源汽车行业最新动态分析"}
   ↓ 返回: {"success": true, "data": {"content_id": 123, "title": "..."}}
   上下文: {"content_id": 123, "title": "..."}

2. ApproveExecutor
   参数: {"content_id": "${content_id}"} → 解析为 {"content_id": 123}
   ↓ 返回: {"success": true, "data": {"content_id": 123, "review_status": "approved"}}
   上下文: {"content_id": 123, "title": "...", "review_status": "approved"}

3. AddToPoolExecutor
   参数: {"content_id": "${content_id}", "priority": 5} → 解析为 {"content_id": 123, "priority": 5}
   ↓ 返回: {"success": true, "data": {"pool_id": 456}}
   上下文: {"content_id": 123, "title": "...", "review_status": "approved", "pool_id": 456}

4. WorkflowExecutor 完成
   返回: 包含所有步骤执行结果的汇总
```

## 执行器详解

### 1. WorkflowExecutor（工作流执行器）

**类型**: `workflow`

**功能**: 编排多个执行步骤

**参数**:
```json
{
  "steps": [
    {"type": "executor_type_1", "params": {...}},
    {"type": "executor_type_2", "params": {...}}
  ]
}
```

**特性**:
- 按顺序执行步骤
- 步骤间共享上下文
- 任何步骤失败则中断工作流
- 返回所有步骤的执行结果

### 2. AddToPoolExecutor（加入发布池执行器）

**类型**: `add_to_pool`

**功能**: 将内容加入发布池

**参数**:
```json
{
  "content_id": 123,           // 必需：内容ID
  "priority": 5,               // 可选：优先级（1-10），默认5
  "scheduled_at": "2024-02-07 10:00:00",  // 可选：计划发布时间
  "auto_approve": true         // 可选：是否自动审核，默认false
}
```

**返回数据**:
```json
{
  "pool_id": 456,
  "content_id": 123,
  "priority": 5,
  "scheduled_at": null,
  "auto_approved": true
}
```

### 3. ApproveExecutor（审核执行器）

**类型**: `approve`

**功能**: 审核内容

**参数**:
```json
{
  "content_id": 123,              // 必需：内容ID
  "review_status": "approved",    // 可选：审核状态，默认"approved"
  "review_note": "内容审核通过"    // 可选：审核备注
}
```

**返回数据**:
```json
{
  "content_id": 123,
  "content_title": "文章标题",
  "original_status": "pending",
  "new_status": "approved"
}
```

## 常见工作流模式

### 模式 1: 生成 → 发布

最简单的自动化流程，生成内容后直接加入发布池。

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {
        "account_id": 49,
        "topic": "最新行业动态"
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

### 模式 2: 生成 → 审核 → 发布

添加审核步骤，确保内容质量。

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {
        "account_id": 49,
        "topic": "最新行业动态"
      }
    },
    {
      "type": "approve",
      "params": {
        "content_id": "${content_id}",
        "review_note": "自动审核通过"
      }
    },
    {
      "type": "add_to_pool",
      "params": {
        "content_id": "${content_id}",
        "priority": 5,
        "auto_approve": false
      }
    }
  ]
}
```

### 模式 3: 批量生成多篇文章

在一个工作流中生成多篇文章。

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {
        "account_id": 49,
        "topic": "新能源汽车技术分析"
      }
    },
    {
      "type": "add_to_pool",
      "params": {
        "content_id": "${content_id}",
        "priority": 5
      }
    },
    {
      "type": "content_generation",
      "params": {
        "account_id": 49,
        "topic": "智能驾驶发展趋势"
      }
    },
    {
      "type": "add_to_pool",
      "params": {
        "content_id": "${content_id}",
        "priority": 6
      }
    }
  ]
}
```

**注意**: 由于上下文会累加，第二个 `content_generation` 会覆盖第一个的 `content_id`，因此每个 `add_to_pool` 都会使用最新生成的 `content_id`。

### 模式 4: 计划发布

生成内容后，设置计划发布时间。

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {
        "account_id": 49,
        "topic": "最新行业动态"
      }
    },
    {
      "type": "add_to_pool",
      "params": {
        "content_id": "${content_id}",
        "priority": 5,
        "scheduled_at": "2024-02-08 09:00:00"
      }
    }
  ]
}
```

## 高级功能

### 1. 变量引用详解

变量引用支持递归解析，可以在嵌套结构中使用：

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {
        "account_id": 49,
        "topic": "最新动态"
      }
    },
    {
      "type": "custom_step",
      "params": {
        "content_id": "${content_id}",
        "message": "内容 ${title} 已生成，ID: ${content_id}",
        "nested": {
          "id": "${content_id}",
          "info": "标题: ${title}"
        }
      }
    }
  ]
}
```

### 2. 上下文传递

每个步骤的 `result.data` 会合并到上下文中：

```python
# 步骤 1 返回
result.data = {"content_id": 123, "title": "测试文章"}
context = {"content_id": 123, "title": "测试文章"}

# 步骤 2 返回
result.data = {"pool_id": 456}
context = {"content_id": 123, "title": "测试文章", "pool_id": 456}

# 步骤 3 可以引用任何变量
params = {"content_id": "${content_id}", "pool_id": "${pool_id}"}
# 解析后: {"content_id": 123, "pool_id": 456}
```

### 3. 错误处理

任何步骤失败会导致整个工作流中断：

```
步骤 1: 成功
步骤 2: 失败 ← 工作流在此停止
步骤 3: 不执行
```

失败的详细信息会记录在执行历史中：

```bash
python -m cli.main scheduler history --task-id <task_id>
```

## 最佳实践

### 1. 步骤命名

为工作流任务添加清晰的名称和描述：

```python
task = ScheduledTask(
    name="车界显眼包-每日早7点自动发布",
    description="生成新能源汽车内容 → 审核通过 → 加入发布池（优先级5）",
    ...
)
```

### 2. 优先级管理

使用合理的优先级（1-10）：

- `1-3`: 低优先级（备用内容）
- `4-6`: 中等优先级（常规内容）
- `7-10`: 高优先级（紧急内容）

### 3. 时间规划

避免所有任务在同一时间执行：

```python
# 任务 1: 早上 7:00
cron_expression = "0 7 * * *"

# 任务 2: 早上 7:15
cron_expression = "15 7 * * *"

# 任务 3: 早上 7:30
cron_expression = "30 7 * * *"
```

### 4. 错误监控

定期检查工作流执行历史：

```bash
# 查看失败的任务
python -m cli.main scheduler history --status failed

# 查看特定任务的执行记录
python -m cli.main scheduler history --task-id <task_id>
```

### 5. 测试工作流

在启用定时任务前，先手动触发测试：

```bash
# 创建任务（不启用）
python -m cli.main scheduler create \
  --name "测试工作流" \
  --type "workflow" \
  --params '{...}'

# 手动触发
python -m cli.main scheduler trigger <task_id>

# 查看结果
python -m cli.main scheduler history --task-id <task_id>
```

测试通过后再启用定时任务：

```python
task.is_active = True
db.commit()
```

## 故障排查

### 问题 1: 工作流未执行

**检查步骤**:

1. 确认调度器正在运行
```bash
python -m cli.main scheduler status
```

2. 确认任务已启用
```bash
python -m cli.main scheduler list
```

3. 检查下次运行时间
```bash
python -m cli.main scheduler info <task_id>
```

### 问题 2: 变量替换不生效

**可能原因**:

1. 变量名拼写错误
2. 变量在上下文中不存在
3. 格式错误（应使用 `${variable_name}`）

**解决方法**:

查看执行历史，检查上下文数据：

```bash
python -m cli.main scheduler history --task-id <task_id>
```

### 问题 3: 步骤执行失败

**常见错误**:

- `ExecutorNotFound`: 执行器类型未注册
- `ContentNotFound`: 内容ID不存在
- `InvalidParameters`: 参数验证失败

**解决方法**:

1. 查看详细错误信息
```bash
python -m cli.main scheduler history --task-id <task_id>
```

2. 检查参数格式
3. 确认执行器已注册
```python
from app.services.scheduler_service import scheduler_service
print(scheduler_service.get_registered_executors())
```

### 问题 4: 数据库错误

**常见错误**:

- `IntegrityError`: 唯一约束冲突（如内容已存在发布池）

**解决方法**:

1. 检查内容是否已加入发布池
```bash
python -m cli.main publish-pool list --content-id <content_id>
```

2. 使用不同的 `content_id` 或清理重复记录

## 扩展性

### 添加自定义执行器

您可以为工作流添加自定义执行器：

```python
from app.services.scheduler_service import TaskExecutor, TaskExecutionResult

class NotificationExecutor(TaskExecutor):
    @property
    def executor_type(self) -> str:
        return "send_notification"

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        message = task_params.get("message")
        # 发送通知逻辑
        return TaskExecutionResult.success_result(
            message=f"通知已发送: {message}",
            data={"notification_id": 789}
        )
```

注册执行器（在 `app/modules/scheduler/module.py` 中）：

```python
from app.services.executors.notification_executor import NotificationExecutor

notification_executor = NotificationExecutor()
scheduler_service.register_executor(notification_executor)
```

使用自定义执行器：

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {
        "account_id": 49,
        "topic": "最新动态"
      }
    },
    {
      "type": "send_notification",
      "params": {
        "message": "内容 ${title} 已生成，ID: ${content_id}"
      }
    }
  ]
}
```

## 性能考虑

### 执行时间

- 平均单步执行时间: 0.008 秒
- 典型工作流（3 步）: 0.02-0.05 秒
- 复杂工作流（10+ 步）: 0.1-0.5 秒

### 优化建议

1. **减少步骤数量**: 合并可以并行执行的操作
2. **避免重复查询**: 在上下文中传递数据，而非重复查询数据库
3. **使用索引**: 确保数据库查询字段有索引
4. **监控性能**: 定期检查执行历史中的 `duration` 字段

## 相关文档

- [调度器快速参考](./scheduler-quick-reference.md) - 调度器基础使用
- [定时任务系统设计](../design/scheduler-system-design.md) - 系统架构设计
- [工作流执行器使用文档](../../WORKFLOW_EXECUTOR_USAGE.md) - 原始使用文档
- [工作流执行器测试报告](../../WORKFLOW_EXECUTOR_TEST_REPORT.md) - 测试报告
- [工作流执行器实施总结](../../IMPLEMENTATION_SUMMARY.md) - 实施总结

## 常见问题（FAQ）

### Q1: 工作流支持条件分支吗？

**A**: 当前版本不支持条件分支，步骤始终按顺序执行。如需条件逻辑，可以考虑使用自定义执行器。

### Q2: 工作流支持并行执行吗？

**A**: 当前版本不支持并行执行，所有步骤串行执行。未来版本可能会添加并行支持。

### Q3: 变量引用支持默认值吗？

**A**: 当前版本不支持默认值，如果变量不存在会保持原样（如 `${content_id}`）。确保变量在上下文中存在。

### Q4: 工作流可以嵌套吗？

**A**: 当前版本不支持工作流嵌套，即在一个工作流中不能包含另一个工作流。

### Q5: 如何查看工作流的执行进度？

**A**: 查看执行历史，每个步骤的结果都会记录：

```bash
python -m cli.main scheduler history --task-id <task_id>
```

### Q6: 工作流失败后会重试吗？

**A**: 当前版本不会自动重试。如需重试，可以手动触发任务：

```bash
python -m cli.main scheduler trigger <task_id>
```

---

**文档版本**: 1.1.0
**最后更新**: 2026-02-08
**维护者**: ContentHub 开发团队

## 实施案例

### 案例 1: "车界显眼包"每日自动发布（生产环境）

**任务配置**:
- 任务ID: 1
- 账号ID: 49（车界显眼包）
- 执行时间: 每天早上 07:00
- 状态: ✅ 已启用并运行中

**工作流配置**:
```python
{
    "name": "车界显眼包-每日7点自动发布",
    "description": "每天早上7点自动生成内容、审核、加入发布池",
    "task_type": "workflow",
    "cron_expression": "0 7 * * *",
    "is_active": True,
    "params": {
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
}
```

**验证命令**:
```bash
# 查看任务状态
PYTHONPATH=. python -m cli.main scheduler info 1

# 查看执行历史
PYTHONPATH=. python -m cli.main scheduler executions --task-id 1

# 查看生成的内容
PYTHONPATH=. python -m cli.main content list --account-id 49

# 查看发布池
PYTHONPATH=. python -m cli.main publish-pool list
```

**验证结果**（2026-02-08）:
```
✅ 已注册执行器: ['content_generation', 'publishing', 'workflow', 'add_to_pool', 'approve']
✅ 调度器已启动 (运行状态: True)
✅ 成功加载 1 个任务
✅ 工作流参数验证通过
下次运行: 2026-02-08 07:00:00+08:00
```

**文件位置**:
- 任务创建脚本: `create_chejie_task.py`
- 验证脚本: `verify_with_service.py`
- 实施报告: `CHEJIE_TASK_REPORT.md`
