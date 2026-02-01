"""
审计日志服务
"""
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.audit_log import AuditLog
from app.utils.custom_logger import log


class AuditService:
    """审计日志服务"""

    # 事件类型定义
    EVENT_TYPES = {
        # 认证相关
        "user_login": "用户登录",
        "user_logout": "用户登出",
        "user_login_failed": "用户登录失败",
        "password_change": "密码修改",
        "password_reset": "密码重置",

        # 数据操作
        "content_create": "创建内容",
        "content_update": "更新内容",
        "content_delete": "删除内容",
        "account_create": "创建账号",
        "account_update": "更新账号",
        "account_delete": "删除账号",
        "platform_create": "创建平台",
        "platform_update": "更新平台",
        "platform_delete": "删除平台",

        # 发布相关
        "content_publish": "发布内容",
        "content_publish_failed": "发布失败",
        "batch_publish": "批量发布",
        "scheduled_publish": "定时发布",

        # 配置相关
        "config_change": "配置修改",
        "writing_style_update": "写作风格更新",
        "content_theme_update": "内容主题更新",

        # 权限相关
        "role_change": "角色变更",
        "permission_change": "权限变更",
        "user_create": "创建用户",
        "user_update": "更新用户",
        "user_delete": "删除用户",

        # 系统相关
        "system_backup": "系统备份",
        "system_restore": "系统恢复",
        "data_export": "数据导出",
        "data_import": "数据导入",
    }

    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        user_id: Optional[int],
        result: str,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        记录审计事件

        :param db: 数据库会话
        :param event_type: 事件类型（如 user_login, content_create 等）
        :param user_id: 用户ID（可选，系统操作时为 None）
        :param result: 操作结果（success/failure）
        :param details: 详细信息（字典）
        :param request: FastAPI Request 对象（可选，用于提取 IP 和 User-Agent）
        :return: 创建的审计日志对象
        """
        try:
            # 提取请求信息
            ip_address = None
            user_agent = None

            if request:
                # 尝试获取真实 IP（考虑代理）
                ip_address = request.headers.get("X-Forwarded-For")
                if ip_address:
                    # 取第一个 IP（可能有多个代理）
                    ip_address = ip_address.split(",")[0].strip()
                if not ip_address:
                    ip_address = request.headers.get("X-Real-IP")
                if not ip_address:
                    ip_address = request.client.host if request.client else None

                # 获取 User-Agent
                user_agent = request.headers.get("User-Agent")

            # 创建审计日志
            audit_log = AuditLog(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                result=result,
                details=details or {}
            )

            db.add(audit_log)
            db.commit()

            log.info(
                f"Audit log created: {event_type} by user {user_id} - {result}",
                extra={"event_type": event_type}
            )

            return audit_log

        except Exception as e:
            log.error(f"Failed to create audit log: {str(e)}")
            # 不抛出异常，避免影响主业务流程
            return None

    @staticmethod
    def get_audit_logs(
        db: Session,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        查询审计日志（分页）

        :param db: 数据库会话
        :param filters: 过滤条件
            - event_type: 事件类型（可选）
            - user_id: 用户ID（可选）
            - result: 结果（success/failure，可选）
            - start_date: 开始日期（可选）
            - end_date: 结束日期（可选）
            - search: 搜索关键字（搜索 details 字段，可选）
        :param page: 页码（从 1 开始）
        :param page_size: 每页数量
        :return: 包含 logs 和 total 的字典
        """
        try:
            # 构建查询
            query = db.query(AuditLog)

            # 应用过滤条件
            if filters:
                if filters.get("event_type"):
                    query = query.filter(AuditLog.event_type == filters["event_type"])

                if filters.get("user_id"):
                    query = query.filter(AuditLog.user_id == filters["user_id"])

                if filters.get("result"):
                    query = query.filter(AuditLog.result == filters["result"])

                if filters.get("start_date"):
                    start_datetime = datetime.combine(filters["start_date"], datetime.min.time())
                    query = query.filter(AuditLog.timestamp >= start_datetime)

                if filters.get("end_date"):
                    end_datetime = datetime.combine(filters["end_date"], datetime.max.time())
                    query = query.filter(AuditLog.timestamp <= end_datetime)

                if filters.get("search"):
                    # 在 details JSON 字段中搜索
                    search_term = f"%{filters['search']}%"
                    # SQLite 的 JSON 搜索可能有限制，这里使用简单的字符串匹配
                    # 实际生产环境可能需要使用 JSON 函数或全文搜索
                    query = query.filter(
                        or_(
                            AuditLog.details.like(search_term),
                            AuditLog.ip_address.like(search_term),
                            AuditLog.user_agent.like(search_term)
                        )
                    )

            # 按时间倒序排序
            query = query.order_by(desc(AuditLog.timestamp))

            # 计算总数
            total = query.count()

            # 分页
            offset = (page - 1) * page_size
            logs = query.offset(offset).limit(page_size).all()

            return {
                "logs": logs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }

        except Exception as e:
            log.error(f"Failed to query audit logs: {str(e)}")
            raise

    @staticmethod
    def get_audit_log_by_id(db: Session, log_id: int) -> Optional[AuditLog]:
        """
        根据 ID 获取审计日志详情

        :param db: 数据库会话
        :param log_id: 日志ID
        :return: 审计日志对象或 None
        """
        try:
            return db.query(AuditLog).filter(AuditLog.id == log_id).first()
        except Exception as e:
            log.error(f"Failed to get audit log by id: {str(e)}")
            raise

    @staticmethod
    def export_audit_logs(
        db: Session,
        start_date: date,
        end_date: date,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        导出审计日志（指定日期范围）

        :param db: 数据库会话
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param filters: 额外的过滤条件（可选）
        :return: 审计日志列表（字典格式）
        """
        try:
            # 构建查询
            query = db.query(AuditLog)

            # 应用日期范围
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(
                and_(
                    AuditLog.timestamp >= start_datetime,
                    AuditLog.timestamp <= end_datetime
                )
            )

            # 应用额外过滤条件
            if filters:
                if filters.get("event_type"):
                    query = query.filter(AuditLog.event_type == filters["event_type"])

                if filters.get("user_id"):
                    query = query.filter(AuditLog.user_id == filters["user_id"])

                if filters.get("result"):
                    query = query.filter(AuditLog.result == filters["result"])

            # 按时间排序
            query = query.order_by(AuditLog.timestamp)

            # 获取所有结果
            logs = query.all()

            # 转换为字典格式
            result = []
            for log_entry in logs:
                result.append({
                    "id": log_entry.id,
                    "timestamp": log_entry.timestamp.isoformat(),
                    "event_type": log_entry.event_type,
                    "event_name": AuditService.EVENT_TYPES.get(log_entry.event_type, log_entry.event_type),
                    "user_id": log_entry.user_id,
                    "ip_address": log_entry.ip_address,
                    "user_agent": log_entry.user_agent,
                    "result": log_entry.result,
                    "details": log_entry.details,
                    "created_at": log_entry.created_at.isoformat() if log_entry.created_at else None,
                })

            log.info(f"Exported {len(result)} audit logs from {start_date} to {end_date}")
            return result

        except Exception as e:
            log.error(f"Failed to export audit logs: {str(e)}")
            raise

    @staticmethod
    def get_audit_statistics(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取审计统计信息

        :param db: 数据库会话
        :param start_date: 开始日期（可选）
        :param end_date: 结束日期（可选）
        :return: 统计信息字典
        """
        try:
            query = db.query(AuditLog)

            # 应用日期范围
            if start_date and end_date:
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                query = query.filter(
                    and_(
                        AuditLog.timestamp >= start_datetime,
                        AuditLog.timestamp <= end_datetime
                    )
                )

            # 总数统计
            total_logs = query.count()

            # 按结果统计
            success_count = query.filter(AuditLog.result == "success").count()
            failure_count = query.filter(AuditLog.result == "failure").count()

            # 按事件类型统计
            event_type_stats = db.query(
                AuditLog.event_type,
                func.count(AuditLog.id).label("count")
            ).group_by(AuditLog.event_type).all()

            # 按用户统计
            user_stats = db.query(
                AuditLog.user_id,
                func.count(AuditLog.id).label("count")
            ).group_by(AuditLog.user_id).order_by(desc("count")).limit(10).all()

            return {
                "total_logs": total_logs,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": round(success_count / total_logs * 100, 2) if total_logs > 0 else 0,
                "event_type_stats": [
                    {"event_type": et, "event_name": AuditService.EVENT_TYPES.get(et, et), "count": cnt}
                    for et, cnt in event_type_stats
                ],
                "top_users": [
                    {"user_id": uid, "count": cnt}
                    for uid, cnt in user_stats
                ]
            }

        except Exception as e:
            log.error(f"Failed to get audit statistics: {str(e)}")
            raise
