"""
内容审核服务
负责内容审核流程
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.models.content import Content


class ContentReviewService:
    """内容审核服务"""

    @staticmethod
    def init():
        """初始化审核服务"""
        pass

    @staticmethod
    def get_pending_reviews(db: Session) -> List[Content]:
        """获取待审核内容列表"""
        return db.query(Content).filter(
            Content.review_status == "pending"
        ).order_by(Content.created_at.desc()).all()

    @staticmethod
    def submit_for_review(db: Session, content_id: int) -> Optional[Content]:
        """提交审核"""
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            content.review_status = "reviewing"
            db.commit()
            db.refresh(content)
        return content

    @staticmethod
    def approve_content(db: Session, content_id: int, reviewer_id: int = None) -> Optional[Content]:
        """审核通过"""
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            content.review_status = "approved"
            content.status = "approved"
            content.reviewed_at = datetime.utcnow()
            content.reviewed_by = reviewer_id
            db.commit()
            db.refresh(content)
        return content

    @staticmethod
    def reject_content(db: Session, content_id: int, reason: str, reviewer_id: int = None) -> Optional[Content]:
        """审核拒绝"""
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            content.review_status = "rejected"
            content.status = "rejected"
            content.reviewed_at = datetime.utcnow()
            content.reviewed_by = reviewer_id
            content.review_comment = reason
            db.commit()
            db.refresh(content)
        return content

    @staticmethod
    def auto_review_content(db: Session, content_id: int) -> Optional[Content]:
        """自动审核内容"""
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            # 简单的自动审核逻辑：检查字数和内容质量
            if content.word_count and content.word_count >= 500:
                content.review_status = "approved"
                content.status = "approved"
                content.reviewed_at = datetime.utcnow()
            else:
                content.review_status = "rejected"
                content.status = "rejected"
                content.reviewed_at = datetime.utcnow()
                content.review_comment = "内容字数不足"
            db.commit()
            db.refresh(content)
        return content

    @staticmethod
    def get_review_history(db: Session, content_id: int) -> Optional[Content]:
        """获取审核历史"""
        return db.query(Content).filter(Content.id == content_id).first()

    @staticmethod
    def batch_review(db: Session, content_ids: List[int], action: str,
                     reason: str = None, reviewer_id: int = None) -> dict:
        """批量审核"""
        processed = 0
        succeeded = 0
        failed = 0

        for content_id in content_ids:
            try:
                if action == "approve":
                    ContentReviewService.approve_content(db, content_id, reviewer_id)
                    succeeded += 1
                elif action == "reject":
                    ContentReviewService.reject_content(db, content_id, reason, reviewer_id)
                    succeeded += 1
            except Exception:
                failed += 1
            processed += 1

        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed
        }

    @staticmethod
    def get_review_statistics(db: Session) -> dict:
        """获取审核统计信息"""
        total = db.query(Content).count()
        pending = db.query(Content).filter(Content.review_status == "pending").count()
        reviewing = db.query(Content).filter(Content.review_status == "reviewing").count()
        approved = db.query(Content).filter(Content.review_status == "approved").count()
        rejected = db.query(Content).filter(Content.review_status == "rejected").count()

        return {
            "total": total,
            "pending": pending,
            "reviewing": reviewing,
            "approved": approved,
            "rejected": rejected
        }


# 全局服务实例
content_review_service = ContentReviewService()
