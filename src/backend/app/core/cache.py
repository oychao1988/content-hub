"""
缓存管理系统

提供内存缓存、Redis缓存和缓存装饰器
"""
from typing import Optional, Any, Callable, Dict, List
from functools import wraps, lru_cache
from datetime import datetime, timedelta
import hashlib
import json
import time

from redis import Redis
from app.core.config import settings
from app.utils.custom_logger import log


# ============================================================================
# Redis 客户端
# ============================================================================

class MockRedisClient:
    """模拟Redis客户端，用于Redis不可用时的降级"""

    def get(self, key: str) -> Optional[str]:
        """模拟get操作，总是返回None"""
        return None

    def setex(self, key: str, time: int, value: str) -> bool:
        """模拟setex操作，总是返回True"""
        return True

    def delete(self, *keys: str) -> int:
        """模拟delete操作，总是返回0"""
        return 0

    def keys(self, pattern: str) -> list:
        """模拟keys操作，总是返回空列表"""
        return []

    def ping(self) -> bool:
        """模拟ping操作，总是返回True"""
        return True

    def close(self):
        """模拟close操作"""
        pass


# 全局同步Redis客户端实例
redis_client: Redis = None


def init_redis_client():
    """初始化Redis客户端"""
    global redis_client
    try:
        redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        # 测试连接
        redis_client.ping()
        log.info("Redis客户端初始化成功")
    except Exception as e:
        log.warning(f"Redis客户端初始化失败，使用Mock客户端降级: {e}")
        # 使用mock客户端，避免应用启动失败
        redis_client = MockRedisClient()


def close_redis_client():
    """关闭Redis客户端"""
    global redis_client
    if redis_client and not isinstance(redis_client, MockRedisClient):
        try:
            redis_client.close()
            log.info("Redis客户端已关闭")
        except Exception as e:
            log.error(f"关闭Redis客户端失败: {e}")


# 自动初始化
init_redis_client()


# ============================================================================
# 内存缓存管理器
# ============================================================================

class MemoryCache:
    """内存缓存管理器（使用字典存储）"""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }

    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        if key in self._cache:
            value, expire_time = self._cache[key]
            # 检查是否过期
            if expire_time is None or datetime.now() < expire_time:
                self._stats["hits"] += 1
                return value
            else:
                # 过期，删除
                del self._cache[key]
                self._stats["misses"] += 1
                return None
        self._stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存数据

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示永不过期
        """
        expire_time = None
        if ttl is not None:
            expire_time = datetime.now() + timedelta(seconds=ttl)

        self._cache[key] = (value, expire_time)
        self._stats["sets"] += 1

    def delete(self, *keys: str) -> int:
        """
        删除缓存数据

        Args:
            *keys: 要删除的缓存键

        Returns:
            删除的数量
        """
        count = 0
        for key in keys:
            if key in self._cache:
                del self._cache[key]
                count += 1
        self._stats["deletes"] += count
        return count

    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
        log.info("内存缓存已清空")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self._stats,
            "size": len(self._cache),
            "hit_rate": round(hit_rate, 2)
        }

    def cleanup_expired(self):
        """清理过期的缓存项"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expire_time) in self._cache.items()
            if expire_time is not None and now >= expire_time
        ]
        if expired_keys:
            for key in expired_keys:
                del self._cache[key]
            log.info(f"清理了 {len(expired_keys)} 个过期缓存项")


# 全局内存缓存实例
memory_cache = MemoryCache()


