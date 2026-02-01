"""
定时任务相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.sql_db import Base


class ScheduledTask(Base):
    """定时任务模型"""

    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)

    # 任务基本信息
    name = Column(String(100), nullable=False, unique=True, comment="任务名称")
    description = Column(String(255), comment="任务描述")
    task_type = Column(String(50), nullable=False, comment="任务类型：content_generation/publishing")

    # 调度配置
    cron_expression = Column(String(50), comment="Cron 表达式")
    interval = Column(Integer, comment="间隔时间")
    interval_unit = Column(String(20), comment="间隔单位：minutes/hours/days")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_run_time = Column(DateTime(timezone=True), comment="上次运行时间")
    next_run_time = Column(DateTime(timezone=True), comment="下次运行时间")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 执行记录
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ScheduledTask(id={self.id}, name={self.name}, task_type={self.task_type})>"


class TaskExecution(Base):
    """任务执行记录"""

    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=False, index=True)

    # 执行信息
    status = Column(String(50), default="running", comment="状态：running/success/failed")
    start_time = Column(DateTime(timezone=True), server_default=func.now(), comment="开始时间")
    end_time = Column(DateTime(timezone=True), comment="结束时间")
    duration = Column(Integer, comment="执行时长（秒）")
    error_message = Column(Text, comment="错误信息")
    result = Column(JSON, comment="执行结果")

    # 关系
    task = relationship("ScheduledTask", back_populates="executions")

    def __repr__(self):
        return f"<TaskExecution(id={self.id}, task_id={self.task_id}, status={self.status})>"
