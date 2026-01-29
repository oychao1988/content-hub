"""
审计日志数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from app.db.database import Base


class AuditLog(Base):
    """审计日志模型"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="时间戳"
    )
    event_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="事件类型：login/logout/create/update/delete/publish/config_change等"
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="用户ID（可选，系统操作时为空）"
    )
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(255), nullable=True, comment="User-Agent")
    result = Column(String(20), nullable=False, comment="结果：success/failure")
    details = Column(JSON, nullable=True, comment="详细信息（JSON格式）")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )

    # 复合索引，优化查询性能
    __table_args__ = (
        Index("ix_audit_logs_timestamp_event_type", "timestamp", "event_type"),
        Index("ix_audit_logs_user_id_timestamp", "user_id", "timestamp"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id}, result={self.result})>"
