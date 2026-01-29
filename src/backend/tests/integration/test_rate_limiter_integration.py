"""
API 限流功能集成测试示例
演示如何在 API 端点中使用限流装饰器
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.main import app
from app.core.rate_limiter import _global_storage


def test_login_rate_limit_integration():
    """
    集成测试：登录接口限流
    演示如何为登录端点添加限流
    """
    # 清空全局存储
    _global_storage.clear()

    client = TestClient(app)

    # 模拟登录请求（这里需要替换为实际的登录端点）
    # 示例代码（假设有登录端点）：
    # for i in range(11):  # 超过登录限流（10次/分钟）
    #     response = client.post("/api/v1/auth/login", json={
    #         "email": "test@example.com",
    #         "password": "password"
    #     })
    #     if i < 10:
    #         assert response.status_code in [200, 401]  # 允许的请求
    #     else:
    #         assert response.status_code == 429  # 被限流

    # 注意：实际使用时，需要在登录端点添加限流装饰器
    # 示例：
    # @router.post("/login")
    # @rate_limit(config_name="login", key_type="ip")
    # async def login(...):
    #     pass


def test_content_generation_rate_limit_integration():
    """
    集成测试：内容生成接口限流
    演示如何为内容生成端点添加限流
    """
    # 清空全局存储
    _global_storage.clear()

    # 注意：实际使用时，需要在内容生成端点添加限流装饰器
    # 示例：
    # @router.post("/generate")
    # @rate_limit(config_name="content_generate", key_type="user")
    # async def generate_content(
    #     request: Request,
    #     payload: ContentGenerateRequest,
    #     current_user: User = Depends(get_current_user)
    # ):
    #     pass


def test_custom_rate_limit_integration():
    """
    集成测试：自定义限流配置
    演示如何为特定端点使用自定义限流配置
    """
    # 清空全局存储
    _global_storage.clear()

    # 示例：发布接口使用自定义限流（50次/小时）
    # @router.post("/publish")
    # @rate_limit(capacity=50, refill_rate=0.014, key_type="user")
    # async def publish_content(
    #     request: Request,
    #     payload: PublishRequest,
    #     current_user: User = Depends(get_current_user)
    # ):
    #     pass


def test_rate_limit_response_headers():
    """
    集成测试：限流响应头
    验证限流响应头是否正确设置
    """
    # 清空全局存储
    _global_storage.clear()

    # 示例：验证响应头
    # response = client.get("/api/v1/content")
    # assert "X-RateLimit-Limit" in response.headers
    # assert "X-RateLimit-Remaining" in response.headers
    # assert "X-RateLimit-Reset" in response.headers

    # 当被限流时：
    # assert response.status_code == 429
    # assert "Retry-After" in response.headers
    # assert response.headers["X-RateLimit-Remaining"] == "0"


# 使用示例文档
"""
## API 限流使用示例

### 1. 基于用户的限流（推荐用于需要认证的接口）

\`\`\`python
from fastapi import APIRouter, Depends, Request
from app.modules.shared.deps import get_current_user
from app.core.rate_limiter import rate_limit

router = APIRouter()

@router.get("/content")
@rate_limit(key_type="user")  # 根据用户角色自动应用限流
async def get_content(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # 管理员: 1000次/小时
    # 操作员: 500次/小时
    # 客户: 200次/小时
    pass
\`\`\`

### 2. 使用预定义配置

\`\`\`python
@router.post("/login")
@rate_limit(config_name="login", key_type="ip")  # 10次/分钟，基于IP
async def login(request: Request, credentials: LoginSchema):
    pass

@router.post("/content/generate")
@rate_limit(config_name="content_generate", key_type="user")  # 20次/小时
async def generate_content(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    pass
\`\`\`

### 3. 自定义限流参数

\`\`\`python
@router.post("/publish")
@rate_limit(capacity=50, refill_rate=0.014, key_type="user")  # 50次/小时
async def publish_content(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    pass
\`\`\`

### 4. 基于 IP 的限流（推荐用于公开接口）

\`\`\`python
@router.post("/public/endpoint")
@rate_limit(capacity=100, refill_rate=0.28, key_type="ip")  # 1000次/小时
async def public_endpoint(request: Request):
    pass
\`\`\`

## 限流配置

### 预定义配置（app/core/rate_limiter.py）

\`\`\`python
RATE_LIMIT_CONFIG = {
    "default": {"capacity": 1000, "refill_rate": 0.28},        # 1000次/小时
    "login": {"capacity": 10, "refill_rate": 0.17},            # 10次/分钟
    "content_generate": {"capacity": 20, "refill_rate": 0.0056}  # 20次/小时
}

ROLE_RATE_LIMITS = {
    "admin": {"capacity": 1000, "refill_rate": 0.28},    # 1000次/小时
    "operator": {"capacity": 500, "refill_rate": 0.14},  # 500次/小时
    "customer": {"capacity": 200, "refill_rate": 0.056}  # 200次/小时
}
\`\`\`

## 响应头

成功请求的响应头：
\`\`\`
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1706456400
\`\`\`

被限流时的响应头（HTTP 429）：
\`\`\`
Retry-After: 60
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706456400
\`\`\`

## 错误处理

当请求被限流时，返回 429 状态码：
\`\`\`json
{
  "detail": "请求过于频繁，请在 60 秒后重试"
}
\`\`\`
"""
