"""
内容管理服务
负责内容的创建、查询、更新、删除、审核等操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.models.content import Content
from app.services.content_creator_service import content_creator_service
from app.services.content_review_service import content_review_service


class ContentService:
    """内容管理服务"""

    @staticmethod
    def get_content_list(
        db: Session,
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """获取内容列表（分页）"""
        query = db.query(Content)
        total = query.count()
        contents = query.order_by(Content.created_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()
        return {
            "items": contents,
            "total": total,
            "page": page,
            "pageSize": page_size
        }

    @staticmethod
    def get_content_detail(db: Session, content_id: int) -> Optional[Content]:
        """获取内容详情"""
        return db.query(Content).filter(Content.id == content_id).first()

    @staticmethod
    def create_content(db: Session, request: dict, account_id: int) -> Content:
        """创建内容（直接创建）"""
        try:
            # 创建内容记录
            content = Content(
                account_id=account_id,
                title=request["title"],
                content_type=request["content_type"],
                content=request["content"],
                summary=request.get("summary"),
                publish_status=request.get("status", "draft"),
                tags=request.get("tags", []),
                cover_image=request.get("cover_image"),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            db.add(content)
            db.commit()
            db.refresh(content)
            return content

        except Exception as e:
            raise Exception(f"内容创建失败: {str(e)}")

    @staticmethod
    def update_content(db: Session, content_id: int, content_data: dict) -> Optional[Content]:
        """更新内容"""
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            for key, value in content_data.items():
                setattr(content, key, value)
            db.commit()
            db.refresh(content)
        return content

    @staticmethod
    def delete_content(db: Session, content_id: int) -> bool:
        """删除内容"""
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            db.delete(content)
            db.commit()
            return True
        return False

    @staticmethod
    def submit_for_review(db: Session, content_id: int) -> Optional[Content]:
        """提交审核"""
        return content_review_service.submit_for_review(db, content_id)

    @staticmethod
    def approve_content(db: Session, content_id: int, reviewer_id: int = None) -> Optional[Content]:
        """审核通过"""
        return content_review_service.approve_content(db, content_id, reviewer_id)

    @staticmethod
    def reject_content(db: Session, content_id: int, reason: str, reviewer_id: int = None) -> Optional[Content]:
        """审核拒绝"""
        return content_review_service.reject_content(db, content_id, reason, reviewer_id)

    @staticmethod
    def get_pending_reviews(db: Session) -> List[Content]:
        """获取待审核列表"""
        return content_review_service.get_pending_reviews(db)

    @staticmethod
    def auto_review_content(db: Session, content_id: int) -> Optional[Content]:
        """自动审核内容"""
        return content_review_service.auto_review_content(db, content_id)

    @staticmethod
    def get_review_statistics(db: Session) -> dict:
        """获取审核统计信息"""
        return content_review_service.get_review_statistics(db)


# 全局服务实例
content_service = ContentService()
