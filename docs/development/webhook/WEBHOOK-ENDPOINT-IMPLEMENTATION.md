# Webhook 接收端点实施总结

## 阶段信息

**阶段**: 阶段 3 - Webhook 接收端点实现
**日期**: 2026-02-09
**状态**: ✅ 已完成

## 实施概览

### 目标
创建 FastAPI 端点接收 content-creator 的 Webhook 回调请求，完成异步内容生成系统的闭环。

### 核心成果
- ✅ Webhook 端点创建完成
- ✅ 请求处理流程实现完成
- ✅ 签名验证集成完成（可选）
- ✅ 错误处理完整（404/401/403/400/500）
- ✅ 日志记录完整
- ✅ 幂等性检查实现完成
- ✅ 三个事件类型处理完成
- ✅ 代码质量检查通过

## 实施详情

### 1. 文件修改

**修改文件**: `src/backend/app/modules/content/endpoints.py`

**新增导入**:
```python
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from typing import Optional, Dict
from app.models import ContentGenerationTask
from app.services.webhook_handler import WebhookHandler, get_webhook_handler
from app.utils.webhook_signature import create_verifier
from app.core.config import settings
from app.utils.custom_logger import log
```

### 2. 端点定义

**端点路径**: `POST /api/v1/content/callback/{task_id}`

**Tags**: `['content', 'webhooks']`（用于 API 文档分组）

**函数签名**:
```python
async def handle_webhook_callback(
    task_id: str,
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    webhook_handler: WebhookHandler = Depends(get_webhook_handler)
)
```

### 3. 功能实现

#### 3.1 请求处理流程

1. **读取请求体**
   - 使用 `await request.json()` 解析 JSON
   - 异常处理返回 400 错误

2. **任务查询**
   - 从数据库查询 `ContentGenerationTask`
   - 不存在返回 404 错误

3. **签名验证**（可选）
   - 检查 `WEBHOOK_REQUIRE_SIGNATURE` 配置
   - 验证签名存在性（403 错误）
   - 验证签名有效性（401 错误）
   - 检查密钥配置（500 错误）

4. **事件类型提取**
   - 验证 `event` 字段存在（400 错误）

5. **事件处理**
   - `completed` → `handle_task_completed()`
   - `failed` → `handle_task_failed()`
   - `progress` → `handle_task_progress()`
   - 未知事件类型（400 错误）

6. **结果记录**
   - 成功/失败日志
   - 幂等性标识

7. **响应返回**
   - 标准格式响应

#### 3.2 错误处理

| HTTP 状态码 | 场景 | 说明 |
|------------|------|------|
| 400 | 请求体格式错误 | JSON 解析失败 |
| 400 | 缺少事件类型 | event 字段缺失 |
| 400 | 未知事件类型 | event 不在支持列表中 |
| 401 | 签名验证失败 | 签名不匹配 |
| 403 | 签名缺失 | 要求签名但未提供 |
| 404 | 任务不存在 | task_id 未找到 |
| 500 | 服务器内部错误 | 未预期的异常 |

#### 3.3 日志记录

**接收请求日志**:
```python
log.info(
    f"Received webhook callback for task {task_id}: "
    f"event={callback_data.get('event')}, "
    f"status={callback_data.get('status')}"
)
```

**成功处理日志**:
```python
log.info(
    f"Webhook callback processed successfully: task {task_id}, "
    f"message={result.get('message')}"
)
```

**幂等性日志**:
```python
log.info(
    f"Webhook callback processed (idempotent): task {task_id}, "
    f"message={result.get('message')}"
)
```

**错误日志**:
```python
log.error(
    f"Unexpected error handling webhook callback for task {task_id}: {e}",
    exc_info=True
)
```

#### 3.4 幂等性保证

- 由 `WebhookHandler` 内部实现
- 检查任务状态是否为最终状态
- 重复回调返回成功但不执行操作
- 响应包含 `skipped` 标识

