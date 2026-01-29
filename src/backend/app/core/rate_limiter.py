"""
API 限流器 - 基于令牌桶算法
支持基于用户和 IP 的限流策略
"""
import time
from typing import Dict, Optional, Callable
from functools import wraps
from fastapi import Request, HTTPException, status
from fastapi.dependencies.utils import get_dependant
from app.core.permissions import get_role_permissions


class TokenBucket:
    """令牌桶限流器实现

    使用令牌桶算法实现 API 限流：
    - 桶的容量固定（capacity）
    - 令牌按固定速率补充（refill_rate，单位：令牌/秒）
    - 请求时消费令牌，令牌不足则拒绝请求

    示例：
        bucket = TokenBucket(capacity=100, refill_rate=0.28)  # 1000次/小时
        if bucket.consume():
            # 处理请求
        else:
            # 拒绝请求（限流）
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶

        Args:
            capacity: 桶的容量（最大令牌数）
            refill_rate: 令牌补充速率（令牌/秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)  # 当前令牌数
        self.last_refill_time = time.time()  # 上次补充时间

    def _refill(self):
        """补充令牌（根据时间差计算应补充的令牌数）"""
        now = time.time()
        time_passed = now - self.last_refill_time

        # 计算应补充的令牌数
        tokens_to_add = time_passed * self.refill_rate

        # 补充令牌，不超过容量
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_time = now

    def consume(self, tokens: int = 1) -> bool:
        """
        消费令牌

        Args:
            tokens: 需要消费的令牌数，默认为 1

        Returns:
            是否成功消费令牌（True=成功，False=令牌不足）
        """
        # 先补充令牌
        self._refill()

        # 检查令牌是否足够
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_available_tokens(self) -> int:
        """
        获取当前可用令牌数

        Returns:
            当前可用令牌数
        """
        self._refill()
        return int(self.tokens)

    def get_wait_time(self, tokens: int = 1) -> float:
        """
        获取需要等待的时间（秒）才能获得足够的令牌

        Args:
            tokens: 需要的令牌数

        Returns:
            需要等待的时间（秒）
        """
        self._refill()

        if self.tokens >= tokens:
            return 0.0

        # 计算需要等待的时间
        tokens_needed = tokens - self.tokens
        wait_time = tokens_needed / self.refill_rate
        return wait_time


class RateLimiterStorage:
    """限流器存储

    使用内存存储多个限流器（按 key 分隔）
    """

    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}

    def get_bucket(self, key: str, capacity: int, refill_rate: float) -> TokenBucket:
        """
        获取或创建限流器

        Args:
            key: 限流键（用户ID、IP地址等）
            capacity: 桶的容量
            refill_rate: 令牌补充速率

        Returns:
            TokenBucket 实例
        """
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(capacity, refill_rate)
        return self._buckets[key]

    def remove_bucket(self, key: str):
        """移除限流器"""
        if key in self._buckets:
            del self._buckets[key]

    def clear(self):
        """清空所有限流器"""
        self._buckets.clear()


# 全局限流器存储实例
_global_storage = RateLimiterStorage()


# 限流配置
RATE_LIMIT_CONFIG = {
    # 默认限流：1000次/小时 (capacity=1000, refill_rate=1000/3600=0.28)
    "default": {"capacity": 1000, "refill_rate": 0.28},
    # 登录限流：10次/分钟 (capacity=10, refill_rate=10/60=0.17)
    "login": {"capacity": 10, "refill_rate": 0.17},
    # 内容生成限流：20次/小时 (capacity=20, refill_rate=20/3600=0.0056)
    "content_generate": {"capacity": 20, "refill_rate": 0.0056},
}


# 基于角色的限流配置
ROLE_RATE_LIMITS = {
    # 管理员：1000次/小时
    "admin": {"capacity": 1000, "refill_rate": 0.28},
    # 操作员：500次/小时 (capacity=500, refill_rate=500/3600=0.14)
    "operator": {"capacity": 500, "refill_rate": 0.14},
    # 客户：200次/小时 (capacity=200, refill_rate=200/3600=0.056)
    "customer": {"capacity": 200, "refill_rate": 0.056},
}


def get_client_ip(request: Request) -> str:
    """
    获取客户端 IP 地址

    Args:
        request: FastAPI 请求对象

    Returns:
        客户端 IP 地址
    """
    # 检查代理头部
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For 可能包含多个 IP，取第一个
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 使用直接连接的 IP
    if request.client:
        return request.client.host

    return "unknown"


def get_rate_limit_key(
    request: Request,
    user=None,
    key_type: str = "user",
) -> str:
    """
    获取限流键

    Args:
        request: FastAPI 请求对象
        user: 当前用户对象（可选）
        key_type: 键类型（"user" 或 "ip"）

    Returns:
        限流键
    """
    if key_type == "user" and user:
        return f"user:{user.id}"
    elif key_type == "ip":
        ip = get_client_ip(request)
        return f"ip:{ip}"
    else:
        # 回退到 IP
        ip = get_client_ip(request)
        return f"ip:{ip}"


def rate_limit(
    capacity: Optional[int] = None,
    refill_rate: Optional[float] = None,
    key_type: str = "user",
    config_name: str = "default",
):
    """
    限流装饰器

    用法：
        # 方式1：直接指定参数
        @rate_limit(capacity=100, refill_rate=0.28)
        async def endpoint():
            pass

        # 方式2：使用预定义配置
        @rate_limit(config_name="login")
        async def login():
            pass

        # 方式3：基于 IP 限流
        @rate_limit(capacity=1000, refill_rate=0.28, key_type="ip")
        async def public_endpoint():
            pass

    Args:
        capacity: 桶的容量（可选，默认使用配置）
        refill_rate: 令牌补充速率（可选，默认使用配置）
        key_type: 键类型（"user" 或 "ip"）
        config_name: 预定义配置名称

    Returns:
        装饰器函数
    """

    # 如果指定了配置名称，使用配置的参数
    if config_name in RATE_LIMIT_CONFIG and capacity is None:
        config = RATE_LIMIT_CONFIG[config_name]
        capacity = config["capacity"]
        refill_rate = config["refill_rate"]

    # 如果没有指定参数，使用默认配置
    if capacity is None:
        capacity = RATE_LIMIT_CONFIG["default"]["capacity"]
    if refill_rate is None:
        refill_rate = RATE_LIMIT_CONFIG["default"]["refill_rate"]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取 request 和 current_user
            request = kwargs.get("request")
            current_user = kwargs.get("current_user")

            # 如果没有 request，尝试从 args 中获取
            if not request and args:
                # 假设第一个参数是 request（对于依赖注入方式）
                request = args[0] if isinstance(args[0], Request) else None

            # 生成限流键
            if key_type == "user" and current_user:
                # 基于用户限流，根据角色使用不同的限流配置
                user_role = getattr(current_user, "role", "customer")
                if user_role in ROLE_RATE_LIMITS:
                    role_config = ROLE_RATE_LIMITS[user_role]
                    capacity_role = role_config["capacity"]
                    refill_rate_role = role_config["refill_rate"]
                else:
                    # 使用默认配置
                    capacity_role = capacity
                    refill_rate_role = refill_rate

                key = get_rate_limit_key(request, current_user, "user")
                bucket = _global_storage.get_bucket(key, capacity_role, refill_rate_role)
            else:
                # 基于 IP 限流
                key = get_rate_limit_key(request, None, "ip")
                bucket = _global_storage.get_bucket(key, capacity, refill_rate)

            # 尝试消费令牌
            if not bucket.consume():
                # 计算重试时间
                wait_time = bucket.get_wait_time()
                retry_after = int(wait_time) + 1

                # 添加限流响应头（如果存在 request）
                if request:
                    request.state.rate_limit = {
                        "limit": bucket.capacity,
                        "remaining": 0,
                        "reset": int(bucket.last_refill_time + (bucket.capacity / bucket.refill_rate)),
                        "retry_after": retry_after,
                    }

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(bucket.capacity),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(
                            int(bucket.last_refill_time + (bucket.capacity / bucket.refill_rate))
                        ),
                    },
                )

            # 请求成功，添加限流信息到 request.state
            if request:
                request.state.rate_limit = {
                    "limit": bucket.capacity,
                    "remaining": bucket.get_available_tokens(),
                    "reset": int(bucket.last_refill_time + (bucket.capacity / bucket.refill_rate)),
                }

            # 执行原函数
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitMiddleware:
    """限流中间件

    为所有请求添加限流响应头
    """

    async def __call__(self, request: Request, call_next):
        # 处理请求
        response = await call_next(request)

        # 如果请求中设置了限流信息，添加到响应头
        if hasattr(request.state, "rate_limit"):
            rate_limit_info = request.state.rate_limit
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])

            if "retry_after" in rate_limit_info:
                response.headers["Retry-After"] = str(rate_limit_info["retry_after"])

        return response


def get_user_rate_limit(user) -> tuple:
    """
    获取用户的限流配置

    Args:
        user: 用户对象

    Returns:
        (capacity, refill_rate) 元组
    """
    user_role = getattr(user, "role", "customer")
    if user_role in ROLE_RATE_LIMITS:
        config = ROLE_RATE_LIMITS[user_role]
        return config["capacity"], config["refill_rate"]
    else:
        # 默认配置
        default = RATE_LIMIT_CONFIG["default"]
        return default["capacity"], default["refill_rate"]
