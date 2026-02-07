# 工作流执行器使用指南

## 概述

ContentHub 现在支持三种新的任务执行器：

1. **WorkflowExecutor** - 工作流执行器，可编排多个步骤
2. **AddToPoolExecutor** - 加入发布池执行器
3. **ApproveExecutor** - 审核执行器

## 执行器详情

### 1. WorkflowExecutor (workflow)

**功能**: 按顺序执行多个步骤，支持变量替换

**参数格式**:
```json
{
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
        "content_id": "${content_id}"
      }
    },
    {
      "type": "add_to_pool",
      "params": {
        "content_id": "${content_id}",
        "priority": 5,
        "auto_approve": true
      }
    }
  ]
}
```

**变量替换**: 支持 `${variable_name}` 格式引用之前步骤返回的数据

---

### 2. AddToPoolExecutor (add_to_pool)

**功能**: 将内容加入发布池，支持自动审核

**必需参数**:
- `content_id` (int) - 内容ID

**可选参数**:
- `priority` (int, 1-10) - 优先级，默认 5
- `scheduled_at` (datetime/string) - 计划发布时间，默认当前时间
- `auto_approve` (bool) - 是否自动审核，默认 false

**示例**:
```json
{
  "content_id": 123,
  "priority": 5,
  "auto_approve": true
}
```

---

### 3. ApproveExecutor (approve)

**功能**: 审核内容，将审核状态设为 "approved"

**必需参数**:
- `content_id` (int) - 内容ID

**可选参数**:
- `review_status` (string) - 审核状态，默认 "approved"
- `review_note` (string) - 审核备注

**示例**:
```json
{
  "content_id": 123
}
```

## 使用方式

### 方式 1: 通过 CLI 创建工作流任务

```bash
cd src/backend

# 创建工作流任务
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
          "priority": 5,
          "auto_approve": false
        }
      }
    ]
  }'
```

### 方式 2: 通过 Python 脚本创建

```python
# scripts/create_workflow_task.py
from app.db.sql_db import get_session_local
from app.models.scheduler import ScheduledTask

task = ScheduledTask(
    name="车界显眼包-每日自动发布",
    task_type="workflow",
    description="每天早上7点自动生成、审核、加入发布池",
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

with get_session_local()() as db:
    db.add(task)
    db.commit()
    print(f"任务创建成功: ID={task.id}")
```

### 方式 3: 直接 SQL 插入

```sql
INSERT INTO scheduled_tasks (
    name,
    task_type,
    description,
    cron_expression,
    is_active,
    params,
    created_at,
    updated_at
) VALUES (
    '车界显眼包-每日自动发布',
    'workflow',
    '每天早上7点自动生成、审核、加入发布池',
    '0 7 * * *',
    1,
    '{"steps": [
        {"type": "content_generation", "params": {"account_id": 49, "topic": "..."}},
        {"type": "approve", "params": {"content_id": "${content_id}"}},
        {"type": "add_to_pool", "params": {"content_id": "${content_id}", "priority": 5}}
    ]}',
    datetime('now'),
    datetime('now')
);
```

## 验证步骤

### 1. 查看任务列表

```bash
python -m cli.main scheduler list --type workflow
```

### 2. 查看任务详情

```bash
python -m cli.main scheduler info <task_id>
```

### 3. 手动触发任务测试

```bash
python -m cli.main scheduler trigger <task_id>
```

### 4. 查看执行历史

```bash
python -m cli.main scheduler history --task-id <task_id>
```

### 5. 验证结果

```bash
# 查看生成的内容
python -m cli.main content list --account-id 49

# 查看发布池
python -m cli.main publish-pool list
```

## 执行流程说明

### 工作流执行流程

```
1. ContentGenerationExecutor
   ↓ 返回 data: {"content_id": 123, "title": "...", ...}

2. ApproveExecutor
   参数: {"content_id": "${content_id}"} → {"content_id": 123}
   ↓ 审核通过

3. AddToPoolExecutor
   参数: {"content_id": "${content_id}", "priority": 5} → {"content_id": 123, "priority": 5}
   ↓ 加入发布池，返回 data: {"pool_id": 456}

4. WorkflowExecutor 完成
   返回: 所有步骤的执行结果
```

### 上下文传递机制

每个步骤执行后，其返回的 `data` 字段会合并到上下文中：