### 4. 请求体格式

#### 4.1 completed 事件

```json
{
  "event": "completed",
  "taskId": "task-123456789abc",
  "workflowType": "content-creator",
  "status": "completed",
  "timestamp": "2026-02-08T12:00:00Z",
  "metadata": {
    "topic": "文章主题",
    "requirements": "创作要求"
  },
  "result": {
    "content": "文章内容...",
    "htmlContent": "<p>文章HTML</p>",
    "images": ["path/to/image1.jpg"],
    "qualityScore": 8.5,
    "wordCount": 1500
  }
}
```

#### 4.2 failed 事件

```json
{
  "event": "failed",
  "taskId": "task-123456789abc",
  "workflowType": "content-creator",
  "status": "failed",
  "timestamp": "2026-02-08T12:00:00Z",
  "error": {
    "message": "错误信息",
    "code": "ERROR_CODE",
    "type": "error_type"
  }
}
```

#### 4.3 progress 事件

```json
{
  "event": "progress",
  "taskId": "task-123456789abc",
  "workflowType": "content-creator",
  "status": "processing",
  "timestamp": "2026-02-08T12:00:00Z",
  "progress": {
    "percentage": 50,
    "message": "正在生成内容",
    "stage": "content_generation"
  }
}
```

### 5. 响应格式

#### 5.1 成功响应

```json
{
  "success": true,
  "message": "Callback processed",
  "details": {
    "review_status": "pending",
    "publish_status": "draft",
    "auto_approved": false,
    "word_count": 1500
  }
}
```

#### 5.2 幂等响应

```json
{
  "success": true,
  "message": "Task already in final state: completed"
}
```

#### 5.3 失败响应

```json
{
  "success": false,
  "message": "Error message"
}
```

### 6. 依赖注入

**数据库会话**: `db: Session = Depends(get_db)`

**Webhook 处理器**: `webhook_handler: WebhookHandler = Depends(get_webhook_handler)`

**签名 Header**: `x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature")`

## 测试验证

### 代码质量验证

运行验证脚本：`verify_webhook_implementation.py`

**结果**: ✅ 9/9 项检查通过

| 检查项 | 状态 |
|--------|------|
| 端点注册 | ✅ 通过 |
| 函数签名 | ✅ 通过 |
| 文档字符串 | ✅ 通过 |
| 事件处理 | ✅ 通过 |
| 签名验证 | ✅ 通过 |
| 错误处理 | ✅ 通过 |
| 日志记录 | ✅ 通过 |
| 幂等性 | ✅ 通过 |
| 响应格式 | ✅ 通过 |

### 功能测试

运行测试脚本：`test_webhook_simple.py`

**结果**: ✅ 4/4 项测试通过

| 测试项 | 状态 |
|--------|------|
| 任务完成事件 | ✅ 通过 |
| 任务失败事件 | ✅ 通过 |
| 进度更新事件 | ✅ 通过 |
| 签名验证功能 | ✅ 通过 |

## 集成组件

### 已集成组件

1. **WebhookHandler** (`app/services/webhook_handler.py`)
   - 阶段 1 实现
   - 提供三个处理方法：`handle_task_completed()`, `handle_task_failed()`, `handle_task_progress()`
   - 内部实现幂等性检查

2. **WebhookSignatureVerifier** (`app/utils/webhook_signature.py`)
   - 阶段 2 实现
   - 提供 `create_verifier()` 工厂函数
   - 支持 HMAC-SHA256 + Base64 签名验证

3. **ContentGenerationTask** (`app/models/content_generation_task.py`)
   - 数据模型
   - 存储任务状态和结果

4. **配置系统** (`app/core/config.py`)
   - `WEBHOOK_REQUIRE_SIGNATURE`: 是否强制要求签名
   - `WEBHOOK_SECRET_KEY`: 签名密钥

## API 文档

### Swagger UI 访问

启动服务后访问：`http://localhost:18010/docs`

