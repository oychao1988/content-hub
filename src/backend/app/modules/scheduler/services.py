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

        # 动态添加到调度器（如果任务已启用）
        if task.is_active:
            try:
                # 使用独立的数据库会话来注册任务，避免会话冲突
                from app.db.database import SessionLocal
                register_db = SessionLocal()
                try:
                    # 重新查询任务以获取新的会话中的对象
                    task_for_register = register_db.query(ScheduledTask).filter(
                        ScheduledTask.id == task.id
                    ).first()
                    if task_for_register:
                        scheduler_service.register_scheduled_task(register_db, task_for_register)
                        from app.utils.custom_logger import log
                        log.info(f"新任务已动态添加到调度器: {task.name} (ID: {task.id})")
                finally:
                    register_db.close()
            except Exception as e:
                from app.utils.custom_logger import log
                log.error(f"添加任务到调度器失败: {str(e)}")
                # 不影响任务创建，只记录错误

        return task

    @staticmethod
    def update_task(db: Session, task_id: int, task_data: dict) -> Optional[ScheduledTask]:
        """更新定时任务"""
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if task:
            # 记录旧状态
            was_active = task.is_active

            # 更新任务数据
            for key, value in task_data.items():
                setattr(task, key, value)
            db.commit()
            db.refresh(task)

            # 动态更新调度器中的任务
            from app.utils.custom_logger import log
            try:
                # 使用独立的数据库会话来注册任务
                from app.db.database import SessionLocal
                register_db = SessionLocal()
                try:
                    task_for_register = register_db.query(ScheduledTask).filter(
                        ScheduledTask.id == task.id
                    ).first()

                    if task_for_register:
                        if task.is_active:
                            # 任务启用或更新时重新注册
                            scheduler_service.register_scheduled_task(register_db, task_for_register)
                            log.info(f"任务已更新并重新注册到调度器: {task.name} (ID: {task.id})")
                        elif was_active and not task.is_active:
                            # 任务从启用变为禁用时，从调度器移除
                            scheduler_service.unregister_task(task.id)
                            log.info(f"任务已禁用并从调度器移除: {task.name} (ID: {task.id})")
                finally:
                    register_db.close()
            except Exception as e:
                log.error(f"更新调度器任务失败: {str(e)}")

        return task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """删除定时任务"""
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if task:
            task_name = task.name
            db.delete(task)
            db.commit()

            # 从调度器中移除任务
            from app.utils.custom_logger import log
            try:
                scheduler_service.unregister_task(task_id)
                log.info(f"任务已从调度器移除: {task_name} (ID: {task_id})")
            except Exception as e:
                log.error(f"从调度器移除任务失败: {str(e)}")

            return True
        return False

    @staticmethod
    def _parse_task_params(task: ScheduledTask) -> dict:
        """
        解析任务参数

        Args:
            task: 定时任务对象

        Returns:
            解析后的参数字典
        """
        # 从 task.params 字段读取参数
        if task.params:
            if isinstance(task.params, dict):
                return task.params
            elif isinstance(task.params, str):
                import json
                try:
                    return json.loads(task.params)
                except json.JSONDecodeError:
                    pass

        # 如果没有参数或解析失败，返回空字典
        return {}

    @staticmethod
    def trigger_task(db: Session, task_id: int) -> dict:
        """手动触发任务"""
        import asyncio
        from app.utils.custom_logger import log

        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if not task:
            return {"success": False, "error": "任务不存在"}

        try:
            log.info(f"手动触发任务 {task_id} (类型: {task.task_type})")

            # 解析任务参数
            task_params = SchedulerManagerService._parse_task_params(task)

            # 执行任务
            result = asyncio.run(
                scheduler_service.execute_task(
                    task_id=task.id,
                    task_type=task.task_type,
                    task_params=task_params,
                    db=db
                )
            )

            # 更新最后运行时间
            task.last_run_time = datetime.utcnow()
            db.commit()

            log.info(f"任务 {task_id} 执行完成: {result.success}")

            return {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "error": result.error
            }

        except Exception as e:
            log.exception(f"手动触发任务 {task_id} 时发生异常")
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

    @staticmethod
    def reload_tasks(db: Session) -> dict:
        """
        重新加载调度器中的所有任务

        此方法会：
        1. 清除调度器中的所有现有任务
        2. 从数据库重新加载所有启用的任务

        Args:
            db: 数据库会话

        Returns:
            dict: 包含重载结果的字典
        """
        from app.utils.custom_logger import log

        try:
            # 获取当前调度器中的任务
            existing_jobs = scheduler_service.scheduler.get_jobs()
            job_ids = [job.id for job in existing_jobs]

            # 移除所有现有任务
            for job_id in job_ids:
                scheduler_service.scheduler.remove_job(job_id)

            # 重新加载任务
            loaded_count = scheduler_service.load_tasks_from_db(db)

            log.info(f"调度器任务重载完成: 移除了 {len(job_ids)} 个旧任务, 加载了 {loaded_count} 个新任务")

            return {
                "success": True,
                "message": f"已重新加载 {loaded_count} 个任务",
                "removed_count": len(job_ids),
                "loaded_count": loaded_count
            }

        except Exception as e:
            log.error(f"重载调度器任务失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# 全局服务实例
scheduler_manager_service = SchedulerManagerService()
