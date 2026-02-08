# 阶段 4：任务提交逻辑修改 - 完成报告

**执行时间**: 2026-02-09
**阶段**: Stage 4 - Task Submission Logic Modification
**目标**: 修改任务提交逻辑，传递回调 URL 给 content-creator

---

## 一、执行概览

### 1.1 任务完成状态

✓ **所有完成标准已达成**：
- [x] 回调 URL 生成逻辑实现完成
- [x] CLI 命令参数添加完成
- [x] 配置检查逻辑实现完成
- [x] 任务记录更新完成（callback_url 字段）
- [x] 日志记录完整
- [x] 配置参数添加完成
- [x] .env.example 更新完成

---

## 二、具体操作清单

### 2.1 数据库模型修改

**文件**: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/models/content_generation_task.py`

**修改内容**:
```python
# 添加 Webhook 回调配置字段
callback_url = Column(String(500), nullable=True, comment="Webhook 回调 URL")
```

**说明**: 在 `ContentGenerationTask` 模型中添加 `callback_url` 字段，用于存储 Webhook 回调 URL。

---

### 2.2 配置文件修改

**文件**: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/core/config.py`

**修改内容**:
```python
# Webhook 回调配置
WEBHOOK_CALLBACK_BASE_URL: Optional[str] = None  # Webhook 回调基础 URL（外部访问地址）
```

**说明**: 添加新的配置参数 `WEBHOOK_CALLBACK_BASE_URL`，用于指定外部可访问的基础 URL。

**配置优先级**:
1. 如果设置了 `WEBHOOK_CALLBACK_BASE_URL`，使用该值
2. 否则，使用 `http://{HOST}:{PORT}` 构造默认值

---

### 2.3 服务层逻辑修改

**文件**: `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/async_content_generation_service.py`

#### 修改 1：`_submit_to_creator()` 方法

**核心逻辑**:
```python
# 处理 Webhook 回调 URL
if settings.WEBHOOK_ENABLED:
    # 构造回调 URL
    base_url = getattr(settings, 'WEBHOOK_CALLBACK_BASE_URL', None)
    if not base_url:
        # 如果没有配置 WEBHOOK_CALLBACK_BASE_URL，使用默认构造
        # 注意：这里使用 HOST 和 PORT，但建议在生产环境配置 WEBHOOK_CALLBACK_BASE_URL
        base_url = f"http://{settings.HOST}:{settings.PORT}"

    callback_url = f"{base_url}/api/v1/content/callback/{task.task_id}"

    # 更新任务记录
    task.callback_url = callback_url
    self.db.commit()

    # 添加到 CLI 命令
    command.extend(["--callback-url", callback_url])

    log.info(f"Webhook callback enabled for task {task.task_id}: {callback_url}")
else:
    log.info(f"Webhook callback disabled for task {task.task_id}")
```

**功能说明**:
1. **检查 Webhook 是否启用**: 通过 `settings.WEBHOOK_ENABLED` 判断
2. **构造回调 URL**:
   - 优先使用 `WEBHOOK_CALLBACK_BASE_URL` 配置
   - 如果未配置，使用 `http://{HOST}:{PORT}` 作为默认值
   - 最终格式：`{base_url}/api/v1/content/callback/{task_id}`
3. **更新数据库**: 将回调 URL 保存到 `task.callback_url` 字段
4. **添加 CLI 参数**: 将 `--callback-url` 参数传递给 content-creator CLI
5. **日志记录**: 记录是否启用 Webhook 以及回调 URL

#### 修改 2：`get_task_status()` 方法

**修改内容**:
```python
return {
    # ... 其他字段 ...
    "callback_url": task.callback_url,
    # ... 其他字段 ...
}
```

**说明**: 在任务状态查询结果中包含 `callback_url` 字段。

---

### 2.4 环境配置文件更新

**文件**: `/Users/Oychao/Documents/Projects/content-hub/src/backend/.env.example`

**新增配置**:
```bash
# Webhook 回调基础 URL（外部访问地址）
# 如果 content-creator 服务需要回调 ContentHub，请配置此外部可访问的地址
# 例如：https://your-domain.com 或 http://your-server-ip:18010
WEBHOOK_CALLBACK_BASE_URL=http://localhost:18010
```

**说明**:
- 添加详细的配置说明
- 提供配置示例（https 和 http）
- 说明配置用途

---

### 2.5 数据库迁移脚本

**文件**: `/Users/Oychao/Documents/Projects/content-hub/src/backend/migrations/add_callback_url_column.py`

**功能**:
- 自动检查 `callback_url` 列是否已存在
- 添加 `callback_url` 列到 `content_generation_tasks` 表
- 验证添加是否成功
- 提供详细的执行日志

**使用方式**:
```bash
cd src/backend
python -m migrations.add_callback_url_column
```

**输出示例**:
```
============================================================
数据库迁移：添加 callback_url 字段
============================================================

正在添加 callback_url 列...
✓ 成功添加 callback_url 列
✓ 验证成功：callback_url 列已存在

============================================================
迁移完成！
============================================================
```

---

### 2.6 集成测试

