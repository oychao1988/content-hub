"""
System module Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class HealthResponse(BaseModel):
    """系统健康检查响应模型"""
    status: str = Field(..., description="健康状态：healthy/degraded/unhealthy")
    version: str = Field(..., description="应用版本")
    uptime: float = Field(..., description="运行时间（秒）")
    database: str = Field(..., description="数据库状态")
    services: Dict[str, str] = Field(default_factory=dict, description="外部服务状态")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.5,
                "database": "connected",
                "services": {
                    "redis": "connected",
                    "content_publisher": "connected",
                    "content_creator": "available"
                }
            }
        }


class SystemInfoResponse(BaseModel):
    """系统信息响应模型"""
    version: str = Field(..., description="应用版本")
    python_version: str = Field(..., description="Python 版本")
    environment: str = Field(..., description="运行环境：development/production")
    platform: str = Field(..., description="操作系统平台")
    app_name: str = Field(..., description="应用名称")
    debug_mode: bool = Field(..., description="调试模式")

    class Config:
        schema_extra = {
            "example": {
                "version": "1.0.0",
                "python_version": "3.11.0",
                "environment": "development",
                "platform": "Linux-5.15.0-x86_64",
                "app_name": "ContentHub",
                "debug_mode": True
            }
        }


class MetricsResponse(BaseModel):
    """系统指标响应模型"""
    requests_total: int = Field(..., description="请求总数")
    requests_per_minute: float = Field(..., description="每分钟请求数")
    active_users: int = Field(..., description="活跃用户数")
    cache_stats: Dict[str, Any] = Field(..., description="缓存统计信息")
    uptime: float = Field(..., description="运行时间（秒）")

    class Config:
        schema_extra = {
            "example": {
                "requests_total": 15420,
                "requests_per_minute": 45.5,
                "active_users": 12,
                "cache_stats": {
                    "hits": 8920,
                    "misses": 1205,
                    "hit_rate": 88.1,
                    "size": 245
                },
                "uptime": 86400.0
            }
        }
