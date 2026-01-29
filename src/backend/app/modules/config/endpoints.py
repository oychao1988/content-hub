"""
系统配置模块 API 端点
提供写作风格和内容主题的 RESTful API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.modules.config.services import writing_style_service, content_theme_service
from app.modules.config.schemas import (
    WritingStyleCreate, WritingStyleUpdate, WritingStyleResponse,
    ContentThemeCreate, ContentThemeUpdate, ContentThemeResponse
)
from app.core.permissions import require_permission, Permission, require_role
from app.modules.shared.deps import get_current_user

router = APIRouter(prefix="/config", tags=["config"])


# ============= 写作风格相关端点 =============

@router.get("/writing-styles", response_model=List[WritingStyleResponse])
@require_permission(Permission.WRITING_STYLE_READ)
async def get_writing_styles(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回记录数"),
    is_system: bool = Query(None, description="筛选系统级风格"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取写作风格列表"""
    if is_system is not None:
        if is_system:
            styles = writing_style_service.get_system_writing_styles(db)
        else:
            styles = writing_style_service.get_custom_writing_styles(db)
    else:
        styles = writing_style_service.get_writing_styles(db, skip, limit)
    return styles


@router.get("/writing-styles/{style_id}", response_model=WritingStyleResponse)
@require_permission(Permission.WRITING_STYLE_READ)
async def get_writing_style(
    style_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取写作风格详情"""
    style = writing_style_service.get_writing_style_by_id(db, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="写作风格不存在")
    return style


@router.post("/writing-styles", response_model=WritingStyleResponse)
@require_permission(Permission.WRITING_STYLE_CREATE)
async def create_writing_style(
    style: WritingStyleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建写作风格（需要管理员权限）"""
    try:
        return writing_style_service.create_writing_style(db, style.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/writing-styles/{style_id}", response_model=WritingStyleResponse)
@require_permission(Permission.WRITING_STYLE_UPDATE)
async def update_writing_style(
    style_id: int,
    style: WritingStyleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新写作风格"""
    try:
        updated_style = writing_style_service.update_writing_style(
            db, style_id, style.dict(exclude_unset=True)
        )
        if not updated_style:
            raise HTTPException(status_code=404, detail="写作风格不存在")
        return updated_style
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/writing-styles/{style_id}")
@require_permission(Permission.WRITING_STYLE_DELETE)
async def delete_writing_style(
    style_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除写作风格（需要管理员权限）"""
    try:
        success = writing_style_service.delete_writing_style(db, style_id)
        if not success:
            raise HTTPException(status_code=404, detail="写作风格不存在")
        return {"message": "写作风格已删除"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ============= 内容主题相关端点 =============

@router.get("/content-themes", response_model=List[ContentThemeResponse])
@require_permission(Permission.CONTENT_THEME_READ)
async def get_content_themes(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回记录数"),
    is_system: bool = Query(None, description="筛选系统级主题"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取内容主题列表"""
    if is_system is not None:
        if is_system:
            themes = content_theme_service.get_system_content_themes(db)
        else:
            themes = content_theme_service.get_custom_content_themes(db)
    else:
        themes = content_theme_service.get_content_themes(db, skip, limit)
    return themes


@router.get("/content-themes/{theme_id}", response_model=ContentThemeResponse)
@require_permission(Permission.CONTENT_THEME_READ)
async def get_content_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取内容主题详情"""
    theme = content_theme_service.get_content_theme_by_id(db, theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="内容主题不存在")
    return theme


@router.post("/content-themes", response_model=ContentThemeResponse)
@require_permission(Permission.CONTENT_THEME_CREATE)
async def create_content_theme(
    theme: ContentThemeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建内容主题（需要管理员权限）"""
    try:
        return content_theme_service.create_content_theme(db, theme.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/content-themes/{theme_id}", response_model=ContentThemeResponse)
@require_permission(Permission.CONTENT_THEME_UPDATE)
async def update_content_theme(
    theme_id: int,
    theme: ContentThemeUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新内容主题"""
    try:
        updated_theme = content_theme_service.update_content_theme(
            db, theme_id, theme.dict(exclude_unset=True)
        )
        if not updated_theme:
            raise HTTPException(status_code=404, detail="内容主题不存在")
        return updated_theme
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/content-themes/{theme_id}")
@require_permission(Permission.CONTENT_THEME_DELETE)
async def delete_content_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除内容主题（需要管理员权限）"""
    try:
        success = content_theme_service.delete_content_theme(db, theme_id)
        if not success:
            raise HTTPException(status_code=404, detail="内容主题不存在")
        return {"message": "内容主题已删除"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