**文件**: `/Users/Oychao/Documents/Projects/content-hub/src/backend/tests/test_webhook_callback_integration.py`

**测试用例**:

1. **test_submit_task_with_webhook_enabled**
   - 测试启用 Webhook 时的任务提交
   - 验证回调 URL 正确生成
   - 验证 CLI 命令包含 `--callback-url` 参数

2. **test_submit_task_with_webhook_disabled**
   - 测试禁用 Webhook 时的任务提交
   - 验证不生成回调 URL
   - 验证 CLI 命令不包含 `--callback-url` 参数

3. **test_submit_task_with_default_base_url**
   - 测试未配置 `WEBHOOK_CALLBACK_BASE_URL` 时的行为
   - 验证使用默认值构造回调 URL

4. **test_get_task_status_includes_callback_url**
   - 测试任务状态查询是否包含回调 URL
   - 验证返回结果的完整性

**运行方式**:
```bash
cd src/backend
python tests/test_webhook_callback_integration.py
```

---

## 三、实现功能详解

### 3.1 回调 URL 生成流程

```
┌─────────────────────────────────────────────────────────────┐
│                     任务提交流程                              │
└─────────────────────────────────────────────────────────────┘

1. 检查 WEBHOOK_ENABLED
   │
   ├─ True  ──→ 继续生成回调 URL
   │
   └─ False ──→ 跳过回调 URL 生成

2. 获取基础 URL
   │
   ├─ 优先使用 WEBHOOK_CALLBACK_BASE_URL
   │
   └─ 否则使用 http://{HOST}:{PORT}

3. 构造完整回调 URL
   │
   └─ 格式：{base_url}/api/v1/content/callback/{task_id}

4. 保存到数据库
   │
   └─ 更新 task.callback_url 字段

5. 添加到 CLI 命令
   │
   └─ command.extend(['--callback-url', callback_url])

6. 记录日志
   │
   └─ log.info("Webhook callback enabled: {callback_url}")
```

---

### 3.2 配置示例

#### 开发环境（使用默认值）

```bash
# .env
WEBHOOK_ENABLED=true
WEBHOOK_CALLBACK_BASE_URL=  # 留空，使用默认值
HOST=0.0.0.0
PORT=18010

# 生成的回调 URL
# http://0.0.0.0:18010/api/v1/content/callback/{task_id}
```

#### 生产环境（配置外部域名）

```bash
# .env
WEBHOOK_ENABLED=true
WEBHOOK_CALLBACK_BASE_URL=https://contenthub.example.com
HOST=0.0.0.0
PORT=18010

# 生成的回调 URL
# https://contenthub.example.com/api/v1/content/callback/{task_id}
```

#### 内网环境（配置内网 IP）

```bash
# .env
WEBHOOK_ENABLED=true
WEBHOOK_CALLBACK_BASE_URL=http://192.168.1.100:18010
HOST=0.0.0.0
PORT=18010

# 生成的回调 URL
# http://192.168.1.100:18010/api/v1/content/callback/{task_id}
```

---

### 3.3 CLI 命令示例

#### 启用 Webhook

```bash
content-creator create \
  --type content-creator \
  --mode async \
  --topic "测试选题" \
  --task-id "task-abc123" \
  --callback-url "https://example.com/api/v1/content/callback/task-abc123"
```

#### 禁用 Webhook

```bash
content-creator create \
  --type content-creator \
  --mode async \
  --topic "测试选题" \
  --task-id "task-abc123"
  # 不包含 --callback-url 参数
```

---

## 四、日志记录示例

### 4.1 启用 Webhook

```
INFO:app.services.async_content_generation_service:Webhook callback enabled for task task-abc123: https://example.com/api/v1/content/callback/task-abc123
DEBUG:app.services.async_content_generation_service:Command arguments: /usr/bin/content-creator create --type content-creator --mode async --topic 测试选题 --task-id task-abc123 --callback-url https://example.com/api/v1/content/callback/task-abc123
INFO:app.services.async_content_generation_service:Submitting task to creator: task-abc123
INFO:app.services.async_content_generation_service:Task task-abc123 submitted successfully
```

### 4.2 禁用 Webhook

```
INFO:app.services.async_content_generation_service:Webhook callback disabled for task task-def456
DEBUG:app.services.async_content_generation_service:Command arguments: /usr/bin/content-creator create --type content-creator --mode async --topic 测试选题 --task-id task-def456
INFO:app.services.async_content_generation_service:Submitting task to creator: task-def456
INFO:app.services.async_content_generation_service:Task task-def456 submitted successfully
```

---

## 五、数据库变更

### 5.1 表结构变更

**表名**: `content_generation_tasks`

**新增列**:
```sql
ALTER TABLE content_generation_tasks
ADD COLUMN callback_url VARCHAR(500);
```

**列属性**:
- 类型: `VARCHAR(500)`
- 可空: `True`（允许为空，兼容历史数据）
- 注释: `Webhook 回调 URL`

### 5.2 数据示例

