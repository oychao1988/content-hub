# Webhook 配置指南

## 概述

ContentHub 的 Webhook 功能允许 content-creator 在任务完成后主动回调通知，提供实时的任务状态更新。

### 核心优势

- **实时性**：任务完成后立即通知，延迟 < 2 秒
- **降低负载**：减少轮询请求，节省服务器资源
- **可靠性**：与轮询机制互为补充，确保任务状态最终一致
- **安全性**：支持 HMAC-SHA256 签名验证

### 工作原理

```
content-creator           ContentHub
      |                          |
      |---(1) 提交异步任务------->|
      |    (含 callback URL)      |
      |                          |
      |    [AI 生成内容...]       |
      |                          |
      |---(2) Webhook 回调------>|
      |    任务完成通知            |
      |                          |
      |---(3) 处理结果------------|
      |                          |
      |<--(4) 返回成功响应--------|
```

---

## 快速开始

### 步骤 1：启用 Webhook

在 `src/backend/.env` 文件中配置：

```bash
# 启用 Webhook 功能
WEBHOOK_ENABLED=true

# 签名密钥（可选，生产环境建议配置）
WEBHOOK_SECRET_KEY=your-secret-key-here

# 回调处理超时（秒）
WEBHOOK_TIMEOUT=10

# 是否要求签名验证（生产环境建议 true）
WEBHOOK_REQUIRE_SIGNATURE=false
```

### 步骤 2：重启服务

```bash
# Docker 环境
make restart-backend

# 本地开发
cd src/backend
python main.py
```

### 步骤 3：验证配置

```bash
# 检查 Webhook 端点是否可用
curl -X GET http://localhost:18010/api/v1/content/health

# 预期响应：
# {"status": "ok", "webhook_enabled": true}
```

### 步骤 4：测试 Webhook

```bash
# 发送测试 Webhook
curl -X POST http://localhost:18010/api/v1/content/callback/test-task-123 \
  -H "Content-Type: application/json" \
  -d '{
    "event": "completed",
    "taskId": "test-task-123",
    "status": "completed",
    "timestamp": "2026-02-08T12:00:00Z",
    "result": {
      "content": "测试文章内容",
      "qualityScore": 8.5
    }
  }'

# 预期响应：
# {"success": true, "message": "Callback processed"}
```

---

## 配置参数详解

### WEBHOOK_ENABLED

**类型**：布尔值
**默认值**：`false`
**说明**：是否启用 Webhook 接收功能

```bash
# 开发环境（不需要 Webhook）
WEBHOOK_ENABLED=false

# 生产环境（推荐启用）
WEBHOOK_ENABLED=true
```

### WEBHOOK_SECRET_KEY

**类型**：字符串
**默认值**：`null`
**说明**：用于 HMAC-SHA256 签名验证的密钥

```bash
# 生成强密钥（推荐）
WEBHOOK_SECRET_KEY=$(openssl rand -hex 32)

# 示例
WEBHOOK_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**密钥生成方法**：

```bash
# 方法 1：使用 OpenSSL
openssl rand -hex 32

# 方法 2：使用 Python
python -c "import secrets; print(secrets.token_hex(32))"

# 方法 3：使用 /dev/urandom
head -c 32 /dev/urandom | xxd -p -c 32
```

### WEBHOOK_TIMEOUT

**类型**：整数（秒）
**默认值**：`10`
**说明**：Webhook 处理超时时间

```bash
# 快速处理（适合高并发）
WEBHOOK_TIMEOUT=5

# 标准处理（推荐）
WEBHOOK_TIMEOUT=10

# 长时间处理（复杂业务逻辑）
WEBHOOK_TIMEOUT=30
```

### WEBHOOK_REQUIRE_SIGNATURE

**类型**：布尔值
**默认值**：`false`
**说明**：是否强制要求签名验证

```bash
# 开发环境（不验证签名）
WEBHOOK_REQUIRE_SIGNATURE=false

# 生产环境（强制验证，推荐）
WEBHOOK_REQUIRE_SIGNATURE=true
```

---

## 签名验证

### 为什么需要签名验证？

- **安全性**：防止恶意伪造的 Webhook 请求
- **完整性**：确保传输过程中数据未被篡改
- **认证**：验证请求确实来自 content-creator

### 签名算法

ContentHub 使用 HMAC-SHA256 签名算法：

1. **签名生成**（content-creator 端）：

```python
import hmac
import hashlib
import base64
import json

