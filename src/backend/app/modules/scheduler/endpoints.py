from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.modules.scheduler.services import scheduler_manager_service
from app.modules.scheduler.schemas import (
    TaskCreate, TaskUpdate, TaskRead,
    TaskExecution, SchedulerStatus
)
from app.db.database import get_db
from app.core.permissions import require_permission, Permission
from app.modules.shared.deps import get_current_user

router = APIRouter(tags=["scheduler"])

@router.get("/tasks")
@require_permission(Permission.SCHEDULER_READ)
async def get_task_list(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取定时任务列表"""
    return scheduler_manager_service.get_task_list(db, page, page_size)

@router.get("/tasks/{id}", response_model=TaskRead)
@require_permission(Permission.SCHEDULER_READ)
async def get_task_detail(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取任务详情"""
    task = scheduler_manager_service.get_task_detail(db, id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@router.post("/tasks", response_model=TaskRead)
@require_permission(Permission.SCHEDULER_CREATE)
async def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """创建定时任务"""
    # 处理前端字段兼容性
    task_data = task.model_dump()
    # 移除前端兼容字段（它们已经通过验证器映射到task_type了）
    task_data.pop('job_type', None)
    task_data.pop('job_params', None)
    return scheduler_manager_service.create_task(db, task_data)

@router.put("/tasks/{id}", response_model=TaskRead)
@require_permission(Permission.SCHEDULER_UPDATE)
async def update_task(id: int, task: TaskUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """更新定时任务"""
    updated_task = scheduler_manager_service.update_task(db, id, task.dict(exclude_unset=True))
    if not updated_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return updated_task

@router.delete("/tasks/{id}")
@require_permission(Permission.SCHEDULER_DELETE)
async def delete_task(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """删除定时任务"""
    success = scheduler_manager_service.delete_task(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务已删除"}

@router.post("/tasks/{id}/trigger")
@require_permission(Permission.SCHEDULER_EXECUTE)
async def trigger_task(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """手动触发任务"""
    result = scheduler_manager_service.trigger_task(db, id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@router.get("/executions", response_model=list[TaskExecution])
@require_permission(Permission.SCHEDULER_READ)
async def get_execution_history(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取执行历史"""
    return scheduler_manager_service.get_execution_history(db)

@router.post("/start")
@require_permission(Permission.SCHEDULER_EXECUTE)
async def start_scheduler(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """启动调度器"""
    return scheduler_manager_service.start_scheduler()

@router.post("/stop")
@require_permission(Permission.SCHEDULER_EXECUTE)
async def stop_scheduler(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """停止调度器"""
    return scheduler_manager_service.stop_scheduler()

@router.get("/status", response_model=SchedulerStatus)
@require_permission(Permission.SCHEDULER_READ)
async def get_scheduler_status(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取调度器状态"""
    return scheduler_manager_service.get_scheduler_status()
