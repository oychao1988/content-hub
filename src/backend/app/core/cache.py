"""
Redis缓存客户端

提供全局的Redis客户端实例，用于缓存操作
"""
from typing import Optional
from redis import Redis
from app.core.config import settings
from app.utils.custom_logger import log


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
