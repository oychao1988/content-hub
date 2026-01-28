"""
发布池管理服务
负责发布池的管理和操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.models.publisher import PublishPool
from app.services.publish_pool_service import publish_pool_service


class PublishPoolManagerService:
    """发布池管理服务"""

    @staticmethod
    def get_publish_pool(db: Session) -> List[PublishPool]:
        """获取发布池列表"""
        return publish_pool_service.get_publish_pool(db)

    @staticmethod
    def add_to_pool(db: Session, content_id: int, priority: int = 5,
                    scheduled_at: datetime = None) -> PublishPool:
        """添加到发布池"""
        return publish_pool_service.add_to_pool(db, content_id, priority, scheduled_at)

    @staticmethod
    def remove_from_pool(db: Session, pool_id: int) -> bool:
        """从发布池移除"""
        return publish_pool_service.remove_from_pool(db, pool_id)

    @staticmethod
    def update_pool_entry(db: Session, pool_id: int, data: dict) -> Optional[PublishPool]:
        """更新发布池条目"""
        return publish_pool_service.update_pool_entry(db, pool_id, data)

    @staticmethod
    def get_pending_entries(db: Session) -> List[PublishPool]:
        """获取待发布条目"""
        return publish_pool_service.get_pending_entries(db)

    @staticmethod
    def start_publishing(db: Session, pool_id: int) -> Optional[PublishPool]:
        """开始发布"""
        return publish_pool_service.start_publishing(db, pool_id)

    @staticmethod
    def complete_publishing(db: Session, pool_id: int, published_log_id: int) -> Optional[PublishPool]:
        """完成发布"""
        return publish_pool_service.complete_publishing(db, pool_id, published_log_id)

    @staticmethod
    def fail_publishing(db: Session, pool_id: int, error_message: str) -> Optional[PublishPool]:
        """发布失败"""
        return publish_pool_service.fail_publishing(db, pool_id, error_message)

    @staticmethod
    def retry_publishing(db: Session, pool_id: int) -> Optional[PublishPool]:
        """重试发布"""
        return publish_pool_service.retry_publishing(db, pool_id)

    @staticmethod
    def get_pool_statistics(db: Session) -> dict:
        """获取发布池统计"""
        return publish_pool_service.get_pool_statistics(db)


# 全局服务实例
publish_pool_manager_service = PublishPoolManagerService()
