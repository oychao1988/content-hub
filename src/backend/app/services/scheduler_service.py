"""
任务调度服务（占位实现）
"""
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings


class SchedulerService:
    """任务调度服务"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()


# 全局调度器实例
scheduler_service = SchedulerService()
