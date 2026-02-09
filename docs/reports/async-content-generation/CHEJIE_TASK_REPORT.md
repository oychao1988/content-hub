# 车界显眼包每日自动发布任务创建报告

## 任务信息确认

### 账号信息
- **账号 ID**: 49
- **账号名称**: 车界显眼包
- **目录名**: wechat_
- **客户**: 欧阳超
- **平台**: 微信公众号
- **运营者**: 欧阳超
- **状态**: 激活
- **创建时间**: 2026-02-07 18:10:58

### 任务配置

#### 基本信息
- **任务 ID**: 1
- **任务名称**: 车界显眼包-每日7点自动发布
- **任务类型**: workflow
- **Cron 表达式**: `0 7 * * *` (每天早上 7:00)
- **状态**: 启用
- **描述**: 每天早上7点自动生成内容、审核、加入发布池

#### 工作流步骤
```json
{
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
        "auto_approve": true
      }
    }
  ]
}
```

## 创建方式

使用 Python 脚本直接创建任务：

**脚本位置**: `/Users/Oychao/Documents/Projects/content-hub/src/backend/create_chejie_task.py`

**执行命令**:
```bash
cd /Users/Oychao/Documents/Projects/content-hub
python src/backend/create_chejie_task.py
```

## 数据库修改

### 添加的字段
为了支持工作流任务，向 `scheduled_tasks` 表添加了以下字段：

1. **params** (JSON): 存储任务参数
2. **enabled** (BOOLEAN): 任务启用状态
3. **executor** (VARCHAR): 执行器标识符

**SQL 命令**:
```sql
ALTER TABLE scheduled_tasks ADD COLUMN params JSON;
ALTER TABLE scheduled_tasks ADD COLUMN enabled BOOLEAN DEFAULT 1;
ALTER TABLE scheduled_tasks ADD COLUMN executor VARCHAR(100);
```

## 执行器注册

### 注册时机
执行器在调度模块启动时自动注册：

**模块文件**: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/modules/scheduler/module.py`

**注册的执行器**:
1. `content_generation` - 内容生成执行器
2. `publishing` - 发布执行器
3. `workflow` - 工作流执行器
4. `add_to_pool` - 加入发布池执行器
5. `approve` - 审核执行器

### 执行器类型映射
- `workflow` → `WorkflowExecutor` (工作流执行器)
  - 负责编排多个步骤按顺序执行
  - 支持变量替换（如 `${content_id}`）
  - 任何步骤失败则中断整个工作流

## 任务工作流程

### 执行流程
1. **内容生成** (Step 1)
   - 使用账号 49 (车界显眼包)
   - 主题：新能源汽车行业最新动态分析
   - 目标受众：汽车爱好者和潜在购车者
   - 语调：专业但通俗易懂
   - 输出：`${content_id}` 变量

2. **自动审核** (Step 2)
   - 使用上一步生成的 `content_id`
   - 自动审核通过

3. **加入发布池** (Step 3)
   - 使用上一步生成的 `content_id`
   - 优先级：5
   - 自动批准：true

### 变量传递
工作流使用上下文在步骤间传递数据：
- `${content_id}` - 从第一步的返回结果中提取

## 验证命令

### 1. 查看任务详情
```bash
# 进入后端目录
cd /Users/Oychao/Documents/Projects/content-hub/src/backend

# 运行验证脚本
python verify_task.py
```

### 2. 直接查询数据库
```bash
# 查看任务基本信息
sqlite3 data/contenthub.db "SELECT id, name, task_type, cron_expression, is_active FROM scheduled_tasks WHERE id = 1;"

# 查看任务参数（格式化 JSON）
sqlite3 data/contenthub.db "SELECT params FROM scheduled_tasks WHERE id = 1;" | python -m json.tool
```

### 3. 通过 CLI（需要启动服务）
```bash
# 查看所有工作流任务
PYTHONPATH=. python -m cli.main scheduler list --type workflow

# 查看任务详情
PYTHONPATH=. python -m cli.main scheduler info 1

# 查看执行历史
PYTHONPATH=. python -m cli.main scheduler executions --task-id 1

# 手动触发任务（测试）
PYTHONPATH=. python -m cli.main scheduler trigger 1