在 Swagger UI 中，Webhook 端点会被归类到 **webhooks** 标签下，便于查找和测试。

### 端点信息

- **路径**: `/api/v1/content/callback/{task_id}`
- **方法**: `POST`
- **标签**: `webhooks`
- **认证**: 不需要（由签名验证保护）
- **请求体**: application/json
- **响应**: application/json

## 使用示例

### cURL 示例

#### 1. 任务完成回调

```bash
curl -X POST http://localhost:18010/api/v1/content/callback/task-123456789abc \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=" \
  -d '{
    "event": "completed",
    "taskId": "task-123456789abc",
    "workflowType": "content-creator",
    "status": "completed",
    "timestamp": "2026-02-09T12:00:00Z",
    "result": {
      "content": "# 测试文章\n\n文章内容...",
      "htmlContent": "<h1>测试文章</h1><p>文章内容...</p>",
      "wordCount": 1500
    }
  }'
```

#### 2. 任务失败回调

```bash
curl -X POST http://localhost:18010/api/v1/content/callback/task-123456789abc \
  -H "Content-Type: application/json" \
  -d '{
    "event": "failed",
    "taskId": "task-123456789abc",
    "error": {
      "message": "AI service unavailable",
      "code": "SERVICE_ERROR",
      "type": "ServiceError"
    }
  }'
```

#### 3. 进度更新回调

```bash
curl -X POST http://localhost:18010/api/v1/content/callback/task-123456789abc \
  -H "Content-Type: application/json" \
  -d '{
    "event": "progress",
    "taskId": "task-123456789abc",
    "progress": {
      "percentage": 50,
      "stage": "content_generation",
      "message": "正在生成文章内容"
    }
  }'
```

### Python 示例

```python
import requests
import json
from app.utils.webhook_signature import generate_signature
from app.core.config import settings

# 准备回调数据
callback_data = {
    "event": "completed",
    "taskId": "task-123456789abc",
    "result": {
        "content": "文章内容...",
        "wordCount": 1500
    }
}

# 生成签名（如果需要）
headers = {"Content-Type": "application/json"}
if settings.WEBHOOK_REQUIRE_SIGNATURE:
    signature = generate_signature(callback_data, settings.WEBHOOK_SECRET_KEY)
    headers["X-Webhook-Signature"] = signature

# 发送回调
response = requests.post(
    f"http://localhost:18010/api/v1/content/callback/task-123456789abc",
    json=callback_data,
    headers=headers
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")
```

## 配置说明

### 环境变量

在 `.env` 文件中配置以下变量：

```bash
# Webhook 配置
WEBHOOK_ENABLED=true                          # 是否启用 Webhook
WEBHOOK_REQUIRE_SIGNATURE=false               # 是否强制要求签名（开发环境：false，生产环境：true）
WEBHOOK_SECRET_KEY=your-secret-key-here       # 签名密钥（生产环境必须配置）
WEBHOOK_URL=http://localhost:18010/api/v1/content/callback/{task_id}  # Webhook URL
WEBHOOK_TIMEOUT=10                            # 请求超时时间（秒）
```

### 开发环境配置

```bash
WEBHOOK_REQUIRE_SIGNATURE=false  # 不要求签名（便于测试）
```

### 生产环境配置

```bash
WEBHOOK_REQUIRE_SIGNATURE=true   # 强制要求签名（安全性）
WEBHOOK_SECRET_KEY=your-production-secret-key-256-bits
```

## 安全性考虑

### 1. 签名验证

- 使用 HMAC-SHA256 算法
- Base64 编码传输
- 常量时间比较（防止时序攻击）
- 生产环境强制启用

### 2. 错误处理

- 不暴露敏感信息
- 详细错误日志记录
- 统一错误响应格式

### 3. 幂等性

- 防止重复处理
- 状态检查机制
- 安全的事务处理

## 监控和日志

### 日志级别