# ============================================================================
# 缓存键生成
# ============================================================================

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成缓存键

    Args:
        prefix: 键前缀（如：user:profile, config:style）
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        生成的缓存键

    Examples:
        >>> generate_cache_key("user:profile", 123)
        'user:profile:123'
        >>> generate_cache_key("config:style", code="professional")
        'config:style:code:professional'
    """
    # 过滤掉 None 值
    filtered_args = [str(arg) for arg in args if arg is not None]
    filtered_kwargs = [f"{k}:{v}" for k, v in sorted(kwargs.items()) if v is not None]

    parts = [prefix] + filtered_args + filtered_kwargs
    key = ":".join(parts)

    # 如果键太长，使用哈希值
    if len(key) > 200:
        key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
        return f"{prefix}:hash:{key_hash}"

    return key


def generate_user_cache_key(user_id: int, prefix: str, *args, **kwargs) -> str:
    """
    生成用户相关的缓存键（多租户隔离）

    Args:
        user_id: 用户ID
        prefix: 键前缀
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        生成的缓存键（包含用户ID）
    """
    return generate_cache_key(f"user:{user_id}:{prefix}", *args, **kwargs)


# ============================================================================
# 缓存装饰器
# ============================================================================

def cache_query(ttl: int = 300, key_prefix: str = "query", use_user_id: bool = False):
    """
    查询结果缓存装饰器

    Args:
        ttl: 缓存过期时间（秒），默认300秒（5分钟）
        key_prefix: 缓存键前缀
        use_user_id: 是否在缓存键中包含用户ID（从kwargs中获取user_id）

    Examples:
        >>> @cache_query(ttl=600, key_prefix="accounts")
        >>> def get_accounts(db: Session, user_id: int):
        ...     return db.query(Account).all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 提取 user_id（如果需要）
            user_id = None
            if use_user_id:
                user_id = kwargs.get("user_id") or (
                    args[1] if len(args) > 1 else None
                )

            # 生成缓存键
            if user_id:
                cache_key = generate_user_cache_key(
                    user_id,
                    key_prefix,
                    *args[1:],  # 跳过 self/db 参数
                    **kwargs
                )
            else:
                cache_key = generate_cache_key(
                    key_prefix,
                    *args[1:],  # 跳过 self/db 参数
                    **kwargs
                )

            # 尝试从缓存获取
            cached_value = memory_cache.get(cache_key)
            if cached_value is not None:
                log.debug(f"缓存命中: {cache_key}")
                return cached_value

            # 缓存未命中，执行函数
            log.debug(f"缓存未命中: {cache_key}")
            result = func(*args, **kwargs)

            # 存入缓存
            memory_cache.set(cache_key, result, ttl=ttl)

            return result

        # 添加缓存失效方法
        def invalidate(*args, **kwargs):
            """失效缓存"""
            if user_id:
                cache_key = generate_user_cache_key(
                    user_id,
                    key_prefix,
                    *args[1:],
                    **kwargs
                )
            else:
                cache_key = generate_cache_key(
                    key_prefix,
                    *args[1:],
                    **kwargs
                )
            memory_cache.delete(cache_key)
            log.info(f"缓存已失效: {cache_key}")

        wrapper.cache_key_prefix = key_prefix
        wrapper.invalidate = invalidate

        return wrapper

    return decorator


def cache_config(ttl: int = 3600, key_prefix: str = "config"):
    """
    系统配置缓存装饰器（长期缓存）

    Args:
        ttl: 缓存过期时间（秒），默认3600秒（1小时）
        key_prefix: 缓存键前缀

    Examples:
        >>> @cache_config(ttl=3600, key_prefix="writing_style")
        >>> def get_writing_styles(db: Session):
        ...     return db.query(WritingStyle).all()
    """
    return cache_query(ttl=ttl, key_prefix=key_prefix, use_user_id=False)


def invalidate_cache_pattern(pattern: str):
    """
    根据模式失效缓存

    Args:
        pattern: 缓存键模式（支持通配符）
    """
    if not pattern.endswith("*"):
        pattern = f"{pattern}*"

    keys_to_delete = [
        key for key in memory_cache._cache.keys()
        if key.startswith(pattern.rstrip("*"))
    ]

    if keys_to_delete:
        memory_cache.delete(*keys_to_delete)
        log.info(f"批量失效缓存: {pattern} ({len(keys_to_delete)} 个键)")


# ============================================================================
# 缓存统计和监控
# ============================================================================

def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    return memory_cache.get_stats()


def reset_cache_stats():
    """重置缓存统计"""
    memory_cache._stats = {
        "hits": 0,
        "misses": 0,
        "sets": 0,
        "deletes": 0
    }
    log.info("缓存统计已重置")
