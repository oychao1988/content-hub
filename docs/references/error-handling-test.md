# ContentHub 错误处理机制测试文档

## 概述

ContentHub 已实现了完善的错误处理机制，包括后端统一错误响应、前端统一错误处理、请求追踪和外部服务降级策略。

## 测试清单

### 1. 后端错误处理测试

#### 1.1 请求 ID 追踪

**测试目的**: 验证每个请求都有唯一的请求 ID，并且在错误响应中返回

**测试方法**:
```bash
# 发送一个会失败的请求
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "wrong", "password": "wrong"}'

# 检查响应头
# 应该看到: X-Request-ID: req_xxxxx
# 响应体应该包含: "requestId": "req_xxxxx"
```

**预期结果**:
- 响应头包含 `X-Request-ID`
- 响应体包含 `requestId` 字段
- 前后端的请求 ID 一致

#### 1.2 验证错误处理

**测试方法**:
```bash
# 发送缺少必填字段的请求
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{}'
```

**预期结果**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "details": {
      "username": "字段 'username' 是必填项",
      "password": "字段 'password' 是必填项"
    }
  },
  "requestId": "req_xxxxx"
}
```

#### 1.3 业务异常处理

**测试方法**:
```bash
# 访问不存在的资源
curl -X GET http://localhost:8000/api/v1/accounts/99999
```

**预期结果**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "账号不存在 (ID: 99999)",
    "details": {
      "resource_id": "99999"
    }
  },
  "requestId": "req_xxxxx"
}
```

#### 1.4 外部服务超时处理

**测试目的**: 验证 Content-Creator CLI 超时时的错误处理

**配置**: 在 `.env` 中设置超时时间
```bash
# .env
CREATOR_CLI_TIMEOUT=5  # 5秒超时
```

**预期结果**:
- 超时后自动重试（最多2次）
- 最终返回超时错误
- 日志记录重试过程

#### 1.5 外部服务降级

**测试目的**: 验证 Content-Publisher 服务降级机制

**测试方法**:
```python
# 模拟 Publisher API 连续失败
# 第1-3次应该重试
# 第4次应该返回降级响应
```

**预期降级响应**:
```json
{
  "success": false,
  "degraded": true,
  "message": "发布服务暂时不可用，已加入重试队列",
  "data": {
    "status": "pending_retry",
    "retry_at": null
  }
}
```

### 2. 前端错误处理测试

#### 2.1 错误提示显示

**测试方法**:
1. 在浏览器中打开应用
2. 故意输入错误的数据（如空密码）
3. 提交表单

**预期结果**:
- 显示友好的错误提示（使用 Element Plus Message）
- 控制台记录详细的错误日志

#### 2.2 Token 过期处理

**测试方法**:
1. 登录应用
2. 手动修改 localStorage 中的 token（使其无效）
3. 执行需要认证的操作

**预期结果**:
- 显示"登录已过期"提示
- 自动跳转到登录页
- 清除本地认证信息

#### 2.3 请求重试

**测试方法**:
1. 临时断开网络连接
2. 执行一个 API 请求
3. 恢复网络连接

**预期结果**:
- 请求自动重试（最多2次）
- 指数退避延迟（1s, 2s）
- 控制台显示重试日志

#### 2.4 降级响应处理

**测试方法**:
1. 模拟后端返回降级响应
2. 检查前端显示

**预期结果**:
- 显示警告（warning）而不是错误
- 提示用户服务繁忙
- 不中断用户操作流程

### 3. 日志验证

#### 3.1 后端日志

**日志位置**: `src/backend/logs/contenthub.log`

**检查内容**:
```log
# 请求开始
INFO - Request started [req_abc123] POST /api/v1/auth/login from 127.0.0.1

# 请求完成
INFO - Request completed [req_abc123] POST /api/v1/auth/login status=200 duration=0.123s

# 错误日志
WARNING - HTTP Exception [req_abc123]: 401 - Unauthorized | Path: /api/v1/auth/login | Method: POST

# 慢请求警告
WARNING - SLOW REQUEST: POST /api/v1/content/generate status=200 3.456s
```

