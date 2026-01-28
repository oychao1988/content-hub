"""
发布管理服务
负责管理发布历史、手动发布、重试发布、批量发布等操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.models.publisher import PublishLog, PublishPool
from app.services.content_publisher_service import content_publisher_service
from app.services.publish_pool_service import publish_pool_service
from app.services.batch_publish_service import batch_publish_service


class PublisherService:
    """发布管理服务"""

    @staticmethod
    def get_publish_history(db: Session) -> List[PublishLog]:
        """获取发布历史"""
        return db.query(PublishLog).order_by(PublishLog.created_at.desc()).all()

    @staticmethod
    def get_publish_detail(db: Session, log_id: int) -> Optional[PublishLog]:
        """获取发布详情"""
        return db.query(PublishLog).filter(PublishLog.id == log_id).first()

    @staticmethod
    def manual_publish(db: Session, request: dict) -> dict:
        """手动发布"""
        try:
            # 调用内容发布服务
            publish_result = content_publisher_service.publish_to_wechat(
                content_id=request["content_id"],
                account_id=request["account_id"],
                publish_to_draft=request.get("publish_to_draft", True)
            )

            # 创建发布日志
            publish_log = PublishLog(
                account_id=request["account_id"],
                content_id=request["content_id"],
                platform="wechat",
                media_id=publish_result.get("media_id"),
                status="success",
                result=str(publish_result)
            )
            db.add(publish_log)
            db.commit()
            db.refresh(publish_log)

            return {
                "success": True,
                "log_id": publish_log.id,
                "media_id": publish_result.get("media_id"),
                "message": "发布成功"
            }

        except Exception as e:
            # 记录失败日志
            publish_log = PublishLog(
                account_id=request["account_id"],
                content_id=request["content_id"],
                platform="wechat",
                status="failed",
                error_message=str(e)
            )
            db.add(publish_log)
            db.commit()

            return {
                "success": False,
                "log_id": publish_log.id,
                "error": str(e)
            }

    @staticmethod
    def retry_publish(db: Session, log_id: int) -> dict:
        """重试发布"""
        publish_log = db.query(PublishLog).filter(PublishLog.id == log_id).first()
        if not publish_log:
            return {"success": False, "error": "发布日志不存在"}

        try:
            # 调用内容发布服务
            publish_result = content_publisher_service.publish_to_wechat(
                content_id=publish_log.content_id,
                account_id=publish_log.account_id,
                publish_to_draft=True
            )

            # 更新发布日志
            publish_log.status = "success"
            publish_log.media_id = publish_result.get("media_id")
            publish_log.error_message = None
            publish_log.result = str(publish_result)
            publish_log.updated_at = datetime.utcnow()
            db.commit()

            return {
                "success": True,
                "log_id": publish_log.id,
                "media_id": publish_result.get("media_id"),
                "message": "重试发布成功"
            }

        except Exception as e:
            # 更新失败信息
            publish_log.status = "failed"
            publish_log.error_message = str(e)
            publish_log.updated_at = datetime.utcnow()
            db.commit()

            return {
                "success": False,
                "log_id": publish_log.id,
                "error": str(e)
            }

    @staticmethod
    def batch_publish(db: Session, request: dict) -> dict:
        """批量发布"""
        return batch_publish_service.process_batch_publish(
            db,
            account_id=request["account_id"],
            content_ids=request["content_ids"]
        )

    @staticmethod
    def get_publish_pool(db: Session) -> List[PublishPool]:
        """查看发布池"""
        return publish_pool_service.get_publish_pool(db)


# 全局服务实例
publisher_service = PublisherService()
