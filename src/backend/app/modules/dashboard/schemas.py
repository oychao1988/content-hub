"""
仪表盘模块的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class DashboardStats(BaseModel):
    """仪表盘统计数据响应模型"""
    account_count: int = Field(..., description="账号总数")
    content_count: int = Field(..., description="内容总数")
    pending_review_count: int = Field(..., description="待审核内容数")
    published_count: int = Field(..., description="发布成功数")
    today_published_count: int = Field(..., description="今日发布数")
    week_published_count: int = Field(..., description="本周发布数")
    scheduled_task_count: int = Field(..., description="定时任务数")

    class Config:
        schema_extra = {
            "example": {
                "account_count": 5,
                "content_count": 100,
                "pending_review_count": 10,
                "published_count": 80,
                "today_published_count": 5,
                "week_published_count": 35,
                "scheduled_task_count": 3
            }
        }


class TrendItem(BaseModel):
    """趋势项模型"""
    date: str = Field(..., description="日期")
    count: int = Field(..., description="数量")

    class Config:
        schema_extra = {
            "example": {
                "date": "2023-10-01",
                "count": 5
            }
        }


class ContentTrend(BaseModel):
    """内容生成趋势响应模型"""
    period_days: int = Field(..., description="统计周期（天）")
    trend: List[TrendItem] = Field(..., description="趋势数据")

    class Config:
        schema_extra = {
            "example": {
                "period_days": 30,
                "trend": [
                    {"date": "2023-10-01", "count": 5},
                    {"date": "2023-10-02", "count": 8}
                ]
            }
        }


class PlatformStat(BaseModel):
    """平台统计模型"""
    platform: str = Field(..., description="平台名称")
    count: int = Field(..., description="发布数量")

    class Config:
        schema_extra = {
            "example": {
                "platform": "wechat",
                "count": 80
            }
        }


class PublishStats(BaseModel):
    """发布统计响应模型"""
    total_publish: int = Field(..., description="总发布数")
    success_publish: int = Field(..., description="成功发布数")
    failed_publish: int = Field(..., description="失败发布数")
    success_rate: float = Field(..., description="发布成功率")
    platform_stats: List[PlatformStat] = Field(..., description="按平台统计")

    class Config:
        schema_extra = {
            "example": {
                "total_publish": 100,
                "success_publish": 90,
                "failed_publish": 10,
                "success_rate": 0.9,
                "platform_stats": [
                    {"platform": "wechat", "count": 90}
                ]
            }
        }
