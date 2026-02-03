# API 限流功能使用指南

**版本**: 1.0.0
**更新日期**: 2026-01-29

---

## 概述

ContentHub 的 API 限流功能基于令牌桶算法实现，支持基于用户角色和 IP 地址的灵活限流策略。限流功能可以防止 API 滥用，保护系统资源，确保公平的服务分配。

---

## 快速开始

### 1. 基本使用（基于用户限流）

```python
from fastapi import APIRouter, Depends, Request
from app.modules.shared.deps import get_current_user
from app.core.rate_limiter import rate_limit

router = APIRouter()

@router.get("/api/v1/content")
@rate_limit(key_type="user")  # 根据用户角色自动限流
async def get_content(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return {"message": "success"}
```

**限流效果**:
- 管理员: 1000 次/小时
- 操作员: 500 次/小时
- 客户: 200 次/小时

### 2. 使用预定义配置

```python
# 登录接口：10次/分钟
@router.post("/api/v1/auth/login")
@rate_limit(config_name="login", key_type="ip")
async def login(request: Request, credentials: LoginSchema):
    return {"token": "xxx"}

# 内容生成：20次/小时
@router.post("/api/v1/content/generate")
@rate_limit(config_name="content_generate", key_type="user")
async def generate_content(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return {"content_id": 123}
```

### 3. 自定义限流参数

```python
# 发布接口：50次/小时
@router.post("/api/v1/publisher/publish")
@rate_limit(
    capacity=50,           # 容量：50个令牌
    refill_rate=0.014,     # 补充速率：50/3600 = 0.014令牌/秒
    key_type="user"
)
async def publish_content(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return {"status": "published"}
```

### 4. 基于 IP 的限流（公开接口）

```python
# 公开API：1000次/小时
@router.get("/api/v1/public/health")
@rate_limit(capacity=1000, refill_rate=0.28, key_type="ip")
async def health_check(request: Request):
    return {"status": "healthy"}
```

---

## 限流配置说明

### 预定义配置

系统提供以下预定义配置：

| 配置名称 | 容量 | 速率 | 说明 |
|---------|------|------|------|
| `default` | 1000 | 0.28/秒 | 1000次/小时，通用限流 |
| `login` | 10 | 0.17/秒 | 10次/分钟，登录限流 |
| `content_generate` | 20 | 0.0056/秒 | 20次/小时，内容生成限流 |

### 基于角色的限流

| 角色 | 容量 | 速率 | 说明 |
|------|------|------|------|
| `admin` | 1000 | 0.28/秒 | 管理员，1000次/小时 |
| `operator` | 500 | 0.14/秒 | 操作员，500次/小时 |
| `customer` | 200 | 0.056/秒 | 客户，200次/小时 |

---

## 响应头说明

### 成功请求的响应头

```
X-RateLimit-Limit: 1000         # 限流容量（总令牌数）
X-RateLimit-Remaining: 950      # 剩余可用令牌数
X-RateLimit-Reset: 1706456400   # 令牌完全重置的时间戳（Unix时间）
```

### 被限流时的响应

**状态码**: 429 Too Many Requests

**响应头**:
```
Retry-After: 60                 # 建议等待的秒数
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706456400
```

**响应体**:
```json
{
  "detail": "请求过于频繁，请在 60 秒后重试"
}
```

---

## 限流参数计算

### 令牌补充速率计算

```
refill_rate = capacity / 时间窗口（秒）

示例：
- 1000次/小时: 1000 / 3600 = 0.28 令牌/秒
- 500次/小时:  500 / 3600 = 0.14 令牌/秒
- 10次/分钟:   10 / 60   = 0.17 令牌/秒
```

### 常用速率参考

| 频率 | 容量 | 速率（令牌/秒） |
|------|------|----------------|
| 1000次/小时 | 1000 | 0.28 |
| 500次/小时 | 500 | 0.14 |
| 200次/小时 | 200 | 0.056 |
| 100次/小时 | 100 | 0.028 |
| 60次/小时 | 60 | 0.017 |
| 10次/分钟 | 10 | 0.17 |

---

## 最佳实践

### 1. 选择合适的限流键

**基于用户限流**（推荐用于需要认证的接口）:
```python
@rate_limit(key_type="user")
async def endpoint(current_user: User = Depends(get_current_user)):
    pass
```

**基于 IP 限流**（推荐用于公开接口）:
```python
@rate_limit(key_type="ip")
async def public_endpoint(request: Request):
    pass
```

### 2. 根据接口类型选择限流策略

| 接口类型 | 限流策略 | 示例 |
|---------|---------|------|
| 登录/注册 | 严格限流 + IP | 10次/分钟，基于IP |
| 内容生成 | 中等限流 + 用户 | 20次/小时，基于用户 |
| 数据查询 | 宽松限流 + 用户 | 1000次/小时，基于用户 |
| 公开API | 中等限流 + IP | 100次/小时，基于IP |
| 敏感操作 | 严格限流 + 用户 | 10次/小时，基于用户 |

