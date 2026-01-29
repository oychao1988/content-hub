"""
API 限流器单元测试
测试令牌桶算法、限流装饰器和基于用户/IP的限流策略
"""
import time
import pytest
from unittest.mock import Mock, MagicMock
from fastapi import Request, HTTPException
from starlette.datastructures import Headers

from app.core.rate_limiter import (
    TokenBucket,
    RateLimiterStorage,
    get_client_ip,
    get_rate_limit_key,
    rate_limit,
    RATE_LIMIT_CONFIG,
    ROLE_RATE_LIMITS,
    get_user_rate_limit,
)


class TestTokenBucket:
    """测试 TokenBucket 类"""

    def test_init(self):
        """测试令牌桶初始化"""
        bucket = TokenBucket(capacity=100, refill_rate=0.28)
        assert bucket.capacity == 100
        assert bucket.refill_rate == 0.28
        assert bucket.tokens == 100.0
        assert bucket.last_refill_time > 0

    def test_consume_success(self):
        """测试成功消费令牌"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.consume(1) is True
        assert bucket.get_available_tokens() == 9

    def test_consume_multiple(self):
        """测试消费多个令牌"""
        bucket = TokenBucket(capacity=100, refill_rate=1.0)
        assert bucket.consume(50) is True
        assert bucket.get_available_tokens() == 50

    def test_consume_insufficient_tokens(self):
        """测试令牌不足时消费失败"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        # 消费所有令牌
        assert bucket.consume(10) is True
        # 再次消费应该失败
        assert bucket.consume(1) is False

    def test_refill(self):
        """测试令牌补充"""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10令牌/秒

        # 消费所有令牌
        bucket.consume(10)
        assert bucket.get_available_tokens() == 0

        # 等待0.1秒，应该补充1个令牌
        time.sleep(0.1)
        assert bucket.consume(1) is True

    def test_refill_not_exceed_capacity(self):
        """测试令牌补充不超过容量"""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)

        # 等待1秒，应该补充到容量
        time.sleep(1)
        assert bucket.get_available_tokens() == 10

    def test_get_wait_time(self):
        """测试获取等待时间"""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10令牌/秒

        # 消费所有令牌
        bucket.consume(10)

        # 获取1个令牌需要等待约0.1秒
        wait_time = bucket.get_wait_time(1)
        assert 0.09 <= wait_time <= 0.12

        # 获取10个令牌需要等待约1秒
        wait_time = bucket.get_wait_time(10)
        assert 0.95 <= wait_time <= 1.05

    def test_get_wait_time_sufficient_tokens(self):
        """测试令牌充足时等待时间为0"""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)
        wait_time = bucket.get_wait_time(5)
        assert wait_time == 0.0


class TestRateLimiterStorage:
    """测试 RateLimiterStorage 类"""

    def test_get_and_create_bucket(self):
        """测试获取和创建限流器"""
        storage = RateLimiterStorage()
        bucket1 = storage.get_bucket("key1", capacity=100, refill_rate=0.28)
        bucket2 = storage.get_bucket("key1", capacity=100, refill_rate=0.28)

        # 应该返回同一个实例
        assert bucket1 is bucket2
        assert bucket1.capacity == 100

    def test_different_keys(self):
        """测试不同的键创建不同的限流器"""
        storage = RateLimiterStorage()
        bucket1 = storage.get_bucket("key1", capacity=100, refill_rate=0.28)
        bucket2 = storage.get_bucket("key2", capacity=200, refill_rate=0.56)

        # 应该是不同的实例
        assert bucket1 is not bucket2
        assert bucket1.capacity == 100
        assert bucket2.capacity == 200

    def test_remove_bucket(self):
        """测试移除限流器"""
        storage = RateLimiterStorage()
        storage.get_bucket("key1", capacity=100, refill_rate=0.28)
        storage.remove_bucket("key1")

        # 再次获取应该创建新的实例
        bucket1 = storage.get_bucket("key1", capacity=100, refill_rate=0.28)
        assert bucket1.tokens == 100.0

    def test_clear(self):
        """测试清空所有限流器"""
        storage = RateLimiterStorage()
        storage.get_bucket("key1", capacity=100, refill_rate=0.28)
        storage.get_bucket("key2", capacity=200, refill_rate=0.56)

        storage.clear()

        # 存储应该为空
        assert len(storage._buckets) == 0


