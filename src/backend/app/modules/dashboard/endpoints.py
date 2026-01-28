from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.modules.dashboard.services import dashboard_service
from app.modules.dashboard.schemas import DashboardStats, ContentTrend, PublishStats
from app.db.database import get_db
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
