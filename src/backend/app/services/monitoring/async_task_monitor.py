"""
异步任务监控服务

收集和报告异步内容生成任务的运行指标。
"""
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.content_generation_task import ContentGenerationTask
from sqlalchemy import func
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AsyncTaskMonitor:
    """异步任务监控服务"""

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取任务指标

        Returns:
            指标字典，包含：
            - timestamp: 指标采集时间
            - total_tasks: 总任务数
            - status_counts: 各状态任务数
            - today_tasks: 今日任务数
            - today_completed: 今日完成任务数
            - success_rate: 成功率（百分比）
            - failed_rate: 失败率（百分比）
            - avg_duration_seconds: 平均执行时间（秒）
            - pending_count: 待处理任务数
            - health: 系统健康状态（healthy/warning/unhealthy）
        """
        db = SessionLocal()

        try:
            # 基础统计
            total_tasks = db.query(func.count(ContentGenerationTask.id)).scalar()

            # 按状态统计
            status_counts = {}
            for status in ['pending', 'submitted', 'processing', 'completed', 'failed', 'timeout', 'cancelled']:
                count = db.query(func.count(ContentGenerationTask.id)).filter(
                    ContentGenerationTask.status == status
                ).scalar()
                status_counts[status] = count

            # 今日任务统计
            today = datetime.utcnow().date()
            today_tasks = db.query(func.count(ContentGenerationTask.id)).filter(
                func.date(ContentGenerationTask.created_at) == today
            ).scalar()

            # 今日完成任务
            today_completed = db.query(func.count(ContentGenerationTask.id)).filter(
                func.date(ContentGenerationTask.created_at) == today,
                ContentGenerationTask.status == 'completed'
            ).scalar()

            # 成功率
            success_rate = 0
            if today_tasks > 0:
                success_rate = (today_completed / today_tasks) * 100

            # 平均执行时间（今日完成的任务）
            avg_duration = self._calculate_avg_duration(db, today)

            # 队列积压
            pending_count = status_counts.get('pending', 0) + status_counts.get('submitted', 0)

            # 失败率
            failed_rate = 0
            if today_tasks > 0:
                failed_count = status_counts.get('failed', 0) + status_counts.get('timeout', 0)
                failed_rate = (failed_count / today_tasks) * 100

            return {
                'timestamp': datetime.utcnow().isoformat(),
                'total_tasks': total_tasks,
                'status_counts': status_counts,
                'today_tasks': today_tasks,
                'today_completed': today_completed,
                'success_rate': round(success_rate, 2),
                'failed_rate': round(failed_rate, 2),
                'avg_duration_seconds': avg_duration,
                'pending_count': pending_count,
                'health': self._calculate_health(status_counts, success_rate, failed_rate)
            }

        finally:
            db.close()

    def _calculate_avg_duration(self, db: Session, date: datetime.date) -> float:
        """
        计算平均执行时间

        Args:
            db: 数据库会话
            date: 日期

        Returns:
            平均执行时间（秒）
        """
        # 获取今天完成的任务
        tasks = db.query(ContentGenerationTask).filter(
            func.date(ContentGenerationTask.created_at) == date,
            ContentGenerationTask.status == 'completed',
            ContentGenerationTask.started_at.isnot(None),
            ContentGenerationTask.completed_at.isnot(None)
        ).all()

        if not tasks:
            return 0.0

        durations = []
        for task in tasks:
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                durations.append(duration)

        return sum(durations) / len(durations) if durations else 0.0

    def _calculate_health(self, status_counts: Dict, success_rate: float, failed_rate: float) -> str:
        """
        计算系统健康状态

        Args:
            status_counts: 各状态任务数
            success_rate: 成功率
            failed_rate: 失败率

        Returns:
            健康状态：healthy/warning/unhealthy
        """
        pending_count = status_counts.get('pending', 0) + status_counts.get('submitted', 0)

        # 健康判断逻辑
        if failed_rate > 20:
            return 'unhealthy'
        elif failed_rate > 10 or pending_count > 50:
            return 'warning'
        else:
            return 'healthy'

    def get_recent_tasks(self, limit: int = 10) -> list:
        """
        获取最近的任务

        Args:
            limit: 返回数量

        Returns:
            任务列表
        """
        db = SessionLocal()

        try:
            tasks = db.query(ContentGenerationTask).order_by(
                ContentGenerationTask.created_at.desc()
            ).limit(limit).all()

            return [
                {
                    'id': task.id,
                    'task_id': task.task_id,
                    'status': task.status,
                    'topic': task.topic,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                }
                for task in tasks
            ]

        finally:
            db.close()

    def get_failed_tasks(self, limit: int = 10) -> list:
        """
        获取失败的任务

        Args:
            limit: 返回数量

        Returns:
            失败任务列表
        """
        db = SessionLocal()

        try:
            tasks = db.query(ContentGenerationTask).filter(
                ContentGenerationTask.status.in_(['failed', 'timeout'])
            ).order_by(
                ContentGenerationTask.created_at.desc()
            ).limit(limit).all()

            return [
                {
                    'id': task.id,
                    'task_id': task.task_id,
                    'status': task.status,
                    'topic': task.topic,
                    'error_message': task.error_message,
                    'retry_count': task.retry_count,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                }
                for task in tasks
            ]

        finally:
            db.close()

    def get_pending_tasks(self, limit: int = 10) -> list:
        """
        获取待处理的任务

        Args:
            limit: 返回数量

        Returns:
            待处理任务列表
        """
        db = SessionLocal()

        try:
            tasks = db.query(ContentGenerationTask).filter(
                ContentGenerationTask.status.in_(['pending', 'submitted'])
            ).order_by(
                ContentGenerationTask.priority.desc(),
                ContentGenerationTask.created_at.asc()
            ).limit(limit).all()

            return [
                {
                    'id': task.id,
                    'task_id': task.task_id,
                    'status': task.status,
                    'topic': task.topic,
                    'priority': task.priority,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                }
                for task in tasks
            ]

        finally:
            db.close()

    def get_daily_stats(self, days: int = 7) -> list:
        """
        获取每日统计

        Args:
            days: 统计天数

        Returns:
            每日统计列表
        """
        db = SessionLocal()

        try:
            stats = []
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).date()

                # 当日任务总数
                total = db.query(func.count(ContentGenerationTask.id)).filter(
                    func.date(ContentGenerationTask.created_at) == date
                ).scalar()

                # 当日完成任务数
                completed = db.query(func.count(ContentGenerationTask.id)).filter(
                    func.date(ContentGenerationTask.created_at) == date,
                    ContentGenerationTask.status == 'completed'
                ).scalar()

                # 当日失败任务数
                failed = db.query(func.count(ContentGenerationTask.id)).filter(
                    func.date(ContentGenerationTask.created_at) == date,
                    ContentGenerationTask.status.in_(['failed', 'timeout'])
                ).scalar()

                stats.append({
                    'date': date.isoformat(),
                    'total': total,
                    'completed': completed,
                    'failed': failed,
                    'success_rate': round((completed / total * 100) if total > 0 else 0, 2)
                })

            return stats[::-1]  # 按日期升序排列

        finally:
            db.close()