- **INFO**: 正常处理流程
- **WARNING**: 幂等性跳过、未知事件类型
- **ERROR**: 处理失败、签名验证失败

### 关键日志

```
# 接收请求
INFO: Received webhook callback for task task-123: event=completed, status=completed

# 签名验证成功
INFO: Webhook signature verified successfully for task task-123

# 处理成功
INFO: Webhook callback processed successfully: task task-123, message=Task completed and content created

# 幂等性跳过
INFO: Webhook callback processed (idempotent): task task-123, message=Task already in final state: completed

# 签名验证失败
WARNING: Webhook callback: Invalid signature for task task-123

# 任务不存在
WARNING: Webhook callback: Task not found: task-123
```

## 故障排查

### 常见问题

#### 1. 签名验证失败（401）

**原因**:
- 签名密钥不匹配
- 请求体被修改
- 签名生成算法不一致

**解决**:
- 检查 `WEBHOOK_SECRET_KEY` 配置
- 确保请求体与签名时一致
- 验证签名算法实现

#### 2. 签名缺失（403）

**原因**:
- 未提供 `X-Webhook-Signature` Header
- `WEBHOOK_REQUIRE_SIGNATURE=True` 但未配置密钥

**解决**:
- 开发环境设置 `WEBHOOK_REQUIRE_SIGNATURE=False`
- 生产环境确保提供签名
- 检查 Header 名称

#### 3. 任务不存在（404）

**原因**:
- task_id 不正确
- 任务已被删除
- 数据库连接问题

**解决**:
- 验证 task_id 正确性
- 检查任务是否创建成功
- 检查数据库连接

#### 4. 请求体格式错误（400）

**原因**:
- JSON 格式错误
- 缺少必需字段
- 字段类型不匹配

**解决**:
- 验证 JSON 格式
- 检查 `event` 字段
- 查看详细错误信息

## 下一步工作

### 建议改进

1. **重试机制**
   - 网络失败自动重试
   - 指数退避策略

2. **监控指标**
   - Webhook 接收成功率
   - 平均处理时间
   - 错误类型统计

3. **限流保护**
   - 防止恶意请求
   - 基于 IP 的限流
   - 基于任务 ID 的限流

4. **批量处理**
   - 支持批量 Webhook
   - 减少 HTTP 请求

### 后续集成

1. **content-creator 集成**
   - 配置 Webhook URL
   - 测试签名生成
   - 验证请求格式

2. **监控告警**
   - Webhook 失败告警
   - 任务超时告警
   - 签名验证失败告警

3. **性能优化**
   - 异步处理
   - 批量数据库操作
   - 缓存机制

## 总结

### 完成标准

| 标准 | 状态 |
|------|------|
| Webhook 端点创建完成 | ✅ |
| 请求处理流程实现完成 | ✅ |
| 签名验证集成完成 | ✅ |
| 错误处理完整 | ✅ |
| 日志记录完整 | ✅ |
| 幂等性检查实现完成 | ✅ |
| 三个事件类型处理完成 | ✅ |
| 代码质量检查通过 | ✅ |

### 技术亮点

1. **完整的依赖注入**：使用 FastAPI 依赖注入系统
2. **可选的签名验证**：基于配置灵活启用/禁用
3. **详细的错误处理**：覆盖所有异常场景
4. **完整的日志记录**：便于监控和调试
5. **幂等性保证**：防止重复处理
6. **完善的文档**：详细的 docstring 和示例

### 交付物

1. **代码文件**:
   - `src/backend/app/modules/content/endpoints.py`（修改）

2. **测试文件**:
   - `src/backend/verify_webhook_implementation.py`（验证脚本）
   - `src/backend/test_webhook_simple.py`（功能测试）

3. **文档**:
   - 本文档（`WEBHOOK-ENDPOINT-IMPLEMENTATION.md`）

---

**实施人员**: Claude Code
**审查状态**: 待审查
**部署状态**: 待部署
