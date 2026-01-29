from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.modules.dashboard.services import dashboard_service
from app.modules.dashboard.schemas import DashboardStats, ContentTrend, PublishStats
from app.db.database import get_db
from app.core.cache import get_cache_stats, reset_cache_stats, memory_cache
from typing import Optional

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表盘统计数据"""
    return dashboard_service.get_dashboard_stats(db)

@router.get("/content-trend", response_model=ContentTrend)
async def get_content_trend(days: Optional[int] = 30, db: Session = Depends(get_db)):
    """获取内容生成趋势"""
    return dashboard_service.get_content_trend(db, days)

@router.get("/publish-stats", response_model=PublishStats)
async def get_publish_stats(db: Session = Depends(get_db)):
    """获取发布统计"""
    return dashboard_service.get_publish_stats(db)


@router.get("/cache-stats")
async def get_cache_statistics():
    """获取缓存统计信息"""
    return get_cache_stats()


@router.post("/cache-stats/reset")
async def reset_cache_statistics():
    """重置缓存统计"""
    reset_cache_stats()
    return {"message": "缓存统计已重置"}


@router.post("/cache/clear")
async def clear_all_cache():
    """清空所有缓存"""
    memory_cache.clear()
    return {"message": "所有缓存已清空"}


@router.post("/cache/cleanup")
async def cleanup_expired_cache():
    """清理过期的缓存"""
    memory_cache.cleanup_expired()
    return {"message": "过期缓存已清理"}
