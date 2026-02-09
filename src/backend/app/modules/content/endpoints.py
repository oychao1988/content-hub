from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict
from app.modules.content.services import content_service
from app.modules.content.schemas import (
    ContentCreateRequest, ContentUpdate, ContentRead, ContentListRead,
    SubmitReviewRequest, ApproveRequest, RejectRequest, ReviewStatistics,
    PaginatedContentList
)
from app.db.database import get_db
from app.core.permissions import require_permission, Permission
from app.modules.shared.deps import get_current_user
from app.models import ContentGenerationTask
from app.services.webhook_handler import WebhookHandler, get_webhook_handler
from app.utils.webhook_signature import create_verifier
from app.core.config import settings
from app.utils.custom_logger import log

router = APIRouter(tags=["content"])

@router.get("/", response_model=PaginatedContentList)
@require_permission(Permission.CONTENT_READ)
async def get_content_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取内容列表（分页）"""
    return content_service.get_content_list(db, page, page_size)

@router.get("/{id}", response_model=ContentRead)
@require_permission(Permission.CONTENT_READ)
async def get_content_detail(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取内容详情"""
    content = content_service.get_content_detail(db, id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.post("/", response_model=ContentRead)
@require_permission(Permission.CONTENT_CREATE)
async def create_content(request: ContentCreateRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """创建内容（调用 content-creator）"""
    try:
        return content_service.create_content(db, request.dict(), current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{id}", response_model=ContentRead)
@require_permission(Permission.CONTENT_UPDATE)
async def update_content(id: int, content: ContentUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """更新内容"""
    updated_content = content_service.update_content(db, id, content.dict(exclude_unset=True))
    if not updated_content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return updated_content

@router.delete("/{id}")
@require_permission(Permission.CONTENT_DELETE)
async def delete_content(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """删除内容"""
    success = content_service.delete_content(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="内容不存在")
    return {"message": "内容已删除"}

@router.post("/{id}/submit-review", response_model=ContentRead)
@require_permission(Permission.CONTENT_UPDATE)
async def submit_for_review(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """提交审核"""
    content = content_service.submit_for_review(db, id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.post("/{id}/approve", response_model=ContentRead)
@require_permission(Permission.CONTENT_PUBLISH)
async def approve_content(id: int, request: ApproveRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """审核通过"""
    content = content_service.approve_content(db, id, request.reviewer_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.post("/{id}/reject", response_model=ContentRead)
@require_permission(Permission.CONTENT_PUBLISH)
async def reject_content(id: int, request: RejectRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """审核拒绝"""
    content = content_service.reject_content(db, id, request.reason, request.reviewer_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.get("/review", response_model=list[ContentListRead])
@require_permission(Permission.CONTENT_PUBLISH)
async def get_pending_reviews(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取待审核列表"""
    return content_service.get_pending_reviews(db)

@router.get("/review/statistics", response_model=ReviewStatistics)
@require_permission(Permission.CONTENT_PUBLISH)
async def get_review_statistics(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取审核统计信息"""
    return content_service.get_review_statistics(db)


# ==================== Webhook 回调端点 ====================

@router.post("/callback/{task_id}", tags=["webhooks"])
async def handle_webhook_callback(
    task_id: str,
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    webhook_handler: WebhookHandler = Depends(get_webhook_handler)
):
    """
    接收 content-creator 的 Webhook 回调

    此端点用于接收来自 content-creator 的异步任务完成通知，支持以下事件类型：
    - completed: 任务成功完成
    - failed: 任务失败
    - progress: 任务进度更新

    **请求处理流程**:
    1. 从数据库查询任务记录
    2. 验证签名（如果启用）
    3. 检查任务状态（幂等性验证）
    4. 根据 event 类型调用对应的处理方法

    **签名验证**:
    - 当 `WEBHOOK_REQUIRE_SIGNATURE=True` 时，必须提供有效的签名
    - 签名位于 Header: `X-Webhook-Signature`
    - 签名算法：HMAC-SHA256 + Base64 编码

    **幂等性保证**:
    - 已完成的任务（completed/failed/timeout/cancelled）不会被重复处理
    - 重复回调会返回成功响应，但不执行任何操作

    **错误处理**:
    - 404: 任务不存在
    - 401: 签名验证失败
    - 403: 签名缺失（当要求签名时）
    - 400: 请求体格式错误

    Args:
        task_id: 任务 ID（URL 路径参数）
        request: FastAPI Request 对象（用于读取请求体）
        db: 数据库会话（依赖注入）
        x_webhook_signature: Webhook 签名（从 Header 中获取）
        webhook_handler: Webhook 处理器（依赖注入）

    Returns:
        成功响应: {"success": true, "message": "Callback processed"}
        幂等响应: {"success": true, "message": "Task already processed"}
        失败响应: {"success": false, "message": "Error message"}

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/content/callback/task-123456789abc \\
          -H "Content-Type: application/json" \\
          -H "X-Webhook-Signature: YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=" \\
          -d '{
            "event": "completed",
            "taskId": "task-123456789abc",
            "workflowType": "content-creator",
            "status": "completed",
            "timestamp": "2026-02-08T12:00:00Z",
            "metadata": {
              "topic": "文章主题",
              "requirements": "创作要求"
            },
            "result": {
              "content": "文章内容...",
              "htmlContent": "<p>文章HTML</p>",
              "images": ["path/to/image1.jpg"],
              "qualityScore": 8.5,
              "wordCount": 1500
            }
          }'
        ```
    """
    try:
        # 1. 读取请求体
        try:
            callback_data = await request.json()
        except Exception as e:
            log.error(f"Failed to parse webhook request body: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request body: {str(e)}"
            )

        # 记录接收到的 Webhook 请求
        log.info(
            f"Received webhook callback for task {task_id}: "
            f"event={callback_data.get('event')}, "
            f"status={callback_data.get('status')}"
        )

        # 2. 从数据库查询任务记录
        task = db.query(ContentGenerationTask).filter(
            ContentGenerationTask.task_id == task_id
        ).first()

        if not task:
            log.warning(f"Webhook callback: Task not found: {task_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Task not found: {task_id}"
            )

        # 3. 签名验证（如果启用）
        if settings.WEBHOOK_REQUIRE_SIGNATURE:
            # 检查签名是否存在
            if not x_webhook_signature:
                log.warning(f"Webhook callback: Missing signature for task {task_id}")
                raise HTTPException(
                    status_code=403,
                    detail="Signature is required but not provided"
                )

            # 检查密钥是否配置
            if not settings.WEBHOOK_SECRET_KEY:
                log.error("Webhook signature verification is enabled but WEBHOOK_SECRET_KEY is not configured")
                raise HTTPException(
                    status_code=500,
                    detail="Server configuration error: signature verification not properly configured"
                )

            # 验证签名
            verifier = create_verifier(
                secret=settings.WEBHOOK_SECRET_KEY,
                require_signature=True
            )

            # 构造请求头字典
            headers = {"X-Webhook-Signature": x_webhook_signature}

            # 验证签名
            is_valid = verifier.verify_from_headers(headers, callback_data)

            if not is_valid:
                log.warning(f"Webhook callback: Invalid signature for task {task_id}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid signature"
                )

            log.info(f"Webhook signature verified successfully for task {task_id}")

        # 4. 提取事件类型
        event = callback_data.get("event")

        if not event:
            log.error(f"Webhook callback: Missing event type for task {task_id}")
            raise HTTPException(
                status_code=400,
                detail="Missing required field: event"
            )

        # 5. 根据 event 类型调用对应的处理方法
        result = None

        if event == "completed":
            # 处理任务完成事件
            result_data = callback_data.get("result", {})
            result = await webhook_handler.handle_task_completed(
                db=db,
                task=task,
                result=result_data
            )

        elif event == "failed":
            # 处理任务失败事件
            error_data = callback_data.get("error", {})
            result = await webhook_handler.handle_task_failed(
                db=db,
                task=task,
                error=error_data
            )

        elif event == "progress":
            # 处理任务进度更新事件
            progress_data = callback_data.get("progress", {})
            result = await webhook_handler.handle_task_progress(
                db=db,
                task=task,
                progress=progress_data
            )

        else:
            # 未知的事件类型
            log.warning(f"Webhook callback: Unknown event type '{event}' for task {task_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Unknown event type: {event}"
            )

        # 6. 记录处理结果
        if result.get("success"):
            if result.get("skipped"):
                log.info(
                    f"Webhook callback processed (idempotent): task {task_id}, "
                    f"message={result.get('message')}"
                )
            else:
                log.info(
                    f"Webhook callback processed successfully: task {task_id}, "
                    f"message={result.get('message')}"
                )
        else:
            log.error(
                f"Webhook callback processing failed: task {task_id}, "
                f"message={result.get('message')}"
            )

        # 7. 返回响应
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Callback processed"),
            **({"details": result.get("details")} if result.get("details") else {})
        }

    except HTTPException:
        # 重新抛出 HTTP 异常（不修改）
        raise
    except Exception as e:
        # 捕获所有未预期的异常
        log.error(
            f"Unexpected error handling webhook callback for task {task_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