def generate_signature(payload: dict, secret: str) -> str:
    """生成 Webhook 签名"""
    # 1. 序列化 payload
    message = json.dumps(payload, sort_keys=True)

    # 2. 计算 HMAC-SHA256
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()

    # 3. Base64 编码
    signature_b64 = base64.b64encode(signature).decode()

    return signature_b64

# 示例
payload = {
    "event": "completed",
    "taskId": "task-123",
    "status": "completed"
}
secret = "your-secret-key"
signature = generate_signature(payload, secret)
```

2. **签名验证**（ContentHub 端）：

ContentHub 自动验证签名，验证逻辑位于 `app/utils/webhook_signature.py`。

### 启用签名验证

#### 步骤 1：配置密钥

```bash
# .env
WEBHOOK_SECRET_KEY=your-secret-key
WEBHOOK_REQUIRE_SIGNATURE=true
```

#### 步骤 2：content-creator 发送签名

```bash
# content-creator 需要在请求头中包含签名
curl -X POST http://content-hub:18010/api/v1/content/callback/task-123 \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=<signature>" \
  -d '{
    "event": "completed",
    "taskId": "task-123",
    ...
  }'
```

#### 步骤 3：验证签名

ContentHub 自动验证签名，如果签名不匹配将返回 403 错误：

```json
{
  "detail": "Invalid signature"
}
```

---

## Webhook 事件类型

### 1. 任务完成（completed）

当任务成功完成时触发。

**Payload 示例**：

```json
{
  "event": "completed",
  "taskId": "uuid-xxxx-xxxx",
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

**处理逻辑**：
1. 更新任务状态为 `completed`
2. 提取生成结果（content, images, qualityScore）
3. 创建或更新 Content 记录
4. 如果 `auto_approve=true`，自动审核通过并添加到发布池

### 2. 任务失败（failed）

当任务执行失败时触发。

**Payload 示例**：

```json
{
  "event": "failed",
  "taskId": "uuid-xxxx-xxxx",
  "workflowType": "content-creator",
  "status": "failed",
  "timestamp": "2026-02-08T12:00:00Z",
  "error": {
    "message": "API 调用失败：OpenAI API 超时",
    "type": "api_timeout",
    "code": "timeout",
    "details": {
      "retryable": true,
      "maxRetries": 3
    }
  }
}
```

**处理逻辑**：
1. 更新任务状态为 `failed`
2. 保存错误信息
3. 检查是否可重试（`retry_count < max_retries`）
4. 如果可重试，将任务重新加入队列

### 3. 任务进度（progress）

任务执行过程中的进度更新（可选）。

**Payload 示例**：

```json
{
  "event": "progress",
  "taskId": "uuid-xxxx-xxxx",
  "status": "running",
  "timestamp": "2026-02-08T12:00:00Z",
  "progress": {
    "percentage": 75,
    "currentStep": "生成图片",
    "totalSteps": 4,
    "completedSteps": 3
  }
}
```

**处理逻辑**：
1. 更新任务进度信息
2. 记录当前步骤
3. 进度更新失败不影响主流程

---

## 回调端点 API

### 端点信息

- **路径**：`/api/v1/content/callback/{task_id}`
- **方法**：POST
- **Content-Type**：`application/json`

### 请求头

| 头部 | 说明 | 必需 |
|------|------|------|
| Content-Type | 必须是 `application/json` | 是 |
| X-Webhook-Signature | HMAC-SHA256 签名 | 条件必需 |

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| task_id | string | 任务 ID |

### 请求体

Webhook 事件 payload（见上文事件类型）。

### 响应

**成功响应**（200 OK）：

```json
{
  "success": true,
  "message": "Callback processed"
}
```

**幂等性响应**（200 OK）：

```json
{
  "success": true,
  "message": "Task already processed"
}
```

**错误响应**：

| 状态码 | 说明 |
|--------|------|
| 400 | 请求格式错误 |
| 401 | 缺少签名（`WEBHOOK_REQUIRE_SIGNATURE=true`） |
| 403 | 签名验证失败 |
| 404 | 任务不存在 |
| 500 | 服务器内部错误 |

---

## 测试方法

### 本地测试

#### 方法 1：使用 curl

```bash
# 测试任务完成事件
curl -X POST http://localhost:18010/api/v1/content/callback/test-task-001 \
  -H "Content-Type: application/json" \
  -d '{
    "event": "completed",
    "taskId": "test-task-001",
    "status": "completed",
    "timestamp": "2026-02-08T12:00:00Z",
    "result": {
      "content": "# 测试文章\n\n这是测试内容。",
      "htmlContent": "<h1>测试文章</h1><p>这是测试内容。</p>",
      "images": [],
      "qualityScore": 8.0,
      "wordCount": 10
    }
  }'

# 测试任务失败事件
curl -X POST http://localhost:18010/api/v1/content/callback/test-task-002 \
  -H "Content-Type: application/json" \
  -d '{
    "event": "failed",
    "taskId": "test-task-002",
    "status": "failed",
    "timestamp": "2026-02-08T12:00:00Z",
    "error": {
      "message": "测试错误",
      "type": "test_error"
    }
  }'
```

#### 方法 2：使用 Python

```python
import requests
import json

url = "http://localhost:18010/api/v1/content/callback/test-task-001"
payload = {
    "event": "completed",
    "taskId": "test-task-001",
    "status": "completed",
    "timestamp": "2026-02-08T12:00:00Z",
    "result": {
        "content": "测试内容",
        "qualityScore": 8.5
    }
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### 带签名测试

```python
import hmac
import hashlib
import base64
import json
import requests

# 配置
secret = "your-secret-key"
url = "http://localhost:18010/api/v1/content/callback/test-task-001"
payload = {
    "event": "completed",
    "taskId": "test-task-001",
    "status": "completed",
    "timestamp": "2026-02-08T12:00:00Z",
    "result": {
        "content": "测试内容",
        "qualityScore": 8.5
    }
}

# 生成签名
message = json.dumps(payload, sort_keys=True)
signature = hmac.new(
    secret.encode(),
    message.encode(),
    hashlib.sha256
).digest()
signature_b64 = base64.b64encode(signature).decode()

# 发送请求
headers = {
    "Content-Type": "application/json",
    "X-Webhook-Signature": signature_b64
}
response = requests.post(url, json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

---

## 故障排查

### 问题 1：Webhook 端点返回 404

**原因**：服务未正确启动或路由未注册

**解决方案**：
```bash
# 1. 检查服务是否运行
curl http://localhost:18010/api/v1/content/health

# 2. 检查日志
tail -f logs/app.log | grep webhook

# 3. 重启服务
make restart-backend
```

### 问题 2：签名验证失败（403）

**原因**：签名不匹配或密钥配置错误

**解决方案**：
```bash
# 1. 验证密钥配置
echo $WEBHOOK_SECRET_KEY

# 2. 确认 content-creator 使用相同的密钥
# 3. 临时禁用签名验证（仅开发环境）
WEBHOOK_REQUIRE_SIGNATURE=false
```

### 问题 3：任务不存在（404）

**原因**：Webhook 回调先于任务记录创建

**解决方案**：
- 这是正常情况，ContentHub 会记录警告日志
- content-creator 应该在任务提交成功后才发送 Webhook

### 问题 4：幂等性问题

**原因**：重复收到相同的 Webhook

**解决方案**：
- ContentHub 自动处理幂等性（检查任务状态）
- 已处理的任务会返回：`{"success": true, "message": "Task already processed"}`

### 问题 5：处理超时

**原因**：Webhook 处理逻辑过于复杂

**解决方案**：
```bash
# 增加超时时间
WEBHOOK_TIMEOUT=30

# 或优化处理逻辑（异步处理）
```

---

## 生产环境部署

### 安全建议

#### 1. 启用签名验证

```bash
WEBHOOK_REQUIRE_SIGNATURE=true
WEBHOOK_SECRET_KEY=$(openssl rand -hex 32)
```

#### 2. 使用 HTTPS

生产环境必须使用 HTTPS 传输 Webhook：

```nginx
# Nginx 配置示例
server {
    listen 443 ssl;
    server_name content-hub.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /api/v1/content/callback {
        proxy_pass http://localhost:18010;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. IP 白名单（可选）

如果 content-creator 有固定 IP，可以限制访问：

```python
# 在 webhook_handler.py 中添加 IP 验证
ALLOWED_IPS = ["192.168.1.100", "10.0.0.50"]

def verify_ip(request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail="IP not allowed")
```

#### 4. 速率限制

防止 Webhook 洪泛攻击：

```bash
# 使用 Nginx 限流
limit_req_zone $binary_remote_addr zone=webhook:10m rate=10r/s;

location /api/v1/content/callback {
    limit_req zone=webhook burst=20;
    proxy_pass http://localhost:18010;
}
```

### 监控和日志

#### 1. 启用详细日志

```bash
# .env
LOG_LEVEL=INFO
WEBHOOK_LOG_LEVEL=DEBUG
```

#### 2. 监控指标

建议监控以下指标：

- Webhook 接收速率（请求/秒）
- Webhook 成功率（成功/总数）
- 平均处理时间
- 签名验证失败次数
- 重复回调次数

#### 3. 告警规则

```yaml
# Prometheus 告警规则示例
groups:
  - name: webhook_alerts
    rules:
      - alert: WebhookHighFailureRate
        expr: webhook_failure_rate > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Webhook 失败率过高"

      - alert: WebhookSignatureFailure
        expr: rate(webhook_signature_failures[5m]) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Webhook 签名验证失败"
```

### 高可用部署

#### 1. 负载均衡

```nginx
upstream content_hub {
    server content-hub-1:18010;
    server content-hub-2:18010;
    server content-hub-3:18010;
}

server {
    location /api/v1/content/callback {
        proxy_pass http://content_hub;
    }
}
```

#### 2. 幂等性保证

- 所有 Webhook 处理逻辑必须是幂等的
- 使用数据库事务确保一致性
- 记录所有 Webhook 接收日志

#### 3. 降级策略

如果 Webhook 服务不可用：

```python
# 降级到轮询模式
if not webhook_available:
    enable_polling_mode()
```

---

## 最佳实践

### 1. 快速响应

Webhook 处理应该快速返回（< 5 秒）：

```python
# 不推荐：阻塞处理
@router.post("/callback/{task_id}")
async def handle_callback(task_id: str, data: dict):
    # 复杂业务逻辑（阻塞）
    process_content(data)
    save_to_database(data)
    send_notification(data)
    return {"success": True}

# 推荐：异步处理
@router.post("/callback/{task_id}")
async def handle_callback(task_id: str, data: dict):
    # 立即返回
    asyncio.create_task(process_webhook_async(data))
    return {"success": True}

async def process_webhook_async(data):
    # 异步处理业务逻辑
    await process_content(data)
    await save_to_database(data)
    await send_notification(data)
```

### 2. 错误处理

```python
try:
    await handle_webhook(data)
except TemporaryError as e:
    # 临时错误：content-creator 可以重试
    raise HTTPException(status_code=503, detail="Service unavailable")
except PermanentError as e:
    # 永久错误：content-creator 不应重试
    logger.error(f"Permanent error: {e}")
    return {"success": False, "message": "Permanent error"}
```

### 3. 日志记录

```python
logger.info(
    f"Webhook received: event={data['event']}, "
    f"task_id={task_id}, status={data.get('status')}"
)
```

### 4. 测试覆盖

- 单元测试：签名验证、payload 解析
- 集成测试：端到端 Webhook 流程
- 压力测试：高并发 Webhook 请求

---

## 附录

### A. 完整配置示例

```bash
# .env 完整配置
WEBHOOK_ENABLED=true
WEBHOOK_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
WEBHOOK_TIMEOUT=10
WEBHOOK_REQUIRE_SIGNATURE=true
```

### B. 相关文件

| 文件 | 说明 |
|------|------|
| `app/services/webhook_handler.py` | Webhook 处理服务 |
| `app/utils/webhook_signature.py` | 签名验证工具 |
| `app/modules/content/endpoints.py` | Webhook 端点定义 |
| `tests/test_webhook_signature.py` | 签名验证测试 |
| `tests/test_webhook_callback_integration.py` | 集成测试 |

### C. 相关文档

- [异步内容生成设计](../design/async-content-generation.md)
- [ContentHub 开发指南](../../CLAUDE.md)
- [API 文档](http://localhost:18010/docs)

### D. 常见问题

**Q: Webhook 和轮询机制可以同时使用吗？**

A: 可以。Webhook 提供实时通知，轮询作为兜底机制，确保任务状态最终一致。

**Q: 如果 content-creator 不支持 Webhook 怎么办？**

A: ContentHub 的轮询机制会自动处理，无需 Webhook 也能正常工作。

**Q: Webhook 失败会重试吗？**

A: content-creator 负责实现重试逻辑（如果支持）。ContentHub 的 Webhook 端点是幂等的，可以安全接收重复请求。

---

**文档版本**：v1.0
**更新日期**：2026-02-08
**作者**：ContentHub 开发团队