```python
context = {}

# 步骤 1: content_generation
result.data = {"content_id": 123, "title": "测试文章"}
context.update(result.data)
# context = {"content_id": 123, "title": "测试文章"}

# 步骤 2: approve
params = {"content_id": "${content_id}"}
# 解析后: params = {"content_id": 123}

# 步骤 3: add_to_pool
params = {"content_id": "${content_id}", "priority": 5}
# 解析后: params = {"content_id": 123, "priority": 5}
```

## 扩展性示例

### 示例 1: 生成 → 通知（假设有通知执行器）

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {"account_id": 49, "topic": "..."}
    },
    {
      "type": "send_notification",
      "params": {
        "message": "内容 ${title} 已生成",
        "content_id": "${content_id}"
      }
    }
  ]
}
```

### 示例 2: 生成 → 审核 → 发布（不经过发布池）

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {"account_id": 49, "topic": "..."}
    },
    {
      "type": "approve",
      "params": {"content_id": "${content_id}"}
    },
    {
      "type": "publishing",
      "params": {
        "content_id": "${content_id}",
        "publish_to_draft": true
      }
    }
  ]
}
```

### 示例 3: 批量生成多篇文章

```json
{
  "steps": [
    {
      "type": "content_generation",
      "params": {"account_id": 49, "topic": "主题1"}
    },
    {
      "type": "add_to_pool",
      "params": {"content_id": "${content_id}", "priority": 5}
    },
    {
      "type": "content_generation",
      "params": {"account_id": 49, "topic": "主题2"}
    },
    {
      "type": "add_to_pool",
      "params": {"content_id": "${content_id}", "priority": 6}
    }
  ]
}
```

## 注意事项

1. **变量引用**: 确保变量在上下文中存在，否则会保持原样（如 `${content_id}`）
2. **步骤失败**: 任何步骤失败会导致整个工作流中断
3. **执行顺序**: 步骤按数组顺序依次执行
4. **上下文覆盖**: 后续步骤的同名变量会覆盖前面的值
5. **执行器类型**: 确保 `type` 字段使用已注册的执行器类型

## 故障排查

### 问题 1: 任务创建成功但未执行

**检查**:
```bash
# 查看调度器状态
python -m cli.main scheduler status

# 查看任务是否启用
python -m cli.main scheduler list
```

**解决**:
- 确保调度器正在运行
- 确保任务的 `is_active` 为 true

### 问题 2: 工作流执行失败

**检查**:
```bash
# 查看执行历史
python -m cli.main scheduler history --task-id <task_id>

# 查看详细错误
python -m cli.main scheduler info <task_id>
```

**常见错误**:
- `ExecutorNotFound`: 执行器类型未注册
- `ContentNotFound`: 内容ID不存在
- `Variable not found`: 上下文中找不到变量

### 问题 3: 变量替换不生效

**检查参数格式**:
- 必须使用 `${variable_name}` 格式
- 变量名必须在前面步骤的 `result.data` 中存在

## 已注册的执行器

当前系统已注册的执行器：

```bash
python -c "
from app.services.scheduler_service import scheduler_service
print('已注册的执行器:')
for executor_type in scheduler_service.get_registered_executors().keys():
    print(f'  - {executor_type}')
"
```

输出示例：
```
已注册的执行器:
  - content_generation
  - publishing
  - workflow
  - add_to_pool
  - approve
```

## 文件清单

本次实施涉及的文件：

### 新增文件
- `src/backend/app/services/executors/workflow_executor.py` - 工作流执行器
- `src/backend/app/services/executors/add_to_pool_executor.py` - 加入发布池执行器
- `src/backend/app/services/executors/approve_executor.py` - 审核执行器
- `src/backend/test_workflow_executors.py` - 单元测试脚本

### 修改文件
- `src/backend/app/services/executors/__init__.py` - 导出新执行器
- `src/backend/app/modules/scheduler/module.py` - 注册新执行器
- `src/backend/cli/modules/scheduler.py` - 添加 `--params` 选项支持

## 总结

通过工作流执行器，您可以：

✅ 编排多个执行步骤
✅ 在步骤间传递数据
✅ 支持变量替换
✅ 灵活组合不同执行器
✅ 实现复杂自动化流程

这使得 ContentHub 的自动化能力大大增强，可以轻松实现各种复杂的业务流程。