### 3. 使用预定义配置

优先使用系统提供的预定义配置，保持限流策略的一致性：

```python
# 推荐
@rate_limit(config_name="login", key_type="ip")

# 不推荐（除非有特殊需求）
@rate_limit(capacity=10, refill_rate=0.17, key_type="ip")
```

### 4. 敏感操作双重限流

对于敏感操作（如密码重置），可以结合应用层限流：

```python
@router.post("/reset-password")
@rate_limit(config_name="login", key_type="ip")  # IP限流
async def reset_password(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # 应用层：每个用户每天只能重置一次
    if not user_service.can_reset_password(current_user.id):
        raise HTTPException(status_code=429, detail="今日已重置，请明天再试")

    # 执行密码重置
    return {"status": "success"}
```

---

## 常见问题

### Q1: 如何为不同端点设置不同的限流？

A: 使用不同的限流装饰器参数：

```python
# 严格限流
@rate_limit(config_name="login", key_type="ip")

# 中等限流
@rate_limit(config_name="content_generate", key_type="user")

# 宽松限流
@rate_limit(key_type="user")  # 使用默认配置
```

### Q2: 限流信息会持久化吗？

A: 当前实现使用内存存储，重启后会丢失。如需持久化，可以考虑使用 Redis。

### Q3: 如何临时禁用某个端点的限流？

A: 移除装饰器或设置一个很大的容量：

```python
# 方式1：移除装饰器
@router.get("/endpoint")
async def endpoint():
    pass

# 方式2：设置大容量
@rate_limit(capacity=1000000, refill_rate=278, key_type="user")
async def endpoint():
    pass
```

### Q4: 如何在响应中查看剩余请求次数？

A: 检查响应头 `X-RateLimit-Remaining`：

```python
response = requests.get("https://api.example.com/content")
remaining = response.headers.get("X-RateLimit-Remaining")
print(f"剩余请求次数: {remaining}")
```

### Q5: 被限流后多久可以重试？

A: 检查响应头 `Retry-After`（秒数）或错误消息：

```python
if response.status_code == 429:
    retry_after = response.headers.get("Retry-After")
    print(f"请在 {retry_after} 秒后重试")
```

---

## 技术细节

### 令牌桶算法

ContentHub 使用令牌桶算法实现限流：

1. **桶的容量固定**: 最多保存 capacity 个令牌
2. **令牌按固定速率补充**: 每秒补充 refill_rate 个令牌
3. **请求时消费令牌**: 每次请求消费 1 个令牌
4. **令牌不足时拒绝**: 没有令牌时返回 429 错误

**优点**:
- 允许短时间内的突发流量
- 平滑的限流效果
- 精确的速率控制

### IP 检测优先级

系统按以下优先级检测客户端 IP：

1. `X-Forwarded-For` 头部（取第一个 IP）
2. `X-Real-IP` 头部
3. `request.client.host`（直接连接的 IP）
4. `unknown`（无法获取时）

### 性能影响

- **时间复杂度**: O(1) - 字典查找和简单计算
- **空间复杂度**: O(n) - n 为活跃用户/IP 数
- **内存占用**: 每个限流器约 100-200 字节

---

## 进阶使用

### 自定义限流键

可以实现自定义的限流键函数：

```python
from app.core.rate_limiter import get_rate_limit_key

# 基于用户ID + 操作类型的限流
key = f"user:{current_user.id}:action:publish"

# 基于租户的限流
key = f"tenant:{current_user.tenant_id}"

# 基于设备ID的限流
key = f"device:{request.headers.get('Device-ID')}"
```

### 动态限流

可以根据时间段或系统负载动态调整限流：

```python
def get_dynamic_limit(user):
    if is_peak_hour():
        return {"capacity": 500, "refill_rate": 0.14}
    else:
        return {"capacity": 1000, "refill_rate": 0.28}

@rate_limit(key_type="user")
async def endpoint(request: Request, current_user: User = Depends(get_current_user)):
    # 在装饰器中使用动态配置
    pass
```

---

## 相关文档

- **设计文档**: `docs/DESIGN.md` 第 8.4 节
- **执行报告**: `PHASE3_COMPLETION_REPORT.md`
- **测试文件**: `tests/unit/test_rate_limiter.py`
- **集成示例**: `tests/integration/test_rate_limiter_integration.py`

---

## 更新日志

### v1.0.0 (2026-01-29)

- ✅ 实现令牌桶算法
- ✅ 实现限流装饰器
- ✅ 支持基于用户和 IP 的限流
- ✅ 添加限流响应头
- ✅ 完成单元测试（90% 覆盖率）
- ✅ 创建使用文档

---

**联系方式**: 如有问题，请查阅相关文档或联系开发团队