class TestGetClientIP:
    """测试获取客户端IP地址"""

    def test_get_ip_from_x_forwarded_for(self):
        """测试从X-Forwarded-For获取IP"""
        request = Mock(spec=Request)
        request.headers = Headers({"x-forwarded-for": "192.168.1.1, 192.168.1.2"})
        request.client = None

        ip = get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_get_ip_from_x_real_ip(self):
        """测试从X-Real-IP获取IP"""
        request = Mock(spec=Request)
        request.headers = Headers({"x-real-ip": "192.168.1.3"})
        request.client = None

        ip = get_client_ip(request)
        assert ip == "192.168.1.3"

    def test_get_ip_from_client(self):
        """测试从client获取IP"""
        request = Mock(spec=Request)
        request.headers = Headers({})
        request.client = Mock(host="192.168.1.4")

        ip = get_client_ip(request)
        assert ip == "192.168.1.4"

    def test_get_ip_unknown(self):
        """测试无法获取IP时返回unknown"""
        request = Mock(spec=Request)
        request.headers = Headers({})
        request.client = None

        ip = get_client_ip(request)
        assert ip == "unknown"


class TestGetRateLimitKey:
    """测试获取限流键"""

    def test_user_key(self):
        """测试基于用户的限流键"""
        request = Mock(spec=Request)
        user = Mock(id=123)

        key = get_rate_limit_key(request, user, "user")
        assert key == "user:123"

    def test_ip_key(self):
        """测试基于IP的限流键"""
        request = Mock(spec=Request)
        request.headers = Headers({"x-forwarded-for": "192.168.1.1"})
        request.client = None

        key = get_rate_limit_key(request, None, "ip")
        assert key == "ip:192.168.1.1"

    def test_fallback_to_ip(self):
        """测试回退到IP限流"""
        request = Mock(spec=Request)
        request.headers = Headers({"x-forwarded-for": "192.168.1.1"})
        request.client = None

        # 当 key_type="user" 但没有提供 user 时，应该回退到 IP
        key = get_rate_limit_key(request, None, "user")
        assert key == "ip:192.168.1.1"


class TestRateLimitDecorator:
    """测试限流装饰器"""

    @pytest.mark.asyncio
    async def test_rate_limit_allow_request(self):
        """测试允许请求通过"""
        # 创建模拟的请求和用户
        request = Mock(spec=Request)
        request.headers = Headers({})
        request.client = Mock(host="192.168.1.1")
        request.state = Mock()

        user = Mock(id=100, role="admin")

        # 创建限流装饰器
        @rate_limit(capacity=100, refill_rate=0.28, key_type="user")
        async def test_endpoint(request=Mock(), current_user=Mock()):
            return {"status": "ok"}

        # 调用端点
        result = await test_endpoint(request=request, current_user=user)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_rate_limit_block_request(self):
        """测试阻止请求（超过限流）"""
        # 清空全局存储
        from app.core.rate_limiter import _global_storage
        _global_storage.clear()

        # 创建模拟的请求和用户
        request = Mock(spec=Request)
        request.headers = Headers({})
        request.client = Mock(host="192.168.1.1")
        request.state = Mock()

        # 使用未知角色，这样会使用装饰器中指定的容量
        user = Mock(id=101, role="unknown")

        # 创建限流装饰器（容量很小，容易触发限流）
        @rate_limit(capacity=5, refill_rate=0.01, key_type="user")
        async def test_endpoint(request=Mock(), current_user=Mock()):
            return {"status": "ok"}

        # 连续调用超过容量
        for _ in range(5):
            await test_endpoint(request=request, current_user=user)

        # 第6次调用应该被限流
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint(request=request, current_user=user)

        assert exc_info.value.status_code == 429
        assert "请求过于频繁" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_rate_limit_by_ip(self):
        """测试基于IP的限流"""
        # 清空全局存储
        from app.core.rate_limiter import _global_storage
        _global_storage.clear()

        request = Mock(spec=Request)
        request.headers = Headers({"x-forwarded-for": "192.168.1.1"})
        request.client = None
        request.state = Mock()

        # 创建限流装饰器（基于IP）
        @rate_limit(capacity=5, refill_rate=0.01, key_type="ip")
        async def test_endpoint(request=Mock()):
            return {"status": "ok"}

        # 连续调用超过容量
        for _ in range(5):
            await test_endpoint(request=request)

        # 第6次调用应该被限流
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint(request=request)

        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limit_config_name(self):
        """测试使用预定义配置"""
        # 清空全局存储
        from app.core.rate_limiter import _global_storage
        _global_storage.clear()

        request = Mock(spec=Request)
        request.headers = Headers({})
        request.client = Mock(host="192.168.1.1")
        request.state = Mock()

        # 使用未知角色，这样会使用配置中指定的容量
        user = Mock(id=102, role="unknown")

        # 使用登录限流配置
        @rate_limit(config_name="login", key_type="user")
        async def test_endpoint(request=Mock(), current_user=Mock()):
            return {"status": "ok"}

        # 连续调用超过容量
        for _ in range(10):
            await test_endpoint(request=request, current_user=user)

        # 第11次调用应该被限流
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint(request=request, current_user=user)

        assert exc_info.value.status_code == 429