#### 3.2 前端日志

**检查位置**: 浏览器开发者工具 Console

**检查内容**:
```javascript
// 请求失败日志
API 请求失败: {
  url: "/api/v1/auth/login",
  method: "POST",
  status: 401,
  data: {...},
  message: "用户名或密码错误",
  requestId: "req_abc123",
  processTime: "0.123"
}
```

### 4. 性能测试

#### 4.1 请求响应时间

**测试目的**: 确保错误处理不影响正常请求的性能

**测试方法**:
```bash
# 使用 Apache Bench 进行压力测试
ab -n 1000 -c 10 http://localhost:8000/health
```

**预期结果**:
- 平均响应时间 < 100ms
- 95% 请求 < 200ms

#### 4.2 错误处理性能

**测试方法**:
```bash
# 发送100个验证错误请求
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{}'
done
```

**预期结果**:
- 错误处理 < 50ms
- 请求 ID 生成正常
- 日志记录正常

## 错误码参考

### 通用错误 (1xxx)
- `INTERNAL_SERVER_ERROR`: 服务器内部错误
- `VALIDATION_ERROR`: 输入数据验证失败
- `NOT_FOUND`: 请求的资源不存在
- `UNAUTHORIZED`: 未授权访问
- `FORBIDDEN`: 没有权限访问

### 认证授权 (2xxx)
- `TOKEN_INVALID`: 登录信息无效
- `TOKEN_EXPIRED`: 登录已过期
- `CREDENTIALS_INVALID`: 用户名或密码错误
- `PERMISSION_DENIED`: 没有权限执行此操作

### 外部服务 (5xxx)
- `EXTERNAL_SERVICE_ERROR`: 外部服务调用失败
- `EXTERNAL_SERVICE_TIMEOUT`: 外部服务响应超时
- `CREATOR_TIMEOUT`: 内容生成超时
- `PUBLISHER_TIMEOUT`: 发布服务超时

## 监控和告警

### 关键指标

1. **错误率**: 监控各类错误的发生频率
2. **响应时间**: 监控 P50, P95, P99 响应时间
3. **外部服务可用性**: 监控 Content-Creator 和 Content-Publisher 的可用性
4. **降级频率**: 监控降级策略触发频率

### 告警规则

建议配置以下告警:
- 错误率 > 5%
- P95 响应时间 > 1s
- 外部服务连续失败 > 3次
- 降级策略触发 > 10次/小时

## 故障排查

### 问题: 请求 ID 不一致

**可能原因**:
- 前端没有发送 X-Request-ID 头
- 中间件未正确注册

**解决方法**:
1. 检查 `factory.py` 中中间件注册顺序
2. 检查前端 `request.js` 是否正确设置请求头

### 问题: 降级策略未触发

**可能原因**:
- `DEGRADE_ENABLED` 设置为 False
- 重试次数未达到阈值

**解决方法**:
1. 检查 `content_publisher_service.py` 配置
2. 增加重试次数或降低阈值

### 问题: 前端错误提示不友好

**可能原因**:
- `errorHandler.js` 中缺少错误码映射
- 未正确提取错误信息

**解决方法**:
1. 在 `errorMessages` 中添加对应的错误码
2. 检查 `extractAxiosError` 方法

## 最佳实践

1. **始终包含请求 ID**: 在所有日志和错误消息中包含请求 ID
2. **使用正确的异常类型**: 根据错误类型选择合适的异常类
3. **提供有用的错误详情**: 在 `details` 字段中包含调试信息
4. **脱敏敏感信息**: 不要在错误响应中暴露密码、token等
5. **记录完整的堆栈**: 后端日志应包含完整的异常堆栈
6. **区分用户消息和日志消息**: 用户看到友好的提示，开发者看到详细日志