# 查看调度器状态
PYTHONPATH=. python -m cli.main scheduler status
```

## 下次执行时间

- **Cron 表达式**: `0 7 * * *`
- **执行时间**: 每天早上 07:00:00
- **下次执行**: 明天早上 07:00:00（如果当前时间已过今天 7:00）

## 使用说明

### 启动服务
```bash
# 开发环境
make up

# 或手动启动
cd src/backend
python main.py
```

### 查看日志
```bash
# 查看所有日志
make logs

# 只查看后端日志
make logs-backend
```

### 管理任务

#### 修改任务
```bash
# 方式 1: 通过 CLI
PYTHONPATH=. python -m cli.main scheduler update 1 \
  --name "新名称" \
  --cron "0 8 * * *" \
  --description "新描述"

# 方式 2: 直接修改数据库
sqlite3 data/contenthub.db "UPDATE scheduled_tasks SET cron_expression='0 8 * * *' WHERE id=1;"
```

#### 暂停任务
```bash
# 通过 CLI
PYTHONPATH=. python -m cli.main scheduler pause 1

# 或直接修改数据库
sqlite3 data/contenthub.db "UPDATE scheduled_tasks SET is_active=0 WHERE id=1;"
```

#### 恢复任务
```bash
# 通过 CLI
PYTHONPATH=. python -m cli.main scheduler resume 1

# 或直接修改数据库
sqlite3 data/contenthub.db "UPDATE scheduled_tasks SET is_active=1 WHERE id=1;"
```

#### 删除任务
```bash
# 通过 CLI
PYTHONPATH=. python -m cli.main scheduler delete 1

# 或直接修改数据库
sqlite3 data/contenthub.db "DELETE FROM scheduled_tasks WHERE id=1;"
```

### 测试任务

#### 手动触发
```bash
# 立即执行一次任务
PYTHONPATH=. python -m cli.main scheduler trigger 1
```

#### 查看执行结果
```bash
# 查看最近的执行记录
PYTHONPATH=. python -m cli.main scheduler executions --task-id 1

# 查看所有执行记录
PYTHONPATH=. python -m cli.main scheduler executions
```

## 注意事项

1. **服务必须启动**: 调度器需要后端服务运行才能执行任务
2. **执行器自动注册**: 执行器在模块启动时自动注册，无需手动操作
3. **变量引用**: 确保使用正确的变量引用格式 `${content_id}`
4. **Cron 表达式**: 使用标准 Cron 格式（分 时 日 月 周）
5. **优先级**: 发布池优先级范围 1-10，5 为中等优先级

## 故障排查

### 任务未执行
1. 检查服务是否运行：`make logs-backend`
2. 检查任务状态：`sqlite3 data/contenthub.db "SELECT is_active FROM scheduled_tasks WHERE id=1;"`
3. 检查调度器状态：`PYTHONPATH=. python -m cli.main scheduler status`
4. 查看执行历史：`PYTHONPATH=. python -m cli.main scheduler executions --task-id 1`

### 执行器未注册
1. 检查模块是否加载：查看启动日志
2. 检查模块文件：`ls app/modules/scheduler/module.py`
3. 重启服务：`make down && make up`

### 参数错误
1. 验证 JSON 格式：使用 `python -m json.tool`
2. 检查变量引用：确保 `${content_id}` 格式正确
3. 查看执行日志：`make logs-backend`

## 相关文件

| 文件 | 路径 |
|------|------|
| 任务创建脚本 | `/Users/Oychao/Documents/Projects/content-hub/src/backend/create_chejie_task.py` |
| 任务验证脚本 | `/Users/Oychao/Documents/Projects/content-hub/src/backend/verify_task.py` |
| 调度模块 | `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/modules/scheduler/module.py` |
| 工作流执行器 | `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/executors/workflow_executor.py` |
| 数据库文件 | `/Users/Oychao/Documents/Projects/content-hub/src/backend/data/contenthub.db` |

## 下一步

1. **启动服务**: `make up` 或 `cd src/backend && python main.py`
2. **查看日志**: 确认任务已加载到调度器
3. **测试执行**: 使用 CLI 手动触发任务进行测试
4. **监控执行**: 查看执行历史和结果

## 技术支持

如有问题，请查看：
- 项目文档：`/Users/Oychao/Documents/Projects/content-hub/docs/`
- CLI 参考手册：`docs/references/CLI-REFERENCE.md`
- 调度系统架构：`docs/architecture/SCHEDULER-ARCHITECTURE.md`
- 工作流执行器指南：`docs/guides/workflow-executor-guide.md`
