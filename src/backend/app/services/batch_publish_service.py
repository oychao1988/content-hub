"""
批量发布服务
负责处理批量发布任务
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.models.publisher import PublishPool, PublishLog
from app.models.content import Content
from app.services.content_publisher_service import content_publisher_service
from app.services.publish_pool_service import publish_pool_service


class BatchPublishService:
    """批量发布服务"""

    @staticmethod
    def process_batch_publish(db: Session, account_id: int, content_ids: List[int]) -> dict:
        """
        处理批量发布任务
        :param db: 数据库会话
        :param account_id: 账号 ID
        :param content_ids: 内容 ID 列表
        :return: 发布结果
        """
        results = []
        success_count = 0
        fail_count = 0

        for content_id in content_ids:
            try:
                # 获取内容信息
                content = db.query(Content).filter(
                    Content.id == content_id,
                    Content.account_id == account_id
                ).first()

                if not content:
                    results.append({
                        "content_id": content_id,
                        "success": False,
                        "error": "内容不存在"
                    })
                    fail_count += 1
                    continue

                # 检查内容状态
                if content.review_status not in ["approved"]:
                    results.append({
                        "content_id": content_id,
                        "success": False,
                        "error": f"内容状态不正确：{content.review_status}"
                    })
                    fail_count += 1
                    continue

                # 查找或创建发布日志
                publish_log = db.query(PublishLog).filter(
                    PublishLog.content_id == content_id
                ).first()

                if not publish_log:
                    # 创建新发布日志
                    publish_log = PublishLog(
                        account_id=account_id,
                        content_id=content_id,
                        platform="wechat",
                        status="pending"
                    )
                    db.add(publish_log)
                    db.commit()
                    db.refresh(publish_log)

                # 添加到发布池
                pool_entry = publish_pool_service.add_to_pool(
                    db,
                    content_id=content_id,
                    priority=5,
                    scheduled_at=datetime.utcnow()
                )

                # 发布到微信公众号
                publish_result = content_publisher_service.publish_to_wechat(
                    content_id=content_id,
                    account_id=account_id,
                    publish_to_draft=True
                )

                # 更新发布日志
                publish_log.status = "success"
                publish_log.media_id = publish_result.get("media_id")
                publish_log.result = str(publish_result)
                db.commit()

                # 更新发布池状态
                publish_pool_service.complete_publishing(
                    db,
                    pool_id=pool_entry.id,
                    published_log_id=publish_log.id
                )

                # 更新内容状态
                content.publish_status = "published"
                content.published_at = datetime.utcnow()
                db.commit()

                results.append({
                    "content_id": content_id,
                    "success": True,
                    "media_id": publish_result.get("media_id"),
                    "published_at": datetime.utcnow().isoformat()
                })
                success_count += 1

            except Exception as e:
                results.append({
                    "content_id": content_id,
                    "success": False,
                    "error": str(e)
                })
                fail_count += 1

        return {
            "total": len(content_ids),
            "success": success_count,
            "fail": fail_count,
            "results": results
        }

    @staticmethod
    def process_scheduled_batch_publish(db: Session) -> dict:
        """
        处理定时批量发布任务
        :param db: 数据库会话
        :return: 发布结果
        """
        # 获取所有待发布的内容
        pending_entries = publish_pool_service.get_pending_entries(db)
        if not pending_entries:
            return {
                "total": 0,
                "success": 0,
                "fail": 0,
                "results": []
            }

        # 按账号分组处理
        account_entries = {}
        for entry in pending_entries:
            content = db.query(Content).filter(Content.id == entry.content_id).first()
            if content:
                if content.account_id not in account_entries:
                    account_entries[content.account_id] = []
                account_entries[content.account_id].append(entry.content_id)

        # 处理每个账号的批量发布
        all_results = []
        total_success = 0
        total_fail = 0

        for account_id, content_ids in account_entries.items():
            result = BatchPublishService.process_batch_publish(db, account_id, content_ids)
            all_results.extend(result["results"])
            total_success += result["success"]
            total_fail += result["fail"]

        return {
            "total": total_success + total_fail,
            "success": total_success,
            "fail": total_fail,
            "results": all_results
        }

    @staticmethod
    def get_batch_publish_history(db: Session, account_id: int, limit: int = 100) -> List[dict]:
        """
        获取批量发布历史记录
        :param db: 数据库会话
        :param account_id: 账号 ID
        :param limit: 限制数量
        :return: 历史记录
        """
        logs = db.query(PublishLog).filter(
            PublishLog.account_id == account_id
        ).order_by(PublishLog.created_at.desc()).limit(limit).all()

        return [
            {
                "id": log.id,
                "content_id": log.content_id,
                "status": log.status,
                "platform": log.platform,
                "media_id": log.media_id,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat(),
                "updated_at": log.updated_at.isoformat()
            }
            for log in logs
        ]

    @staticmethod
    def get_batch_publish_statistics(db: Session, account_id: int) -> dict:
        """
        获取批量发布统计信息
        :param db: 数据库会话
        :param account_id: 账号 ID
        :return: 统计信息
        """
        total = db.query(PublishLog).filter(PublishLog.account_id == account_id).count()
        success = db.query(PublishLog).filter(
            PublishLog.account_id == account_id,
            PublishLog.status == "success"
        ).count()
        failed = db.query(PublishLog).filter(
            PublishLog.account_id == account_id,
            PublishLog.status == "failed"
        ).count()

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0
        }


# 全局服务实例
batch_publish_service = BatchPublishService()
