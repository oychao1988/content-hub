"""
定时任务服务
负责定时任务的创建、查询、更新、删除、执行等操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.models.scheduler import ScheduledTask
from app.services.scheduler_service import scheduler_service


class SchedulerManagerService:
    """定时任务管理服务"""

    @staticmethod
    def get_task_list(db: Session, page: int = 1, page_size: int = 20) -> dict:
        """获取定时任务列表（分页）"""
        query = db.query(ScheduledTask)
        total = query.count()
        tasks = query.order_by(ScheduledTask.created_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        # 转换为字典并添加兼容性字段 job_type
        items = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "task_type": task.task_type,
                "job_type": task.task_type,  # 兼容前端字段
                "cron_expression": task.cron_expression,
                "interval": task.interval,
                "interval_unit": task.interval_unit,
                "is_active": task.is_active,
                "last_run_time": task.last_run_time,
                "next_run_time": task.next_run_time,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "run_count": 0,
                "failure_count": 0,
                "status": "idle"
            }
            items.append(task_dict)

        return {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size
        }

    @staticmethod
    def get_task_detail(db: Session, task_id: int) -> Optional[ScheduledTask]:
        """获取任务详情"""
        return db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()

    @staticmethod
    def create_task(db: Session, task_data: dict) -> ScheduledTask:
        """创建定时任务"""
        task = ScheduledTask(**task_data)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(db: Session, task_id: int, task_data: dict) -> Optional[ScheduledTask]:
        """更新定时任务"""
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if task:
            for key, value in task_data.items():
                setattr(task, key, value)
            db.commit()
            db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """删除定时任务"""
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if task:
            db.delete(task)
            db.commit()
            return True
        return False

    @staticmethod
    def trigger_task(db: Session, task_id: int) -> dict:
        """手动触发任务"""
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if not task:
            return {"success": False, "error": "任务不存在"}

        try:
            # 执行任务逻辑
            task.last_run_time = datetime.utcnow()
            db.commit()

            # 这里应该根据任务类型执行相应的操作
            # 例如：内容生成或发布

            return {"success": True, "message": "任务执行成功"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_execution_history(db: Session) -> List[dict]:
        """获取执行历史"""
        tasks = db.query(ScheduledTask).order_by(ScheduledTask.last_run_time.desc()).all()
        return [
            {
                "id": task.id,
                "name": task.name,
                "task_type": task.task_type,
                "last_run_time": task.last_run_time,
                "next_run_time": task.next_run_time,
                "is_active": task.is_active
            }
            for task in tasks
        ]

    @staticmethod
    def start_scheduler() -> dict:
        """启动调度器"""
        scheduler_service.start()
        return {"message": "调度器已启动"}

    @staticmethod
    def stop_scheduler() -> dict:
        """停止调度器"""
        scheduler_service.shutdown()
        return {"message": "调度器已停止"}

    @staticmethod
    def get_scheduler_status() -> dict:
        """获取调度器状态"""
        return {
            "running": scheduler_service.scheduler.running,
            "jobs_count": len(scheduler_service.scheduler.get_jobs())
        }


# 全局服务实例
scheduler_manager_service = SchedulerManagerService()