```sql
-- 启用 Webhook 的任务
SELECT task_id, callback_url, status
FROM content_generation_tasks
WHERE callback_url IS NOT NULL;

/*
task_id       | callback_url                                           | status
--------------+--------------------------------------------------------+--------
task-abc123   | https://example.com/api/v1/content/callback/task-abc123| submitted

-- 禁用 Webhook 的任务
task_id       | callback_url | status
--------------+--------------+--------
task-def456   | NULL         | submitted
*/
```

---

## 六、API 变更

### 6.1 任务状态查询响应

**新增字段**: `callback_url`

**响应示例**:
```json
{
  "task_id": "task-abc123",
  "status": "submitted",
  "account_id": 1,
  "topic": "测试选题",
  "priority": 5,
  "auto_approve": true,
  "callback_url": "https://example.com/api/v1/content/callback/task-abc123",
  "created_at": "2026-02-09T10:30:00Z",
  "submitted_at": "2026-02-09T10:30:05Z",
  "started_at": null,
  "completed_at": null,
  "timeout_at": "2026-02-09T11:00:00Z",
  "error": null,
  "content_id": null
}
```

---

## 七、兼容性说明

### 7.1 向后兼容性

✓ **完全向后兼容**:
- `callback_url` 字段允许为 `NULL`
- 历史任务不受影响
- Webhook 功能可配置启用/禁用

### 7.2 升级建议

1. **运行迁移脚本**:
   ```bash
   python -m migrations.add_callback_url_column
   ```

2. **配置环境变量**:
   - 开发环境：使用默认值即可
   - 生产环境：配置 `WEBHOOK_CALLBACK_BASE_URL`

3. **测试验证**:
   - 运行集成测试
   - 检查日志输出
   - 验证数据库记录

---

## 八、问题排查

### 8.1 回调 URL 未生成

**可能原因**:
1. `WEBHOOK_ENABLED=false`
2. `WEBHOOK_CALLBACK_BASE_URL` 配置错误
3. 数据库 `callback_url` 字段不存在

**排查步骤**:
```bash
# 1. 检查配置
grep WEBHOOK .env

# 2. 检查数据库字段
sqlite3 data/contenthub.db "PRAGMA table_info(content_generation_tasks);"

# 3. 检查日志
grep "Webhook callback" logs/contenthub.log
```

### 8.2 CLI 命令不包含回调 URL

**可能原因**:
- Webhook 功能被禁用
- 配置未生效

**解决方案**:
```bash
# 确认环境变量已设置
export WEBHOOK_ENABLED=true
export WEBHOOK_CALLBACK_BASE_URL=https://example.com

# 重启服务
python main.py
```

---

## 九、后续工作建议

### 9.1 短期任务

1. **实现 Webhook 回调接收端点**
   - 创建 `/api/v1/content/callback/{task_id}` 路由
   - 实现回调验证逻辑
   - 处理回调数据

2. **添加回调重试机制**
   - 记录回调失败次数
   - 实现指数退避重试
   - 设置最大重试次数

3. **完善监控和告警**
   - 回调成功率监控
   - 失败告警通知
   - 性能指标统计

### 9.2 长期优化

1. **支持批量回调**
   - 一次性回调多个任务
   - 减少网络开销

2. **回调签名验证**
   - 使用 `WEBHOOK_SECRET_KEY`
   - 验证回调来源
   - 防止伪造请求

3. **回调幂等性**
   - 处理重复回调
   - 避免重复处理

---

## 十、总结

### 10.1 完成情况

✓ **所有功能已实现并通过验证**：
- 回调 URL 生成逻辑
- CLI 参数传递
- 数据库字段存储
- 配置文件更新
- 日志记录完善
- 测试用例覆盖

### 10.2 代码质量

- ✓ 所有文件语法检查通过
- ✓ 遵循项目代码规范
- ✓ 完整的错误处理
- ✓ 详细的日志记录
- ✓ 清晰的注释说明

### 10.3 文档完整性

- ✓ 实现报告（本文档）
- ✓ 配置说明（.env.example）
- ✓ 迁移指南（迁移脚本）
- ✓ 测试文档（测试用例）

---

## 附录

### A. 修改文件清单

1. `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/models/content_generation_task.py`
2. `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/core/config.py`
3. `/Users/Oychao/Documents/Projects/content-hub/src/backend/app/services/async_content_generation_service.py`
4. `/Users/Oychao/Documents/Projects/content-hub/src/backend/.env.example`

### B. 新增文件清单

1. `/Users/Oychao/Documents/Projects/content-hub/src/backend/migrations/add_callback_url_column.py`
2. `/Users/Oychao/Documents/Projects/content-hub/src/backend/tests/test_webhook_callback_integration.py`

### C. 测试执行命令

```bash
# 1. 语法检查
python -m py_compile app/services/async_content_generation_service.py
python -m py_compile app/core/config.py
python -m py_compile app/models/content_generation_task.py

# 2. 数据库迁移
python -m migrations.add_callback_url_column

# 3. 运行测试
python tests/test_webhook_callback_integration.py

# 4. 启动服务
python main.py
```

---

**报告生成时间**: 2026-02-09
**报告版本**: 1.0
**执行者**: Claude Code (Stage 4 Implementation)
