"""
仪表盘服务
负责仪表盘数据的统计和展示
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from datetime import datetime, timedelta
from app.db.database import get_db
from app.models.content import Content
from app.models.publisher import PublishLog
from app.models.account import Account
from app.models.scheduler import ScheduledTask


class DashboardService:
    """仪表盘服务"""

    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        # 账号总数
        account_count = db.query(Account).count()

        # 内容总数
        content_count = db.query(Content).count()

        # 待审核内容数
        pending_review_count = db.query(Content).filter(
            Content.review_status == "pending"
        ).count()

        # 发布成功数
        published_count = db.query(PublishLog).filter(
            PublishLog.status == "success"
        ).count()

        # 今日发布数
        today = datetime.utcnow().date()
        today_published_count = db.query(PublishLog).filter(
            func.date(PublishLog.created_at) == today,
            PublishLog.status == "success"
        ).count()

        # 本周发布数
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_published_count = db.query(PublishLog).filter(
            PublishLog.created_at >= week_ago,
            PublishLog.status == "success"
        ).count()

        # 定时任务数
        scheduled_task_count = db.query(ScheduledTask).filter(
            ScheduledTask.is_active == True
        ).count()

        return {
            "account_count": account_count,
            "content_count": content_count,
            "pending_review_count": pending_review_count,
            "published_count": published_count,
            "today_published_count": today_published_count,
            "week_published_count": week_published_count,
            "scheduled_task_count": scheduled_task_count
        }

    @staticmethod
    def get_content_trend(db: Session, days: int = 30) -> Dict[str, Any]:
        """获取内容生成趋势"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 按天统计内容创建数量
        content_trend = db.query(
            func.date(Content.created_at).label("date"),
            func.count(Content.id).label("count")
        ).filter(
            Content.created_at >= start_date
        ).group_by(
            func.date(Content.created_at)
        ).all()

        return {
            "period_days": days,
            "trend": [
                {
                    "date": str(item.date),
                    "count": item.count
                }
                for item in content_trend
            ]
        }

    @staticmethod
    def get_publish_stats(db: Session) -> Dict[str, Any]:
        """获取发布统计"""
        # 总发布数
        total_publish = db.query(PublishLog).count()

        # 成功发布数
        success_publish = db.query(PublishLog).filter(
            PublishLog.status == "success"
        ).count()

        # 失败发布数
        failed_publish = db.query(PublishLog).filter(
            PublishLog.status == "failed"
        ).count()

        # 发布成功率
        success_rate = success_publish / total_publish if total_publish > 0 else 0

        # 按平台统计
        platform_stats = db.query(
            PublishLog.platform,
            func.count(PublishLog.id).label("count")
        ).group_by(
            PublishLog.platform
        ).all()

        return {
            "total_publish": total_publish,
            "success_publish": success_publish,
            "failed_publish": failed_publish,
            "success_rate": success_rate,
            "platform_stats": [
                {
                    "platform": item.platform,
                    "count": item.count
                }
                for item in platform_stats
            ]
        }


# 全局服务实例
dashboard_service = DashboardService()