class TestRoleRateLimits:
    """测试基于角色的限流配置"""

    def test_admin_rate_limit(self):
        """测试管理员限流配置"""
        config = ROLE_RATE_LIMITS["admin"]
        assert config["capacity"] == 1000
        assert config["refill_rate"] == 0.28  # 1000次/小时

    def test_operator_rate_limit(self):
        """测试操作员限流配置"""
        config = ROLE_RATE_LIMITS["operator"]
        assert config["capacity"] == 500
        assert config["refill_rate"] == 0.14  # 500次/小时

    def test_customer_rate_limit(self):
        """测试客户限流配置"""
        config = ROLE_RATE_LIMITS["customer"]
        assert config["capacity"] == 200
        assert config["refill_rate"] == 0.056  # 200次/小时

    def test_get_user_rate_limit_admin(self):
        """测试获取管理员限流配置"""
        user = Mock(id=123, role="admin")
        capacity, refill_rate = get_user_rate_limit(user)
        assert capacity == 1000
        assert refill_rate == 0.28

    def test_get_user_rate_limit_operator(self):
        """测试获取操作员限流配置"""
        user = Mock(id=123, role="operator")
        capacity, refill_rate = get_user_rate_limit(user)
        assert capacity == 500
        assert refill_rate == 0.14

    def test_get_user_rate_limit_customer(self):
        """测试获取客户限流配置"""
        user = Mock(id=123, role="customer")
        capacity, refill_rate = get_user_rate_limit(user)
        assert capacity == 200
        assert refill_rate == 0.056

    def test_get_user_rate_limit_unknown_role(self):
        """测试未知角色使用默认配置"""
        user = Mock(id=123, role="unknown")
        capacity, refill_rate = get_user_rate_limit(user)
        # 应该使用默认配置
        default = RATE_LIMIT_CONFIG["default"]
        assert capacity == default["capacity"]
        assert refill_rate == default["refill_rate"]


class TestRateLimitConfigs:
    """测试限流配置"""

    def test_default_config(self):
        """测试默认限流配置"""
        config = RATE_LIMIT_CONFIG["default"]
        assert config["capacity"] == 1000
        assert config["refill_rate"] == 0.28  # 1000次/小时

    def test_login_config(self):
        """测试登录限流配置"""
        config = RATE_LIMIT_CONFIG["login"]
        assert config["capacity"] == 10
        assert config["refill_rate"] == 0.17  # 10次/分钟

    def test_content_generate_config(self):
        """测试内容生成限流配置"""
        config = RATE_LIMIT_CONFIG["content_generate"]
        assert config["capacity"] == 20
        assert config["refill_rate"] == 0.0056  # 20次/小时


class TestTokenBucketRecovery:
    """测试令牌桶恢复机制"""

    def test_tokens_recover_over_time(self):
        """测试令牌随时间恢复"""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10令牌/秒

        # 消费所有令牌
        bucket.consume(10)
        assert bucket.get_available_tokens() == 0

        # 等待0.5秒，应该恢复5个令牌
        time.sleep(0.5)
        available = bucket.get_available_tokens()
        assert 4 <= available <= 6  # 考虑时间误差

    def test_refill_rate_accuracy(self):
        """测试补充速率的准确性"""
        bucket = TokenBucket(capacity=100, refill_rate=100.0)  # 100令牌/秒

        # 消费所有令牌
        bucket.consume(100)
        assert bucket.get_available_tokens() == 0

        # 等待1秒，应该恢复100个令牌（达到容量）
        time.sleep(1)
        assert bucket.get_available_tokens() == 100


class TestRateLimitWithDifferentRoles:
    """测试不同角色的限流"""

    @pytest.mark.asyncio
    async def test_admin_has_higher_limit(self):
        """测试管理员有更高的限流"""
        request = Mock(spec=Request)
        request.headers = Headers({})
        request.client = Mock(host="192.168.1.1")
        request.state = Mock()

        admin = Mock(id=1, role="admin")
        customer = Mock(id=2, role="customer")

        @rate_limit(key_type="user")
        async def test_endpoint(request=Mock(), current_user=Mock()):
            return {"status": "ok"}

        # 管理员可以发起更多请求
        admin_success_count = 0
        for _ in range(1000):
            try:
                await test_endpoint(request=request, current_user=admin)
                admin_success_count += 1
            except HTTPException:
                break

        # 客户的限流更严格
        customer_success_count = 0
        for _ in range(300):
            try:
                await test_endpoint(request=request, current_user=customer)
                customer_success_count += 1
            except HTTPException:
                break

        # 管理员的请求次数应该远多于客户
        assert admin_success_count > customer_success_count
        assert admin_success_count >= 1000  # 管理员限额
        assert customer_success_count >= 200  # 客户限额


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
