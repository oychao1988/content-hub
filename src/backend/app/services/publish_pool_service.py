"""
发布池服务
负责管理发布池和发布调度
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.models.publisher import PublishPool


class PublishPoolService:
    """发布池服务"""

    @staticmethod
    def init():
        """初始化发布池"""
        pass

    @staticmethod
    def get_publish_pool(db: Session) -> List[PublishPool]:
        """获取发布池列表"""
        return db.query(PublishPool).order_by(
            PublishPool.priority.asc(),
            PublishPool.scheduled_at.asc()
        ).all()

    @staticmethod
    def add_to_pool(db: Session, content_id: int, priority: int = 5,
                    scheduled_at: datetime = None) -> PublishPool:
        """添加到发布池"""
        entry = PublishPool(
            content_id=content_id,
            priority=priority,
            scheduled_at=scheduled_at or datetime.utcnow()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def remove_from_pool(db: Session, pool_id: int) -> bool:
        """从发布池移除"""
        entry = db.query(PublishPool).filter(PublishPool.id == pool_id).first()
        if entry:
            db.delete(entry)
            db.commit()
            return True
        return False

    @staticmethod
    def update_pool_entry(db: Session, pool_id: int, data: dict) -> Optional[PublishPool]:
        """更新发布池条目"""
        entry = db.query(PublishPool).filter(PublishPool.id == pool_id).first()
        if entry:
            for key, value in data.items():
                setattr(entry, key, value)
            db.commit()
            db.refresh(entry)
        return entry

    @staticmethod
    def get_pending_entries(db: Session) -> List[PublishPool]:
        """获取待发布条目"""
        now = datetime.utcnow()
        return db.query(PublishPool).filter(
            PublishPool.status == "pending",
            PublishPool.scheduled_at <= now
        ).order_by(
            PublishPool.priority.asc(),
            PublishPool.scheduled_at.asc()
        ).all()

    @staticmethod
    def start_publishing(db: Session, pool_id: int) -> Optional[PublishPool]:
        """开始发布"""
        entry = db.query(PublishPool).filter(PublishPool.id == pool_id).first()
        if entry:
            entry.status = "publishing"
            db.commit()
            db.refresh(entry)
        return entry

    @staticmethod
    def complete_publishing(db: Session, pool_id: int, published_log_id: int) -> Optional[PublishPool]:
        """完成发布"""
        entry = db.query(PublishPool).filter(PublishPool.id == pool_id).first()
        if entry:
            entry.status = "published"
            entry.published_at = datetime.utcnow()
            entry.published_log_id = published_log_id
            db.commit()
            db.refresh(entry)
        return entry

    @staticmethod
    def fail_publishing(db: Session, pool_id: int, error_message: str) -> Optional[PublishPool]:
        """发布失败"""
        entry = db.query(PublishPool).filter(PublishPool.id == pool_id).first()
        if entry:
            entry.status = "failed"
            entry.retry_count += 1
            entry.last_error = error_message
            db.commit()
            db.refresh(entry)
        return entry

    @staticmethod
    def retry_publishing(db: Session, pool_id: int) -> Optional[PublishPool]:
        """重试发布"""
        entry = db.query(PublishPool).filter(PublishPool.id == pool_id).first()
        if entry and entry.retry_count < entry.max_retries:
            entry.status = "pending"
            entry.scheduled_at = datetime.utcnow()
            db.commit()
            db.refresh(entry)
        return entry

    @staticmethod
    def get_pool_statistics(db: Session) -> dict:
        """获取发布池统计"""
        total = db.query(PublishPool).count()
        pending = db.query(PublishPool).filter(PublishPool.status == "pending").count()
        publishing = db.query(PublishPool).filter(PublishPool.status == "publishing").count()
        published = db.query(PublishPool).filter(PublishPool.status == "published").count()
        failed = db.query(PublishPool).filter(PublishPool.status == "failed").count()

        return {
            "total": total,
            "pending": pending,
            "publishing": publishing,
            "published": published,
            "failed": failed
        }


# 全局服务实例
publish_pool_service = PublishPoolService()
