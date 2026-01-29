"""
Audit module Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, date


class AuditLogCreate(BaseModel):
    """创建审计日志请求模型（内部使用）"""
    event_type: str = Field(..., description="事件类型")
    user_id: Optional[int] = Field(None, description="用户ID")
    result: str = Field(..., description="结果：success/failure")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="详细信息")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="User-Agent")

    class Config:
        schema_extra = {
            "example": {
                "event_type": "user_login",
                "user_id": 1,
                "result": "success",
                "details": {"username": "admin"},
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            }
        }


class AuditLogResponse(BaseModel):
    """审计日志响应模型"""
    id: int = Field(..., description="日志ID")
    timestamp: datetime = Field(..., description="时间戳")
    event_type: str = Field(..., description="事件类型")
    event_name: Optional[str] = Field(None, description="事件名称")
    user_id: Optional[int] = Field(None, description="用户ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="User-Agent")
    result: str = Field(..., description="结果：success/failure")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "timestamp": "2024-01-29T10:30:00",
                "event_type": "user_login",
                "event_name": "用户登录",
                "user_id": 1,
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "result": "success",
                "details": {"username": "admin"},
                "created_at": "2024-01-29T10:30:00"
            }
        }


class AuditLogListResponse(BaseModel):
    """审计日志列表响应模型"""
    logs: List[AuditLogResponse] = Field(..., description="日志列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        schema_extra = {
            "example": {
                "logs": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


class AuditLogQueryParams(BaseModel):
    """审计日志查询参数"""
    event_type: Optional[str] = Field(None, description="事件类型")
    user_id: Optional[int] = Field(None, description="用户ID")
    result: Optional[str] = Field(None, description="结果：success/failure")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    search: Optional[str] = Field(None, description="搜索关键字")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

    class Config:
        schema_extra = {
            "example": {
                "event_type": "user_login",
                "user_id": 1,
                "result": "success",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "search": "admin",
                "page": 1,
                "page_size": 20
            }
        }


class AuditLogExportRequest(BaseModel):
    """审计日志导出请求模型"""
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    event_type: Optional[str] = Field(None, description="事件类型（可选）")
    user_id: Optional[int] = Field(None, description="用户ID（可选）")
    result: Optional[str] = Field(None, description="结果（可选）")

    class Config:
        schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "event_type": "user_login",
                "user_id": 1,
                "result": "success"
            }
        }


class AuditStatisticsResponse(BaseModel):
    """审计统计响应模型"""
    total_logs: int = Field(..., description="总日志数")
    success_count: int = Field(..., description="成功数")
    failure_count: int = Field(..., description="失败数")
    success_rate: float = Field(..., description="成功率（百分比）")
    event_type_stats: List[Dict[str, Any]] = Field(..., description="事件类型统计")
    top_users: List[Dict[str, Any]] = Field(..., description="活跃用户排行")

    class Config:
        schema_extra = {
            "example": {
                "total_logs": 1000,
                "success_count": 950,
                "failure_count": 50,
                "success_rate": 95.0,
                "event_type_stats": [
                    {"event_type": "user_login", "event_name": "用户登录", "count": 500}
                ],
                "top_users": [
                    {"user_id": 1, "count": 200}
                ]
            }
        }
