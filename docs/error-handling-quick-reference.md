# ContentHub 错误处理快速参考

## 错误响应格式

### 标准错误响应
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "用户友好的错误描述",
    "details": {}
  },
  "requestId": "req_abc123def456"
}
```

### 降级响应
```json
{
  "success": false,
  "degraded": true,
  "message": "服务暂时不可用，已加入重试队列",
  "data": {
    "status": "pending_retry"
  }
}
```

## 常用错误码

### 通用错误 (1xxx)
- `INTERNAL_SERVER_ERROR` - 服务器内部错误
- `VALIDATION_ERROR` - 输入数据验证失败
- `NOT_FOUND` - 请求的资源不存在
- `UNAUTHORIZED` - 未授权访问
- `FORBIDDEN` - 没有权限访问

### 认证授权 (2xxx)
- `TOKEN_EXPIRED` - 登录已过期
- `CREDENTIALS_INVALID` - 用户名或密码错误
- `PERMISSION_DENIED` - 没有权限执行此操作

### 资源错误 (3xxx)
- `RESOURCE_NOT_FOUND` - 资源不存在
- `RESOURCE_ALREADY_EXISTS` - 资源已存在

### 外部服务 (5xxx)
- `CREATOR_TIMEOUT` - 内容生成超时
- `PUBLISHER_TIMEOUT` - 发布服务超时
- `EXTERNAL_SERVICE_UNAVAILABLE` - 外部服务不可用

## 后端使用指南

### 抛出业务异常

```python
from app.core.exceptions import (
    ResourceNotFoundException,
    BusinessException,
    InvalidStateException
)

# 资源未找到
raise ResourceNotFoundException("账号", account_id)

# 一般业务错误
raise BusinessException("操作失败", details={"reason": "余额不足"})

# 状态错误
raise InvalidStateException(
    "当前状态不允许此操作",
    current_state="published",
    required_state="draft"
)
```

### 外部服务调用

```python
from app.services.content_creator_service import content_creator_service
from app.services.content_publisher_service import content_publisher_service

# 内容生成（自动重试和超时处理）
try:
    result = content_creator_service.create_content(
        account_id=1,
        topic="人工智能",
        category="技术"
    )
except CreatorTimeoutException:
    # 处理超时
    pass
except CreatorException as e:
    # 处理其他错误
    pass

# 内容发布（自动重试、降级）
result = content_publisher_service.publish_to_wechat(
    content_id=123,
    account_id=1
)

# 检查是否为降级响应
if result.get("degraded"):
    # 处理降级情况
    pass
```

## 前端使用指南

### API 调用示例

```javascript
import request from '@/utils/request'

// 标准 GET 请求
request.get('/api/v1/accounts')
  .then(data => {
    console.log('成功:', data)
  })
  .catch(error => {
    if (error.degraded) {
      // 降级响应
      console.warn('服务降级:', error.userMessage)
    } else if (error.handled) {
      // 已处理的错误（已显示提示）
      console.log('错误已处理')
    } else {
      // 未处理的错误
      console.error('未处理的错误:', error)
    }
  })

// 静默请求（不显示错误提示）
import { silentRequest } from '@/utils/request'

silentRequest.get('/api/v1/status')
  .then(data => {
    // 即使失败也不会显示错误提示
  })

// 不重试的请求
import { noRetryRequest } from '@/utils/request'

noRetryRequest.post('/api/v1/logout', {})
  .then(data => {
    // 即使失败也不会重试
  })
```

### 错误处理示例

```javascript
import errorHandler from '@/utils/errorHandler'

// 处理 API 错误
function handleApiError(error) {
  const errorInfo = errorHandler.extractAxiosError(error)

  if (errorInfo.degraded) {
    // 降级响应
    return '服务暂时繁忙，请稍后重试'
  }

  if (errorHandler.shouldLogout(errorInfo.status, errorInfo.data)) {
    // 需要重新登录
    return '登录已过期'
  }

  // 其他错误
  return errorInfo.message
}

// 检查是否可重试
if (errorHandler.isRetryable(status, response)) {
  // 可以重试
}
```

## 日志追踪

### 后端日志

```python
# 在异常处理器中自动记录
# 日志格式包含请求 ID
"""
WARNING - HTTP Exception [req_abc123] 404 - Not Found | Path: /api/v1/accounts/999 | Method: GET
"""

# 手动记录请求 ID
from fastapi import Request

@router.get("/test")
async def test_endpoint(request: Request):
    request_id = request.state.request_id
    log.info(f"Processing request {request_id}")
    return {"requestId": request_id}
```

### 前端日志

```javascript
// 在浏览器控制台查看
console.error('API 请求失败:', {
  url: "/api/v1/auth/login",
  method: "POST",
  status: 401,
  data: {...},
  message: "用户名或密码错误",
  requestId: "req_abc123",
  processTime: "0.123"
})

// 使用响应头中的请求 ID
response.headers['x-request-id']
```

## 配置选项

### 后端配置

```python
# .env 文件

# Content-Creator
CREATOR_CLI_PATH=/path/to/creator
CREATOR_WORK_DIR=/path/to/workdir

# Content-Publisher
PUBLISHER_API_URL=http://localhost:3010
PUBLISHER_API_KEY=your_api_key

# 日志
LOG_LEVEL=INFO
LOG_FILE=logs/contenthub.log
LOG_FORMAT=detailed
```

### 前端配置

```javascript
// src/config/index.js

export default {
  apiBaseUrl: 'http://localhost:8000',
  apiVersion: '/api/v1',
  timeout: 30000,  // 请求超时（毫秒）
}
```

## 测试调试

### 模拟错误响应

```python
# 后端：返回测试错误
from fastapi import HTTPException

@router.get("/test-error")
async def test_error():
    raise HTTPException(
        status_code=400,
        detail={
            "code": "VALIDATION_ERROR",
            "message": "测试错误",
            "details": {"field": "测试字段"}
        }
    )
```

```javascript
// 前端：模拟错误响应
import request from '@/utils/request'

// 测试降级响应
request.get('/api/v1/test/degraded')

// 测试验证错误
request.post('/api/v1/auth/login', {})
```

### 检查点清单

- [ ] 请求 ID 在请求和响应中一致
- [ ] 错误日志包含完整的堆栈信息
- [ ] 敏感信息已脱敏（password, token 等）
- [ ] 前端显示友好的错误提示
- [ ] 外部服务失败时正确降级
- [ ] Token 过期时自动登出
- [ ] 慢请求被记录（>3秒）

## 常见问题

### Q: 如何禁用请求重试？
A: 使用 `noRetryRequest` 或设置 `_skipRetry: true`

### Q: 如何静默处理错误？
A: 使用 `silentRequest` 或设置 `_silent: true`

### Q: 如何自定义错误提示？
A: 在 `errorHandler.js` 的 `errorMessages` 中添加映射

### Q: 如何追踪一个请求的完整流程？
A: 使用请求 ID 在前后端日志中搜索

### Q: 降级响应和错误响应有什么区别？
A: 降级响应表示服务部分可用，错误响应表示请求失败

## 相关文档

- 完整测试指南: `docs/error-handling-test.md`
- 实施总结: `docs/error-handling-summary.md`
- 后端 API 文档: `http://localhost:8000/docs`
- 前端组件文档: `src/frontend/src/components/`

## 获取帮助

- 查看日志: `src/backend/logs/contenthub.log`
- 查看错误日志: `src/backend/logs/error_YYYY-MM-DD.log`
- 检查配置: `src/backend/.env`
- 运行测试: `python tests/test_error_handling.py`
